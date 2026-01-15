#!/usr/bin/env python
"""Test script for CSV upload functionality."""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'callfairy.core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from callfairy.apps.calls.views import CSVUploadViewSet
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.request import Request
from io import BytesIO

User = get_user_model()

# Get test user
user = User.objects.filter(is_superuser=True).first()
if not user:
    print("❌ No superuser found. Please create one first.")
    sys.exit(1)

print(f"✓ Using user: {user.email}")

# Create test CSV content
csv_content = b"""name,phone_number,email
Test User 1,+12025551234,test1@example.com
Test User 2,+13105557890,test2@example.com
Test User 3,+14155559999,test3@example.com"""

print(f"✓ Created test CSV with 3 contacts")

# Create uploaded file
csv_file = SimpleUploadedFile(
    "test_contacts.csv",
    csv_content,
    content_type="text/csv"
)

print("\n" + "="*60)
print("TESTING CSV VALIDATION")
print("="*60)

# Test validation
factory = APIRequestFactory()
django_request = factory.post(
    '/api/v1/calls/csv-uploads/',
    {'validate_only': 'true', 'csv_file': csv_file},
    format='multipart'
)
request = Request(django_request)
request.user = user
force_authenticate(request, user=user)

viewset = CSVUploadViewSet()
viewset.format_kwarg = None
viewset.request = request

try:
    response = viewset.create(request)
    print(f"\n✓ Validation Status Code: {response.status_code}")
    print(f"✓ Response Data: {response.data}")
    
    if response.status_code == 200:
        print("\n✅ VALIDATION PASSED!")
        print(f"   - Total rows: {response.data.get('total_rows')}")
        print(f"   - Valid rows: {response.data.get('valid_rows')}")
        print(f"   - Invalid rows: {response.data.get('invalid_rows')}")
    else:
        print(f"\n❌ VALIDATION FAILED!")
        print(f"   - Error: {response.data}")
except Exception as e:
    print(f"\n❌ VALIDATION ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TESTING CSV IMPORT")
print("="*60)

# Reset file for import test
csv_file.seek(0)
csv_file2 = SimpleUploadedFile(
    "test_contacts.csv",
    csv_content,
    content_type="text/csv"
)

django_request2 = factory.post(
    '/api/v1/calls/csv-uploads/',
    {'csv_file': csv_file2},
    format='multipart'
)
request2 = Request(django_request2)
request2.user = user
force_authenticate(request2, user=user)

viewset2 = CSVUploadViewSet()
viewset2.format_kwarg = None
viewset2.request = request2

try:
    response2 = viewset2.create(request2)
    print(f"\n✓ Import Status Code: {response2.status_code}")
    print(f"✓ Response Data: {response2.data}")
    
    if response2.status_code == 201:
        print("\n✅ IMPORT SUCCESSFUL!")
        print(f"   - Successful imports: {response2.data.get('successful_imports')}")
        print(f"   - Failed imports: {response2.data.get('failed_imports')}")
        print(f"   - Total rows: {response2.data.get('total_rows')}")
        print(f"   - Status: {response2.data.get('status')}")
        
        # Check if contacts were created
        from callfairy.apps.calls.models import Contact
        contacts = Contact.objects.filter(user=user, name__startswith='Test User')
        print(f"\n✓ Contacts in database: {contacts.count()}")
        for contact in contacts[:3]:
            print(f"   - {contact.name}: {contact.phone_number}")
    else:
        print(f"\n❌ IMPORT FAILED!")
        print(f"   - Error: {response2.data}")
except Exception as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
