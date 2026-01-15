from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.utils.text import slugify
import uuid
import secrets
from datetime import timedelta
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError(_('The Email must be set'))
        if not password:
            raise ValueError(_('The Password must be set'))
        email = self.normalize_email(email)

        # Validate password strength
        validate_password(password)

        # New users are inactive until email verification completes
        extra_fields.setdefault('is_active', False)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with UUID primary key and email as username."""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('superuser', 'Super User'),
        ('superadmin', 'Super Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    name = models.CharField(_('full name'), max_length=255)
    is_active = models.BooleanField(_('active'), default=False)
    is_staff = models.BooleanField(_('staff status'), default=False)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    
    # Role-based access control
    role = models.CharField(
        _('role'), 
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='user',
        help_text='User role for permission management'
    )

    # Optional profile fields
    company = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.name
    
    @property
    def is_superadmin(self):
        """Check if user is SuperAdmin."""
        return self.role == 'superadmin'
    
    @property
    def is_superuser_role(self):
        """Check if user is SuperUser or above."""
        return self.role in ['superadmin', 'superuser']
    
    @property
    def is_regular_user(self):
        """Check if user is regular user."""
        return self.role == 'user'
    
    def get_role_display_name(self):
        """Get human-readable role name."""
        return dict(self.ROLE_CHOICES).get(self.role, 'User')
    
    # ============ AGENT & PERMISSION METHODS ============
    
    def is_agent(self):
        """Check if this user is an agent for any organisation."""
        return hasattr(self, '_is_agent_cache') and self._is_agent_cache or \
               Agent.objects.filter(user=self, is_active=True).exists()
    
    def get_managed_organisation(self):
        """Get the organisation this user manages (if they're an agent)."""
        if not self.is_agent():
            return None
        agent = Agent.objects.filter(user=self, is_active=True).first()
        return agent.organisation if agent else None
    
    def get_agent_permissions(self):
        """Get all permissions this user has as an agent."""
        if not self.is_agent():
            return Permission.objects.none()
        try:
            agent = Agent.objects.get(user=self, is_active=True)
            return Permission.objects.filter(agentpermissions__agent=agent)
        except Agent.DoesNotExist:
            return Permission.objects.none()
    
    def get_direct_permissions(self):
        """Get all direct permissions assigned to this user."""
        return Permission.objects.filter(userpermissionaccess__user=self)
    
    def get_all_permissions(self):
        """Get all permissions (direct + agent permissions)."""
        direct_perms = self.get_direct_permissions()
        agent_perms = self.get_agent_permissions()
        return (direct_perms | agent_perms).distinct()
    
    def has_permission(self, permission_key):
        """
        Check if user has a specific permission.
        SuperAdmin has all permissions by default.
        """
        if self.is_superadmin:
            return True
        return self.get_all_permissions().filter(key=permission_key).exists()
    
    def sync_role_with_agent_status(self):
        """
        Automatically update role based on agent status.
        - If user is an agent and not superuser, upgrade to superuser
        - If user is not an agent but is superuser, downgrade to user
        """
        is_agent_now = self.is_agent()
        
        if is_agent_now and self.role != 'superuser':
            self.role = 'superuser'
            self.save(update_fields=['role'])
        elif not is_agent_now and self.role == 'superuser':
            self.role = 'user'
            self.save(update_fields=['role'])


class EmailVerificationToken(models.Model):
    """One-time email verification token for activating accounts."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_tokens')
    token = models.CharField(max_length=128, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["token"])]

    def __str__(self):
        return f"EmailVerificationToken(user={self.user_id}, used={self.is_used})"

    @classmethod
    def create_for_user(cls, user, ttl_hours: int = 24):
        token = secrets.token_urlsafe(32)
        expires = timezone.now() + timedelta(hours=ttl_hours)
        return cls.objects.create(user=user, token=token, expires_at=expires)

    def is_valid(self) -> bool:
        return (not self.is_used) and (timezone.now() <= self.expires_at)


class AllowedEmailDomain(models.Model):
    """Whitelist of email domains allowed to authenticate (optional global restriction)."""

    domain = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Allowed email domain"
        verbose_name_plural = "Allowed email domains"

    def __str__(self):
        return f"{self.domain} ({'active' if self.is_active else 'inactive'})"


class GoogleSignInAudit(models.Model):
    """Audit log for Google sign-in attempts."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='google_signin_audits')
    email = models.EmailField()
    domain = models.CharField(max_length=255)
    provider_sub = models.CharField(max_length=255, blank=True)
    success = models.BooleanField(default=False)
    reason = models.CharField(max_length=255, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["email", "created_at"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"GoogleSignInAudit(email={self.email}, success={self.success}, at={self.created_at:%Y-%m-%d %H:%M:%S})"


class Organisation(models.Model):
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f'{self.name} - {self.city} - {self.pincode}'

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"


class UserOrganisation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.user} - {self.organisation}"
    
    class Meta:
        verbose_name = "User Organisation"
        verbose_name_plural = "User Organisations"
        unique_together = ('user', 'organisation')


class Permission(models.Model):
    """Defines a specific permission that can be granted to users or agents."""
    name = models.CharField(max_length=255, help_text="Human-readable permission name")
    key = models.SlugField(
        max_length=255, 
        unique=True, 
        help_text="Unique permission key (e.g., 'view_reports')"
    )
    description = models.TextField(blank=True, help_text="What this permission allows")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.key})"


