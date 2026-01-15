"""
User Management Template Views
Django template-based views for managing users, organisations, agents, and permissions
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import User, Organisation, Agent, Permission, AgentPermissions, UserOrganisation
from .utils import get_user_accessible_organisations, can_user_manage_organisation


# ============= UTILITY FUNCTIONS =============

def require_superadmin(view_func):
    """Decorator to require SuperAdmin role"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'superadmin':
            messages.error(request, 'Access denied. SuperAdmin privileges required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def grant_basic_agent_permissions(agent):
    """Grant basic agent permissions (view-only)"""
    basic_permissions = [
        'manage_organisation',
        'view_users',
        'view_reports',
    ]
    for perm_key in basic_permissions:
        try:
            permission = Permission.objects.get(key=perm_key)
            AgentPermissions.objects.get_or_create(
                agent=agent,
                permission=permission
            )
        except Permission.DoesNotExist:
            pass


def grant_standard_agent_permissions(agent):
    """Grant standard agent permissions (recommended)"""
    standard_permissions = [
        'manage_organisation',
        'view_users',
        'view_reports',
        'view_contacts',
        'view_calls',
        'create_contacts',
    ]
    for perm_key in standard_permissions:
        try:
            permission = Permission.objects.get(key=perm_key)
            AgentPermissions.objects.get_or_create(
                agent=agent,
                permission=permission
            )
        except Permission.DoesNotExist:
            pass


def grant_advanced_agent_permissions(agent):
    """Grant advanced agent permissions (power user)"""
    advanced_permissions = [
        'manage_organisation',
        'view_users',
        'create_users',
        'edit_users',
        'view_reports',
        'view_contacts',
        'create_contacts',
        'view_calls',
        'make_calls',
        'manage_campaigns',
    ]
    for perm_key in advanced_permissions:
        try:
            permission = Permission.objects.get(key=perm_key)
            AgentPermissions.objects.get_or_create(
                agent=agent,
                permission=permission
            )
        except Permission.DoesNotExist:
            pass


# ============= ORGANISATION MANAGEMENT =============

@login_required
def organisations_list_view(request):
    """List organisations based on user role"""
    user = request.user
    
    # Get accessible organisations
    if user.role == 'superadmin':
        organisations = Organisation.objects.all().annotate(
            user_count=Count('userorganisation')
        )
    elif user.is_agent():
        managed_org = user.get_managed_organisation()
        organisations = Organisation.objects.filter(id=managed_org.id).annotate(
            user_count=Count('userorganisation')
        ) if managed_org else Organisation.objects.none()
    else:
        # Regular users see member organisations
        organisations = get_user_accessible_organisations(user).annotate(
            user_count=Count('userorganisation')
        )
    
    # Get agent information for each org
    for org in organisations:
        org.agent_user = Agent.get_agent_for_organisation(org)
    
    context = {
        'organisations': organisations,
        'can_create': user.role == 'superadmin',
    }
    return render(request, 'user_management/organisations_list.html', context)


@login_required
def organisation_detail_view(request, org_id):
    """View organisation details"""
    user = request.user
    organisation = get_object_or_404(Organisation, id=org_id)
    
    # Check access
    if user.role != 'superadmin':
        if user.is_agent():
            managed_org = user.get_managed_organisation()
            if not managed_org or managed_org.id != org_id:
                messages.error(request, 'Access denied. You can only view your organisation.')
                return redirect('organisations_list')
        else:
            # Check if user is member
            if not UserOrganisation.objects.filter(user=user, organisation=organisation).exists():
                messages.error(request, 'Access denied.')
                return redirect('organisations_list')
    
    # Get agent
    agent = Agent.get_agent_for_organisation(organisation)
    
    # Get members
    members = UserOrganisation.objects.filter(organisation=organisation).select_related('user')
    
    # Can manage check
    can_manage = can_user_manage_organisation(user, organisation)
    
    context = {
        'organisation': organisation,
        'agent': agent,
        'members': members,
        'member_count': members.count(),
        'can_manage': can_manage,
        'is_superadmin': user.role == 'superadmin',
    }
    return render(request, 'user_management/organisation_detail.html', context)


@login_required
def organisation_edit_view(request, org_id):
    """Edit organisation"""
    user = request.user
    organisation = get_object_or_404(Organisation, id=org_id)
    
    # Check permission
    if not can_user_manage_organisation(user, organisation):
        messages.error(request, 'Access denied.')
        return redirect('organisation_detail', org_id=org_id)
    
    if request.method == 'POST':
        organisation.name = request.POST.get('name', organisation.name)
        organisation.description = request.POST.get('description', '')
        organisation.address = request.POST.get('address', '')
        organisation.city = request.POST.get('city', '')
        organisation.state = request.POST.get('state', '')
        organisation.country = request.POST.get('country', '')
        organisation.pincode = request.POST.get('pincode', '')
        organisation.save()
        
        messages.success(request, 'Organisation updated successfully!')
        return redirect('organisation_detail', org_id=org_id)
    
    context = {
        'organisation': organisation,
    }
    return render(request, 'user_management/organisation_edit.html', context)


@login_required
@require_superadmin
def organisation_create_view(request):
    """Create new organisation (SuperAdmin only)"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        city = request.POST.get('city', '')
        
        if not name:
            messages.error(request, 'Organisation name is required.')
        else:
            organisation = Organisation.objects.create(
                name=name,
                description=description,
                city=city,
                address=request.POST.get('address', ''),
                state=request.POST.get('state', ''),
                country=request.POST.get('country', ''),
                pincode=request.POST.get('pincode', ''),
            )
            messages.success(request, f'Organisation "{name}" created successfully!')
            return redirect('organisation_detail', org_id=organisation.id)
    
    return render(request, 'user_management/organisation_create.html')


# ============= AGENT MANAGEMENT =============

@login_required
@require_superadmin
def agents_list_view(request):
    """List all agents (SuperAdmin only)"""
    agents = Agent.objects.filter(is_active=True).select_related('user', 'organisation', 'assigned_by')
    
    # Get agent permissions
    for agent in agents:
        agent.permission_list = agent.get_permissions()
    
    context = {
        'agents': agents,
        'total_agents': agents.count(),
    }
    return render(request, 'user_management/agents_list.html', context)


@login_required
@require_superadmin
def agent_assign_view(request):
    """Assign agent to organisation (SuperAdmin only)"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        org_id = request.POST.get('organisation_id')
        permission_package = request.POST.get('permission_package', 'standard')
        
        try:
            user = User.objects.get(id=user_id)
            organisation = Organisation.objects.get(id=org_id)
            
            # Check if user is already an agent elsewhere
            existing_agent = Agent.get_agent_for_user(user)
            if existing_agent and existing_agent.is_active and existing_agent.organisation.id != organisation.id:
                messages.error(request, f'{user.name} is already an agent for {existing_agent.organisation.name}')
                return redirect('agent_assign')
            
            # Assign agent
            agent = Agent.assign_agent(user, organisation, request.user)
            
            # Grant permissions based on package
            if permission_package == 'basic':
                grant_basic_agent_permissions(agent)
                messages.success(request, f'{user.name} assigned as agent with Basic permissions!')
            elif permission_package == 'advanced':
                grant_advanced_agent_permissions(agent)
                messages.success(request, f'{user.name} assigned as agent with Advanced permissions!')
            else:  # standard (default)
                grant_standard_agent_permissions(agent)
                messages.success(request, f'{user.name} assigned as agent with Standard permissions!')
            
            return redirect('agents_list')
            
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
        except Organisation.DoesNotExist:
            messages.error(request, 'Organisation not found.')
        except Exception as e:
            messages.error(request, f'Error assigning agent: {str(e)}')
    
    # Get users who are not agents
    non_agent_users = User.objects.filter(
        Q(role='user') | Q(agent_assignments__is_active=False) | Q(agent_assignments__isnull=True)
    ).distinct()
    
    # Get organisations
    organisations = Organisation.objects.all()
    
    context = {
        'users': non_agent_users,
        'organisations': organisations,
    }
    return render(request, 'user_management/agent_assign.html', context)


@login_required
@require_superadmin
def agent_revoke_view(request, agent_id):
    """Revoke agent (SuperAdmin only)"""
    agent = get_object_or_404(Agent, user__id=agent_id, is_active=True)
    
    if request.method == 'POST':
        agent.is_active = False
        agent.revoked_by = request.user
        agent.save()
        
        messages.success(request, f'{agent.user.name} has been revoked as agent.')
        return redirect('agents_list')
    
    context = {
        'agent': agent,
    }
    return render(request, 'user_management/agent_revoke_confirm.html', context)


@login_required
@require_superadmin
def agent_permissions_view(request, agent_id):
    """Manage agent permissions (SuperAdmin only)"""
    agent = get_object_or_404(Agent, user__id=agent_id, is_active=True)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        permission_key = request.POST.get('permission_key')
        
        try:
            permission = Permission.objects.get(key=permission_key)
            
            if action == 'grant':
                AgentPermissions.objects.get_or_create(agent=agent, permission=permission)
                messages.success(request, f'Permission "{permission.name}" granted to {agent.user.name}')
            elif action == 'revoke':
                AgentPermissions.objects.filter(agent=agent, permission=permission).delete()
                messages.success(request, f'Permission "{permission.name}" revoked from {agent.user.name}')
                
        except Permission.DoesNotExist:
            messages.error(request, 'Permission not found.')
    
    # Get current permissions
    current_permissions = agent.get_permissions()
    current_perm_keys = set(current_permissions.values_list('key', flat=True))
    
    # Get all permissions grouped by category
    all_permissions = Permission.objects.all().order_by('key')
    
    # Group permissions
    permission_groups = {}
    for perm in all_permissions:
        category = perm.key.split('_')[-1]  # Simplified grouping
        if 'user' in perm.key:
            category = 'Users'
        elif 'organisation' in perm.key:
            category = 'Organisations'
        elif 'report' in perm.key or 'analytics' in perm.key:
            category = 'Reports'
        elif 'call' in perm.key or 'campaign' in perm.key:
            category = 'Calls'
        elif 'contact' in perm.key:
            category = 'Contacts'
        else:
            category = 'System'
        
        if category not in permission_groups:
            permission_groups[category] = []
        
        permission_groups[category].append({
            'permission': perm,
            'has_permission': perm.key in current_perm_keys,
            'is_system': category == 'System',
        })
    
    context = {
        'agent': agent,
        'permission_groups': permission_groups,
        'current_permission_count': len(current_perm_keys),
    }
    return render(request, 'user_management/agent_permissions.html', context)


# ============= SYSTEM USER MANAGEMENT =============

@login_required
@require_superadmin
def system_users_list_view(request):
    """List all users in the system (SuperAdmin only)"""
    users = User.objects.all().order_by('-date_joined')
    
    # Add agent info
    for user in users:
        user.is_active_agent = user.is_agent()
        if user.is_active_agent:
            user.managed_org = user.get_managed_organisation()
    
    context = {
        'users': users,
        'total_users': users.count(),
        'superadmins': users.filter(role='superadmin').count(),
        'agents': Agent.objects.filter(is_active=True).count(),
        'regular_users': users.filter(role='user').count(),
    }
    return render(request, 'user_management/system_users_list.html', context)


@login_required
def user_profile_view(request, user_id):
    """View user profile"""
    profile_user = get_object_or_404(User, id=user_id)
    
    # Permission check
    if request.user.role != 'superadmin':
        if request.user.id != profile_user.id:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    
    # Get agent info
    is_agent = profile_user.is_agent()
    managed_org = None
    agent_permissions = []
    
    if is_agent:
        managed_org = profile_user.get_managed_organisation()
        agent_permissions = profile_user.get_agent_permissions()
    
    # Get organisations
    accessible_orgs = get_user_accessible_organisations(profile_user)
    
    context = {
        'profile_user': profile_user,
        'is_agent': is_agent,
        'managed_org': managed_org,
        'agent_permissions': agent_permissions,
        'accessible_orgs': accessible_orgs,
        'is_own_profile': request.user.id == profile_user.id,
        'can_edit': request.user.role == 'superadmin' or request.user.id == profile_user.id,
    }
    return render(request, 'user_management/user_profile.html', context)


# ============= PERMISSIONS VIEW =============

@login_required
def permissions_list_view(request):
    """List all available permissions"""
    permissions = Permission.objects.all().order_by('key')
    
    # Group by category
    permission_groups = {}
    for perm in permissions:
        if 'user' in perm.key:
            category = 'Users'
        elif 'organisation' in perm.key:
            category = 'Organisations'
        elif 'report' in perm.key or 'analytics' in perm.key:
            category = 'Reports'
        elif 'call' in perm.key or 'campaign' in perm.key:
            category = 'Calls'
        elif 'contact' in perm.key:
            category = 'Contacts'
        else:
            category = 'System'
        
        if category not in permission_groups:
            permission_groups[category] = []
        permission_groups[category].append(perm)
    
    context = {
        'permission_groups': permission_groups,
        'total_permissions': permissions.count(),
    }
    return render(request, 'user_management/permissions_list.html', context)
