# 🔐 Role Permission Assignments - Default Configuration

## Overview

This document defines the default permissions assigned to each role when users are created or promoted.

---

## 🎯 Permission Assignment Strategy

### Core Principle
```
SuperAdmin  → ALL permissions (automatic bypass)
Agent       → Manually granted by SuperAdmin (flexible)
User        → NO permissions by default (read-only)
```

---

## 👑 SuperAdmin - Automatic Permissions

**Assignment:** Automatic (all permissions via bypass)  
**Count:** All 24 permissions  
**Method:** Code-level bypass (no database records needed)

### Logic
```python
if user.role == 'superadmin':
    return True  # Has all permissions automatically
```

### Permissions Included
✅ ALL 24 permissions automatically without database storage

---

## 👔 Agent/SuperUser - Suggested Default Permissions

**Assignment:** Manual by SuperAdmin  
**Recommended Defaults:** 5-8 permissions  
**Method:** Database records in `AgentPermissions`

### Recommended Starter Package
When assigning a new agent, SuperAdmin should grant these by default:

#### Must-Have (Core Agent Permissions)
1. **manage_organisation** - Edit their organisation details
2. **view_users** - See users in their organisation  
3. **view_reports** - Access organisation reports

#### Recommended (Common Needs)
4. **view_contacts** - View organisation contacts
5. **view_calls** - See call history

#### Optional (Based on Agent Role)
6. **create_users** - Add new users to organisation
7. **edit_users** - Modify user details
8. **create_contacts** - Add new contacts
9. **make_calls** - Make outbound calls
10. **manage_campaigns** - Manage calling campaigns

### Permission Tiers

#### 🥉 Basic Agent (View Only)
```yaml
Permissions (3):
  - manage_organisation
  - view_users
  - view_reports

Use Case: Junior agents, viewers
```

#### 🥈 Standard Agent (Most Common)
```yaml
Permissions (6):
  - manage_organisation
  - view_users
  - view_reports
  - view_contacts
  - view_calls
  - create_contacts

Use Case: Regular organisation managers
```

#### 🥇 Advanced Agent (Full Control)
```yaml
Permissions (10):
  - manage_organisation
  - view_users
  - create_users
  - edit_users
  - view_reports
  - view_contacts
  - create_contacts
  - view_calls
  - make_calls
  - manage_campaigns

Use Case: Senior agents, power users
```

---

## 👤 Regular User - Default Permissions

**Assignment:** None by default  
**Count:** 0 permissions  
**Access:** Read-only to member organisations

### Default Access (No Permissions Needed)
- ✅ View own profile
- ✅ View member organisations (read-only)
- ✅ Update own account settings

### Why No Permissions?
Regular users are typically organisation members with minimal access. If they need more, they should be made agents.

---

## 📊 Permission Categories & Assignment Rules

### Users Category
```yaml
view_users: ✅ Agents (recommended)
create_users: 🔶 Agents (if they manage team)
edit_users: 🔶 Agents (if they manage team)
delete_users: ❌ Not recommended (data safety)
```

### Organisations Category
```yaml
view_organisations: ✅ Agents (automatic via their org)
manage_organisation: ✅ Agents (MUST have for their org)
edit_organisation_settings: 🔶 Agents (advanced settings)
```

### Reports Category
```yaml
view_reports: ✅ Agents (recommended)
export_reports: 🔶 Agents (if they need exports)
view_analytics: 🔶 Agents (if they need analytics)
```

### Calls Category
```yaml
make_calls: 🔶 Agents (if they make calls)
view_calls: ✅ Agents (recommended)
manage_campaigns: 🔶 Agents (if they run campaigns)
view_call_recordings: 🔶 Agents (if recordings needed)
```

### Contacts Category
```yaml
view_contacts: ✅ Agents (recommended)
create_contacts: ✅ Agents (recommended)
edit_contacts: 🔶 Agents (if they manage contacts)
delete_contacts: ❌ Not recommended (data safety)
import_contacts: 🔶 Agents (if they import data)
```

