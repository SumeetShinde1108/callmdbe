"""
Celery tasks for Bland AI call processing.
"""
import sys
import os
import time
from celery import shared_task
from django.utils import timezone
from django.conf import settings
import logging

# Add project root to path to import utils
sys.path.insert(0, os.path.join(settings.BASE_DIR.parent))
from utils import BlandClient, BlandApiError

from .models import Call, BatchCall, Contact, CallLog

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_single_call(self, call_id):
    """
    Process a single call using Bland AI.
    
    Args:
        call_id: UUID of the Call instance
    """
    try:
        call = Call.objects.get(id=call_id)
        call.status = 'initiated'
        call.started_at = timezone.now()
        call.save()
        
        # Create log entry
        CallLog.objects.create(
            call=call,
            event_type='task_started',
            message='Celery task started processing call'
        )
        
        # Initialize Bland AI client
        client = BlandClient()
        
        # Prepare call parameters
        call_params = {
            'phone_number': call.phone_number,
            'task': call.task,
            'record': call.record,
        }
        
        # Add optional parameters
        if call.voice:
            call_params['voice'] = call.voice
        if call.model:
            call_params['model'] = call.model
        if call.first_sentence:
            call_params['first_sentence'] = call.first_sentence
        if call.max_duration:
            call_params['max_duration'] = call.max_duration
        if call.wait_for_greeting is not None:
            call_params['wait_for_greeting'] = call.wait_for_greeting
        
        # Add any additional config
        if call.config:
            call_params.update(call.config)
        
        # Send the call
        logger.info(f"Sending call to {call.phone_number}")
        response = client.send_call(**call_params)
        
        # Update call with Bland AI response
        call.bland_call_id = response.get('call_id')
        call.status = 'in_progress'
        call.save()
        
        # Log success
        CallLog.objects.create(
            call=call,
            event_type='call_initiated',
            message='Call successfully initiated with Bland AI',
            data=response
        )
        
        logger.info(f"Call initiated successfully: {call.bland_call_id}")
        return {
            'status': 'success',
            'call_id': str(call.id),
            'bland_call_id': call.bland_call_id
        }
        
    except Call.DoesNotExist:
        logger.error(f"Call {call_id} not found")
        return {'status': 'error', 'message': 'Call not found'}
    
    except BlandApiError as e:
        logger.error(f"Bland AI API error: {e}")
        call.status = 'failed'
        call.error_message = str(e)
        call.save()
        
        CallLog.objects.create(
            call=call,
            event_type='call_failed',
            message=f'Bland AI API error: {str(e)}',
            data={'status_code': e.status_code, 'response': e.response}
        )
        
        # Retry the task if retries are available
        raise self.retry(exc=e, countdown=60)
    
    except Exception as e:
        logger.error(f"Unexpected error processing call: {e}")
        call.status = 'failed'
        call.error_message = str(e)
        call.save()
        
        CallLog.objects.create(
            call=call,
            event_type='call_failed',
            message=f'Unexpected error: {str(e)}'
        )
        
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True, max_retries=3)
def process_batch_call(self, batch_id):
    """
    Process a batch of calls using Bland AI - makes individual calls sequentially.
    
    Args:
        batch_id: UUID of the BatchCall instance
    """
    try:
        batch = BatchCall.objects.get(id=batch_id)
        batch.status = 'processing'
        batch.started_at = timezone.now()
        batch.save()
        
        logger.info(f"Processing batch: {batch.label}")
        
        # Get all calls for this batch
        calls = Call.objects.filter(batch=batch, status='queued').order_by('created_at')
        
        if not calls.exists():
            logger.warning(f"No queued calls found for batch {batch_id}")
            batch.status = 'completed'
            batch.completed_at = timezone.now()
            batch.save()
            return {'status': 'warning', 'message': 'No calls to process'}
        
        # Initialize Bland AI client
        client = BlandClient()
        
        total_calls = calls.count()
        batch.total_contacts = total_calls
        batch.save()
        
        successful_calls = 0
        failed_calls = 0
        
        # Process each call sequentially
        logger.info(f"Processing {total_calls} calls sequentially")
        
        for call in calls:
            try:
                logger.info(f"Processing call {call.id} to {call.phone_number}")
                
                # Update call status
                call.status = 'initiated'
                call.started_at = timezone.now()
                call.save()
                
                # Prepare call parameters
                call_params = {
                    'phone_number': call.phone_number,
                    'task': call.task,
                    'record': call.record if call.record is not None else batch.record,
                }
                
                # Add optional parameters
                if call.voice or batch.voice:
                    call_params['voice'] = call.voice or batch.voice
                if call.model or batch.model:
                    call_params['model'] = call.model or batch.model
                if call.max_duration or batch.max_duration:
                    call_params['max_duration'] = call.max_duration or batch.max_duration
                if call.wait_for_greeting is not None:
                    call_params['wait_for_greeting'] = call.wait_for_greeting
                elif batch.wait_for_greeting is not None:
                    call_params['wait_for_greeting'] = batch.wait_for_greeting
                
                # Send the call
                response = client.send_call(**call_params)
                
                # Update call with Bland AI response
                call.bland_call_id = response.get('call_id')
                call.status = 'in_progress'
                call.save()
                
                successful_calls += 1
                logger.info(f"Call {call.id} initiated successfully: {call.bland_call_id}")
                
                # Create log entry
                CallLog.objects.create(
                    call=call,
                    event_type='call_initiated',
                    message=f'Batch call initiated with Bland AI',
                    data=response
                )
                
                # Add delay between calls to avoid rate limits
                # Wait 3 seconds before next call (adjust if needed)
                if successful_calls < total_calls:  # Don't wait after last call
                    logger.info("Waiting 70 seconds before next call to avoid rate limits...")
                    time.sleep(70)
                
            except BlandApiError as e:
                logger.error(f"Bland API error for call {call.id}: {e}")
                
                # If rate limit error, wait and retry once
                if e.status_code == 429:
                    logger.warning(f"Rate limit hit for call {call.id}. Waiting 10 seconds and retrying...")
                    time.sleep(10)
                    
                    try:
                        # Retry the call
                        response = client.send_call(**call_params)
                        call.bland_call_id = response.get('call_id')
                        call.status = 'in_progress'
                        call.save()
                        successful_calls += 1
                        logger.info(f"Call {call.id} retry successful: {call.bland_call_id}")
                        
                        CallLog.objects.create(
                            call=call,
                            event_type='call_initiated',
                            message=f'Batch call initiated after rate limit retry',
                            data=response
                        )
                        continue  # Skip to next call
                        
                    except Exception as retry_error:
                        logger.error(f"Retry also failed for call {call.id}: {retry_error}")
                
                # Mark call as failed
                call.status = 'failed'
                call.error_message = str(e)
                call.save()
                failed_calls += 1
                
                CallLog.objects.create(
                    call=call,
                    event_type='call_failed',
                    message=f'Bland AI API error: {str(e)}',
                    data={'status_code': e.status_code, 'response': e.response}
                )
                
            except Exception as e:
                logger.error(f"Unexpected error for call {call.id}: {e}")
                call.status = 'failed'
                call.error_message = str(e)
                call.save()
                failed_calls += 1
                
                CallLog.objects.create(
                    call=call,
                    event_type='call_failed',
                    message=f'Unexpected error: {str(e)}'
                )
        
        # Update batch status
        batch.successful_calls = successful_calls
        batch.failed_calls = failed_calls
        batch.status = 'completed'
        batch.completed_at = timezone.now()
        batch.save()
        
        logger.info(f"Batch {batch.label} completed: {successful_calls} successful, {failed_calls} failed")
        
        # Schedule status updates for all in-progress calls after 1 minute
        in_progress_calls = Call.objects.filter(batch=batch, status='in_progress')
        for call in in_progress_calls:
            if call.bland_call_id:
                update_call_status.apply_async(args=[str(call.id)], countdown=60)
                logger.info(f"Scheduled status update for call {call.id} in 60 seconds")
        
        return {
            'status': 'success',
            'batch_id': str(batch.id),
            'total_calls': total_calls,
            'successful': successful_calls,
            'failed': failed_calls
        }
        
    except BatchCall.DoesNotExist:
        logger.error(f"Batch {batch_id} not found")
        return {'status': 'error', 'message': 'Batch not found'}
    
    except Exception as e:
        logger.error(f"Unexpected error processing batch: {e}")
        if 'batch' in locals():
            batch.status = 'failed'
            batch.completed_at = timezone.now()
            batch.save()
        
        return {'status': 'error', 'message': str(e)}


