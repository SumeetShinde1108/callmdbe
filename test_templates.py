#!/usr/bin/env python
"""Quick script to test if Django can find templates."""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'callfairy.core.settings')
django.setup()

from django.conf import settings
from django.template.loader import get_template

print("=" * 60)
print("TEMPLATE CONFIGURATION TEST")
print("=" * 60)

print(f"\nBASE_DIR: {settings.BASE_DIR}")
print(f"\nTEMPLATE DIRS: {settings.TEMPLATES[0]['DIRS']}")

# Check if template directories exist
for template_dir in settings.TEMPLATES[0]['DIRS']:
    print(f"\nChecking: {template_dir}")
    if os.path.exists(template_dir):
        print(f"  ✓ Directory exists")
        # List subdirectories
        subdirs = [d for d in os.listdir(template_dir) if os.path.isdir(os.path.join(template_dir, d))]
        print(f"  Subdirectories: {subdirs}")
    else:
        print(f"  ✗ Directory does NOT exist")

# Try to load templates
print("\n" + "=" * 60)
print("TEMPLATE LOADING TEST")
print("=" * 60)

templates_to_test = [
    'auth/login.html',
    'auth/register.html',
    'base/base.html',
    'calls/dashboard.html',
]

for template_name in templates_to_test:
    try:
        template = get_template(template_name)
        print(f"\n✓ {template_name} - FOUND")
        print(f"  Origin: {template.origin.name if hasattr(template, 'origin') else 'N/A'}")
    except Exception as e:
        print(f"\n✗ {template_name} - NOT FOUND")
        print(f"  Error: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
