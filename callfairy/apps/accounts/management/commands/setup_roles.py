"""
Management command to set up initial roles and create admin users.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up initial roles and create admin users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superadmin',
            action='store_true',
            help='Create a SuperAdmin user',
        )
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create a SuperUser',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the user',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the user',
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Full name for the user',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Role Setup ==='))
        
        # Show available roles
        self.stdout.write('\nAvailable roles:')
        self.stdout.write('  - user: Regular user with access to own data')
        self.stdout.write('  - superuser: Can view all data and manage users')
        self.stdout.write('  - superadmin: Full system access')
        
        if options['create_superadmin']:
            self.create_superadmin(options)
        elif options['create_superuser']:
            self.create_superuser_role(options)
        else:
            self.stdout.write('\nUse --create-superadmin or --create-superuser with --email, --password, and --name')
            self.stdout.write('\nExample:')
            self.stdout.write('  python manage.py setup_roles --create-superadmin --email admin@example.com --password Admin@123 --name "Super Admin"')

    def create_superadmin(self, options):
        """Create a SuperAdmin user."""
        email = options.get('email')
        password = options.get('password')
        name = options.get('name')
        
        if not all([email, password, name]):
            self.stdout.write(self.style.ERROR('Email, password, and name are required!'))
            return
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'User with email {email} already exists!'))
            return
        
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            is_active=True,
            is_staff=True,
            is_superuser=True,
            role='superadmin'
        )
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ SuperAdmin created successfully!'))
        self.stdout.write(f'  Email: {user.email}')
        self.stdout.write(f'  Name: {user.name}')
        self.stdout.write(f'  Role: {user.get_role_display_name()}')

    def create_superuser_role(self, options):
        """Create a SuperUser."""
        email = options.get('email')
        password = options.get('password')
        name = options.get('name')
        
        if not all([email, password, name]):
            self.stdout.write(self.style.ERROR('Email, password, and name are required!'))
            return
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'User with email {email} already exists!'))
            return
        
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            is_active=True,
            is_staff=True,
            role='superuser'
        )
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ SuperUser created successfully!'))
        self.stdout.write(f'  Email: {user.email}')
        self.stdout.write(f'  Name: {user.name}')
        self.stdout.write(f'  Role: {user.get_role_display_name()}')
