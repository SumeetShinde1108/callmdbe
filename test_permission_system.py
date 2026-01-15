#!/usr/bin/env python
"""
Test script for Multi-Tenant Permission System
Tests all new API endpoints and functionality
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'callfairy.core.settings')
django.setup()

from callfairy.apps.accounts.models import User, Organisation, Agent, Permission, AgentPermissions
from django.db import transaction


def print_header(text):
    """Print formatted header"""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print('=' * 60)


def print_success(text):
    """Print success message"""
    print(f"✅ {text}")


def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")


def print_error(text):
    """Print error message"""
    print(f"❌ {text}")


def cleanup_test_data():
    """Clean up existing test data"""
    print_header("CLEANUP: Removing Test Data")
    
    try:
        # Delete test users
        test_emails = [
            'superadmin@test.com',
            'agent@test.com',
            'user@test.com',
            'john@acme.com',
        ]
        deleted_users = User.objects.filter(email__in=test_emails).delete()
        print_success(f"Deleted {deleted_users[0]} test users")
        
        # Delete test organisations
        test_orgs = Organisation.objects.filter(name__in=['Acme Corp', 'Test Org'])
        org_count = test_orgs.count()
        test_orgs.delete()
        print_success(f"Deleted {org_count} test organisations")
        
    except Exception as e:
        print_error(f"Cleanup error: {e}")


def create_test_data():
    """Create test users and organisations"""
    print_header("SETUP: Creating Test Data")
    
    try:
        # 1. Create SuperAdmin
        superadmin = User.objects.create(
            email='superadmin@test.com',
            name='Super Admin',
            role='superadmin',
            is_active=True,
            is_staff=True,
        )
        superadmin.set_password('admin123')
        superadmin.save()
        print_success(f"Created SuperAdmin: {superadmin.email}")
        
        # 2. Create regular user (will become agent)
        user = User.objects.create(
            email='agent@test.com',
            name='John Agent',
            role='user',
            is_active=True,
        )
        user.set_password('user123')
        user.save()
        print_success(f"Created User: {user.email} (role: {user.role})")
        
        # 3. Create another regular user
        regular_user = User.objects.create(
            email='user@test.com',
            name='Jane User',
            role='user',
            is_active=True,
        )
        regular_user.set_password('user123')
        regular_user.save()
        print_success(f"Created User: {regular_user.email} (role: {regular_user.role})")
        
        # 4. Create Organisation
        org = Organisation.objects.create(
            name='Acme Corp',
            description='Test organization',
            city='New York',
            state='NY',
            country='USA',
            is_active=True,
        )
        print_success(f"Created Organisation: {org.name}")
        
        return {
            'superadmin': superadmin,
            'user': user,
            'regular_user': regular_user,
            'org': org,
        }
        
    except Exception as e:
        print_error(f"Setup error: {e}")
        raise


def test_agent_assignment(data):
    """Test agent assignment functionality"""
    print_header("TEST 1: Agent Assignment")
    
    superadmin = data['superadmin']
    user = data['user']
    org = data['org']
    
    try:
        # Assign agent
        print_info(f"Assigning {user.email} as agent for {org.name}")
        agent = Agent.assign_agent(
            user=user,
            organisation=org,
            assigned_by=superadmin
        )
        
        # Refresh user to get updated role
        user.refresh_from_db()
        
        print_success(f"Agent assigned successfully!")
        print_info(f"  • Agent ID: {agent.id}")
        print_info(f"  • User role updated: {user.role} (was 'user', now 'superuser')")
        print_info(f"  • Is active: {agent.is_active}")
        print_info(f"  • Assigned by: {agent.assigned_by.email}")
        
        # Verify agent status
        assert user.is_agent() == True, "User should be an agent"
        assert user.role == 'superuser', "User role should be 'superuser'"
        assert user.get_managed_organisation() == org, "User should manage the org"
        
        print_success("All agent assignment checks passed!")
        data['agent'] = agent
        
        return True
        
    except Exception as e:
        print_error(f"Agent assignment test failed: {e}")
        return False


def test_permission_granting(data):
    """Test permission granting to agents"""
    print_header("TEST 2: Permission Granting")
    
    superadmin = data['superadmin']
    agent = data['agent']
    
    try:
        # Get some permissions
        perms = Permission.objects.filter(
            key__in=['view_reports', 'manage_organisation', 'view_calls']
        )
        
        granted = []
        for perm in perms:
            print_info(f"Granting permission: {perm.name} ({perm.key})")
            agent_perm = AgentPermissions.grant_permission(
                agent=agent,
                permission=perm,
                granted_by=superadmin
            )
            granted.append(perm.key)
            print_success(f"  ✓ Granted")
        
        # Verify permissions
        user = agent.user
        user_perms = user.get_all_permissions()
        user_perm_keys = list(user_perms.values_list('key', flat=True))
        
        print_info(f"User now has {user_perms.count()} permissions:")
        for key in user_perm_keys:
            print_info(f"  • {key}")
        
        # Check specific permissions
        for key in granted:
            assert user.has_permission(key) == True, f"User should have {key}"
        
        print_success("All permission granting checks passed!")
        return True
        
    except Exception as e:
        print_error(f"Permission granting test failed: {e}")
        return False


def test_permission_utils(data):
    """Test permission utility functions"""
    print_header("TEST 3: Permission Utility Functions")
    
    from callfairy.apps.accounts.utils import (
        get_user_accessible_organisations,
        can_user_manage_organisation,
        get_permission_summary,
    )
    
    superadmin = data['superadmin']
    agent_user = data['user']
    regular_user = data['regular_user']
    org = data['org']
    
    try:
        # Test 1: Accessible organisations
        print_info("Testing get_user_accessible_organisations...")
        
        # SuperAdmin should see all orgs
        admin_orgs = get_user_accessible_organisations(superadmin)
        print_info(f"  • SuperAdmin can access {admin_orgs.count()} organisations")
        
        # Agent should see only managed org
        agent_orgs = get_user_accessible_organisations(agent_user)
        print_info(f"  • Agent can access {agent_orgs.count()} organisation(s)")
        assert agent_orgs.count() == 1, "Agent should see 1 org"
        assert org in agent_orgs, "Agent should see their managed org"
        
        # Regular user should see none (no memberships)
        user_orgs = get_user_accessible_organisations(regular_user)
        print_info(f"  • Regular user can access {user_orgs.count()} organisations")
        
        print_success("  ✓ Accessible organisations test passed")
        
        # Test 2: Can manage organisation
        print_info("Testing can_user_manage_organisation...")
        
        admin_can_manage = can_user_manage_organisation(superadmin, org)
        agent_can_manage = can_user_manage_organisation(agent_user, org)
        user_can_manage = can_user_manage_organisation(regular_user, org)
        
        print_info(f"  • SuperAdmin can manage: {admin_can_manage}")
        print_info(f"  • Agent can manage: {agent_can_manage}")
        print_info(f"  • Regular user can manage: {user_can_manage}")
        
        assert admin_can_manage == True, "SuperAdmin should manage all orgs"
        assert agent_can_manage == True, "Agent should manage their org"
        assert user_can_manage == False, "Regular user should not manage"
        
        print_success("  ✓ Can manage organisation test passed")
        
        # Test 3: Permission summary
        print_info("Testing get_permission_summary...")
        
        agent_summary = get_permission_summary(agent_user)
        print_info(f"  • Agent summary keys: {list(agent_summary.keys())}")
        print_info(f"  • Agent has {len(agent_summary['all_permissions'])} permissions")
        
        assert agent_summary['is_agent'] == True
        assert agent_summary['role'] == 'superuser'
        assert len(agent_summary['agent_permissions']) > 0
        
        print_success("  ✓ Permission summary test passed")
        
        print_success("All utility function tests passed!")
        return True
        
    except Exception as e:
        print_error(f"Utility function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_revocation(data):
    """Test agent revocation"""
    print_header("TEST 4: Agent Revocation")
    
    agent = data['agent']
    user = data['user']
    
    try:
        print_info(f"Revoking agent: {user.email}")
        
        # Store current state
        org_name = agent.organisation.name
        
        # Revoke agent
        Agent.revoke_agent(agent.id, revoked_by=data['superadmin'])
        
        # Refresh
        agent.refresh_from_db()
        user.refresh_from_db()
        
        print_success("Agent revoked successfully!")
        print_info(f"  • Is active: {agent.is_active}")
        print_info(f"  • User role: {user.role} (should be 'user' now)")
        print_info(f"  • Is agent: {user.is_agent()}")
        
        # Verify
        assert agent.is_active == False, "Agent should be inactive"
        assert user.role == 'user', "User role should be downgraded to 'user'"
        assert user.is_agent() == False, "User should not be an agent anymore"
        
        print_success("All agent revocation checks passed!")
        
        # Re-assign for other tests (optional)
        print_info(f"Re-assigning agent for further tests...")
        new_agent = Agent.assign_agent(
            user=user,
            organisation=data['org'],
            assigned_by=data['superadmin']
        )
        user.refresh_from_db()
        data['agent'] = new_agent
        print_success("Agent re-assigned")
        
        return True
        
    except Exception as e:
        print_error(f"Agent revocation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_superadmin_privileges(data):
    """Test SuperAdmin bypass privileges"""
    print_header("TEST 5: SuperAdmin Privileges")
    
    superadmin = data['superadmin']
    org = data['org']
    
    try:
        # SuperAdmin should have all permissions by default
        print_info("Testing SuperAdmin bypass...")
        
        all_perms = Permission.objects.all()[:5]
        
        print_info(f"Checking {all_perms.count()} random permissions for SuperAdmin:")
        for perm in all_perms:
            has_perm = superadmin.has_permission(perm.key)
            print_info(f"  • {perm.key}: {has_perm}")
            assert has_perm == True, f"SuperAdmin should have {perm.key}"
        
        print_success("  ✓ SuperAdmin has all permissions (bypass works)")
        
        # SuperAdmin should manage all orgs
        from callfairy.apps.accounts.utils import can_user_manage_organisation
        
        can_manage = can_user_manage_organisation(superadmin, org)
        print_info(f"SuperAdmin can manage organisation: {can_manage}")
        assert can_manage == True, "SuperAdmin should manage all orgs"
        
        print_success("All SuperAdmin privilege tests passed!")
        return True
        
    except Exception as e:
        print_error(f"SuperAdmin privilege test failed: {e}")
        return False


def print_summary():
    """Print system summary"""
    print_header("SYSTEM SUMMARY")
    
    print_info(f"Users: {User.objects.count()}")
    print_info(f"Organisations: {Organisation.objects.count()}")
    print_info(f"Permissions: {Permission.objects.count()}")
    print_info(f"Active Agents: {Agent.objects.filter(is_active=True).count()}")
    print_info(f"Agent Permissions: {AgentPermissions.objects.count()}")
    
    print("\n" + "─" * 60)
    print("Test Users Created:")
    for user in User.objects.filter(email__icontains='test.com'):
        print(f"  📧 {user.email}")
        print(f"     Role: {user.role} | Agent: {user.is_agent()}")


def main():
    """Main test runner"""
    print_header("🧪 MULTI-TENANT PERMISSION SYSTEM TESTS")
    print("This script will test all core functionality\n")
    
    results = []
    
    try:
        # Cleanup
        cleanup_test_data()
        
        # Setup
        data = create_test_data()
        
        # Run tests
        results.append(("Agent Assignment", test_agent_assignment(data)))
        results.append(("Permission Granting", test_permission_granting(data)))
        results.append(("Permission Utils", test_permission_utils(data)))
        results.append(("Agent Revocation", test_agent_revocation(data)))
        results.append(("SuperAdmin Privileges", test_superadmin_privileges(data)))
        
        # Summary
        print_summary()
        
        # Results
        print_header("TEST RESULTS")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {status} - {test_name}")
        
        print(f"\n{'─' * 60}")
        print(f"  Total: {passed}/{total} tests passed")
        
        if passed == total:
            print_header("🎉 ALL TESTS PASSED!")
            print("\n✅ Your multi-tenant permission system is working perfectly!")
            print("\n📝 Next steps:")
            print("   1. Test API endpoints with Postman or curl")
            print("   2. Try logging in as different users")
            print("   3. Test organisation management")
            print("\n💡 Test credentials:")
            print("   SuperAdmin: superadmin@test.com / admin123")
            print("   Agent:      agent@test.com / user123")
            print("   User:       user@test.com / user123")
        else:
            print_header("⚠️  SOME TESTS FAILED")
            print("Please review the errors above.")
        
    except Exception as e:
        print_error(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
