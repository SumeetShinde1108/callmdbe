# 🔐 Role-Based Access Control Matrix

## Quick Reference Guide for Frontend Development

---

## 🎯 API Endpoint Access Matrix

| Endpoint | Method | SuperAdmin | Agent | User | Permission Required |
|----------|--------|------------|-------|------|---------------------|
| **AUTHENTICATION** |
| `/api/accounts/register/` | POST | ✅ | ✅ | ✅ | None (Public) |
| `/api/accounts/login/` | POST | ✅ | ✅ | ✅ | None (Public) |
| `/api/accounts/login/google/` | POST | ✅ | ✅ | ✅ | None (Public) |
| `/api/accounts/token/refresh/` | POST | ✅ | ✅ | ✅ | Valid refresh token |
| `/api/accounts/verify-email/` | POST | ✅ | ✅ | ✅ | Valid token |
| `/api/accounts/password/reset/` | POST | ✅ | ✅ | ✅ | None (Public) |
| `/api/accounts/password/reset/confirm/` | POST | ✅ | ✅ | ✅ | Valid reset token |
| `/api/accounts/2fa/totp/enable/` | POST | ✅ | ✅ | ✅ | Authenticated |
| `/api/accounts/2fa/totp/verify/` | POST | ✅ | ✅ | ✅ | Authenticated |
| `/api/accounts/2fa/totp/disable/` | POST | ✅ | ✅ | ✅ | Authenticated |
| **USER PROFILE** |
| `/api/accounts/me/` | GET | ✅ | ✅ | ✅ | Authenticated |
| `/api/accounts/me/permissions/` | GET | ✅ | ✅ | ✅ | Authenticated |
| `/api/accounts/me/organisations/` | GET | ✅ | ✅ | ✅ | Authenticated |
| **ORGANISATIONS** |
| `/api/accounts/organisations/` | GET | ✅ All | ✅ Own | ✅ Member | Authenticated |
| `/api/accounts/organisations/{id}/` | GET | ✅ Any | ✅ Own | ✅ Member | CanAccessOrganisation |
| `/api/accounts/organisations/{id}/update/` | PATCH | ✅ Any | ✅ Own | ❌ | CanManageOrganisation |
| **AGENT MANAGEMENT** |
| `/api/accounts/agents/` | GET | ✅ | ❌ | ❌ | IsSuperAdmin |
| `/api/accounts/agents/assign/` | POST | ✅ | ❌ | ❌ | IsSuperAdmin |
| `/api/accounts/agents/{id}/revoke/` | POST | ✅ | ❌ | ❌ | IsSuperAdmin |
| `/api/accounts/agents/{id}/permissions/grant/` | POST | ✅ | ❌ | ❌ | IsSuperAdmin |
| `/api/accounts/agents/{id}/permissions/{key}/` | DELETE | ✅ | ❌ | ❌ | IsSuperAdmin |
| **PERMISSIONS** |
| `/api/accounts/permissions/` | GET | ✅ | ✅ | ✅ | Authenticated |

**Legend:**
- ✅ = Allowed
- ❌ = Forbidden (403)
- ✅ All = Can access all items
- ✅ Own = Can access only their own
- ✅ Member = Can access only member items

---

## 🎨 Frontend UI Visibility Matrix

### Navigation Menu Components

