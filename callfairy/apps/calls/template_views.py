"""
Template-based views for the calls app frontend.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import Contact, Call, BatchCall, CSVUpload, CallLog
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def dashboard_view(request):
    """Dashboard with statistics and recent activity."""
    user = request.user
    
    # Calculate statistics
    total_contacts = Contact.objects.filter(user=user).count()
    total_calls = Call.objects.filter(user=user).count()
    total_batches = BatchCall.objects.filter(user=user).count()
    
    completed_calls = Call.objects.filter(user=user, status='completed').count()
    success_rate = round((completed_calls / total_calls * 100) if total_calls > 0 else 0, 1)
    
    # Recent activity
    recent_calls = Call.objects.filter(user=user).order_by('-created_at')[:5]
    recent_batches = BatchCall.objects.filter(user=user).order_by('-created_at')[:5]
    
    context = {
        'stats': {
            'total_contacts': total_contacts,
            'total_calls': total_calls,
            'total_batches': total_batches,
            'success_rate': success_rate,
        },
        'recent_calls': recent_calls,
        'recent_batches': recent_batches,
    }
    
    return render(request, 'calls/dashboard.html', context)


@login_required
def make_call_view(request):
    """Make a single call."""
    if request.method == 'POST':
        # Handle form submission
        try:
            import sys
            import os
            from django.conf import settings
            
            # Import BlandClient from utils
            sys.path.insert(0, str(settings.BASE_DIR.parent))
            from utils import BlandClient, BlandApiError
            
            phone_number = request.POST.get('phone_number')
            task = request.POST.get('task')
            contact_id = request.POST.get('contact_id')
            voice = request.POST.get('voice', '')
            model = request.POST.get('model', 'turbo')
            max_duration = request.POST.get('max_duration')
            record = request.POST.get('record') == 'on'
            
            # Create Call record
            call = Call.objects.create(
                user=request.user,
                phone_number=phone_number,
                task=task,
                voice=voice,
                model=model,
                max_duration=max_duration,
                record=record,
                status='initiated',
                started_at=timezone.now()
            )
            
            # Call Bland API directly (no Celery for single calls)
            client = BlandClient()
            
            call_params = {
                'phone_number': phone_number,
                'task': task,
                'record': record,
            }
            
            if voice:
                call_params['voice'] = voice
            if model:
                call_params['model'] = model
            if max_duration:
                call_params['max_duration'] = max_duration
            
            # Send the call immediately
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
            
            messages.success(request, f'Call initiated successfully! Call ID: {call.bland_call_id}')
            return redirect('calls_list')
            
        except BlandApiError as e:
            call.status = 'failed'
            call.error_message = str(e)
            call.save()
            messages.error(request, f'Bland AI Error: {str(e)}')
            return redirect('calls_list')
            
        except Exception as e:
            if 'call' in locals():
                call.status = 'failed'
                call.error_message = str(e)
                call.save()
            messages.error(request, f'Error initiating call: {str(e)}')
    
    # GET request - check for contact_id or phone in query params
    context = {}
    contact_id = request.GET.get('contact')
    phone = request.GET.get('phone')
    
    if contact_id:
        try:
            contact = Contact.objects.get(id=contact_id, user=request.user)
            context['prefilled_phone'] = contact.phone_number
            context['contact_name'] = contact.name
        except Contact.DoesNotExist:
            pass
    elif phone:
        context['prefilled_phone'] = phone
    
    return render(request, 'calls/make_call.html', context)


@login_required
def contacts_list_view(request):
    """List all contacts."""
    return render(request, 'calls/contacts_list.html')


@login_required
def calls_list_view(request):
    """List all calls."""
    calls = Call.objects.filter(user=request.user).select_related('contact').order_by('-created_at')
    return render(request, 'calls/calls_list.html', {'calls': calls})


@login_required
def batches_list_view(request):
    """List all batch campaigns."""
    batches = BatchCall.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'calls/batches_list.html', {'batches': batches})


@login_required
def batch_detail_view(request, batch_id):
    """View details of a specific batch campaign."""
    from django.shortcuts import get_object_or_404
    
    batch = get_object_or_404(BatchCall, id=batch_id, user=request.user)
    calls = Call.objects.filter(batch=batch).select_related('contact').order_by('created_at')
    
    # Calculate statistics
    total_calls = calls.count()
    completed_calls = calls.filter(status='completed').count()
    in_progress_calls = calls.filter(status='in_progress').count()
    failed_calls = calls.filter(status='failed').count()
    queued_calls = calls.filter(status='queued').count()
    
    # Calculate total duration
    total_duration = 0
    for call in calls:
        if call.duration:
            total_duration += call.duration
    
    context = {
        'batch': batch,
        'calls': calls,
        'total_calls': total_calls,
        'completed_calls': completed_calls,
        'in_progress_calls': in_progress_calls,
        'failed_calls': failed_calls,
        'queued_calls': queued_calls,
        'total_duration': total_duration,
    }
    
    return render(request, 'calls/batch_detail.html', context)


@login_required
def create_campaign_view(request):
    """Create a batch campaign."""
    if request.method == 'POST':
        try:
            label = request.POST.get('label')
            base_prompt = request.POST.get('base_prompt')
            contact_ids = request.POST.getlist('contact_ids')
            script_mode = request.POST.get('script_mode', 'same')
            
            # Create batch
            batch = BatchCall.objects.create(
                user=request.user,
                label=label,
                base_prompt=base_prompt if script_mode == 'same' else 'Custom per-contact scripts',
                voice=request.POST.get('voice', ''),
                model=request.POST.get('model', 'turbo'),  # Always use turbo
                max_duration=request.POST.get('max_duration'),
                record=request.POST.get('record') == 'on',
            )
            
            # Create Call objects for each contact
            contacts = Contact.objects.filter(id__in=contact_ids, user=request.user)
            calls = []
            for contact in contacts:
                # Determine the script for this contact
                if script_mode == 'different':
                    # Get per-contact script
                    contact_script_key = f'contact_script_{contact.id}'
                    contact_script = request.POST.get(contact_script_key, batch.base_prompt)
                else:
                    contact_script = batch.base_prompt
                
                calls.append(Call(
                    user=request.user,
                    contact=contact,
                    batch=batch,
                    phone_number=contact.phone_number,
                    task=contact_script,  # Use per-contact script
                    voice=batch.voice,
                    model=batch.model,
                    max_duration=batch.max_duration,
                    record=batch.record,
                ))
            
            Call.objects.bulk_create(calls)
            
            # Trigger Celery task to process batch calls sequentially
            from .tasks import process_batch_call
            process_batch_call.delay(str(batch.id))
            
            messages.success(request, f'Bulk call "{label}" created successfully with {len(calls)} calls!')
            return redirect('batches_list')
        except Exception as e:
            messages.error(request, f'Error creating bulk call: {str(e)}')
    
    contacts = Contact.objects.filter(user=request.user).order_by('name')
    return render(request, 'calls/create_campaign.html', {'contacts': contacts})


@login_required
def import_csv_view(request):
    """Import contacts from CSV."""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        try:
            csv_file = request.FILES['csv_file']
            
            csv_upload = CSVUpload.objects.create(
                user=request.user,
                file=csv_file,
                filename=csv_file.name
            )
            
            # Process CSV (this is handled in the views.py CSVUploadViewSet)
            messages.success(request, 'CSV file uploaded successfully! Processing contacts...')
            return redirect('contacts_list')
        except Exception as e:
            messages.error(request, f'Error uploading CSV: {str(e)}')
    
    return render(request, 'calls/import_csv.html')


@login_required
def users_list_view(request):
    """List all users (SuperUser and SuperAdmin only)."""
    if not request.user.is_superuser_role:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'calls/users_list.html', {'users': users})
