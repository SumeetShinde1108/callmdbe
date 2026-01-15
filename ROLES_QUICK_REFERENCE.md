# 🚀 User Roles - Quick Reference Card

## 3 Roles. 1 Minute. Everything You Need.

---

## 👑 SuperAdmin

```yaml
Role: superadmin
Count: 1-5 (limited)
Scope: Platform-wide
Assignment: Manual (createsuperuser)

Access:
  - ALL organisations ✅
  - ALL users ✅
  - ALL permissions ✅ (automatic bypass)
  - System settings ✅
  - Agent management ✅

Can Do:
  - Assign/revoke agents
  - Grant/revoke permissions
  - Manage all organisations
  - View all data
  - Configure system

Cannot Do:
  - Nothing restricted

API Endpoints:
  - Full access to all 22 endpoints
  - Only role that can access /agents/* endpoints
```

**Quick Check:**
```javascript
if (user.role === 'superadmin') {
  // Can do ANYTHING
  return true;
}
```

---

## 👔 Agent / SuperUser

```yaml
Role: superuser
Count: 1 per organisation
Scope: Organisation-level
Assignment: Automatic (when assigned as agent)

Access:
  - THEIR organisation ✅
  - GRANTED permissions only 🔒
  - Organisation users 🔒 (if permission granted)
  - Organisation data 🔒 (if permission granted)

Can Do:
  - Manage their organisation
  - Features based on granted permissions
  - View/edit org details
  - Access org-specific data

Cannot Do:
  - Access other organisations ❌
  - Assign agents ❌
  - Grant permissions ❌
  - Access system settings ❌
  - View all users ❌

API Endpoints:
  - /me/ ✅
  - /organisations/ ✅ (only theirs)
  - /organisations/{their_id}/ ✅
  - /organisations/{their_id}/update/ ✅
  - /agents/* ❌ (all forbidden)

Role Change:
  Assigned → role: 'user' → 'superuser'
  Revoked  → role: 'superuser' → 'user'
```

**Quick Check:**
```javascript
if (user.is_agent && user.managed_organisation?.id === orgId) {
  // Can manage THIS org
  // Check permissions for features
}
```

---

## 👤 Regular User

```yaml
Role: user
Count: Unlimited
Scope: Member-level
Assignment: Default (on registration)

Access:
  - MEMBER organisations ✅ (read-only)
  - Own profile ✅
  - Minimal permissions ❌

Can Do:
  - View own profile
  - View member organisations
  - Update own settings

Cannot Do:
  - Manage organisations ❌
  - Manage users ❌
  - Access agent features ❌
  - Access system features ❌

API Endpoints:
  - /me/ ✅
  - /organisations/ ✅ (member orgs only)
  - /organisations/{member_id}/ ✅ (read-only)
  - /organisations/{id}/update/ ❌
  - /agents/* ❌
```

**Quick Check:**
```javascript
if (user.role === 'user' && !user.is_agent) {
  // Limited access
  // Mostly read-only
}
```

---

## 🎯 At a Glance

| Feature | SuperAdmin | Agent | User |
|---------|------------|-------|------|
| **Organisations** | All | Own | Member |
| **Users** | All | Own Org* | None |
| **Permissions** | All | Granted | None |
| **Agent Mgmt** | Yes | No | No |
| **System** | Yes | No | No |

`*` If permission granted

---

## 🔑 Permission Examples

### 24 Total Permissions

**Users (4):**
- view_users
- create_users
- edit_users
- delete_users

**Organisations (3):**
- view_organisations
- manage_organisation
- edit_organisation_settings

**Reports (3):**
- view_reports
- export_reports
- view_analytics

**Calls (4):**
- make_calls
- view_calls
- manage_campaigns
- view_call_recordings

**Contacts (5):**
- view_contacts
- create_contacts
- edit_contacts
- delete_contacts
- import_contacts

**System (5) - SuperAdmin Only:**
- manage_permissions
- manage_agents
- view_system_settings
- edit_system_settings
- view_audit_logs

---

## 💻 Frontend Code Snippets

### Check Role
```javascript
const isSuperAdmin = user.role === 'superadmin';
const isAgent = user.is_agent;
const isUser = user.role === 'user' && !user.is_agent;
```

### Check Permission
```javascript
const hasPermission = (key) => {
  if (user.role === 'superadmin') return true;
  return user.all_permissions?.includes(key) || false;
};
```

### Check Org Access
```javascript
const canManageOrg = (orgId) => {
  if (user.role === 'superadmin') return true;
  return user.is_agent && 
         user.managed_organisation?.id === orgId;
};
```

