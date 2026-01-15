# 👥 User Roles & Permissions - Complete Documentation

## Overview

This document defines all user roles in the multi-tenant permission system, their accessible views, modules, and permissions aligned with business rules.

---

## 📊 User Role Hierarchy

```
┌─────────────────────────────────────────────┐
│          SuperAdmin (Platform Level)        │
│          ✓ Full System Access               │
└─────────────────┬───────────────────────────┘
                  │
     ┌────────────┴────────────┐
     ▼                         ▼
┌──────────────┐      ┌──────────────┐
│Agent/SuperUser│      │Regular User  │
│(Org Level)    │      │(Member Level)│
└──────────────┘      └──────────────┘
```

---

## 🔐 Role Definitions

### 1. SuperAdmin
- **Database Value:** `role = 'superadmin'`
- **Display Name:** "Super Admin"
- **Level:** Platform-wide administrator
- **Assignment:** Manual (createsuperuser or admin panel)
- **Count:** Limited (1-5 recommended)

### 2. Agent / SuperUser
- **Database Value:** `role = 'superuser'`
- **Display Name:** "Super User"
- **Level:** Organisation administrator
- **Assignment:** Automatic (when assigned as agent)
- **Count:** 1 per organisation (active)
- **Revocation:** Role downgrades to 'user' when revoked

### 3. Regular User
- **Database Value:** `role = 'user'`
- **Display Name:** "User"
- **Level:** Organisation member
- **Assignment:** Default for all new users
- **Count:** Unlimited

---

## 🎭 Role 1: SuperAdmin

### Business Rules
- ✅ Has access to ALL organisations
- ✅ Can assign/revoke agents for any organisation
- ✅ Can grant/revoke permissions to any agent
- ✅ Has ALL permissions automatically (bypass)
- ✅ Can manage system-wide settings
- ✅ Can view audit logs
- ✅ Read/Write access to everything

### Post-Login Dashboard View

#### Profile Information
```json
{
  "id": "uuid",
  "email": "superadmin@test.com",
  "name": "Super Admin",
  "role": "superadmin",
  "role_display": "Super Admin",
  "is_agent": false,
  "managed_organisation": null,
  "accessible_organisations": ["All organisations in system"],
  "all_permissions": ["All 24 permissions automatically"]
}
```

### Accessible API Endpoints

#### ✅ Full Access (All Endpoints)

**Authentication (11):**
- `POST /api/accounts/register/`
- `POST /api/accounts/login/`
- `POST /api/accounts/login/google/`
- `POST /api/accounts/token/refresh/`
- `POST /api/accounts/verify-email/`
- `POST /api/accounts/password/reset/`
- `POST /api/accounts/password/reset/confirm/`
- `POST /api/accounts/2fa/totp/enable/`
- `POST /api/accounts/2fa/totp/verify/`
- `POST /api/accounts/2fa/totp/disable/`
- `GET /api/accounts/me/`

**User Profile (3):**
- `GET /api/accounts/me/` - Full profile with all permissions
- `GET /api/accounts/me/permissions/` - Permission summary
- `GET /api/accounts/me/organisations/` - All organisations

**Organisations (3):**
- `GET /api/accounts/organisations/` - List ALL organisations
- `GET /api/accounts/organisations/{id}/` - Any organisation details
- `PATCH /api/accounts/organisations/{id}/update/` - Update ANY organisation

**Agent Management (5) - SuperAdmin ONLY:**
- `GET /api/accounts/agents/` - List all agents
- `POST /api/accounts/agents/assign/` - Assign agent to org
- `POST /api/accounts/agents/{id}/revoke/` - Revoke agent
- `POST /api/accounts/agents/{id}/permissions/grant/` - Grant permission
- `DELETE /api/accounts/agents/{id}/permissions/{key}/` - Revoke permission

**Permissions (1):**
- `GET /api/accounts/permissions/` - List all 24 permissions

### Accessible Modules

#### ✅ Platform Administration
- User Management (all users)
- Organisation Management (all orgs)
- Agent Assignment & Revocation
- Permission Management
- System Configuration
- Audit Logs (if implemented)

