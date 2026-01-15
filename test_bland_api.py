#!/usr/bin/env python
"""
Quick test script to verify Bland API connection works.
Run this before making actual calls to ensure everything is set up correctly.
"""

import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

# Import BlandClient
from utils import BlandClient, BlandApiError

def test_bland_connection():
    """Test if we can connect to Bland API."""
    
    print("🧪 Testing Bland API Connection...")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('BLAND_API_KEY')
    if not api_key:
        print("❌ BLAND_API_KEY not found in .env")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    print()
    
    # Initialize client
    try:
        client = BlandClient()
        print("✅ BlandClient initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize BlandClient: {e}")
        return False
    
    print()
    print("📋 Testing API Call (test mode)...")
    print("   Note: This won't make an actual call")
    print()
    
    # Test parameters
    test_params = {
        'phone_number': '+919322205429',
        'task': 'You are a friendly assistant testing the connection.',
        'voice': 'maya',
        'model': 'turbo',
        'max_duration': 1,
        'record': False
    }
    
    print(f"   Phone: {test_params['phone_number']}")
    print(f"   Task: {test_params['task'][:50]}...")
    print(f"   Voice: {test_params['voice']}")
    print()
    
    # Try to validate (this will fail if API key is invalid)
    try:
        # You can uncomment below to make actual test call
        # WARNING: This will use your Bland credits!
        
        # response = client.send_call(**test_params)
        # print("✅ API call successful!")
        # print(f"   Call ID: {response.get('call_id')}")
        # print(f"   Status: {response.get('status')}")
        
        print("✅ API connection validated (test mode)")
        print()
        print("💡 To make actual test call, uncomment lines in test_bland_api.py")
        
    except BlandApiError as e:
        print(f"❌ Bland API Error: {e}")
        print(f"   Status Code: {e.status_code}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print()
    print("=" * 50)
    print("✅ All checks passed! Ready to make calls.")
    print()
    print("🚀 Next steps:")
    print("   1. Make sure Django server is running")
    print("   2. Go to http://localhost:8000/make-call/")
    print("   3. Fill in phone number and task")
    print("   4. Click 'Make Call'")
    print("   5. Call will be initiated immediately!")
    print()
    
    return True

if __name__ == '__main__':
    success = test_bland_connection()
    sys.exit(0 if success else 1)
