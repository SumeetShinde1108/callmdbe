"""
Models for Bland AI call management.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Contact(models.Model):
    """Model to store contacts for calls."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    
    # Contact Information
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, help_text="E.164 format (e.g., +12223334444)")
    email = models.EmailField(blank=True, null=True)
    
    # Additional Data
    metadata = models.JSONField(default=dict, blank=True, help_text="Custom metadata for the contact")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing contacts")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'phone_number']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.phone_number}"


class BatchCall(models.Model):
    """Model to track batch call campaigns."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='batch_calls')
    
    # Batch Information
    label = models.CharField(max_length=255, help_text="Label for the batch")
    base_prompt = models.TextField(help_text="Base prompt/task for all calls")
    
    # Bland AI Configuration
    voice = models.CharField(max_length=50, blank=True, null=True)
    model = models.CharField(max_length=20, default='base', choices=[('base', 'Base'), ('turbo', 'Turbo')])
    max_duration = models.IntegerField(blank=True, null=True, help_text="Maximum call duration in minutes")
    record = models.BooleanField(default=True)
    wait_for_greeting = models.BooleanField(default=False)
    
    # Status & Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    bland_batch_id = models.CharField(max_length=255, blank=True, null=True, help_text="Bland AI batch ID")
    total_contacts = models.IntegerField(default=0)
    successful_calls = models.IntegerField(default=0)
    failed_calls = models.IntegerField(default=0)
    
    # Additional Configuration
    config = models.JSONField(default=dict, blank=True, help_text="Additional Bland AI configuration")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.label} - {self.status}"


class Call(models.Model):
    """Model to track individual calls."""
    
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('no_answer', 'No Answer'),
        ('busy', 'Busy'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calls')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='calls')
    batch = models.ForeignKey(BatchCall, on_delete=models.SET_NULL, null=True, blank=True, related_name='calls')
    
    # Call Information
    phone_number = models.CharField(max_length=20)
    task = models.TextField(help_text="Instructions for the AI agent")
    
    # Bland AI Configuration
    voice = models.CharField(max_length=50, blank=True, null=True)
    model = models.CharField(max_length=20, default='base')
    first_sentence = models.TextField(blank=True, null=True)
    max_duration = models.IntegerField(blank=True, null=True)
    record = models.BooleanField(default=True)
    wait_for_greeting = models.BooleanField(default=False)
    
    # Status & Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    bland_call_id = models.CharField(max_length=255, blank=True, null=True, help_text="Bland AI call ID")
    
    # Call Data
    duration = models.IntegerField(blank=True, null=True, help_text="Call duration in seconds")
    recording_url = models.URLField(blank=True, null=True)
    transcript = models.TextField(blank=True, null=True)
    analysis = models.JSONField(default=dict, blank=True, help_text="AI analysis results")
    metadata = models.JSONField(default=dict, blank=True, help_text="Custom metadata")
    
    # Additional Configuration
    config = models.JSONField(default=dict, blank=True, help_text="Additional Bland AI configuration")
    
    # Error Handling
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['bland_call_id']),
            models.Index(fields=['batch', 'status']),
        ]
    
    def __str__(self):
        return f"Call to {self.phone_number} - {self.status}"


class CallLog(models.Model):
    """Model to store detailed call logs and events."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name='logs')
    
    # Log Information
    event_type = models.CharField(max_length=50, help_text="Type of event (e.g., status_change, webhook)")
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['call', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at}"


class CSVUpload(models.Model):
    """Model to track CSV file uploads for contact imports."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='csv_uploads')
    
    # File Information
    file = models.FileField(upload_to='csv_uploads/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    
    # Processing Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_rows = models.IntegerField(default=0)
    successful_imports = models.IntegerField(default=0)
    failed_imports = models.IntegerField(default=0)
    
    # Error Details
    error_log = models.JSONField(default=list, blank=True, help_text="List of errors during processing")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.filename} - {self.status}"