#### ✅ Organisation Features
- View all organisations
- Manage all organisations
- Access all org data
- View all users in all orgs
- Full CRUD on all resources

#### ✅ Reporting & Analytics
- System-wide reports
- All organisation reports
- User activity logs
- Permission usage analytics

### Permission Bypass Logic
```python
# SuperAdmin has ALL permissions automatically
def has_permission(user, permission_key):
    if user.role == 'superadmin':
        return True  # Bypass - automatic access
    # ... check permissions
```

### UI/Frontend Visibility

**Navigation Menu:**
```
Dashboard
├── My Profile
├── System Management
│   ├── All Organisations
│   ├── All Users
│   ├── Agent Management ⭐ (SuperAdmin only)
│   └── System Settings ⭐ (SuperAdmin only)
├── Permissions
│   ├── View All Permissions
│   ├── Manage Agent Permissions ⭐
│   └── Audit Logs ⭐
├── Reports & Analytics
│   └── System-wide Reports ⭐
└── Settings
```

### Business Logic Examples

**Organisation Access:**
```python
# SuperAdmin can access ANY organisation
orgs = get_user_accessible_organisations(superadmin_user)
# Returns: QuerySet of ALL organisations
```

**Permission Check:**
```python
# SuperAdmin bypasses all permission checks
can_delete_users = check_user_permission(superadmin_user, 'delete_users')
# Returns: True (automatic)
```

---

## 👔 Role 2: Agent / SuperUser

### Business Rules
- ✅ Manages ONE organisation (1:1 relationship)
- ✅ Has only GRANTED permissions
- ✅ Cannot assign other agents
- ✅ Can manage their organisation
- ✅ Can view/manage users in their org
- ✅ Role automatically upgraded when assigned
- ✅ Role automatically downgraded when revoked
- ❌ Cannot access other organisations
- ❌ Cannot grant permissions
- ❌ No system-wide access

### Post-Login Dashboard View

#### Profile Information
```json
{
  "id": "uuid",
  "email": "agent@acme.com",
  "name": "John Agent",
  "role": "superuser",
  "role_display": "Super User",
  "is_agent": true,
  "managed_organisation": {
    "id": 1,
    "name": "Acme Corp",
    "city": "New York"
  },
  "agent_permissions": [
    {"key": "manage_organisation", "name": "Manage Organisation"},
    {"key": "view_reports", "name": "View Reports"},
    {"key": "view_calls", "name": "View Calls"}
  ],
  "all_permissions": ["Only granted permissions"],
  "accessible_organisations": [
    {"id": 1, "name": "Acme Corp"}
  ]
}
```

### Accessible API Endpoints

#### ✅ Allowed Endpoints

**Authentication (11):**
- All authentication endpoints (same as SuperAdmin)

**User Profile (3):**
- `GET /api/accounts/me/` - Own profile with org info
- `GET /api/accounts/me/permissions/` - Own permissions
- `GET /api/accounts/me/organisations/` - Only their org

**Organisations (3):**
- `GET /api/accounts/organisations/` - Only THEIR organisation
- `GET /api/accounts/organisations/{their_org_id}/` - Their org details
- `PATCH /api/accounts/organisations/{their_org_id}/update/` - Update their org

**Permissions (1):**
- `GET /api/accounts/permissions/` - List all permissions (read-only)

#### ❌ Restricted Endpoints

**Agent Management (5) - FORBIDDEN:**
- `GET /api/accounts/agents/` - ❌ 403 Forbidden
- `POST /api/accounts/agents/assign/` - ❌ 403 Forbidden
- `POST /api/accounts/agents/{id}/revoke/` - ❌ 403 Forbidden
- `POST /api/accounts/agents/{id}/permissions/grant/` - ❌ 403 Forbidden
- `DELETE /api/accounts/agents/{id}/permissions/{key}/` - ❌ 403 Forbidden

**Other Organisations:**
- `GET /api/accounts/organisations/{other_org_id}/` - ❌ 403 Forbidden
- `PATCH /api/accounts/organisations/{other_org_id}/update/` - ❌ 403 Forbidden