| Menu Item | SuperAdmin | Agent | User | Notes |
|-----------|------------|-------|------|-------|
| **Dashboard** | ✅ | ✅ | ✅ | All users |
| **My Profile** | ✅ | ✅ | ✅ | All users |
| **Organisations** | ✅ | ✅ | ✅ | Different scopes |
| └─ All Organisations | ✅ | ❌ | ❌ | SuperAdmin only |
| └─ My Organisation | ✅ | ✅ | ❌ | SuperAdmin + Agent |
| └─ Member Organisations | ✅ | ❌ | ✅ | Read-only for User |
| **Users** | ✅ | 🔒 | ❌ | Agent needs permission |
| └─ All Users | ✅ | ❌ | ❌ | SuperAdmin only |
| └─ Organisation Users | ✅ | 🔒 | ❌ | If `view_users` granted |
| └─ Create User | ✅ | 🔒 | ❌ | If `create_users` granted |
| **Agent Management** | ✅ | ❌ | ❌ | SuperAdmin only |
| └─ View Agents | ✅ | ❌ | ❌ | SuperAdmin only |
| └─ Assign Agent | ✅ | ❌ | ❌ | SuperAdmin only |
| └─ Revoke Agent | ✅ | ❌ | ❌ | SuperAdmin only |
| └─ Manage Permissions | ✅ | ❌ | ❌ | SuperAdmin only |
| **Calls** | ✅ | 🔒 | ❌ | Agent needs permission |
| └─ View Calls | ✅ | 🔒 | ❌ | If `view_calls` granted |
| └─ Make Calls | ✅ | 🔒 | ❌ | If `make_calls` granted |
| └─ Manage Campaigns | ✅ | 🔒 | ❌ | If `manage_campaigns` granted |
| **Contacts** | ✅ | 🔒 | ❌ | Agent needs permission |
| └─ View Contacts | ✅ | 🔒 | ❌ | If `view_contacts` granted |
| └─ Create Contact | ✅ | 🔒 | ❌ | If `create_contacts` granted |
| └─ Import Contacts | ✅ | 🔒 | ❌ | If `import_contacts` granted |
| **Reports** | ✅ | 🔒 | ❌ | Agent needs permission |
| └─ View Reports | ✅ | 🔒 | ❌ | If `view_reports` granted |
| └─ Export Reports | ✅ | 🔒 | ❌ | If `export_reports` granted |
| └─ Analytics | ✅ | 🔒 | ❌ | If `view_analytics` granted |
| **System Settings** | ✅ | ❌ | ❌ | SuperAdmin only |
| └─ View Settings | ✅ | ❌ | ❌ | SuperAdmin only |
| └─ Edit Settings | ✅ | ❌ | ❌ | SuperAdmin only |
| └─ Audit Logs | ✅ | ❌ | ❌ | SuperAdmin only |

**Legend:**
- ✅ = Always visible
- ❌ = Hidden
- 🔒 = Visible only if permission granted

---

## 💻 Frontend Implementation Guide

### 1. Check User Role

```javascript
// After login, store user data
const userData = {
  id: "uuid",
  email: "user@example.com",
  role: "superuser",  // or "superadmin" or "user"
  is_agent: true,
  managed_organisation: { id: 1, name: "Acme Corp" },
  all_permissions: ["view_reports", "manage_organisation"]
};

// Role checks
const isSuperAdmin = userData.role === 'superadmin';
const isAgent = userData.role === 'superuser' && userData.is_agent;
const isRegularUser = userData.role === 'user';
```

### 2. Show/Hide Navigation Items

```javascript
// React example
const Navigation = ({ user }) => {
  const isSuperAdmin = user.role === 'superadmin';
  const isAgent = user.is_agent;
  const hasPermission = (key) => user.all_permissions.includes(key);

  return (
    <nav>
      <NavItem to="/dashboard">Dashboard</NavItem>
      <NavItem to="/profile">My Profile</NavItem>
      
      {/* Organisations - Different for each role */}
      {isSuperAdmin && (
        <NavItem to="/organisations/all">All Organisations</NavItem>
      )}
      {isAgent && (
        <NavItem to="/organisations/mine">My Organisation</NavItem>
      )}
      {!isAgent && !isSuperAdmin && (
        <NavItem to="/organisations/member">Member Organisations</NavItem>
      )}
      
      {/* Agent Management - SuperAdmin Only */}
      {isSuperAdmin && (
        <NavGroup label="Agent Management">
          <NavItem to="/agents">View Agents</NavItem>
          <NavItem to="/agents/assign">Assign Agent</NavItem>
        </NavGroup>
      )}
      
      {/* Permission-based items */}
      {(isSuperAdmin || hasPermission('view_reports')) && (
        <NavItem to="/reports">Reports</NavItem>
      )}
      
      {(isSuperAdmin || hasPermission('view_calls')) && (
        <NavItem to="/calls">Calls</NavItem>
      )}
      
      {/* System Settings - SuperAdmin Only */}
      {isSuperAdmin && (
        <NavItem to="/settings">System Settings</NavItem>
      )}
    </nav>
  );
};
```

