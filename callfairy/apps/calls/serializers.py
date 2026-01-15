"""
Serializers for Bland AI call management.
"""
from rest_framework import serializers
from .models import Contact, Call, BatchCall, CallLog, CSVUpload


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model."""
    
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'phone_number', 'email', 'metadata', 
            'tags', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_phone_number(self, value):
        """Validate phone number format (E.164)."""
        if not value.startswith('+'):
            raise serializers.ValidationError("Phone number must be in E.164 format (e.g., +12223334444)")
        return value


class ContactBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk contact creation."""
    
    contacts = serializers.ListField(
        child=ContactSerializer(),
        min_length=1
    )


class CallLogSerializer(serializers.ModelSerializer):
    """Serializer for CallLog model."""
    
    class Meta:
        model = CallLog
        fields = ['id', 'event_type', 'message', 'data', 'created_at']
        read_only_fields = ['id', 'created_at']


class CallSerializer(serializers.ModelSerializer):
    """Serializer for Call model."""
    
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    logs = CallLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = Call
        fields = [
            'id', 'phone_number', 'task', 'voice', 'model', 'first_sentence',
            'max_duration', 'record', 'wait_for_greeting', 'status', 'bland_call_id',
            'duration', 'recording_url', 'transcript', 'analysis', 'metadata',
            'config', 'error_message', 'contact', 'contact_name', 'batch',
            'created_at', 'updated_at', 'started_at', 'ended_at', 'logs'
        ]
        read_only_fields = [
            'id', 'status', 'bland_call_id', 'duration', 'recording_url',
            'transcript', 'analysis', 'error_message', 'created_at', 
            'updated_at', 'started_at', 'ended_at', 'logs'
        ]
    
    def validate_phone_number(self, value):
        """Validate phone number format (E.164)."""
        if not value.startswith('+'):
            raise serializers.ValidationError("Phone number must be in E.164 format (e.g., +12223334444)")
        return value


class CallCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a single call."""
    
    class Meta:
        model = Call
        fields = [
            'phone_number', 'task', 'voice', 'model', 'first_sentence',
            'max_duration', 'record', 'wait_for_greeting', 'contact',
            'metadata', 'config'
        ]
    
    def validate_phone_number(self, value):
        """Validate phone number format (E.164)."""
        if not value.startswith('+'):
            raise serializers.ValidationError("Phone number must be in E.164 format (e.g., +12223334444)")
        return value


class BatchCallSerializer(serializers.ModelSerializer):
    """Serializer for BatchCall model."""
    
    calls = CallSerializer(many=True, read_only=True)
    calls_count = serializers.IntegerField(source='calls.count', read_only=True)
    
    class Meta:
        model = BatchCall
        fields = [
            'id', 'label', 'base_prompt', 'voice', 'model', 'max_duration',
            'record', 'wait_for_greeting', 'status', 'bland_batch_id',
            'total_contacts', 'successful_calls', 'failed_calls', 'config',
            'created_at', 'updated_at', 'started_at', 'completed_at',
            'calls', 'calls_count'
        ]
        read_only_fields = [
            'id', 'status', 'bland_batch_id', 'total_contacts', 
            'successful_calls', 'failed_calls', 'created_at', 'updated_at',
            'started_at', 'completed_at', 'calls', 'calls_count'
        ]


class BatchCallCreateSerializer(serializers.Serializer):
    """Serializer for creating a batch call campaign."""
    
    label = serializers.CharField(max_length=255)
    base_prompt = serializers.CharField()
    contact_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of contact IDs to call"
    )
    
    # Optional Bland AI configuration
    voice = serializers.CharField(max_length=50, required=False, allow_null=True)
    model = serializers.ChoiceField(choices=['base', 'turbo'], default='base', required=False)
    max_duration = serializers.IntegerField(required=False, allow_null=True)
    record = serializers.BooleanField(default=True, required=False)
    wait_for_greeting = serializers.BooleanField(default=False, required=False)
    config = serializers.JSONField(required=False, default=dict)
    
    def validate_contact_ids(self, value):
        """Validate that all contact IDs exist and belong to the user."""
        user = self.context['request'].user
        existing_ids = Contact.objects.filter(
            id__in=value,
            user=user
        ).values_list('id', flat=True)
        
        if len(existing_ids) != len(value):
            missing = set(value) - set(existing_ids)
            raise serializers.ValidationError(
                f"Invalid or unauthorized contact IDs: {missing}"
            )
        return value


class CSVUploadSerializer(serializers.ModelSerializer):
    """Serializer for CSV upload."""
    
    class Meta:
        model = CSVUpload
        fields = [
            'id', 'file', 'filename', 'status', 'total_rows',
            'successful_imports', 'failed_imports', 'error_log',
            'created_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'filename', 'status', 'total_rows', 'successful_imports',
            'failed_imports', 'error_log', 'created_at', 'processed_at'
        ]
    
    def validate_file(self, value):
        """Validate that the uploaded file is a CSV."""
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are allowed.")
        return value


class CallStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating call status from webhook."""
    
    call_id = serializers.CharField()
    status = serializers.CharField()
    duration = serializers.IntegerField(required=False)
    recording_url = serializers.URLField(required=False)
    transcript = serializers.CharField(required=False, allow_blank=True)
    analysis = serializers.JSONField(required=False)