### Accessible Modules

#### ✅ Organisation Management
- View their organisation details
- Update their organisation
- Manage users in their org (if permission granted)
- View organisation reports (if permission granted)

#### ✅ Permission-Based Features
Depends on granted permissions:

**If granted `manage_organisation`:**
- Edit organisation settings
- Manage organisation details

**If granted `view_users`:**
- View users in their organisation

**If granted `create_users`:**
- Add users to their organisation

**If granted `view_reports`:**
- View organisation reports

**If granted `view_calls`:**
- View call records for their org

**If granted `manage_campaigns`:**
- Manage marketing campaigns

### Permission Logic
```python
# Agent has ONLY granted permissions
def has_permission(user, permission_key):
    if user.role == 'superadmin':
        return True  # Bypass
    
    if user.role == 'superuser':
        # Check granted agent permissions
        return user.get_agent_permissions().filter(key=permission_key).exists()
    
    # Regular user logic...
```

### UI/Frontend Visibility

**Navigation Menu:**
```
Dashboard
├── My Profile
├── My Organisation ⭐
│   ├── Organisation Details
│   ├── Edit Organisation (if manage_organisation)
│   └── Organisation Users (if view_users)
├── Features (permission-based)
│   ├── View Reports (if view_reports)
│   ├── Manage Campaigns (if manage_campaigns)
│   ├── View Calls (if view_calls)
│   └── Manage Users (if create_users/edit_users)
└── Settings
    └── My Account
```

### Business Logic Examples

**Organisation Access:**
```python
# Agent can access ONLY their organisation
orgs = get_user_accessible_organisations(agent_user)
# Returns: QuerySet with 1 organisation (their managed org)
```

**Permission Check:**
```python
# Agent permissions are checked
can_view_reports = check_user_permission(agent_user, 'view_reports', org)
# Returns: True only if permission was granted
```

**Automatic Role Sync:**
```python
# When assigned as agent
Agent.assign_agent(user, org, superadmin)
# Signal fires → user.role changes from 'user' to 'superuser'

# When revoked
agent.is_active = False
agent.save()
# Signal fires → user.role changes from 'superuser' to 'user'
```

---

## 👤 Role 3: Regular User

### Business Rules
- ✅ Default role for all new users
- ✅ Can access organisations they're members of
- ✅ Has only DIRECT permissions (if granted)
- ✅ Cannot manage organisations
- ✅ Read-only access mostly
- ❌ Cannot be agent
- ❌ Cannot manage other users
- ❌ No administrative access

### Post-Login Dashboard View

#### Profile Information
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "Regular User",
  "role": "user",
  "role_display": "User",
  "is_agent": false,
  "managed_organisation": null,
  "direct_permissions": [],
  "agent_permissions": [],
  "all_permissions": [],
  "accessible_organisations": [
    "Only organisations where they have UserOrganisation membership"
  ]
}
```

### Accessible API Endpoints

#### ✅ Allowed Endpoints

**Authentication (11):**
- All authentication endpoints (same as others)

**User Profile (3):**
- `GET /api/accounts/me/` - Own profile
- `GET /api/accounts/me/permissions/` - Own permissions (usually empty)
- `GET /api/accounts/me/organisations/` - Member organisations

**Organisations (1-2):**
- `GET /api/accounts/organisations/` - Only member organisations
- `GET /api/accounts/organisations/{member_org_id}/` - Details of member orgs

**Permissions (1):**
- `GET /api/accounts/permissions/` - List permissions (read-only)

#### ❌ Restricted Endpoints

**Organisation Management:**
- `PATCH /api/accounts/organisations/{id}/update/` - ❌ 403 Forbidden

**Agent Management (all):**
- All agent endpoints - ❌ 403 Forbidden

**Non-member Organisations:**
- `GET /api/accounts/organisations/{non_member_org}/` - ❌ 403 Forbidden

### Accessible Modules

#### ✅ Limited Access
- View own profile
- View organisations they're members of
- Access features based on direct permissions (rare)

#### ❌ No Access
- Cannot manage organisations
- Cannot view other organisations
- Cannot manage users
- Cannot access admin features

### Permission Logic
```python
# Regular user has very limited permissions
def has_permission(user, permission_key):
    if user.role == 'superadmin':
        return True
    
    if user.role == 'superuser':
        return user.get_agent_permissions().filter(key=permission_key).exists()
    
    # Regular user - check direct permissions (rarely granted)
    return user.get_direct_permissions().filter(key=permission_key).exists()