### System Category
```yaml
manage_permissions: ❌ NEVER (SuperAdmin only)
manage_agents: ❌ NEVER (SuperAdmin only)
view_system_settings: ❌ NEVER (SuperAdmin only)
edit_system_settings: ❌ NEVER (SuperAdmin only)
view_audit_logs: ❌ NEVER (SuperAdmin only)
```

**Legend:**
- ✅ **Recommended** - Should be granted to most agents
- 🔶 **Optional** - Grant based on agent's role
- ❌ **Never** - Should never be granted to agents

---

## 🔄 Permission Assignment Workflow

### When New Agent is Assigned

```python
# SuperAdmin assigns user as agent
Agent.assign_agent(user, organisation, superadmin)

# SuperAdmin manually grants permissions
# Option 1: Use template packages
grant_basic_agent_permissions(agent)  # 3 permissions
# OR
grant_standard_agent_permissions(agent)  # 6 permissions
# OR
grant_advanced_agent_permissions(agent)  # 10 permissions

# Option 2: Custom selection
grant_permission(agent, 'manage_organisation')
grant_permission(agent, 'view_users')
# ... custom permissions
```

### Implementation Functions

```python
# In utils or management command
def grant_basic_agent_permissions(agent):
    """Grant basic agent permissions (view-only)"""
    basic_permissions = [
        'manage_organisation',
        'view_users',
        'view_reports',
    ]
    for perm_key in basic_permissions:
        permission = Permission.objects.get(key=perm_key)
        AgentPermissions.objects.get_or_create(
            agent=agent,
            permission=permission
        )

def grant_standard_agent_permissions(agent):
    """Grant standard agent permissions (most common)"""
    standard_permissions = [
        'manage_organisation',
        'view_users',
        'view_reports',
        'view_contacts',
        'view_calls',
        'create_contacts',
    ]
    for perm_key in standard_permissions:
        permission = Permission.objects.get(key=perm_key)
        AgentPermissions.objects.get_or_create(
            agent=agent,
            permission=permission
        )

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
        permission = Permission.objects.get(key=perm_key)
        AgentPermissions.objects.get_or_create(
            agent=agent,
            permission=permission
        )
```

---

## 🎨 UI Implementation

### Permission Selection in Frontend

```html
<!-- Agent Permission Selection -->
<form method="post">
    <h3>Select Permission Package</h3>
    
    <!-- Pre-defined packages -->
    <div class="permission-packages">
        <label>
            <input type="radio" name="package" value="basic">
            Basic Agent (3 permissions) - View only
        </label>
        <label>
            <input type="radio" name="package" value="standard" checked>
            Standard Agent (6 permissions) - Recommended
        </label>
        <label>
            <input type="radio" name="package" value="advanced">
            Advanced Agent (10 permissions) - Power user
        </label>
        <label>
            <input type="radio" name="package" value="custom">
            Custom - Select individually
        </label>
    </div>
    
    <!-- Custom selection (shown if 'custom' selected) -->
    <div id="custom-permissions" style="display:none;">
        <h4>Users</h4>
        <label><input type="checkbox" name="permissions" value="view_users"> View Users</label>
        <label><input type="checkbox" name="permissions" value="create_users"> Create Users</label>
        <!-- ... more permissions -->
    </div>
    
    <button type="submit">Assign Agent with Permissions</button>
</form>
```

---

## 📋 Permission Assignment Matrix

