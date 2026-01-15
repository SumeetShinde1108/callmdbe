# 🔐 Multi-Tenant Permission System - Complete Implementation Guide

## 🎉 System Overview

A three-tier role-based access control (RBAC) system with agent-based organization management.

### Core Concepts

1. **SuperAdmin** - Platform administrator with global access
2. **Agent (SuperUser)** - Organization manager (1:1 with organization)
3. **User** - Regular user with customizable permissions

---

## ✅ What's Been Implemented

### 1. Database Models

#### **Agent Model** (`callfairy/apps/accounts/models.py`)
- One-to-one relationship between user and organization
- Automatic role synchronization
- Audit trail (assigned_by, revoked_by)
- Active/inactive status

#### **AgentPermissions Model**
- Links agents to permissions
- Context-specific permissions for organization management
- Grant/revoke methods

#### **Enhanced Permission Model**
- Human-readable names and keys
- Descriptions for clarity
- Auto-slug generation

### 2. User Model Extensions

Added methods to User model:
- `is_agent()` - Check if user is an agent
- `get_managed_organisation()` - Get the org user manages
- `get_agent_permissions()` - Get agent-specific permissions
- `get_direct_permissions()` - Get directly assigned permissions
- `get_all_permissions()` - Get combined permissions
- `has_permission(key)` - Check specific permission
- `sync_role_with_agent_status()` - Auto role synchronization

### 3. Utility Functions

**File:** `callfairy/apps/accounts/utils/permissions.py`

- `check_user_permission()` - Permission check with org context
- `get_user_accessible_organisations()` - Get orgs user can access
- `can_user_access_organisation()` - Check org access
- `get_user_permissions_for_organisation()` - Org-specific perms
- `can_user_manage_organisation()` - Check management rights
- `get_organisation_agent()` - Get org's agent
- `is_user_agent_of_organisation()` - Specific agent check
- `get_permission_summary()` - Complete permission overview

### 4. DRF Permission Classes

**File:** `callfairy/apps/accounts/permissions.py`

- `IsSuperAdmin` - SuperAdmin only
- `IsAgentOfOrganisation` - Agent of specific org
- `HasPermissionKey` - Specific permission check
- `CanManageOrganisation` - Management rights check
- `CanAccessOrganisation` - Access rights check
- `HasOrganisationPermission` - Permission + org context

### 5. Signals

**File:** `callfairy/apps/accounts/signals.py`

- Auto role upgrade when agent assigned
- Auto role downgrade when agent revoked
- Audit logging for agent changes

### 6. Management Commands

**File:** `callfairy/apps/accounts/management/commands/seed_permissions.py`

Seeds 25+ initial permissions including:
- User management
- Organisation management
- Reports & analytics
- Call management
- Contact management
- Permission management
- System settings
- Audit logs

---

## 🚀 Setup & Migration

### Step 1: Create Migrations

```bash
# Generate migrations for new models
python manage.py makemigrations accounts

# You should see:
# Migrations for 'accounts':
#   callfairy/apps/accounts/migrations/0XXX_agent_agentpermissions.py
#     - Create model Agent
#     - Create model AgentPermissions
#     - Alter field permission on userpermissionaccess
#     - Add field granted_at to userpermissionaccess
#     - Add field granted_by to userpermissionaccess
```

### Step 2: Apply Migrations

```bash
# Apply migrations to database
python manage.py migrate accounts

# Expected output:
# Running migrations:
#   Applying accounts.0XXX_agent_agentpermissions... OK
```

### Step 3: Seed Permissions

```bash
# Seed initial permissions
python manage.py seed_permissions

# Output:
# 🔐 Seeding Permissions...
#   ✓ Created: View Users (view_users)
#   ✓ Created: Create Users (create_users)
#   ...
# ✅ Permissions seeded successfully!
#    Created: 25
#    Total: 25
```

---

## 📋 Usage Examples

### Example 1: Assign Agent

```python
from callfairy.apps.accounts.models import Agent, User, Organisation

# Get users and organisation
superadmin = User.objects.get(email='admin@example.com')
user = User.objects.get(email='john@example.com')
org = Organisation.objects.get(name='Acme Corp')

# Assign user as agent
agent = Agent.assign_agent(
    user=user,
    organisation=org,
    assigned_by=superadmin
)

# User's role is now automatically 'superuser'
print(user.role)  # 'superuser'
print(user.is_agent())  # True
print(user.get_managed_organisation())  # <Organisation: Acme Corp>
```

### Example 2: Grant Agent Permissions

```python
from callfairy.apps.accounts.models import AgentPermissions, Permission

# Get or create permissions
view_reports = Permission.objects.get(key='view_reports')
manage_org = Permission.objects.get(key='manage_organisation')

# Grant permissions to agent
AgentPermissions.grant_permission(agent, view_reports, granted_by=superadmin)
AgentPermissions.grant_permission(agent, manage_org, granted_by=superadmin)

# Check permissions
print(user.has_permission('view_reports'))  # True
print(user.has_permission('manage_organisation'))  # True
```