```

### UI/Frontend Visibility

**Navigation Menu:**
```
Dashboard
├── My Profile
├── My Organisations (read-only)
│   └── View organisations I'm a member of
└── Settings
    └── My Account
```

### Business Logic Examples

**Organisation Access:**
```python
# User can access only member organisations
orgs = get_user_accessible_organisations(regular_user)
# Returns: QuerySet of organisations where UserOrganisation exists
```

**Permission Check:**
```python
# Regular user has minimal permissions
can_manage = check_user_permission(regular_user, 'manage_organisation', org)
# Returns: False (unless directly granted - rare)
```

---

## 📋 Permission Matrix

### Complete Permission List (24 Permissions)

| Category | Permission Key | SuperAdmin | Agent | User |
|----------|----------------|------------|-------|------|
| **Users** | view_users | ✅ Auto | 🔒 If Granted | ❌ No |
| | create_users | ✅ Auto | 🔒 If Granted | ❌ No |
| | edit_users | ✅ Auto | 🔒 If Granted | ❌ No |
| | delete_users | ✅ Auto | 🔒 If Granted | ❌ No |
| **Organisations** | view_organisations | ✅ Auto | 🔒 If Granted | ❌ No |
| | manage_organisation | ✅ Auto | 🔒 If Granted | ❌ No |
| | edit_organisation_settings | ✅ Auto | 🔒 If Granted | ❌ No |
| **Reports** | view_reports | ✅ Auto | 🔒 If Granted | ❌ No |
| | export_reports | ✅ Auto | 🔒 If Granted | ❌ No |
| | view_analytics | ✅ Auto | 🔒 If Granted | ❌ No |
| **Calls** | make_calls | ✅ Auto | 🔒 If Granted | ❌ No |
| | view_calls | ✅ Auto | 🔒 If Granted | ❌ No |
| | manage_campaigns | ✅ Auto | 🔒 If Granted | ❌ No |
| | view_call_recordings | ✅ Auto | 🔒 If Granted | ❌ No |
| **Contacts** | view_contacts | ✅ Auto | 🔒 If Granted | ❌ No |
| | create_contacts | ✅ Auto | 🔒 If Granted | ❌ No |
| | edit_contacts | ✅ Auto | 🔒 If Granted | ❌ No |
| | delete_contacts | ✅ Auto | 🔒 If Granted | ❌ No |
| | import_contacts | ✅ Auto | 🔒 If Granted | ❌ No |
| **System** | manage_permissions | ✅ Auto | ❌ No | ❌ No |
| | manage_agents | ✅ Auto | ❌ No | ❌ No |
| | view_system_settings | ✅ Auto | ❌ No | ❌ No |
| | edit_system_settings | ✅ Auto | ❌ No | ❌ No |
| | view_audit_logs | ✅ Auto | ❌ No | ❌ No |

**Legend:**
- ✅ **Auto** - Automatic (bypass)
- 🔒 **If Granted** - Only if permission explicitly granted
- ❌ **No** - Not available

---

## 🔄 Role Lifecycle

### User Journey

#### 1. New User Registration
```
Register → Email Verified → role = 'user'
```

#### 2. Promoted to Agent
```
SuperAdmin assigns → role changes: 'user' → 'superuser'
                  → Agent record created
                  → Permissions can be granted
```

#### 3. Agent Revoked
```
SuperAdmin revokes → role changes: 'superuser' → 'user'
                   → Agent.is_active = False
                   → Permissions lost
```

### Automatic Role Synchronization

**Via Django Signals:**
```python
@receiver(post_save, sender=Agent)
def sync_user_role(sender, instance, **kwargs):
    if instance.is_active:
        # Upgrade to superuser
        instance.user.role = 'superuser'
    else:
        # Downgrade to user
        instance.user.role = 'user'
    instance.user.save()
