# 🚀 Multi-Tenant Permission System - Quick Start

## ⚡ 3-Minute Setup

### Step 1: Run Migrations
```bash
python manage.py makemigrations accounts
python manage.py migrate accounts
```

### Step 2: Seed Permissions
```bash
python manage.py seed_permissions
```

### Step 3: Test in Shell
```bash
python manage.py shell
```

```python
from callfairy.apps.accounts.models import *

# Create test data
admin = User.objects.create(email='admin@test.com', name='Admin', role='superadmin', is_active=True)
admin.set_password('admin123')
admin.save()

user = User.objects.create(email='john@test.com', name='John', role='user', is_active=True)
user.set_password('user123')
user.save()

org = Organisation.objects.create(name='Test Org', city='NYC', is_active=True)

# Assign agent
agent = Agent.assign_agent(user, org, admin)

# Check results
user.refresh_from_db()
print(f"✓ User role: {user.role}")  # superuser
print(f"✓ Is agent: {user.is_agent()}")  # True
print(f"✓ Manages: {user.get_managed_organisation()}")  # Test Org

# Grant permission
perm = Permission.objects.get(key='view_reports')
AgentPermissions.grant_permission(agent, perm, admin)
print(f"✓ Has permission: {user.has_permission('view_reports')}")  # True
```

---

## 📁 Files Created

```
callfairy/apps/accounts/
├── models.py                    [MODIFIED] - Added Agent, AgentPermissions
├── permissions.py               [MODIFIED] - Added 5 new permission classes
├── signals.py                   [NEW] - Auto role synchronization
├── apps.py                      [MODIFIED] - Import signals
├── utils/
│   ├── __init__.py             [NEW]
│   └── permissions.py          [NEW] - 8 utility functions
├── management/commands/
│   └── seed_permissions.py     [NEW] - Seed 25 permissions
└── example_views.py            [NEW] - 10+ API view examples

Documentation:
├── MULTI_TENANT_PERMISSION_SYSTEM.md  - Complete guide
├── IMPLEMENTATION_COMPLETE.md         - Implementation details
└── QUICK_START.md                     - This file
```

---

## 🎯 Key Models

### Agent (New)
```python
Agent.assign_agent(user, organisation, assigned_by)
Agent.revoke_agent(agent_id, revoked_by)
```

### AgentPermissions (New)
```python
AgentPermissions.grant_permission(agent, permission, granted_by)
AgentPermissions.revoke_permission(agent, permission)
```

### User (Extended)
```python
user.is_agent()                    # Check if agent
user.get_managed_organisation()    # Get managed org
user.has_permission('key')         # Check permission
user.get_all_permissions()         # Get all perms
```

---

## 🔑 Permission Classes (DRF)

```python
from callfairy.apps.accounts.permissions import (
    IsSuperAdmin,              # SuperAdmin only
    IsAgentOfOrganisation,     # Agent of specific org
    HasPermissionKey,          # Has specific permission
    CanManageOrganisation,     # Can manage org
    CanAccessOrganisation,     # Can access org data
    HasOrganisationPermission, # Permission + org context
)

# Usage in views
class MyView(APIView):
    permission_classes = [HasOrganisationPermission]
    permission_required = 'view_reports'
```

---

## 🛠️ Utility Functions

```python
from callfairy.apps.accounts.utils import (
    check_user_permission,              # Check with org context
    get_user_accessible_organisations,  # Get accessible orgs
    can_user_manage_organisation,       # Check management rights
    get_permission_summary,             # Get complete summary
)

# Usage
orgs = get_user_accessible_organisations(request.user)
can_view = check_user_permission(user, 'view_reports', org)
```

---

## 📝 Quick Examples

### Example 1: Assign Agent
```python
agent = Agent.assign_agent(
    user=john,
    organisation=acme,
    assigned_by=admin
)
# john.role is now 'superuser' automatically
```

### Example 2: Grant Permissions
```python
perm = Permission.objects.get(key='view_reports')
AgentPermissions.grant_permission(agent, perm, admin)
# john can now view reports for acme
```

### Example 3: API View with Permission
```python
class ReportsView(APIView):
    permission_classes = [HasOrganisationPermission]
    permission_required = 'view_reports'
    
    def get(self, request, org_id):
        org = get_object_or_404(Organisation, id=org_id)
        self.check_object_permissions(request, org)
        # User has permission for this org
```

---

## 🎨 Complete API Example

```python
# urls.py
from .example_views import *

urlpatterns = [
    path('agents/assign/', AssignAgentView.as_view()),
    path('organisations/', OrganisationListView.as_view()),
    path('organisations/<int:org_id>/', OrganisationDetailView.as_view()),
    path('me/permissions/', MyPermissionsView.as_view()),
]

# Test
curl -X POST http://localhost:8000/api/agents/assign/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{"user_id": "UUID", "organisation_id": 1}'
```

---

## ✅ Verification Checklist

- [ ] Migrations run successfully
- [ ] 25 permissions seeded
- [ ] Test agent assignment works
- [ ] Role syncs automatically (user → superuser)
- [ ] Permissions check correctly
- [ ] API endpoints created
- [ ] Permission classes work in views

---

## 📚 Documentation

**Full Guide:** `MULTI_TENANT_PERMISSION_SYSTEM.md`
- Complete system overview
- Usage examples
- Testing guide
- Best practices

**Implementation Details:** `IMPLEMENTATION_COMPLETE.md`
- What was implemented
- File structure
- Migration strategy

**Example Code:** `callfairy/apps/accounts/example_views.py`
- 10+ ready-to-use API views
- Copy-paste friendly

---

## 🎉 You're Ready!

Your multi-tenant permission system is complete. Run migrations and start using it!

**Next:** `python manage.py makemigrations accounts`
