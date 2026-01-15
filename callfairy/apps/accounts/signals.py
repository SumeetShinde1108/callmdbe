"""
Django signals for automatic role synchronization and audit logging.

Handles automatic updates when agents are assigned/revoked.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Agent, User
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Agent)
def sync_user_role_on_agent_assign(sender, instance, created, **kwargs):
    """
    Automatically update user role when agent is assigned.
    
    When a user is assigned as an agent (is_active=True),
    their role is automatically set to 'superuser'.
    """
    if instance.is_active:
        user = instance.user
        if user.role != 'superuser':
            user.role = 'superuser'
            user.save(update_fields=['role'])
            logger.info(
                f"Auto-upgraded user {user.email} to superuser (assigned as agent for {instance.organisation.name})"
            )


@receiver(pre_save, sender=Agent)
def sync_user_role_on_agent_revoke(sender, instance, **kwargs):
    """
    Automatically update user role when agent is revoked.
    
    When an agent is deactivated (is_active=False),
    check if user should be downgraded from 'superuser' to 'user'.
    """
    if instance.pk:  # Only for existing instances (updates)
        try:
            old_instance = Agent.objects.get(pk=instance.pk)
            
            # Check if agent is being deactivated
            if old_instance.is_active and not instance.is_active:
                user = instance.user
                
                # Check if user has any other active agent assignments
                other_active_agents = Agent.objects.filter(
                    user=user,
                    is_active=True
                ).exclude(pk=instance.pk).exists()
                
                # Only downgrade if no other active agent assignments
                if not other_active_agents and user.role == 'superuser':
                    user.role = 'user'
                    user.save(update_fields=['role'])
                    logger.info(
                        f"Auto-downgraded user {user.email} to user (agent revoked for {instance.organisation.name})"
                    )
        except Agent.DoesNotExist:
            pass


@receiver(post_delete, sender=Agent)
def sync_user_role_on_agent_delete(sender, instance, **kwargs):
    """
    Automatically update user role when agent assignment is deleted.
    
    When an agent assignment is completely deleted,
    check if user should be downgraded from 'superuser'.
    """
    user = instance.user
    
    # Check if user has any remaining active agent assignments
    has_other_agents = Agent.objects.filter(
        user=user,
        is_active=True
    ).exists()
    
    # Downgrade if no other agent assignments and currently superuser
    if not has_other_agents and user.role == 'superuser':
        user.role = 'user'
        user.save(update_fields=['role'])
        logger.info(
            f"Auto-downgraded user {user.email} to user (agent assignment deleted)"
        )


# Optional: Add audit logging signals

@receiver(post_save, sender=Agent)
def log_agent_assignment(sender, instance, created, **kwargs):
    """
    Log agent assignment/revocation for audit purposes.
    """
    if created:
        logger.info(
            f"AUDIT: Agent assigned - User: {instance.user.email}, "
            f"Organisation: {instance.organisation.name}, "
            f"Assigned by: {instance.assigned_by.email if instance.assigned_by else 'System'}"
        )
    elif not instance.is_active:
        logger.info(
            f"AUDIT: Agent revoked - User: {instance.user.email}, "
            f"Organisation: {instance.organisation.name}, "
            f"Revoked by: {instance.revoked_by.email if instance.revoked_by else 'System'}"
        )
