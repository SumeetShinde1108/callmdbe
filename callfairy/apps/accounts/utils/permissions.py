"""
Utility functions for permission checking and organization access control.

This module provides helper functions for checking user permissions and
determining which organizations a user can access based on their role.
"""

from django.db.models import QuerySet
from typing import Optional


def check_user_permission(user, permission_key: str, organisation=None) -> bool:
    """
    Check if user has permission, considering organizational context.
    
    Rules:
    1. SuperAdmin always has access to everything
    2. Agent has permissions only for their managed organisation
    3. Regular users have their direct permissions
    
    Args:
        user: User instance to check
        permission_key: Permission key to check (e.g., 'view_reports')
        organisation: Organisation instance for context (optional)
    
    Returns:
        bool: True if user has the permission, False otherwise
    
    Example:
        >>> check_user_permission(user, 'view_reports', organisation=org)
        True
    """
    # SuperAdmin bypasses all checks
    if user.is_superadmin:
        return True
    
    # If organisation context is provided and user is an agent
    if organisation and user.is_agent():
        managed_org = user.get_managed_organisation()
        # Agent can only access their own organisation
        if managed_org and managed_org.id == organisation.id:
            return user.has_permission(permission_key)
        else:
            # Agent trying to access a different organisation
            return False
    
    # Check direct permissions for regular users
    return user.has_permission(permission_key)


def get_user_accessible_organisations(user) -> QuerySet:
    """
    Get all organisations a user can access based on their role.
    
    Access Rules:
    - SuperAdmin: All active organisations
    - Agent: Only their managed organisation
    - Regular User: Organisations they're part of via UserOrganisation
    
    Args:
        user: User instance
    
    Returns:
        QuerySet: Organisation queryset filtered by access rules
    
    Example:
        >>> orgs = get_user_accessible_organisations(user)
        >>> for org in orgs:
        ...     print(org.name)
    """
    from callfairy.apps.accounts.models import Organisation, UserOrganisation
    
    # SuperAdmin has access to all organisations
    if user.is_superadmin:
        return Organisation.objects.filter(is_active=True)
    
    # Agent has access only to their managed organisation
    if user.is_agent():
        managed_org = user.get_managed_organisation()
        if managed_org:
            return Organisation.objects.filter(id=managed_org.id, is_active=True)
        return Organisation.objects.none()
    
    # Regular users have access to organisations they're members of
    return Organisation.objects.filter(
        userorganisation__user=user,
        is_active=True
    ).distinct()


def can_user_access_organisation(user, organisation) -> bool:
    """
    Check if a user can access a specific organisation.
    
    Args:
        user: User instance
        organisation: Organisation instance
    
    Returns:
        bool: True if user can access the organisation
    
    Example:
        >>> if can_user_access_organisation(user, org):
        ...     # Allow access
        ...     pass
    """
    accessible_orgs = get_user_accessible_organisations(user)
    return accessible_orgs.filter(id=organisation.id).exists()


def get_user_permissions_for_organisation(user, organisation) -> QuerySet:
    """
    Get all permissions a user has for a specific organisation.
    
    Args:
        user: User instance
        organisation: Organisation instance
    
    Returns:
        QuerySet: Permission queryset
    
    Example:
        >>> perms = get_user_permissions_for_organisation(user, org)
        >>> if perms.filter(key='edit_users').exists():
        ...     # User can edit users
        ...     pass
    """
    from callfairy.apps.accounts.models import Permission
    
    # SuperAdmin has all permissions
    if user.is_superadmin:
        return Permission.objects.all()
    
    # Agent has their assigned permissions for their managed org
    if user.is_agent():
        managed_org = user.get_managed_organisation()
        if managed_org and managed_org.id == organisation.id:
            return user.get_agent_permissions()
        return Permission.objects.none()
    
    # Regular users have their direct permissions
    return user.get_direct_permissions()


def can_user_manage_organisation(user, organisation) -> bool:
    """
    Check if user can manage/administer an organisation.
    
    Only SuperAdmins and the designated Agent can manage an organisation.
    
    Args:
        user: User instance
        organisation: Organisation instance
    
    Returns:
        bool: True if user can manage the organisation
    """
    # SuperAdmin can manage all organisations
    if user.is_superadmin:
        return True
    
    # Check if user is the agent for this organisation
    if user.is_agent():
        managed_org = user.get_managed_organisation()
        return managed_org and managed_org.id == organisation.id
    
    return False


def get_organisation_agent(organisation) -> Optional['User']:
    """
    Get the active agent (manager) for an organisation.
    
    Args:
        organisation: Organisation instance
    
    Returns:
        User: The agent user, or None if no agent assigned
    
    Example:
        >>> agent = get_organisation_agent(org)
        >>> if agent:
        ...     print(f"Manager: {agent.name}")
    """
    from callfairy.apps.accounts.models import Agent
    
    agent_assignment = Agent.get_agent_for_organisation(organisation)
    return agent_assignment.user if agent_assignment else None


def is_user_agent_of_organisation(user, organisation) -> bool:
    """
    Check if a specific user is the agent for a specific organisation.
    
    Args:
        user: User instance
        organisation: Organisation instance
    
    Returns:
        bool: True if user is the agent for this organisation
    """
    if not user.is_agent():
        return False
    
    managed_org = user.get_managed_organisation()
    return managed_org and managed_org.id == organisation.id


def get_permission_summary(user) -> dict:
    """
    Get a summary of all permissions and access for a user.
    
    Useful for admin interfaces and debugging.
    
    Args:
        user: User instance
    
    Returns:
        dict: Summary containing role, agent status, permissions, and organisations
    
    Example:
        >>> summary = get_permission_summary(user)
        >>> print(f"Role: {summary['role']}")
        >>> print(f"Is Agent: {summary['is_agent']}")
        >>> print(f"Permissions: {', '.join(summary['permissions'])}")
    """
    from callfairy.apps.accounts.models import Agent
    
    is_agent = user.is_agent()
    managed_org = user.get_managed_organisation() if is_agent else None
    
    return {
        'user_id': str(user.id),
        'email': user.email,
        'name': user.name,
        'role': user.role,
        'role_display': user.get_role_display_name(),
        'is_superadmin': user.is_superadmin,
        'is_agent': is_agent,
        'managed_organisation': {
            'id': str(managed_org.id),
            'name': managed_org.name,
        } if managed_org else None,
        'direct_permissions': list(user.get_direct_permissions().values_list('key', flat=True)),
        'agent_permissions': list(user.get_agent_permissions().values_list('key', flat=True)) if is_agent else [],
        'all_permissions': list(user.get_all_permissions().values_list('key', flat=True)),
        'accessible_organisations': list(
            get_user_accessible_organisations(user).values('id', 'name')
        ),
    }