class UserPermissionAccess(models.Model):
    """Direct permission grants to users (global permissions)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='direct_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='granted_permissions'
    )
    
    def __str__(self):
        return f"{self.user.email} → {self.permission.key}"
    
    class Meta:
        verbose_name = "User Permission Access"
        verbose_name_plural = "User Permission Access"
        unique_together = ['user', 'permission']
        ordering = ['-granted_at']


class Agent(models.Model):
    """
    Designates a user as an agent (manager) for a specific organisation.
    One organisation can have only ONE active agent at a time (1:1 relationship).
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='agent_assignments',
        help_text="User designated as agent"
    )
    organisation = models.ForeignKey(
        Organisation, 
        on_delete=models.CASCADE, 
        related_name='agents',
        help_text="Organisation managed by this agent"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='agents_assigned',
        help_text="SuperAdmin who assigned this agent"
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="Whether this agent assignment is currently active"
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='agents_revoked'
    )
    
    class Meta:
        verbose_name = "Agent"
        verbose_name_plural = "Agents"
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['organisation', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organisation'],
                condition=models.Q(is_active=True),
                name='unique_active_agent_per_org'
            ),
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_active=True),
                name='unique_active_agent_per_user'
            ),
        ]
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.user.name} → {self.organisation.name} ({status})"
    
    @classmethod
    def assign_agent(cls, user, organisation, assigned_by):
        """
        Assign a user as agent to an organisation.
        - Removes any existing agent from that organisation
        - Updates user role to 'superuser'
        - Creates audit trail
        
        Args:
            user: User to be assigned as agent
            organisation: Organisation to manage
            assigned_by: SuperAdmin making the assignment
        
        Returns:
            Agent: The newly created agent instance
        """
        # Deactivate existing agent for this organisation
        existing_agents = cls.objects.filter(organisation=organisation, is_active=True)
        for agent in existing_agents:
            agent.is_active = False
            agent.revoked_at = timezone.now()
            agent.revoked_by = assigned_by
            agent.save()
            # Sync old agent's role
            agent.user.sync_role_with_agent_status()
        
        # Deactivate any existing agent assignment for this user
        user_agents = cls.objects.filter(user=user, is_active=True)
        for agent in user_agents:
            agent.is_active = False
            agent.revoked_at = timezone.now()
            agent.revoked_by = assigned_by
            agent.save()
        
        # Create new agent assignment
        new_agent = cls.objects.create(
            user=user,
            organisation=organisation,
            assigned_by=assigned_by,
            is_active=True
        )
        
        # Update user role to superuser
        user.role = 'superuser'
        user.save(update_fields=['role'])
        
        return new_agent
    
    @classmethod
    def revoke_agent(cls, agent_id, revoked_by=None):
        """
        Revoke agent designation.
        - Deactivates the agent
        - Reverts user role back to regular user
        
        Args:
            agent_id: ID of agent to revoke
            revoked_by: User revoking the agent (optional)
        
        Returns:
            Agent: The revoked agent instance
        """
        agent = cls.objects.get(id=agent_id)
        agent.is_active = False
        agent.revoked_at = timezone.now()
        agent.revoked_by = revoked_by
        agent.save()
        
        # Sync user role
        agent.user.sync_role_with_agent_status()
        
        return agent
    
    @classmethod
    def get_agent_for_organisation(cls, organisation):
        """Get the active agent for an organisation."""
        return cls.objects.filter(organisation=organisation, is_active=True).first()
    
    @classmethod
    def get_agent_for_user(cls, user):
        """Get the active agent assignment for a user."""
        return cls.objects.filter(user=user, is_active=True).first()
    
    def get_permissions(self):
        """Get all permissions assigned to this agent."""
        return Permission.objects.filter(agentpermissions__agent=self)


class AgentPermissions(models.Model):
    """
    Permissions granted to agents for managing their specific organisation.
    These permissions are context-specific - only valid for the agent's organisation.
    """
    agent = models.ForeignKey(
        Agent, 
        on_delete=models.CASCADE, 
        related_name='permissions'
    )
    permission = models.ForeignKey(
        Permission, 
        on_delete=models.CASCADE
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='agent_permissions_granted'
    )
    
    class Meta:
        verbose_name = "Agent Permission"
        verbose_name_plural = "Agent Permissions"
        unique_together = ['agent', 'permission']
        ordering = ['-granted_at']
    
    def __str__(self):
        return f"{self.agent.user.email} ({self.agent.organisation.name}) → {self.permission.key}"
    
    @classmethod
    def grant_permission(cls, agent, permission, granted_by=None):
        """
        Grant a permission to an agent.
        
        Args:
            agent: Agent instance
            permission: Permission instance or permission key
            granted_by: User granting the permission
        
        Returns:
            AgentPermissions: The created permission grant
        """
        if isinstance(permission, str):
            permission = Permission.objects.get(key=permission)
        
        agent_perm, created = cls.objects.get_or_create(
            agent=agent,
            permission=permission,
            defaults={'granted_by': granted_by}
        )
        return agent_perm
    
    @classmethod
    def revoke_permission(cls, agent, permission):
        """
        Revoke a permission from an agent.
        
        Args:
            agent: Agent instance
            permission: Permission instance or permission key
        """
        if isinstance(permission, str):
            permission = Permission.objects.get(key=permission)
        
        cls.objects.filter(agent=agent, permission=permission).delete()
    
    @classmethod
    def get_agent_permissions(cls, agent):
        """Get all permissions for a specific agent."""
        return cls.objects.filter(agent=agent).select_related('permission')