### 3. Protect Routes

```javascript
// React Router example
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children, requiredRole, requiredPermission }) => {
  const user = useAuth();
  
  // Check role
  if (requiredRole === 'superadmin' && user.role !== 'superadmin') {
    return <Navigate to="/unauthorized" />;
  }
  
  // Check permission
  if (requiredPermission && !user.all_permissions.includes(requiredPermission)) {
    if (user.role !== 'superadmin') { // SuperAdmin bypasses
      return <Navigate to="/unauthorized" />;
    }
  }
  
  return children;
};

// Usage
<Routes>
  <Route path="/dashboard" element={<Dashboard />} />
  
  <Route 
    path="/agents" 
    element={
      <ProtectedRoute requiredRole="superadmin">
        <AgentManagement />
      </ProtectedRoute>
    } 
  />
  
  <Route 
    path="/reports" 
    element={
      <ProtectedRoute requiredPermission="view_reports">
        <Reports />
      </ProtectedRoute>
    } 
  />
</Routes>
```

### 4. Filter Organisation Lists

```javascript
// Organisation list component
const OrganisationList = ({ user }) => {
  const [organisations, setOrganisations] = useState([]);
  
  useEffect(() => {
    // Fetch organisations
    fetch('/api/accounts/organisations/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => {
      // SuperAdmin sees all
      // Agent sees only their org
      // User sees only member orgs
      setOrganisations(data.organisations);
    });
  }, []);
  
  return (
    <div>
      {organisations.map(org => (
        <OrganisationCard 
          key={org.id} 
          org={org}
          canManage={user.role === 'superadmin' || 
                    (user.is_agent && org.id === user.managed_organisation?.id)}
        />
      ))}
    </div>
  );
};
```

### 5. Conditional Button Display

```javascript
// Organisation detail page
const OrganisationDetail = ({ org, user }) => {
  const isSuperAdmin = user.role === 'superadmin';
  const isOrgAgent = user.is_agent && user.managed_organisation?.id === org.id;
  const canManage = isSuperAdmin || isOrgAgent;
  
  return (
    <div>
      <h1>{org.name}</h1>
      <p>{org.description}</p>
      
      {/* Edit button - only if can manage */}
      {canManage && (
        <button onClick={handleEdit}>Edit Organisation</button>
      )}
      
      {/* Assign agent - SuperAdmin only */}
      {isSuperAdmin && (
        <button onClick={handleAssignAgent}>Assign Agent</button>
      )}
      
      {/* View users - if has permission */}
      {(isSuperAdmin || user.all_permissions.includes('view_users')) && (
        <button onClick={handleViewUsers}>View Users</button>
      )}
    </div>
  );
};
```

---

## 🔒 Permission Check Functions

### Backend (Django)

```python
# In views.py or utils
def can_user_perform_action(user, action, organisation=None):
    """
    Check if user can perform action.
    
    Args:
        user: User instance
        action: Permission key (e.g., 'view_reports')
        organisation: Organisation instance (optional)
    
    Returns:
        bool: True if user has permission
    """
    # SuperAdmin bypass
    if user.role == 'superadmin':
        return True
    
    # Agent permissions
    if user.is_agent():
        # Check if action is in their granted permissions
        agent_perms = user.get_agent_permissions()
        if agent_perms.filter(key=action).exists():
            # If organisation specified, check if it's their org
            if organisation:
                managed_org = user.get_managed_organisation()
                return managed_org == organisation
            return True
    
    # Direct user permissions (rare)
    direct_perms = user.get_direct_permissions()
    return direct_perms.filter(key=action).exists()
```

