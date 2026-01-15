"""
Custom permissions and role-based access control.
"""
from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission for SuperAdmin role only.
    SuperAdmin has full access to everything.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'superadmin'


class IsSuperUser(permissions.BasePermission):
    """
    Permission for SuperUser role and above.
    SuperUser can manage users and view all data.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['superadmin', 'superuser']


class IsUser(permissions.BasePermission):
    """
    Permission for authenticated users.
    Regular users can only access their own data.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsSuperAdminOrReadOnly(permissions.BasePermission):
    """
    SuperAdmin can edit, others can only read.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.role == 'superadmin'


# ============ AGENT & ORGANISATION-BASED PERMISSIONS ============


class IsAgentOfOrganisation(permissions.BasePermission):
    """
    User must be the agent of the organisation being accessed.
    SuperAdmins bypass this check.
    
    Usage:
        class OrganisationDetailView(APIView):
            permission_classes = [IsAgentOfOrganisation]
            
            def get(self, request, org_id):
                org = Organisation.objects.get(id=org_id)
                self.check_object_permissions(request, org)
                # ... return data
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the agent of the organisation."""
        # SuperAdmin bypasses all checks
        if request.user.is_superadmin:
            return True
        
        # Determine the organisation from the object
        from callfairy.apps.accounts.models import Organisation
        
        if hasattr(obj, 'organisation'):
            org = obj.organisation
        elif isinstance(obj, Organisation):
            org = obj
        else:
            # Can't determine organisation, deny access
            return False
        
        # Check if user is the agent for this organisation
        if request.user.is_agent():
            managed_org = request.user.get_managed_organisation()
            return managed_org and managed_org.id == org.id
        
        return False


class HasPermissionKey(permissions.BasePermission):
    """
    Check if user has a specific permission key.
    SuperAdmins bypass this check.
    
    Usage:
        class ReportsView(APIView):
            permission_classes = [HasPermissionKey]
            permission_required = 'view_reports'
            
            def get(self, request):
                # User must have 'view_reports' permission
                # ...
    """
    
    def has_permission(self, request, view):
        """Check if user has the required permission."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # SuperAdmin has all permissions
        if request.user.is_superadmin:
            return True
        
        # Get required permission from view
        permission_key = getattr(view, 'permission_required', None)
        if not permission_key:
            # No specific permission required
            return True
        
        # Check if user has the permission
        return request.user.has_permission(permission_key)


class CanManageOrganisation(permissions.BasePermission):
    """
    Check if user can manage/administer the organisation.
    Only SuperAdmins and the designated Agent can manage.
    
    Usage:
        class OrganisationSettingsView(APIView):
            permission_classes = [CanManageOrganisation]
            
            def put(self, request, org_id):
                org = Organisation.objects.get(id=org_id)
                self.check_object_permissions(request, org)
                # ... update org
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user can manage the organisation."""
        from callfairy.apps.accounts.utils import can_user_manage_organisation
        from callfairy.apps.accounts.models import Organisation
        
        # SuperAdmin can manage all organisations
        if request.user.is_superadmin:
            return True
        
        # Determine the organisation
        if hasattr(obj, 'organisation'):
            org = obj.organisation
        elif isinstance(obj, Organisation):
            org = obj
        else:
            return False
        
        return can_user_manage_organisation(request.user, org)


class CanAccessOrganisation(permissions.BasePermission):
    """
    Check if user can access the organisation's data.
    
    Access Rules:
    - SuperAdmin: All organisations
    - Agent: Their managed organisation
    - User: Organisations they're members of
    
    Usage:
        class OrganisationDataView(APIView):
            permission_classes = [CanAccessOrganisation]
            
            def get(self, request, org_id):
                org = Organisation.objects.get(id=org_id)
                self.check_object_permissions(request, org)
                # ... return data
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access the organisation."""
        from callfairy.apps.accounts.utils import can_user_access_organisation
        from callfairy.apps.accounts.models import Organisation
        
        # SuperAdmin can access all organisations
        if request.user.is_superadmin:
            return True
        
        # Determine the organisation
        if hasattr(obj, 'organisation'):
            org = obj.organisation
        elif isinstance(obj, Organisation):
            org = obj
        else:
            return False
        
        return can_user_access_organisation(request.user, org)


class HasOrganisationPermission(permissions.BasePermission):
    """
    Check if user has a specific permission for a specific organisation.
    Combines organisation access check with permission check.
    
    Usage:
        class OrganisationReportsView(APIView):
            permission_classes = [HasOrganisationPermission]
            permission_required = 'view_reports'
            
            def get(self, request, org_id):
                org = Organisation.objects.get(id=org_id)
                self.check_object_permissions(request, org)
                # ... return reports
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission for the organisation."""
        from callfairy.apps.accounts.utils import check_user_permission
        from callfairy.apps.accounts.models import Organisation
        
        # SuperAdmin has all permissions
        if request.user.is_superadmin:
            return True
        
        # Determine the organisation
        if hasattr(obj, 'organisation'):
            org = obj.organisation
        elif isinstance(obj, Organisation):
            org = obj
        else:
            return False
        
        # Get required permission from view
        permission_key = getattr(view, 'permission_required', None)
        if not permission_key:
            # No specific permission required, just check access
            from callfairy.apps.accounts.utils import can_user_access_organisation
            return can_user_access_organisation(request.user, org)
        
        # Check permission with organisation context
        return check_user_permission(request.user, permission_key, organisation=org)
