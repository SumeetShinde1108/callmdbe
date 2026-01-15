#!/usr/bin/env python
"""Test script to verify contacts API works."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'callfairy.core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

# Get test user
user = User.objects.filter(email='sumeet111@gmail.com').first()
if not user:
    print("❌ User not found")
    exit(1)

print(f"✓ Testing with user: {user.email}")

# Create test client
client = Client()

# Login
login_success = client.login(username=user.email, password='your_password_here')
print(f"Login attempt: {'✓ Success' if login_success else '❌ Failed (try manual login)'}")

# Test contacts API
print("\n" + "="*60)
print("Testing Contacts API Endpoint")
print("="*60)

response = client.get('/api/v1/calls/contacts/')
print(f"\nStatus Code: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")

if response.status_code == 200:
    import json
    data = json.loads(response.content)
    print(f"\n✅ API WORKING!")
    print(f"   - Response has 'results': {'results' in data}")
    print(f"   - Response has 'count': {'count' in data}")
    if 'results' in data:
        print(f"   - Number of contacts: {len(data['results'])}")
        if len(data['results']) > 0:
            print(f"   - First contact: {data['results'][0].get('name')}")
    else:
        print(f"   - Direct array length: {len(data)}")
else:
    print(f"\n❌ API ERROR")
    print(f"Response: {response.content.decode()[:500]}")

# Check if contacts exist
from callfairy.apps.calls.models import Contact
total_contacts = Contact.objects.count()
user_contacts = Contact.objects.filter(user=user).count()

print(f"\n" + "="*60)
print("Database Check")
print("="*60)
print(f"Total contacts in database: {total_contacts}")
print(f"Contacts for user {user.email}: {user_contacts}")

if user_contacts > 0:
    print("\nSample contacts:")
    for contact in Contact.objects.filter(user=user)[:5]:
        print(f"  - {contact.name}: {contact.phone_number}")
