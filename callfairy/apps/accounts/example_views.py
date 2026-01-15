"""
Example API views demonstrating the multi-tenant permission system.

These examples show how to use the permission classes and utilities
in real API endpoints. Copy and adapt these for your actual views.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Agent, User, Organisation, Permission, AgentPermissions
from .permissions import (
    IsSuperAdmin,
    IsAgentOfOrganisation,
    HasPermissionKey,
    CanManageOrganisation,
    CanAccessOrganisation,
    HasOrganisationPermission,
)
from .utils import (
    get_user_accessible_organisations,
    check_user_permission,
    get_permission_summary,
    can_user_manage_organisation,
)


# ============ AGENT MANAGEMENT (SuperAdmin Only) ============

class AssignAgentView(APIView):
    """
    Assign a user as agent to an organisation.
    Only SuperAdmins can assign agents.
    
    POST /api/agents/assign/
    {
        "user_id": "uuid",
        "organisation_id": 123
    }
    """
    permission_classes = [IsSuperAdmin]
    
    def post(self, request):
        user_id = request.data.get('user_id')
        org_id = request.data.get('organisation_id')
        
        if not user_id or not org_id:
            return Response(
                {'error': 'user_id and organisation_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            org = Organisation.objects.get(id=org_id)
            
            # Check if user is already an agent somewhere
            existing_agent = Agent.get_agent_for_user(user)
            if existing_agent and existing_agent.is_active:
                return Response({
                    'error': f'User is already agent for {existing_agent.organisation.name}',
                    'existing_organisation': existing_agent.organisation.name
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Assign agent
            agent = Agent.assign_agent(
                user=user,
                organisation=org,
                assigned_by=request.user
            )
            
            return Response({
                'message': f'{user.name} assigned as agent for {org.name}',
                'agent': {
                    'id': str(agent.id),
                    'user': {
                        'id': str(user.id),
                        'email': user.email,
                        'name': user.name,
                        'role': user.role,
                    },
                    'organisation': {
                        'id': org.id,
                        'name': org.name,
                    },
                    'assigned_at': agent.assigned_at.isoformat(),
                }
            }, status=status.HTTP_201_CREATED)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Organisation.DoesNotExist:
            return Response(
                {'error': 'Organisation not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class RevokeAgentView(APIView):
    """
    Revoke agent designation.
    Only SuperAdmins can revoke agents.
    
    POST /api/agents/{agent_id}/revoke/
    """
    permission_classes = [IsSuperAdmin]
    
    def post(self, request, agent_id):
        try:
            agent = Agent.objects.get(id=agent_id, is_active=True)
            
            # Revoke agent
            Agent.revoke_agent(agent_id, revoked_by=request.user)
            
            return Response({
                'message': f'Agent {agent.user.name} revoked from {agent.organisation.name}',
                'user_role': agent.user.role,  # Will be 'user' now
            })
            
        except Agent.DoesNotExist:
            return Response(
                {'error': 'Active agent not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class GrantAgentPermissionView(APIView):
    """
    Grant a permission to an agent.
    Only SuperAdmins can grant permissions.
    
    POST /api/agents/{agent_id}/permissions/grant/
    {
        "permission_key": "view_reports"
    }
    """
    permission_classes = [IsSuperAdmin]
    
    def post(self, request, agent_id):
        permission_key = request.data.get('permission_key')
        
        if not permission_key:
            return Response(
                {'error': 'permission_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            agent = Agent.objects.get(id=agent_id, is_active=True)
            permission = Permission.objects.get(key=permission_key)
            
            # Grant permission
            agent_perm = AgentPermissions.grant_permission(
                agent=agent,
                permission=permission,
                granted_by=request.user
            )
            
            return Response({
                'message': f'Permission {permission.name} granted to {agent.user.name}',
                'permission': {
                    'key': permission.key,
                    'name': permission.name,
                },
                'agent': {
                    'user': agent.user.name,
                    'organisation': agent.organisation.name,
                }
            }, status=status.HTTP_201_CREATED)
            
        except Agent.DoesNotExist:
            return Response({'error': 'Agent not found'}, status=404)
        except Permission.DoesNotExist:
            return Response({'error': 'Permission not found'}, status=404)


# ============ ORGANISATION VIEWS ============

class OrganisationListView(APIView):
    """
    Get list of organisations user can access.
    
    - SuperAdmin: All organisations
    - Agent: Their managed organisation
    - User: Organisations they're members of
    
    GET /api/organisations/
    """
    def get(self, request):
        # Get accessible organisations for this user
        orgs = get_user_accessible_organisations(request.user)
        
        data = []
        for org in orgs:
            # Get agent for this org
            agent = Agent.get_agent_for_organisation(org)
            
            data.append({
                'id': org.id,
                'name': org.name,
                'city': org.city,
                'is_active': org.is_active,
                'agent': {
                    'name': agent.user.name,
                    'email': agent.user.email,
                } if agent else None,
                'can_manage': can_user_manage_organisation(request.user, org),
            })
        
        return Response({
            'organisations': data,
            'count': len(data),
            'user_role': request.user.role,
        })


class OrganisationDetailView(APIView):
    """
    Get organisation details.
    User must have access to the organisation.
    
    GET /api/organisations/{org_id}/
    """
    permission_classes = [CanAccessOrganisation]
    
    def get(self, request, org_id):
        org = get_object_or_404(Organisation, id=org_id)
        self.check_object_permissions(request, org)
        
        # Get agent
        agent = Agent.get_agent_for_organisation(org)
        
        # Get user's permissions for this org
        from .utils import get_user_permissions_for_organisation
        perms = get_user_permissions_for_organisation(request.user, org)
        
        return Response({
            'id': org.id,
            'name': org.name,
            'description': org.description,
            'city': org.city,
            'state': org.state,
            'country': org.country,
            'is_active': org.is_active,
            'agent': {
                'id': str(agent.user.id),
                'name': agent.user.name,
                'email': agent.user.email,
            } if agent else None,
            'user_can_manage': can_user_manage_organisation(request.user, org),
            'user_permissions': list(perms.values_list('key', flat=True)),
        })


class OrganisationUpdateView(APIView):
    """
    Update organisation details.
    Only SuperAdmins and the designated Agent can update.
    
    PUT /api/organisations/{org_id}/
    {
        "name": "New Name",
        "description": "New description"
    }
    """
    permission_classes = [CanManageOrganisation]
    
    def put(self, request, org_id):
        org = get_object_or_404(Organisation, id=org_id)
        self.check_object_permissions(request, org)
        
        # Update fields
        org.name = request.data.get('name', org.name)
        org.description = request.data.get('description', org.description)
        org.address = request.data.get('address', org.address)
        org.city = request.data.get('city', org.city)
        org.state = request.data.get('state', org.state)
        org.country = request.data.get('country', org.country)
        org.pincode = request.data.get('pincode', org.pincode)
        org.save()
        
        return Response({
            'message': 'Organisation updated successfully',
            'organisation': {
                'id': org.id,
                'name': org.name,
                'description': org.description,
            }
        })


# ============ PERMISSION-BASED VIEWS ============

class OrganisationReportsView(APIView):
    """
    View reports for an organisation.
    User must have 'view_reports' permission for this organisation.
    
    GET /api/organisations/{org_id}/reports/
    """
    permission_classes = [HasOrganisationPermission]
    permission_required = 'view_reports'
    
    def get(self, request, org_id):
        org = get_object_or_404(Organisation, id=org_id)
        self.check_object_permissions(request, org)
        
        # User has 'view_reports' permission for this org
        # Generate reports...
        
        return Response({
            'organisation': org.name,
            'reports': [
                {
                    'type': 'calls',
                    'total': 150,
                    'completed': 120,
                    'failed': 30,
                },
                {
                    'type': 'users',
                    'total': 25,
                    'active': 20,
                },
            ],
            'generated_at': '2025-11-05T20:00:00Z',
        })


class UserManagementView(APIView):
    """
    Manage users in organisation.
    Requires 'edit_users' permission.
    
    GET /api/organisations/{org_id}/users/
    POST /api/organisations/{org_id}/users/
    """
    permission_classes = [HasOrganisationPermission]
    permission_required = 'edit_users'
    
    def get(self, request, org_id):
        """List users in organisation."""
        org = get_object_or_404(Organisation, id=org_id)
        self.check_object_permissions(request, org)
        
        # Get users in this organisation
        users = User.objects.filter(
            userorganisation__organisation=org
        ).values('id', 'email', 'name', 'role', 'is_active')
        
        return Response({
            'organisation': org.name,
            'users': list(users),
            'count': len(users),
        })
    
    def post(self, request, org_id):
        """Add user to organisation."""
        org = get_object_or_404(Organisation, id=org_id)
        self.check_object_permissions(request, org)
        
        user_email = request.data.get('email')
        
        # Create or get user, add to organisation
        # ... implementation
        
        return Response({
            'message': 'User added to organisation',
        }, status=status.HTTP_201_CREATED)


# ============ USER PROFILE & PERMISSIONS ============

class MyPermissionsView(APIView):
    """
    Get current user's permissions and access.
    
    GET /api/me/permissions/
    """
    def get(self, request):
        summary = get_permission_summary(request.user)
        return Response(summary)


class MyOrganisationsView(APIView):
    """
    Get organisations the current user can access.
    
    GET /api/me/organisations/
    """
    def get(self, request):
        orgs = get_user_accessible_organisations(request.user)
        
        data = []
        for org in orgs:
            data.append({
                'id': org.id,
                'name': org.name,
                'city': org.city,
                'role': 'Agent' if request.user.is_agent() and 
                        request.user.get_managed_organisation() == org
                        else 'Member',
            })
        
        return Response({
            'organisations': data,
            'count': len(data),
            'is_agent': request.user.is_agent(),
            'managed_organisation': {
                'id': request.user.get_managed_organisation().id,
                'name': request.user.get_managed_organisation().name,
            } if request.user.is_agent() else None,
        })


# ============ URL CONFIGURATION ============

"""
Add these to your urls.py:

