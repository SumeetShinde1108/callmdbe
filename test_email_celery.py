#!/usr/bin/env python
"""
Test script to diagnose email and Celery configuration.
Run this to check if your email system is working correctly.
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'callfairy.core.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from callfairy.apps.accounts.tasks import send_password_reset_email


def print_section(title):
    """Print a section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def test_email_settings():
    """Test 1: Check email configuration."""
    print_section("TEST 1: Email Configuration")
    
    print(f"✓ EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"✓ EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"✓ EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"✓ EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"✓ EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"✓ EMAIL_HOST_PASSWORD: {'***' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    print(f"✓ DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    if not settings.EMAIL_HOST_PASSWORD or settings.EMAIL_HOST_PASSWORD == 'your-gmail-app-password-here':
        print("\n⚠️  WARNING: EMAIL_HOST_PASSWORD is not set!")
        print("   Please set your Gmail App Password in .env file")
        return False
    
    if 'console' in settings.EMAIL_BACKEND:
        print("\n⚠️  WARNING: Using console backend (emails won't be sent)")
        print("   Change EMAIL_BACKEND to smtp.EmailBackend in .env")
        return False
    
    print("\n✓ Email configuration looks good!")
    return True


def test_redis_connection():
    """Test 2: Check Redis/Celery connection."""
    print_section("TEST 2: Redis & Celery Configuration")
    
    try:
        from celery import Celery
        from django.core.cache import cache
        
        print(f"✓ CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")
        
        # Try to connect to Redis
        cache.set('test_key', 'test_value', 10)
        value = cache.get('test_key')
        
        if value == 'test_value':
            print("✓ Redis connection successful!")
            return True
        else:
            print("✗ Redis connection failed")
            return False
            
    except Exception as e:
        print(f"✗ Error connecting to Redis: {e}")
        print("\n⚠️  Make sure Redis is running:")
        print("   sudo systemctl start redis")
        return False


def test_celery_worker():
    """Test 3: Check if Celery worker is running."""
    print_section("TEST 3: Celery Worker Status")
    
    try:
        from celery import current_app
        
        # Check active workers
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print("✓ Celery workers are running!")
            for worker, info in stats.items():
                print(f"  - Worker: {worker}")
            return True
        else:
            print("✗ No Celery workers found")
            print("\n⚠️  Start Celery worker:")
            print("   bash start_celery.sh")
            return False
            
    except Exception as e:
        print(f"✗ Error checking Celery workers: {e}")
        print("\n⚠️  Make sure Celery worker is running:")
        print("   bash start_celery.sh")
        return False


def test_direct_email():
    """Test 4: Send a test email directly (without Celery)."""
    print_section("TEST 4: Direct Email Sending")
    
    test_email = settings.EMAIL_HOST_USER
    
    print(f"Sending test email to: {test_email}")
    
    try:
        result = send_mail(
            subject='Test Email - CallFairy',
            message='This is a test email from CallFairy. If you receive this, email is working!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        
        if result == 1:
            print(f"✓ Test email sent successfully to {test_email}!")
            print("  Check your inbox (and spam folder)")
            return True
        else:
            print("✗ Email sending failed")
            return False
            
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        print("\nCommon issues:")
        print("  1. Wrong Gmail App Password")
        print("  2. 2-Step Verification not enabled")
        print("  3. Using regular password instead of App Password")
        return False


def test_celery_email():
    """Test 5: Send a test email via Celery."""
    print_section("TEST 5: Celery Email Task")
    
    test_email = settings.EMAIL_HOST_USER
    test_url = "http://localhost:8000/password-reset-confirm/test/token/"
    
    print(f"Queuing test email task to: {test_email}")
    
    try:
        # Queue the task
        task = send_password_reset_email.delay(
            user_email=test_email,
            user_name="Test User",
            reset_url=test_url
        )
        
        print(f"✓ Task queued successfully! Task ID: {task.id}")
        print("  Waiting for task to complete...")
        
        # Wait for result (max 30 seconds)
        result = task.get(timeout=30)
        
        if result.get('status') == 'success':
            print(f"✓ Email sent successfully via Celery!")
            print(f"  Check inbox: {test_email}")
            return True
        else:
            print(f"✗ Task failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"✗ Error with Celery task: {e}")
        print("\nMake sure:")
        print("  1. Celery worker is running (bash start_celery.sh)")
        print("  2. Redis is running (sudo systemctl start redis)")
        return False


def main():
    """Run all tests."""
    print("\n" + "█"*60)
    print("  CallFairy Email & Celery Diagnostic Tool")
    print("█"*60)
    
    results = []
    
    # Run all tests
    results.append(("Email Configuration", test_email_settings()))
    results.append(("Redis Connection", test_redis_connection()))
    results.append(("Celery Worker", test_celery_worker()))
    results.append(("Direct Email", test_direct_email()))
    results.append(("Celery Email Task", test_celery_email()))
    
    # Summary
    print_section("SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Email system is working!")
        print("\nYou can now:")
        print("  1. Test password reset on the website")
        print("  2. Check your Gmail inbox for test emails")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nQuick fixes:")
        print("  1. Set Gmail App Password in .env file (line 25)")
        print("  2. Start Redis: sudo systemctl start redis")
        print("  3. Start Celery: bash start_celery.sh")
        print("  4. Restart Django: python manage.py runserver")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