### Frontend (JavaScript)

```javascript
// Permission utility functions
const PermissionUtils = {
  // Check if user has permission
  hasPermission: (user, permissionKey) => {
    // SuperAdmin has all permissions
    if (user.role === 'superadmin') {
      return true;
    }
    
    // Check in user's permissions array
    return user.all_permissions?.includes(permissionKey) || false;
  },
  
  // Check if user can manage organisation
  canManageOrganisation: (user, organisationId) => {
    // SuperAdmin can manage all
    if (user.role === 'superadmin') {
      return true;
    }
    
    // Agent can manage their organisation
    if (user.is_agent && user.managed_organisation?.id === organisationId) {
      return true;
    }
    
    return false;
  },
  
  // Check if user can access organisation
  canAccessOrganisation: (user, organisationId) => {
    // SuperAdmin can access all
    if (user.role === 'superadmin') {
      return true;
    }
    
    // Agent can access their organisation
    if (user.is_agent && user.managed_organisation?.id === organisationId) {
      return true;
    }
    
    // User can access member organisations
    return user.accessible_organisations?.some(
      org => org.id === organisationId
    ) || false;
  },
  
  // Get allowed organisations for user
  getAccessibleOrganisations: (user) => {
    if (user.role === 'superadmin') {
      return 'all'; // Fetch all organisations
    }
    
    if (user.is_agent) {
      return [user.managed_organisation]; // Only their org
    }
    
    return user.accessible_organisations || []; // Member orgs
  }
};

// Usage
if (PermissionUtils.hasPermission(currentUser, 'view_reports')) {
  // Show reports section
}

if (PermissionUtils.canManageOrganisation(currentUser, orgId)) {
  // Show edit button
}
```

---

## 📱 UI Component Examples

### Permission-Based Button

```jsx
// React component
const PermissionButton = ({ 
  permission, 
  organisation, 
  children, 
  onClick 
}) => {
  const user = useAuth();
  
  // SuperAdmin bypass
  if (user.role === 'superadmin') {
    return <button onClick={onClick}>{children}</button>;
  }
  
  // Check permission
  const hasPermission = user.all_permissions?.includes(permission);
  
  // Check organisation access if specified
  if (organisation && user.is_agent) {
    if (user.managed_organisation?.id !== organisation.id) {
      return null; // Hide if wrong org
    }
  }
  
  if (!hasPermission) {
    return null; // Hide if no permission
  }
  
  return <button onClick={onClick}>{children}</button>;
};

// Usage
<PermissionButton 
  permission="edit_users" 
  organisation={currentOrg}
  onClick={handleEditUser}
>
  Edit User
</PermissionButton>
```

### Role-Based Section

```jsx
const RoleBasedSection = ({ requiredRole, children }) => {
  const user = useAuth();
  
  const hasAccess = () => {
    switch (requiredRole) {
      case 'superadmin':
        return user.role === 'superadmin';
      case 'agent':
        return user.is_agent || user.role === 'superadmin';
      case 'user':
        return true; // All authenticated users
      default:
        return false;
    }
  };
  
  if (!hasAccess()) {
    return null;
  }
  
  return <>{children}</>;
};

// Usage
<RoleBasedSection requiredRole="superadmin">
  <AgentManagementPanel />
</RoleBasedSection>

<RoleBasedSection requiredRole="agent">
  <OrganisationSettings />
</RoleBasedSection>
```

---

## 🎬 Complete Flow Examples

### Example 1: Organisation Page