```

---

## 🎯 Business Rule Enforcement

### Rule 1: One Agent Per Organisation
```python
# Enforced by database constraint
class Meta:
    constraints = [
        UniqueConstraint(
            fields=['organisation'],
            condition=Q(is_active=True),
            name='unique_active_agent_per_org'
        )
    ]
```

### Rule 2: SuperAdmin Bypass
```python
def has_permission(self, permission_key, organisation=None):
    # SuperAdmin bypasses all checks
    if self.role == 'superadmin':
        return True
    # ... other logic
```

### Rule 3: Agent Organisation Isolation
```python
def get_user_accessible_organisations(user):
    if user.role == 'superadmin':
        return Organisation.objects.all()
    
    if user.is_agent():
        # Only their managed organisation
        return Organisation.objects.filter(agents__user=user, agents__is_active=True)
    
    # Regular users: member organisations
    return Organisation.objects.filter(members__user=user)
```

---

## 📊 Visual Role Comparison

```
┌────────────────────────────────────────────────────────────┐
│                     FEATURE MATRIX                         │
├────────────────────────┬─────────┬─────────┬──────────────┤
│ Feature                │SuperAdmin│  Agent  │ Regular User │
├────────────────────────┼─────────┼─────────┼──────────────┤
│ Manage All Orgs        │    ✅    │   ❌    │      ❌      │
│ Manage Own Org         │    ✅    │   ✅    │      ❌      │
│ Assign Agents          │    ✅    │   ❌    │      ❌      │
│ Grant Permissions      │    ✅    │   ❌    │      ❌      │
│ View All Users         │    ✅    │   ❌    │      ❌      │
│ View Org Users         │    ✅    │   🔒    │      ❌      │
│ Access All Orgs        │    ✅    │   ❌    │      ❌      │
│ Access Own Org         │    ✅    │   ✅    │      ❌      │
│ Access Member Orgs     │    ✅    │   N/A   │      ✅      │
│ All Permissions        │    ✅    │   ❌    │      ❌      │
│ Granted Permissions    │    ✅    │   ✅    │      🔒      │
│ Update Profile         │    ✅    │   ✅    │      ✅      │
└────────────────────────┴─────────┴─────────┴──────────────┘

✅ = Yes/Allowed
❌ = No/Forbidden
🔒 = If Permission Granted
```

---

## 🔍 Testing Role Access

### SuperAdmin Test
```bash
# Login as SuperAdmin
TOKEN=$(curl -s -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@test.com","password":"admin123"}' \
  | jq -r '.access')

# Test access to all orgs
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/accounts/organisations/
# Expected: All organisations

# Test agent management
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/accounts/agents/
# Expected: 200 OK with agent list
```

### Agent Test
```bash
# Login as Agent
TOKEN=$(curl -s -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"agent@test.com","password":"user123"}' \
  | jq -r '.access')

# Test access to own org
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/accounts/me/
# Expected: Profile with managed_organisation

# Test agent management (should fail)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/accounts/agents/
# Expected: 403 Forbidden
```

### Regular User Test
```bash
# Login as User
TOKEN=$(curl -s -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"user123"}' \
  | jq -r '.access')

# Test org access
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/accounts/organisations/
# Expected: Empty or member organisations only
```

---

## 📝 Summary

### Role Capabilities at a Glance

**SuperAdmin:**
- 🌐 Platform-wide access
- 👥 Manage all users & organisations
- 🔐 All permissions automatically
- ⚙️ System configuration
- 📊 All reports & analytics

**Agent/SuperUser:**
- 🏢 One organisation management
- 🔒 Permission-based features
- 👔 Organisation administration
- 📈 Org-specific reports
- ❌ No system-wide access

**Regular User:**
- 👤 Personal profile only
- 📋 View member organisations
- 👀 Read-only mostly
- ❌ No management capabilities
- ❌ Minimal permissions

---

**Documentation Complete** ✅  
All roles documented with their post-login views, accessible modules, and permissions aligned with business rules.