### Example 3: Check Permissions

```python
from callfairy.apps.accounts.utils import check_user_permission

# Check permission with organisation context
can_view = check_user_permission(
    user=user,
    permission_key='view_reports',
    organisation=org
)

if can_view:
    # Show reports
    pass
```

### Example 4: Get Accessible Organisations

```python
from callfairy.apps.accounts.utils import get_user_accessible_organisations

# SuperAdmin - gets all organisations
orgs = get_user_accessible_organisations(superadmin)
print(orgs.count())  # All organisations

# Agent - gets only managed organisation
orgs = get_user_accessible_organisations(agent_user)
print(orgs.count())  # 1

# Regular user - gets organisations they're members of
orgs = get_user_accessible_organisations(regular_user)
print(orgs)  # Their organisations via UserOrganisation
```

### Example 5: Revoke Agent

```python
# Revoke agent designation
Agent.revoke_agent(agent.id, revoked_by=superadmin)

# User's role is automatically downgraded
print(user.role)  # 'user'
print(user.is_agent())  # False
```

---

## 🔌 API View Examples

### Example 1: Organisation Detail View

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from callfairy.apps.accounts.permissions import CanAccessOrganisation
from callfairy.apps.accounts.models import Organisation

class OrganisationDetailView(APIView):
    permission_classes = [CanAccessOrganisation]
    
    def get(self, request, org_id):
        """Get organisation details."""
        try:
            org = Organisation.objects.get(id=org_id)
            self.check_object_permissions(request, org)
            
            # User has access to this organisation
            return Response({
                'id': str(org.id),
                'name': org.name,
                'city': org.city,
                'is_active': org.is_active,
            })
        except Organisation.DoesNotExist:
            return Response(
                {'error': 'Organisation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
```

### Example 2: Reports View with Permission Check

```python
from callfairy.apps.accounts.permissions import HasPermissionKey
from callfairy.apps.accounts.utils import get_user_accessible_organisations

class OrganisationReportsView(APIView):
    permission_classes = [HasPermissionKey]
    permission_required = 'view_reports'
    
    def get(self, request):
        """Get reports for accessible organisations."""
        # Get organisations user can access
        orgs = get_user_accessible_organisations(request.user)
        
        # Generate reports for these organisations
        reports = []
        for org in orgs:
            reports.append({
                'organisation': org.name,
                'total_calls': org.calls.count(),
                'active_users': org.users.filter(is_active=True).count(),
                # ... more stats
            })
        
        return Response({'reports': reports})
```

### Example 3: Agent Management View (SuperAdmin Only)

```python
from callfairy.apps.accounts.permissions import IsSuperAdmin
from callfairy.apps.accounts.models import Agent

class AssignAgentView(APIView):
    permission_classes = [IsSuperAdmin]
    
    def post(self, request):
        """Assign a user as agent to an organisation."""
        user_id = request.data.get('user_id')
        org_id = request.data.get('organisation_id')
        
        try:
            user = User.objects.get(id=user_id)
            org = Organisation.objects.get(id=org_id)
            
            # Assign agent
            agent = Agent.assign_agent(
                user=user,
                organisation=org,
                assigned_by=request.user
            )
            
            return Response({
                'message': f'{user.name} assigned as agent for {org.name}',
                'agent_id': str(agent.id),
                'user_role': user.role,
            }, status=status.HTTP_201_CREATED)
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        except Organisation.DoesNotExist:
            return Response({'error': 'Organisation not found'}, status=404)
```

### Example 4: Organisation Management View

```python
from callfairy.apps.accounts.permissions import CanManageOrganisation

class OrganisationSettingsView(APIView):
    permission_classes = [CanManageOrganisation]
    
    def put(self, request, org_id):
        """Update organisation settings (Agent or SuperAdmin only)."""
        try:
            org = Organisation.objects.get(id=org_id)
            self.check_object_permissions(request, org)
            
            # Update organisation
            org.name = request.data.get('name', org.name)
            org.description = request.data.get('description', org.description)
            org.save()
            
            return Response({
                'message': 'Organisation updated successfully',
                'organisation': {
                    'id': str(org.id),
                    'name': org.name,
                    'description': org.description,
                }
            })
        except Organisation.DoesNotExist:
            return Response({'error': 'Organisation not found'}, status=404)
```

---

## 🧪 Testing Guide

### Test 1: Agent Assignment

```python
def test_agent_assignment():
    """Test agent assignment and role synchronization."""
    # Create test data
    superadmin = User.objects.create(
        email='admin@test.com',
        role='superadmin',
        is_active=True
    )
    user = User.objects.create(
        email='user@test.com',
        role='user',
        is_active=True
    )
    org = Organisation.objects.create(name='Test Org')
    
    # Assign agent
    agent = Agent.assign_agent(user, org, superadmin)
    
    # Refresh user from database
    user.refresh_from_db()
    
    # Assertions
    assert user.role == 'superuser', "User role should be upgraded to superuser"
    assert user.is_agent() == True, "User should be an agent"
    assert user.get_managed_organisation() == org, "User should manage the org"
    assert agent.is_active == True, "Agent should be active"
    
    print("✓ Agent assignment test passed")
```

### Test 2: Permission Checking

```python
def test_permission_checking():
    """Test permission checking for different roles."""
    from callfairy.apps.accounts.models import Permission, AgentPermissions
    
    # Create permission
    perm = Permission.objects.create(
        key='view_reports',
        name='View Reports'
    )
    
    # Grant to agent
    AgentPermissions.grant_permission(agent, perm)
    
    # Test permission check
    assert user.has_permission('view_reports') == True
    assert user.has_permission('non_existent') == False
    
    # Test with organisation context
    from callfairy.apps.accounts.utils import check_user_permission
    
    assert check_user_permission(user, 'view_reports', org) == True
    
    # Different organisation should fail
    other_org = Organisation.objects.create(name='Other Org')
    assert check_user_permission(user, 'view_reports', other_org) == False
    
    print("✓ Permission checking test passed")
```

### Test 3: Agent Revocation

```python
def test_agent_revocation():
    """Test agent revocation and role downgrade."""
    # Revoke agent
    Agent.revoke_agent(agent.id, revoked_by=superadmin)
    
    # Refresh user
    user.refresh_from_db()
    
    # Assertions
    assert user.role == 'user', "User role should be downgraded to user"
    assert user.is_agent() == False, "User should not be an agent"
    assert user.get_managed_organisation() == None, "User should not manage any org"
    
    # Refresh agent
    agent.refresh_from_db()
    assert agent.is_active == False, "Agent should be inactive"
    
    print("✓ Agent revocation test passed")
```

### Test 4: Organisation Access

```python
def test_organisation_access():
    """Test organisation access for different user types."""
    from callfairy.apps.accounts.utils import get_user_accessible_organisations
    
    # SuperAdmin - all orgs
    admin_orgs = get_user_accessible_organisations(superadmin)
    assert admin_orgs.count() >= 2, "SuperAdmin should see all orgs"
    
    # Agent - only managed org
    agent_orgs = get_user_accessible_organisations(user)  # user is agent
    assert agent_orgs.count() == 1, "Agent should see only managed org"
    assert agent_orgs.first() == org, "Should be the managed org"
    
    # Regular user - member orgs
    regular_user = User.objects.create(
        email='regular@test.com',
        role='user'
    )
    UserOrganisation.objects.create(user=regular_user, organisation=org)
    
    user_orgs = get_user_accessible_organisations(regular_user)
    assert user_orgs.count() == 1, "User should see member orgs"
    
    print("✓ Organisation access test passed")
```

### Run All Tests

```bash
# Create test file
# tests/test_permissions.py

# Run tests
python manage.py test callfairy.apps.accounts.tests.test_permissions

# Or use pytest
pytest tests/test_permissions.py -v
```

---

## 📊 Database Schema

```
User
├─ id (UUID, PK)
├─ email (unique)
├─ role (superadmin/superuser/user)
└─ ... profile fields

Organisation
├─ id (PK)
├─ name
└─ ... address fields

Agent (1:1:1 relationship)
├─ id (PK)
├─ user_id (FK → User, unique)
├─ organisation_id (FK → Organisation, unique)
├─ is_active
├─ assigned_by (FK → User)
└─ revoked_by (FK → User)

Permission
├─ id (PK)
├─ key (unique, slug)
├─ name
└─ description

UserPermissionAccess (direct permissions)
├─ user_id (FK → User)
├─ permission_id (FK → Permission)
├─ granted_by (FK → User)
└─ granted_at

AgentPermissions (agent permissions)
├─ agent_id (FK → Agent)
├─ permission_id (FK → Permission)
├─ granted_by (FK → User)
└─ granted_at

UserOrganisation (membership)
├─ user_id (FK → User)
└─ organisation_id (FK → Organisation)
```

---

## 🔐 Permission Hierarchy

```
SuperAdmin
  ├─ All permissions (bypass all checks)
  └─ Can assign/revoke agents

Agent (SuperUser)
  ├─ Permissions assigned via AgentPermissions
  ├─ Only for their managed organisation
  └─ Can manage their organisation

User
  ├─ Permissions assigned via UserPermissionAccess
  └─ Can access organisations they're members of
```

---

## 💡 Best Practices

### 1. Always Check Organisation Context

```python
# ❌ Bad - No organisation context
if user.has_permission('view_reports'):
    show_all_reports()

# ✅ Good - With organisation context
if check_user_permission(user, 'view_reports', organisation=org):
    show_org_reports(org)
```

### 2. Use DRF Permission Classes

```python
# ✅ Good - Let DRF handle permission checks
class MyView(APIView):
    permission_classes = [HasOrganisationPermission]
    permission_required = 'view_reports'
    
    def get(self, request, org_id):
        org = Organisation.objects.get(id=org_id)
        self.check_object_permissions(request, org)
        # ... proceed
```

### 3. Filter Querysets by Access

```python
# ✅ Good - Only show accessible organisations
def get_queryset(self):
    return get_user_accessible_organisations(self.request.user)
```

### 4. Use Utility Functions

```python
# ✅ Good - Use provided utilities
from callfairy.apps.accounts.utils import (
    check_user_permission,
    can_user_manage_organisation,
    get_permission_summary,
)
```

---

## 🚨 Common Pitfalls

### 1. Forgetting Organisation Context

```python
# ❌ Agent can access other orgs' data
if user.has_permission('view_reports'):
    return all_reports()

# ✅ Check with organisation context
if check_user_permission(user, 'view_reports', org):
    return org_reports(org)
```

### 2. Not Using Object Permissions

```python
# ❌ Only checks has_permission
class MyView(APIView):
    permission_classes = [HasPermissionKey]

# ✅ Use object-level permissions
class MyView(APIView):
    permission_classes = [HasOrganisationPermission]
    
    def get(self, request, org_id):
        org = Organisation.objects.get(id=org_id)
        self.check_object_permissions(request, org)  # Important!
```

### 3. Manual Role Management

```python
# ❌ Manually changing roles
user.role = 'superuser'
user.save()

# ✅ Use Agent.assign_agent - handles role automatically
Agent.assign_agent(user, org, assigned_by)
```

---

## 📝 Seeded Permissions Reference

| Key | Name | Description |
|-----|------|-------------|
| `view_users` | View Users | Can view list of users and their details |
| `create_users` | Create Users | Can create new users in the system |
| `edit_users` | Edit Users | Can edit existing user details and roles |
| `delete_users` | Delete Users | Can delete users from the system |
| `view_organisations` | View Organisations | Can view organisations list and details |
| `manage_organisation` | Manage Organisation | Can manage organisation settings |
| `view_reports` | View Reports | Can view reports and analytics |
| `export_reports` | Export Reports | Can export reports to various formats |
| `make_calls` | Make Calls | Can initiate AI calls |
| `view_calls` | View Calls | Can view call history |
| `manage_campaigns` | Manage Campaigns | Can create/manage call campaigns |
| `view_contacts` | View Contacts | Can view contacts list |
| `create_contacts` | Create Contacts | Can add new contacts |
| `edit_contacts` | Edit Contacts | Can edit existing contacts |
| `delete_contacts` | Delete Contacts | Can delete contacts |
| `import_contacts` | Import Contacts | Can import contacts from CSV |
| `manage_permissions` | Manage Permissions | Can assign/revoke permissions |
| `manage_agents` | Manage Agents | Can assign/revoke agent designations |
| `view_audit_logs` | View Audit Logs | Can view system audit logs |

---

## 🎯 Next Steps

1. **Run Migrations**
   ```bash
   python manage.py makemigrations accounts
   python manage.py migrate accounts
   ```

2. **Seed Permissions**
   ```bash
   python manage.py seed_permissions
   ```

3. **Create SuperAdmin**
   ```bash
   python manage.py createsuperuser
   # Set role to 'superadmin' in Django admin or shell
   ```

4. **Test in Django Shell**
   ```bash
   python manage.py shell
   >>> from callfairy.apps.accounts.models import *
   >>> # Test agent assignment, permissions, etc.
   ```

5. **Implement API Views**
   - Use provided permission classes
   - Add agent management endpoints
   - Add permission management endpoints

6. **Add Frontend Integration**
   - Check permissions in templates
   - Show/hide UI based on permissions
   - Display user's role and managed organisation

---

## ✅ Implementation Checklist

- [x] Agent model created
- [x] AgentPermissions model created
- [x] User model extended with permission methods
- [x] Utility functions created
- [x] DRF permission classes created
- [x] Signals for role synchronization
- [x] Management command for seeding
- [ ] Run migrations
- [ ] Seed permissions
- [ ] Create test data
- [ ] Test agent assignment
- [ ] Test permission checking
- [ ] Create API views
- [ ] Add frontend integration
- [ ] Write unit tests
- [ ] Deploy to production

---

**🎉 Your multi-tenant permission system is ready to use!**

For questions or issues, refer to this guide or check the inline code documentation.