```jsx
const OrganisationPage = ({ orgId }) => {
  const user = useAuth();
  const [org, setOrg] = useState(null);
  
  useEffect(() => {
    // Fetch organisation
    fetchOrganisation(orgId).then(setOrg);
  }, [orgId]);
  
  const isSuperAdmin = user.role === 'superadmin';
  const isOrgAgent = user.is_agent && 
                     user.managed_organisation?.id === parseInt(orgId);
  const canManage = isSuperAdmin || isOrgAgent;
  
  return (
    <div>
      <h1>{org?.name}</h1>
      
      {/* Basic info - everyone who has access can see */}
      <InfoSection org={org} />
      
      {/* Edit button - SuperAdmin or Agent of this org */}
      {canManage && (
        <button onClick={handleEdit}>Edit Organisation</button>
      )}
      
      {/* Users section - if has permission */}
      {(isSuperAdmin || user.all_permissions.includes('view_users')) && (
        <UsersSection orgId={orgId} />
      )}
      
      {/* Agent management - SuperAdmin only */}
      {isSuperAdmin && (
        <AgentSection org={org} />
      )}
      
      {/* Reports - if has permission */}
      {(isSuperAdmin || user.all_permissions.includes('view_reports')) && (
        <ReportsSection orgId={orgId} />
      )}
    </div>
  );
};
```

### Example 2: User Management Page

```jsx
const UserManagementPage = () => {
  const user = useAuth();
  const [users, setUsers] = useState([]);
  
  // Only SuperAdmin or Agents with view_users permission
  if (user.role !== 'superadmin' && 
      !user.all_permissions.includes('view_users')) {
    return <UnauthorizedPage />;
  }
  
  useEffect(() => {
    fetchUsers().then(setUsers);
  }, []);
  
  const isSuperAdmin = user.role === 'superadmin';
  const canCreateUser = isSuperAdmin || 
                        user.all_permissions.includes('create_users');
  const canEditUser = isSuperAdmin || 
                      user.all_permissions.includes('edit_users');
  const canDeleteUser = isSuperAdmin || 
                        user.all_permissions.includes('delete_users');
  
  return (
    <div>
      <h1>Users</h1>
      
      {/* Create button */}
      {canCreateUser && (
        <button onClick={handleCreateUser}>Create User</button>
      )}
      
      {/* User list */}
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            {canEditUser && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {users.map(u => (
            <tr key={u.id}>
              <td>{u.name}</td>
              <td>{u.email}</td>
              <td>{u.role_display}</td>
              {canEditUser && (
                <td>
                  <button onClick={() => handleEdit(u)}>Edit</button>
                  {canDeleteUser && (
                    <button onClick={() => handleDelete(u)}>Delete</button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

## 📊 Quick Decision Tree

### "Can I show this feature?"

```
START
  ↓
Is user SuperAdmin?
  ├─ YES → SHOW (bypass all checks)
  └─ NO → Continue
       ↓
Is this a system feature?
(Agent management, system settings)
  ├─ YES → HIDE
  └─ NO → Continue
       ↓
Is this organisation-specific?
  ├─ YES → Is user agent of THIS org?
  │         ├─ YES → Check permission
  │         └─ NO → HIDE
  └─ NO → Check permission
       ↓
Does user have required permission?
  ├─ YES → SHOW
  └─ NO → HIDE
```

---

## 🎯 Summary

### Quick Rules

1. **SuperAdmin** = Show everything
2. **Agent** = Show only their org + granted permissions
3. **User** = Show only member orgs (read-only mostly)

### Key Checks

```javascript
// SuperAdmin check
if (user.role === 'superadmin') { /* allow */ }

// Agent check
if (user.is_agent && user.managed_organisation?.id === orgId) { /* allow */ }

// Permission check
if (user.all_permissions.includes('permission_key')) { /* allow */ }

// Combined check
if (user.role === 'superadmin' || user.all_permissions.includes('key')) { /* allow */ }
```

---

**Access Control Matrix Complete** ✅

This matrix provides all the information needed to implement role-based UI visibility and access control in your frontend application.
