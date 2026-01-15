"""
Management command to seed initial permissions into the database.

Usage:
    python manage.py seed_permissions
    python manage.py seed_permissions --clear  # Clear existing and re-seed
"""

from django.core.management.base import BaseCommand
from callfairy.apps.accounts.models import Permission


class Command(BaseCommand):
    help = 'Seeds initial permissions into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing permissions before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing permissions...'))
            Permission.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared all permissions'))

        permissions_data = [
            # User Management
            {
                'key': 'view_users',
                'name': 'View Users',
                'description': 'Can view list of users and their details'
            },
            {
                'key': 'create_users',
                'name': 'Create Users',
                'description': 'Can create new users in the system'
            },
            {
                'key': 'edit_users',
                'name': 'Edit Users',
                'description': 'Can edit existing user details and roles'
            },
            {
                'key': 'delete_users',
                'name': 'Delete Users',
                'description': 'Can delete users from the system'
            },
            
            # Organisation Management
            {
                'key': 'view_organisations',
                'name': 'View Organisations',
                'description': 'Can view organisations list and details'
            },
            {
                'key': 'manage_organisation',
                'name': 'Manage Organisation',
                'description': 'Can manage organisation settings and details'
            },
            {
                'key': 'edit_organisation_settings',
                'name': 'Edit Organisation Settings',
                'description': 'Can modify organisation settings and configuration'
            },
            
            # Reports & Analytics
            {
                'key': 'view_reports',
                'name': 'View Reports',
                'description': 'Can view reports and analytics'
            },
            {
                'key': 'export_reports',
                'name': 'Export Reports',
                'description': 'Can export reports to various formats'
            },
            {
                'key': 'view_analytics',
                'name': 'View Analytics',
                'description': 'Can access analytics dashboard'
            },
            
            # Call Management (CallFairy specific)
            {
                'key': 'make_calls',
                'name': 'Make Calls',
                'description': 'Can initiate AI calls'
            },
            {
                'key': 'view_calls',
                'name': 'View Calls',
                'description': 'Can view call history and details'
            },
            {
                'key': 'manage_campaigns',
                'name': 'Manage Campaigns',
                'description': 'Can create and manage call campaigns'
            },
            {
                'key': 'view_call_recordings',
                'name': 'View Call Recordings',
                'description': 'Can access call recordings and transcripts'
            },
            
            # Contact Management
            {
                'key': 'view_contacts',
                'name': 'View Contacts',
                'description': 'Can view contacts list'
            },
            {
                'key': 'create_contacts',
                'name': 'Create Contacts',
                'description': 'Can add new contacts'
            },
            {
                'key': 'edit_contacts',
                'name': 'Edit Contacts',
                'description': 'Can edit existing contacts'
            },
            {
                'key': 'delete_contacts',
                'name': 'Delete Contacts',
                'description': 'Can delete contacts'
            },
            {
                'key': 'import_contacts',
                'name': 'Import Contacts',
                'description': 'Can import contacts from CSV/file'
            },
            
            # Permission Management
            {
                'key': 'manage_permissions',
                'name': 'Manage Permissions',
                'description': 'Can assign and revoke user permissions'
            },
            {
                'key': 'manage_agents',
                'name': 'Manage Agents',
                'description': 'Can assign and revoke agent designations'
            },
            
            # System Settings
            {
                'key': 'view_system_settings',
                'name': 'View System Settings',
                'description': 'Can view system configuration'
            },
            {
                'key': 'edit_system_settings',
                'name': 'Edit System Settings',
                'description': 'Can modify system configuration'
            },
            
            # Audit & Logs
            {
                'key': 'view_audit_logs',
                'name': 'View Audit Logs',
                'description': 'Can view system audit logs and activity'
            },
        ]

        created_count = 0
        updated_count = 0
        
        self.stdout.write(self.style.MIGRATE_HEADING('\n🔐 Seeding Permissions...\n'))

        for perm_data in permissions_data:
            permission, created = Permission.objects.update_or_create(
                key=perm_data['key'],
                defaults={
                    'name': perm_data['name'],
                    'description': perm_data.get('description', '')
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created: {permission.name} ({permission.key})')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'  ↻ Updated: {permission.name} ({permission.key})')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Permissions seeded successfully!'
                f'\n   Created: {created_count}'
                f'\n   Updated: {updated_count}'
                f'\n   Total: {Permission.objects.count()}'
            )
        )
        
        self.stdout.write(
            self.style.MIGRATE_LABEL(
                '\n💡 Next steps:'
                '\n   1. Assign agents to organisations'
                '\n   2. Grant permissions to agents'
                '\n   3. Assign direct permissions to users'
            )
        )
