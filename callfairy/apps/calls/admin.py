"""
Admin configuration for calls app.
"""
from django.contrib import admin
from .models import Contact, Call, BatchCall, CallLog, CSVUpload


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Admin for Contact model."""
    
    list_display = ['name', 'phone_number', 'email', 'user', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['name', 'phone_number', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('id', 'user', 'name', 'phone_number', 'email')
        }),
        ('Additional Data', {
            'fields': ('metadata', 'tags')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class CallLogInline(admin.TabularInline):
    """Inline admin for CallLog."""
    model = CallLog
    extra = 0
    readonly_fields = ['event_type', 'message', 'data', 'created_at']
    can_delete = False


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    """Admin for Call model."""
    
    list_display = [
        'phone_number', 'status', 'user', 'batch', 
        'created_at', 'duration', 'bland_call_id'
    ]
    list_filter = ['status', 'created_at', 'user', 'model']
    search_fields = ['phone_number', 'bland_call_id', 'task']
    readonly_fields = [
        'id', 'bland_call_id', 'status', 'duration', 'recording_url',
        'transcript', 'analysis', 'error_message', 'created_at', 
        'updated_at', 'started_at', 'ended_at'
    ]
    inlines = [CallLogInline]
    
    fieldsets = (
        ('Call Information', {
            'fields': ('id', 'user', 'contact', 'batch', 'phone_number', 'task')
        }),
        ('Configuration', {
            'fields': ('voice', 'model', 'first_sentence', 'max_duration', 
                      'record', 'wait_for_greeting', 'config')
        }),
        ('Status & Results', {
            'fields': ('status', 'bland_call_id', 'duration', 'recording_url',
                      'transcript', 'analysis', 'error_message')
        }),
        ('Additional Data', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'started_at', 'ended_at')
        }),
    )


@admin.register(BatchCall)
class BatchCallAdmin(admin.ModelAdmin):
    """Admin for BatchCall model."""
    
    list_display = [
        'label', 'status', 'user', 'total_contacts', 
        'successful_calls', 'failed_calls', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'user', 'model']
    search_fields = ['label', 'bland_batch_id', 'base_prompt']
    readonly_fields = [
        'id', 'bland_batch_id', 'status', 'total_contacts',
        'successful_calls', 'failed_calls', 'created_at', 
        'updated_at', 'started_at', 'completed_at'
    ]
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('id', 'user', 'label', 'base_prompt')
        }),
        ('Configuration', {
            'fields': ('voice', 'model', 'max_duration', 'record', 
                      'wait_for_greeting', 'config')
        }),
        ('Status & Results', {
            'fields': ('status', 'bland_batch_id', 'total_contacts',
                      'successful_calls', 'failed_calls')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'started_at', 'completed_at')
        }),
    )


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    """Admin for CallLog model."""
    
    list_display = ['call', 'event_type', 'message', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['message', 'call__phone_number', 'call__bland_call_id']
    readonly_fields = ['id', 'call', 'event_type', 'message', 'data', 'created_at']
    
    def has_add_permission(self, request):
        """Prevent manual creation of logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of logs."""
        return False


@admin.register(CSVUpload)
class CSVUploadAdmin(admin.ModelAdmin):
    """Admin for CSVUpload model."""
    
    list_display = [
        'filename', 'user', 'status', 'total_rows',
        'successful_imports', 'failed_imports', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'user']
    search_fields = ['filename', 'user__email']
    readonly_fields = [
        'id', 'filename', 'status', 'total_rows', 'successful_imports',
        'failed_imports', 'error_log', 'created_at', 'processed_at'
    ]
    
    fieldsets = (
        ('Upload Information', {
            'fields': ('id', 'user', 'file', 'filename')
        }),
        ('Processing Status', {
            'fields': ('status', 'total_rows', 'successful_imports', 
                      'failed_imports', 'error_log')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at')
        }),
    )
