from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_otp.plugins.otp_totp.models import TOTPDevice

from .models import (
    AllowedEmailDomain, 
    GoogleSignInAudit,
    Organisation,
    Agent,
    Permission,
    AgentPermissions,
    UserPermissionAccess,
)
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    UserDetailSerializer,
    CustomTokenObtainPairSerializer,
    EmailVerificationSerializer,
    GoogleLoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    OrganisationSerializer,
    AgentSerializer,
    AssignAgentSerializer,
    GrantAgentPermissionSerializer,
    PermissionSerializer,
)
from .permissions import (
    IsSuperAdmin,
    CanAccessOrganisation,
    CanManageOrganisation,
)
from .utils import (
    get_user_accessible_organisations,
    get_permission_summary,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # Optionally include email verification token in DEBUG for convenience/tests
        token = self.get_serializer_context().get('email_verification_token')
        data = response.data if isinstance(response.data, dict) else {}
        data.update({"detail": "Registration successful. Please verify your email to activate your account."})
        if settings.DEBUG and token:
            data["email_verification_token"] = token
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """Issue JWT tokens with embedded user payload; blocks inactive users."""
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

class MeView(APIView):
    """
    Get current user's profile with full permission details.
    
    GET /api/me/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get detailed user profile with permissions and organisations."""
        serializer = UserDetailSerializer(
            request.user,
            context={'request': request, 'include_permissions': True}
        )
        return Response(serializer.data)


class EmailVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evt = serializer.validated_data['evt']
        user = evt.user
        user.is_active = True
        user.save(update_fields=["is_active"])
        evt.is_used = True
        evt.save(update_fields=["is_used"])
        return Response({"detail": "Email verified. You can now log in."}, status=status.HTTP_200_OK)


class TOTPEnableView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Create or reuse an unconfirmed device
        device, created = TOTPDevice.objects.get_or_create(
            user=request.user,
            name="default",
            defaults={"confirmed": False},
        )
        if not created and device.confirmed:
            return Response({"detail": "2FA already enabled."}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure device is unconfirmed for verification step
        device.confirmed = False
        device.save(update_fields=["confirmed"])

        provisioning_uri = getattr(device, "config_url", None)
        data = {"device_id": device.id}
        if provisioning_uri:
            data["provisioning_uri"] = provisioning_uri
        return Response(data, status=status.HTTP_200_OK)


class TOTPVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = str(request.data.get("code", "")).strip()
        if not code:
            return Response({"code": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            device = TOTPDevice.objects.get(user=request.user, name="default")
        except TOTPDevice.DoesNotExist:
            return Response({"detail": "No TOTP device to verify."}, status=status.HTTP_400_BAD_REQUEST)

        if device.verify_token(code):
            device.confirmed = True
            device.save(update_fields=["confirmed"])
            return Response({"detail": "2FA enabled."}, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)


class TOTPDisableView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        deleted, _ = TOTPDevice.objects.filter(user=request.user).delete()
        if deleted:
            return Response({"detail": "2FA disabled."}, status=status.HTTP_200_OK)
        return Response({"detail": "No 2FA device found."}, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(APIView):
    """Authenticate with Google id_token and issue JWT tokens."""
    permission_classes = [permissions.AllowAny]

    def _client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        name = serializer.validated_data.get('name') or ''
        sub = serializer.validated_data.get('google_sub') or ''
        domain = email.split('@')[-1].lower() if '@' in email else ''

        # Domain restriction: if any active domains exist, enforce membership
        active_domains = list(AllowedEmailDomain.objects.filter(is_active=True).values_list('domain', flat=True))
        if active_domains and domain not in [d.lower() for d in active_domains]:
            GoogleSignInAudit.objects.create(
                user=None,
                email=email,
                domain=domain,
                provider_sub=sub,
                success=False,
                reason=f"domain_not_allowed: {domain}",
                ip=self._client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            return Response({"detail": "Email domain not allowed."}, status=status.HTTP_403_FORBIDDEN)

        user, created = User.objects.get_or_create(email=email, defaults={
            'name': name,
            'is_active': True,
        })
        # Ensure the user is active (email is verified by Google)
        if not user.is_active:
            user.is_active = True
            if name and not user.name:
                user.name = name
            user.save(update_fields=["is_active", "name"]) if name else user.save(update_fields=["is_active"])

        # Audit success
        GoogleSignInAudit.objects.create(
            user=user,
            email=email,
            domain=domain,
            provider_sub=sub,
            success=True,
            reason="",
            ip=self._client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        refresh = RefreshToken.for_user(user)
        payload = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
        payload.update(UserSerializer(user).data)
        return Response(payload, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')
        # Always respond success to prevent user enumeration
        response = {"detail": "If an account with that email exists, a password reset link has been sent."}
        if user:
            payload = serializer.create_reset_payload(user)
            # TODO: Send email using EMAIL_BACKEND and template with link containing uid/token
            if settings.DEBUG:
                response.update(payload)
        return Response(response, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save(update_fields=["password"])
        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)


# ============ MULTI-TENANT PERMISSION VIEWS ============


class OrganisationListView(APIView):
    """
    List all organisations accessible to the current user.
    
    - SuperAdmin: All organisations
    - Agent: Their managed organisation
    - User: Organisations they're members of
    
    GET /api/organisations/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get organisations accessible to current user."""
        orgs = get_user_accessible_organisations(request.user)
        serializer = OrganisationSerializer(
            orgs, 
            many=True, 
            context={'request': request}
        )
        return Response({
            'organisations': serializer.data,
            'count': orgs.count(),
            'user_role': request.user.role,
        })


class OrganisationDetailView(APIView):
    """
    Get details of a specific organisation.
    User must have access to the organisation.
    
    GET /api/organisations/{id}/
    """
    permission_classes = [CanAccessOrganisation]
    
    def get(self, request, pk):
        """Get organisation details."""
        org = get_object_or_404(Organisation, pk=pk)
        self.check_object_permissions(request, org)
        
        serializer = OrganisationSerializer(org, context={'request': request})
        return Response(serializer.data)


class OrganisationUpdateView(APIView):
    """
    Update organisation details.
    Only SuperAdmins and designated Agents can update.
    
    PUT /api/organisations/{id}/
    PATCH /api/organisations/{id}/
    """
    permission_classes = [CanManageOrganisation]
    
    def put(self, request, pk):
        """Update organisation."""
        return self._update(request, pk, partial=False)
    
    def patch(self, request, pk):
        """Partial update organisation."""
        return self._update(request, pk, partial=True)
    
    def _update(self, request, pk, partial=False):
        """Handle update logic."""
        org = get_object_or_404(Organisation, pk=pk)
        self.check_object_permissions(request, org)
        
        serializer = OrganisationSerializer(
            org, 
            data=request.data, 
            partial=partial,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Organisation updated successfully',
            'organisation': serializer.data,
        })


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
        """Assign agent to organisation."""
        serializer = AssignAgentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        org = serializer.validated_data['organisation']
        
        # Assign agent
        agent = Agent.assign_agent(
            user=user,
            organisation=org,
            assigned_by=request.user
        )
        
        # Return agent details
        agent_serializer = AgentSerializer(agent, context={'request': request})
        return Response({
            'message': f'{user.name} assigned as agent for {org.name}',
            'agent': agent_serializer.data,
        }, status=status.HTTP_201_CREATED)


class RevokeAgentView(APIView):
    """
    Revoke agent designation.
    Only SuperAdmins can revoke agents.
    
    POST /api/agents/{agent_id}/revoke/
    """
    permission_classes = [IsSuperAdmin]
    
    def post(self, request, agent_id):
        """Revoke agent designation."""
        agent = get_object_or_404(Agent, id=agent_id, is_active=True)
        
        user_name = agent.user.name
        org_name = agent.organisation.name
        
        # Revoke agent
        Agent.revoke_agent(agent_id, revoked_by=request.user)
        
        # Refresh agent to get updated status
        agent.refresh_from_db()
        agent.user.refresh_from_db()
        
        return Response({
            'message': f'Agent {user_name} revoked from {org_name}',
            'user_role': agent.user.role,  # Will be 'user' now
        })


class AgentListView(APIView):
    """
    List all agents.
    Only SuperAdmins can list all agents.
    
    GET /api/agents/
    """
    permission_classes = [IsSuperAdmin]
    
    def get(self, request):
        """List all active agents."""
        active_only = request.query_params.get('active', 'true').lower() == 'true'
        
        if active_only:
            agents = Agent.objects.filter(is_active=True)
        else:
            agents = Agent.objects.all()
        
        agents = agents.select_related('user', 'organisation', 'assigned_by').order_by('-assigned_at')
        
        serializer = AgentSerializer(agents, many=True, context={'request': request})
        return Response({
            'agents': serializer.data,
            'count': agents.count(),
        })


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
        """Grant permission to agent."""
        agent = get_object_or_404(Agent, id=agent_id, is_active=True)
        
        serializer = GrantAgentPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        permission = serializer.validated_data['permission_key']
        
        # Grant permission
        agent_perm = AgentPermissions.grant_permission(
            agent=agent,
            permission=permission,
            granted_by=request.user
        )
        
        return Response({
            'message': f'Permission {permission.name} granted to {agent.user.name}',
            'permission': PermissionSerializer(permission).data,
            'agent': {
                'user': agent.user.name,
                'organisation': agent.organisation.name,
            }
        }, status=status.HTTP_201_CREATED)


class RevokeAgentPermissionView(APIView):
    """
    Revoke a permission from an agent.
    Only SuperAdmins can revoke permissions.
    
    DELETE /api/agents/{agent_id}/permissions/{permission_key}/
    """
    permission_classes = [IsSuperAdmin]
    
    def delete(self, request, agent_id, permission_key):
        """Revoke permission from agent."""
        agent = get_object_or_404(Agent, id=agent_id, is_active=True)
        
        try:
            permission = Permission.objects.get(key=permission_key)
        except Permission.DoesNotExist:
            return Response(
                {'error': 'Permission not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Revoke permission
        AgentPermissions.revoke_permission(agent, permission)
        
        return Response({
            'message': f'Permission {permission.name} revoked from {agent.user.name}',
        })


class PermissionListView(APIView):
    """
    List all available permissions.
    
    GET /api/permissions/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """List all permissions."""
        perms = Permission.objects.all().order_by('name')
        serializer = PermissionSerializer(perms, many=True)
        
        return Response({
            'permissions': serializer.data,
            'count': perms.count(),
        })


class MyPermissionsView(APIView):
    """
    Get current user's permission summary.
    
    GET /api/me/permissions/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get permission summary for current user."""
        summary = get_permission_summary(request.user)
        return Response(summary)


class MyOrganisationsView(APIView):
    """
    Get organisations accessible to current user.
    
    GET /api/me/organisations/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get organisations user can access."""
        orgs = get_user_accessible_organisations(request.user)
        serializer = OrganisationSerializer(orgs, many=True, context={'request': request})
        
        managed_org = None
        if request.user.is_agent():
            org = request.user.get_managed_organisation()
            if org:
                managed_org = {
                    'id': org.id,
                    'name': org.name,
                    'city': org.city,
                }
        
        return Response({
            'organisations': serializer.data,
            'count': orgs.count(),
            'is_agent': request.user.is_agent(),
            'managed_organisation': managed_org,
        })
