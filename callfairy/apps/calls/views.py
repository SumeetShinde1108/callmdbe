"""
Views for Bland AI call management API.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
import csv
import io

from .models import Contact, Call, BatchCall, CallLog, CSVUpload
from .serializers import (
    ContactSerializer, CallSerializer, BatchCallSerializer,
    CallLogSerializer, CSVUploadSerializer, CallCreateSerializer,
    BatchCallCreateSerializer, ContactBulkCreateSerializer,
    CallStatusUpdateSerializer
)
from .tasks import process_single_call, process_batch_call, update_call_status, update_batch_status


class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing contacts.
    
    Provides CRUD operations for contacts and bulk operations.
    """
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'phone_number', 'email']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter contacts by current user."""
        return Contact.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set user when creating contact."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Bulk create multiple contacts.
        
        POST /api/v1/calls/contacts/bulk_create/
        Body: {"contacts": [{"name": "...", "phone_number": "..."}, ...]}
        """
        serializer = ContactBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contacts = []
        for contact_data in serializer.validated_data['contacts']:
            contacts.append(Contact(user=request.user, **contact_data))
        
        created_contacts = Contact.objects.bulk_create(contacts)
        
        return Response(
            {
                'message': f'{len(created_contacts)} contacts created successfully',
                'contacts': ContactSerializer(created_contacts, many=True).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """
        Bulk delete contacts by IDs.
        
        DELETE /api/v1/calls/contacts/bulk_delete/
        Body: {"ids": ["uuid1", "uuid2", ...]}
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': 'No IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count, _ = Contact.objects.filter(
            id__in=ids,
            user=request.user
        ).delete()
        
        return Response(
            {'message': f'{deleted_count} contacts deleted successfully'},
            status=status.HTTP_200_OK
        )


class CallViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing individual calls.
    
    Provides CRUD operations and call status updates.
    """
    serializer_class = CallSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'batch']
    search_fields = ['phone_number', 'bland_call_id']
    ordering_fields = ['created_at', 'started_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter calls by current user."""
        return Call.objects.filter(user=self.request.user).select_related('contact', 'batch')
    
    def get_serializer_class(self):
        """Use different serializer for creation."""
        if self.action == 'create':
            return CallCreateSerializer
        return CallSerializer
    
    def perform_create(self, serializer):
        """Create call and trigger Celery task."""
        call = serializer.save(user=self.request.user)
        
        # Trigger async task to process the call
        process_single_call.delay(str(call.id))
        
        return call
    
    def create(self, request, *args, **kwargs):
        """Create a new call and initiate it."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        call = self.perform_create(serializer)
        
        return Response(
            {
                'message': 'Call queued successfully',
                'call': CallSerializer(call).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def refresh_status(self, request, pk=None):
        """
        Manually refresh call status from Bland AI.
        
        POST /api/v1/calls/calls/{id}/refresh_status/
        """
        call = self.get_object()
        
        if not call.bland_call_id:
            return Response(
                {'error': 'Call has not been initiated yet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trigger async task to update status
        update_call_status.delay(str(call.id))
        
        return Response(
            {'message': 'Status update queued'},
            status=status.HTTP_202_ACCEPTED
        )
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """
        Get logs for a specific call.
        
        GET /api/v1/calls/calls/{id}/logs/
        """
        call = self.get_object()
        logs = call.logs.all()
        serializer = CallLogSerializer(logs, many=True)
        return Response(serializer.data)


class BatchCallViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing batch calls.
    
    Provides operations for creating and monitoring batch call campaigns.
    """
    serializer_class = BatchCallSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['label', 'bland_batch_id']
    ordering_fields = ['created_at', 'started_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter batches by current user."""
        return BatchCall.objects.filter(user=self.request.user).prefetch_related('calls')
    
    def get_serializer_class(self):
        """Use different serializer for creation."""
        if self.action == 'create':
            return BatchCallCreateSerializer
        return BatchCallSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a batch call campaign.
        
        POST /api/v1/calls/batches/
        Body: {
            "label": "Campaign Name",
            "base_prompt": "Call script...",
            "contact_ids": ["uuid1", "uuid2", ...],
            "voice": "maya",
            "model": "turbo"
        }
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Create batch
        batch = BatchCall.objects.create(
            user=request.user,
            label=serializer.validated_data['label'],
            base_prompt=serializer.validated_data['base_prompt'],
            voice=serializer.validated_data.get('voice'),
            model=serializer.validated_data.get('model', 'base'),
            max_duration=serializer.validated_data.get('max_duration'),
            record=serializer.validated_data.get('record', True),
            wait_for_greeting=serializer.validated_data.get('wait_for_greeting', False),
            config=serializer.validated_data.get('config', {}),
        )
        
        # Create Call objects for each contact
        contacts = Contact.objects.filter(
            id__in=serializer.validated_data['contact_ids'],
            user=request.user
        )
        
        calls = []
        for contact in contacts:
            calls.append(Call(
                user=request.user,
                contact=contact,
                batch=batch,
                phone_number=contact.phone_number,
                task=batch.base_prompt,
                voice=batch.voice,
                model=batch.model,
                max_duration=batch.max_duration,
                record=batch.record,
                wait_for_greeting=batch.wait_for_greeting,
                metadata=contact.metadata,
                config=batch.config,
            ))
        
        Call.objects.bulk_create(calls)
        
        # Trigger async task to process the batch
        process_batch_call.delay(str(batch.id))
        
        return Response(
            {
                'message': 'Batch call campaign created and queued',
                'batch': BatchCallSerializer(batch).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def refresh_status(self, request, pk=None):
        """
        Manually refresh batch status.
        
        POST /api/v1/calls/batches/{id}/refresh_status/
        """
        batch = self.get_object()
        
        if not batch.bland_batch_id:
            return Response(
                {'error': 'Batch has not been initiated yet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trigger async task to update status
        update_batch_status.delay(str(batch.id))
        
        return Response(
            {'message': 'Status update queued'},
            status=status.HTTP_202_ACCEPTED
        )
    
    @action(detail=True, methods=['get'])
    def calls(self, request, pk=None):
        """
        Get all calls for a batch.
        
        GET /api/v1/calls/batches/{id}/calls/
        """
        batch = self.get_object()
        calls = batch.calls.all()
        
        # Apply pagination
        page = self.paginate_queryset(calls)
        if page is not None:
            serializer = CallSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CallSerializer(calls, many=True)
        return Response(serializer.data)


class CSVUploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CSV upload and contact import.
    
    Allows users to upload CSV files to bulk import contacts.
    Intelligently maps various column header formats.
    """
    serializer_class = CSVUploadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    # Add parsers for multipart form data
    from rest_framework.parsers import MultiPartParser, FormParser
    parser_classes = [MultiPartParser, FormParser]
    
    # Flexible column name mappings
    COLUMN_MAPPINGS = {
        'name': ['name', 'full_name', 'fullname', 'customer_name', 'contact_name', 
                 'full name', 'customer name', 'contact name', 'client_name', 
                 'client name', 'person', 'contact', 'first_name', 'firstname'],
        'phone_number': ['phone_number', 'phone', 'phonenumber', 'mobile', 'cell',
                        'phone number', 'mobile_number', 'mobile number', 'cell_number',
                        'cell number', 'telephone', 'tel', 'contact_number', 'number',
                        'phone_no', 'mobile_no'],
        'email': ['email', 'email_address', 'email address', 'e-mail', 'e_mail',
                  'mail', 'contact_email', 'contact email'],
        'tags': ['tags', 'tag', 'category', 'categories', 'label', 'labels', 'type'],
    }
    
    def get_queryset(self):
        """Filter uploads by current user."""
        return CSVUpload.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Handle both validation and import."""
        # Access raw Django request to avoid parser issues
        django_request = request._request if hasattr(request, '_request') else request
        
        # Check for validate_only in POST data or query params
        validate_only_value = django_request.POST.get('validate_only', 'false')
        validate_only = validate_only_value.lower() == 'true'
        
        if validate_only:
            # Validation mode
            return self._validate_csv(request)
        else:
            # Import mode - bypass serializer completely
            csv_file = django_request.FILES.get('csv_file') or django_request.FILES.get('file')
            
            if not csv_file:
                print("ERROR: No CSV file in request.FILES")
                print(f"request.FILES keys: {list(request.FILES.keys())}")
                return Response(
                    {'error': 'No CSV file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file is CSV
            if not csv_file.name.endswith('.csv'):
                return Response(
                    {'error': 'Only CSV files are allowed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                print(f"Creating CSVUpload for file: {csv_file.name}, user: {request.user}")
                
                # Create CSV upload record directly
                csv_upload = CSVUpload.objects.create(
                    user=request.user,
                    file=csv_file,
                    filename=csv_file.name,
                    status='pending'
                )
                
                print(f"CSVUpload created with ID: {csv_upload.id}")
                
                # Process the CSV file
                self._process_csv(csv_upload)
                
                # Refresh to get updated data
                csv_upload.refresh_from_db()
                
                print(f"Processing complete. Status: {csv_upload.status}, Imports: {csv_upload.successful_imports}")
                
                # Return custom response with import results
                return Response(
                    {
                        'message': 'Import completed successfully' if csv_upload.status == 'completed' else 'Import completed with errors',
                        'successful_imports': csv_upload.successful_imports or 0,
                        'failed_imports': csv_upload.failed_imports or 0,
                        'total_rows': csv_upload.total_rows or 0,
                        'status': csv_upload.status,
                        'errors': csv_upload.error_log[:5] if csv_upload.error_log else []
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"CSV Import Error: {error_details}")  # Log full error to console
                return Response(
                    {'error': f'Import failed: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    def perform_create(self, serializer):
        """Process CSV file and create contacts."""
        csv_upload = serializer.save(
            user=self.request.user,
            filename=serializer.validated_data['file'].name
        )
        
        # Process the CSV file
        self._process_csv(csv_upload)
    
    def _validate_csv(self, request):
        """Validate CSV without importing."""
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return Response(
                {'error': 'No CSV file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Read CSV file - seek to beginning first
            csv_file.seek(0)
            file_content = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(file_content))
            
            total_rows = 0
            valid_rows = 0
            invalid_rows = 0
            errors = []
            
            # Get column mappings
            headers = csv_reader.fieldnames or []
            mapped_headers = self._map_headers(headers)
            
            if not mapped_headers.get('name'):
                return Response(
                    {'error': 'Could not find name column. Please include a column for names.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not mapped_headers.get('phone_number'):
                return Response(
                    {'error': 'Could not find phone number column. Please include a column for phone numbers.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate each row
            for row_num, row in enumerate(csv_reader, start=1):
                total_rows += 1
                
                try:
                    # Extract data using flexible mapping
                    name = self._get_mapped_value(row, mapped_headers.get('name', []))
                    phone_number = self._get_mapped_value(row, mapped_headers.get('phone_number', []))
                    
                    # Validate required fields
                    if not name or not name.strip():
                        raise ValueError(f"Row {row_num}: Name is required")
                    
                    if not phone_number or not phone_number.strip():
                        raise ValueError(f"Row {row_num}: Phone number is required")
                    
                    # Validate phone number format
                    phone_number = phone_number.strip()
                    if not phone_number.startswith('+'):
                        raise ValueError(f"Row {row_num}: Phone number must start with + (E.164 format)")
                    
                    valid_rows += 1
                    
                except Exception as e:
                    invalid_rows += 1
                    errors.append(str(e))
            
            return Response({
                'total_rows': total_rows,
                'valid_rows': valid_rows,
                'invalid_rows': invalid_rows,
                'errors': errors[:10],  # Limit to first 10 errors
                'message': 'Validation complete'
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to validate CSV: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _map_headers(self, headers):
        """Map CSV headers to standard field names."""
        mapped = {}
        headers_lower = [h.lower().strip() for h in headers]
        
        for field, variations in self.COLUMN_MAPPINGS.items():
            for variation in variations:
                if variation.lower() in headers_lower:
                    idx = headers_lower.index(variation.lower())
                    original_header = headers[idx]
                    mapped[field] = [original_header]
                    break
        
        return mapped
    
    def _get_mapped_value(self, row, header_options):
        """Get value from row using header options."""
        for header in header_options:
            if header in row:
                value = row[header]
                if value and str(value).strip():
                    return str(value).strip()
        return ''
    
    def _process_csv(self, csv_upload):
        """Process uploaded CSV file and create contacts with flexible header mapping."""
        csv_upload.status = 'processing'
        csv_upload.save()
        
        errors = []
        successful_imports = 0
        failed_imports = 0
        
        try:
            # Read CSV file - seek to beginning first
            csv_upload.file.seek(0)
            file_content = csv_upload.file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(file_content))
            
            # Map headers
            headers = csv_reader.fieldnames or []
            mapped_headers = self._map_headers(headers)
            
            total_rows = 0
            contacts_to_create = []
            
            for row_num, row in enumerate(csv_reader, start=1):
                total_rows += 1
                
                try:
                    # Extract data from CSV using flexible mapping
                    name = self._get_mapped_value(row, mapped_headers.get('name', []))
                    phone_number = self._get_mapped_value(row, mapped_headers.get('phone_number', []))
                    email = self._get_mapped_value(row, mapped_headers.get('email', []))
                    tags_str = self._get_mapped_value(row, mapped_headers.get('tags', []))
                    
                    # Validate required fields
                    if not name or not phone_number:
                        raise ValueError("Name and phone_number are required")
                    
                    # Validate phone number format
                    if not phone_number.startswith('+'):
                        raise ValueError("Phone number must be in E.164 format (e.g., +12223334444)")
                    
                    # Extract metadata (any additional columns not mapped)
                    metadata = {}
                    mapped_keys = []
                    for field_mappings in mapped_headers.values():
                        mapped_keys.extend(field_mappings)
                    
                    for key, value in row.items():
                        if key not in mapped_keys and value:
                            metadata[key] = value
                    
                    # Extract tags if present
                    tags = []
                    if tags_str:
                        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                    
                    contacts_to_create.append(Contact(
                        user=csv_upload.user,
                        name=name,
                        phone_number=phone_number,
                        email=email if email else None,
                        metadata=metadata,
                        tags=tags
                    ))
                    
                    successful_imports += 1
                    
                except Exception as e:
                    failed_imports += 1
                    errors.append({
                        'row': row_num,
                        'error': str(e),
                        'data': row
                    })
            
            # Bulk create contacts
            if contacts_to_create:
                Contact.objects.bulk_create(contacts_to_create)
            
            # Update CSV upload record
            csv_upload.status = 'completed'
            csv_upload.total_rows = total_rows
            csv_upload.successful_imports = successful_imports
            csv_upload.failed_imports = failed_imports
            csv_upload.error_log = errors
            csv_upload.processed_at = timezone.now()
            csv_upload.save()
            
        except Exception as e:
            csv_upload.status = 'failed'
            csv_upload.error_log = [{'error': f'Failed to process CSV: {str(e)}'}]
            csv_upload.save()