| Permission | SuperAdmin | Basic Agent | Standard Agent | Advanced Agent | User |
|------------|------------|-------------|----------------|----------------|------|
| **Users** |
| view_users | ✅ Auto | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| create_users | ✅ Auto | ❌ No | ❌ No | ✅ Yes | ❌ No |
| edit_users | ✅ Auto | ❌ No | ❌ No | ✅ Yes | ❌ No |
| delete_users | ✅ Auto | ❌ No | ❌ No | ❌ No | ❌ No |
| **Organisations** |
| view_organisations | ✅ Auto | ✅ Auto | ✅ Auto | ✅ Auto | ❌ No |
| manage_organisation | ✅ Auto | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| edit_organisation_settings | ✅ Auto | ❌ No | ❌ No | ✅ Yes | ❌ No |
| **Reports** |
| view_reports | ✅ Auto | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| export_reports | ✅ Auto | ❌ No | ❌ No | ✅ Yes | ❌ No |
| view_analytics | ✅ Auto | ❌ No | ❌ No | ✅ Yes | ❌ No |
| **Calls** |
| make_calls | ✅ Auto | ❌ No | ❌ No | ✅ Yes | ❌ No |
| view_calls | ✅ Auto | ❌ No | ✅ Yes | ✅ Yes | ❌ No |
| manage_campaigns | ✅ Auto | ❌ No | ❌ No | ✅ Yes | ❌ No |
| view_call_recordings | ✅ Auto | ❌ No | ❌ No | ✅ Yes | ❌ No |
| **Contacts** |
| view_contacts | ✅ Auto | ❌ No | ✅ Yes | ✅ Yes | ❌ No |
| create_contacts | ✅ Auto | ❌ No | ✅ Yes | ✅ Yes | ❌ No |
| edit_contacts | ✅ Auto | ❌ No | ❌ No | ✅ Yes | ❌ No |
| delete_contacts | ✅ Auto | ❌ No | ❌ No | ❌ No | ❌ No |
| import_contacts | ✅ Auto | ❌ No | ❌ No | ✅ Yes | ❌ No |
| **System** |
| manage_permissions | ✅ Auto | ❌ Never | ❌ Never | ❌ Never | ❌ Never |
| manage_agents | ✅ Auto | ❌ Never | ❌ Never | ❌ Never | ❌ Never |
| view_system_settings | ✅ Auto | ❌ Never | ❌ Never | ❌ Never | ❌ Never |
| edit_system_settings | ✅ Auto | ❌ Never | ❌ Never | ❌ Never | ❌ Never |
| view_audit_logs | ✅ Auto | ❌ Never | ❌ Never | ❌ Never | ❌ Never |

---

## 🔐 Security Considerations

### Never Grant to Agents
1. **manage_permissions** - Only SuperAdmin can manage permissions
2. **manage_agents** - Only SuperAdmin can assign/revoke agents
3. **view_system_settings** - System-wide settings are SuperAdmin only
4. **edit_system_settings** - System-wide settings are SuperAdmin only
5. **view_audit_logs** - Audit logs are SuperAdmin only

### Use with Caution
1. **delete_users** - Data loss risk
2. **delete_contacts** - Data loss risk
3. **edit_users** - Can modify user roles/data
4. **create_users** - Can add users to organisation

### Safe to Grant
1. **view_*** permissions - Read-only, safe
2. **manage_organisation** - Limited to their org
3. **create_contacts** - Safe, limited to their org
4. **view_calls** - Read-only call data

---

## 🚀 Quick Start Commands

### Assign Basic Agent
```bash
python manage.py shell
>>> from callfairy.apps.accounts.models import User, Organisation, Agent
>>> user = User.objects.get(email='agent@example.com')
>>> org = Organisation.objects.get(id=1)
>>> superadmin = User.objects.get(role='superadmin')
>>> agent = Agent.assign_agent(user, org, superadmin)
>>> # Grant basic permissions
>>> from callfairy.apps.accounts.utils.permissions import grant_basic_agent_permissions
>>> grant_basic_agent_permissions(agent)
```

### Assign Standard Agent
```bash
>>> grant_standard_agent_permissions(agent)
```

### Assign Advanced Agent
```bash
>>> grant_advanced_agent_permissions(agent)
```

---

## 📖 Summary

### Default Permissions by Role

**SuperAdmin:**
- ALL 24 permissions (automatic)

**Basic Agent:**
- 3 permissions (view-only)

**Standard Agent:**
- 6 permissions (recommended for most)

**Advanced Agent:**
- 10 permissions (power users)

**Regular User:**
- 0 permissions (read-only member access)

### Best Practices
1. ✅ Start with Standard Agent package
2. ✅ Grant more permissions as needed
3. ✅ Never grant system permissions to agents
4. ✅ Review permissions regularly
5. ✅ Use packages instead of custom selections (consistency)

---

**Permission Assignment Strategy Complete** ✅

This provides a clear, secure, and flexible permission system for your multi-tenant platform.