### Show/Hide UI
```javascript
{isSuperAdmin && <AgentManagement />}
{isAgent && <MyOrganisation />}
{hasPermission('view_reports') && <Reports />}
```

---

## 🔐 API Response Examples

### SuperAdmin Login Response
```json
{
  "role": "superadmin",
  "role_display": "Super Admin",
  "is_agent": false,
  "managed_organisation": null,
  "all_permissions": ["all 24 permissions"],
  "accessible_organisations": [/* all orgs */]
}
```

### Agent Login Response
```json
{
  "role": "superuser",
  "role_display": "Super User",
  "is_agent": true,
  "managed_organisation": {
    "id": 1,
    "name": "Acme Corp"
  },
  "agent_permissions": [
    "manage_organisation",
    "view_reports"
  ],
  "accessible_organisations": [
    {"id": 1, "name": "Acme Corp"}
  ]
}
```

### User Login Response
```json
{
  "role": "user",
  "role_display": "User",
  "is_agent": false,
  "managed_organisation": null,
  "all_permissions": [],
  "accessible_organisations": [/* member orgs */]
}
```

---

## 📋 Decision Matrix

### "Should I show this button?"

```
Is user SuperAdmin?
  YES → SHOW ✅
  NO → Continue...

Is feature agent-only (assign agent, grant perm)?
  YES → HIDE ❌
  NO → Continue...

Does feature need permission?
  NO → SHOW ✅
  YES → User has permission?
    YES → SHOW ✅
    NO → HIDE ❌
```

---

## 🎨 UI Layout by Role

### SuperAdmin Dashboard
```
┌──────────────────────────────┐
│ Welcome, Super Admin         │
├──────────────────────────────┤
│ • All Organisations (50)     │
│ • All Users (500)            │
│ • Agent Management ⭐        │
│ • System Settings ⭐         │
│ • All Reports                │
│ • Audit Logs ⭐              │
└──────────────────────────────┘
```

### Agent Dashboard
```
┌──────────────────────────────┐
│ Welcome, John (Agent)        │
├──────────────────────────────┤
│ • My Organisation: Acme Corp │
│ • Manage Organisation        │
│ • View Reports 🔒            │
│ • View Calls 🔒              │
│ • Manage Users 🔒            │
└──────────────────────────────┘
🔒 = If permission granted
```

### User Dashboard
```
┌──────────────────────────────┐
│ Welcome, Regular User        │
├──────────────────────────────┤
│ • My Profile                 │
│ • Member Organisations (2)   │
│   ├─ View Org 1              │
│   └─ View Org 2              │
└──────────────────────────────┘
```

---

## ⚡ Quick Tests

### Test SuperAdmin
```bash
curl -H "Authorization: Bearer SUPERADMIN_TOKEN" \
  /api/accounts/agents/
# Expected: 200 OK (list of agents)
```

### Test Agent
```bash
curl -H "Authorization: Bearer AGENT_TOKEN" \
  /api/accounts/agents/
# Expected: 403 Forbidden

curl -H "Authorization: Bearer AGENT_TOKEN" \
  /api/accounts/organisations/
# Expected: 200 OK (only their org)
```

### Test User
```bash
curl -H "Authorization: Bearer USER_TOKEN" \
  /api/accounts/organisations/1/update/
# Expected: 403 Forbidden
```

---

## 🎯 Remember

### Golden Rules

1. **SuperAdmin** = Everything allowed
2. **Agent** = Only their org + permissions
3. **User** = Very limited access

### Always Check

```javascript
// In every component
const user = useAuth();

// Then check:
user.role === 'superadmin'  // SuperAdmin?
user.is_agent               // Agent?
user.all_permissions        // Has permission?
```

### Common Mistakes

❌ **DON'T:**
```javascript
// Wrong - doesn't check SuperAdmin
if (user.all_permissions.includes('view_reports'))
```

✅ **DO:**
```javascript
// Correct - SuperAdmin bypass
if (user.role === 'superadmin' || 
    user.all_permissions.includes('view_reports'))
```

---

## 📚 Full Documentation

For complete details, see:
- **USER_ROLES_DOCUMENTATION.md** - Full role guide
- **ROLE_BASED_ACCESS_CONTROL_MATRIX.md** - Access control matrix
- **API_TESTING_GUIDE.md** - API testing examples

---

**Quick Reference Complete** ✅

Print this, bookmark it, keep it handy! 🚀