from .example_views import (
    AssignAgentView, RevokeAgentView, GrantAgentPermissionView,
    OrganisationListView, OrganisationDetailView, OrganisationUpdateView,
    OrganisationReportsView, UserManagementView,
    MyPermissionsView, MyOrganisationsView,
)

urlpatterns = [
    # Agent Management
    path('agents/assign/', AssignAgentView.as_view(), name='assign-agent'),
    path('agents/<uuid:agent_id>/revoke/', RevokeAgentView.as_view(), name='revoke-agent'),
    path('agents/<uuid:agent_id>/permissions/grant/', GrantAgentPermissionView.as_view(), name='grant-agent-permission'),
    
    # Organisations
    path('organisations/', OrganisationListView.as_view(), name='organisation-list'),
    path('organisations/<int:org_id>/', OrganisationDetailView.as_view(), name='organisation-detail'),
    path('organisations/<int:org_id>/update/', OrganisationUpdateView.as_view(), name='organisation-update'),
    path('organisations/<int:org_id>/reports/', OrganisationReportsView.as_view(), name='organisation-reports'),
    path('organisations/<int:org_id>/users/', UserManagementView.as_view(), name='organisation-users'),
    
    # User Profile
    path('me/permissions/', MyPermissionsView.as_view(), name='my-permissions'),
    path('me/organisations/', MyOrganisationsView.as_view(), name='my-organisations'),
]
"""