@shared_task
def update_call_status(call_id):
    """
    Fetch and update call status from Bland AI.
    
    Args:
        call_id: UUID of the Call instance
    """
    try:
        call = Call.objects.get(id=call_id)
        
        if not call.bland_call_id:
            logger.warning(f"Call {call_id} has no Bland AI call ID")
            return {'status': 'error', 'message': 'No Bland AI call ID'}
        
        # Initialize Bland AI client
        client = BlandClient()
        
        # Get call details from Bland AI
        response = client.get_call(call.bland_call_id)
        
        # Update call with response data
        status_mapping = {
            'completed': 'completed',
            'failed': 'failed',
            'no-answer': 'no_answer',
            'busy': 'busy',
            'in-progress': 'in_progress',
        }
        
        bland_status = response.get('status', '').lower()
        call.status = status_mapping.get(bland_status, call.status)
        
        # Update call data
        if response.get('duration'):
            call.duration = response.get('duration')
        if response.get('recording_url'):
            call.recording_url = response.get('recording_url')
        if response.get('transcript'):
            call.transcript = response.get('transcript')
        if response.get('analysis'):
            call.analysis = response.get('analysis')
        
        # Set ended_at if call is complete
        if call.status in ['completed', 'failed', 'no_answer', 'busy']:
            if not call.ended_at:
                call.ended_at = timezone.now()
        
        call.save()
        
        # Create log entry
        CallLog.objects.create(
            call=call,
            event_type='status_updated',
            message=f'Call status updated to {call.status}',
            data=response
        )
        
        logger.info(f"Call {call_id} status updated to {call.status}")
        return {'status': 'success', 'call_status': call.status}
        
    except Call.DoesNotExist:
        logger.error(f"Call {call_id} not found")
        return {'status': 'error', 'message': 'Call not found'}
    
    except BlandApiError as e:
        logger.error(f"Bland AI API error: {e}")
        return {'status': 'error', 'message': str(e)}
    
    except Exception as e:
        logger.error(f"Unexpected error updating call status: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def update_batch_status(batch_id):
    """
    Fetch and update batch status from Bland AI.
    
    Args:
        batch_id: UUID of the BatchCall instance
    """
    try:
        batch = BatchCall.objects.get(id=batch_id)
        
        if not batch.bland_batch_id:
            logger.warning(f"Batch {batch_id} has no Bland AI batch ID")
            return {'status': 'error', 'message': 'No Bland AI batch ID'}
        
        # Initialize Bland AI client
        client = BlandClient()
        
        # Get batch details from Bland AI
        response = client.get_batch(batch.bland_batch_id)
        
        # Update batch statistics
        calls = batch.calls.all()
        batch.successful_calls = calls.filter(status='completed').count()
        batch.failed_calls = calls.filter(status__in=['failed', 'no_answer', 'busy']).count()
        
        # Check if batch is complete
        total_processed = batch.successful_calls + batch.failed_calls
        if total_processed >= batch.total_contacts:
            batch.status = 'completed'
            batch.completed_at = timezone.now()
        
        batch.save()
        
        logger.info(f"Batch {batch_id} status updated: {batch.successful_calls}/{batch.total_contacts} successful")
        return {
            'status': 'success',
            'batch_status': batch.status,
            'successful': batch.successful_calls,
            'failed': batch.failed_calls
        }
        
    except BatchCall.DoesNotExist:
        logger.error(f"Batch {batch_id} not found")
        return {'status': 'error', 'message': 'Batch not found'}
    
    except BlandApiError as e:
        logger.error(f"Bland AI API error: {e}")
        return {'status': 'error', 'message': str(e)}
    
    except Exception as e:
        logger.error(f"Unexpected error updating batch status: {e}")
        return {'status': 'error', 'message': str(e)}
