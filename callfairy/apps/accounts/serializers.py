from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
import requests

from .models import (
    User, 
    EmailVerificationToken, 
    Organisation, 
    Agent, 
    Permission, 
    AgentPermissions,
    UserPermissionAccess,
)

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password2', 'name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        # Create email verification token
        token = EmailVerificationToken.create_for_user(user)
        # NOTE: Hook actual email sending here using settings.EMAIL_* and a mail backend.
        # For development/tests, we expose token via serializer context if needed.
        self.context["email_verification_token"] = token.token
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        if not user.is_active:
            raise serializers.ValidationError('User is inactive')
        return {'user': user}


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile data with role and permissions."""
    role_display = serializers.CharField(source='get_role_display_name', read_only=True)
    is_agent = serializers.SerializerMethodField()
    managed_organisation = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'name', 'role', 'role_display',
            'company', 'job_title', 'phone', 'date_joined',
            'is_agent', 'managed_organisation', 'permissions'
        )
        read_only_fields = ('id', 'date_joined', 'role')
    
    def get_is_agent(self, obj):
        """Check if user is an agent."""
        return obj.is_agent()
    
    def get_managed_organisation(self, obj):
        """Get the organisation this user manages if they're an agent."""
        if not obj.is_agent():
            return None
        org = obj.get_managed_organisation()
        if org:
            return {
                'id': org.id,
                'name': org.name,
                'city': org.city,
            }
        return None
    
    def get_permissions(self, obj):
        """Get all permission keys for this user."""
        # Only include in detail views, not in lists
        if self.context.get('include_permissions', False):
            return list(obj.get_all_permissions().values_list('key', flat=True))
        return []


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer that includes user data in response."""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        # Block inactive users
        if not self.user.is_active:
            raise serializers.ValidationError('Account is inactive. Please verify your email.')
        user_serializer = UserSerializer(self.user)
        data.update(user_serializer.data)
        return data


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        token = attrs.get('token')
        try:
            evt = EmailVerificationToken.objects.select_related('user').get(token=token)
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError({'token': 'Invalid token'})
        if not evt.is_valid():
            raise serializers.ValidationError({'token': 'Token expired or already used'})
        attrs['evt'] = evt
        return attrs


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()

    def validate(self, attrs):
        id_token = attrs.get('id_token')
        if not id_token:
            raise serializers.ValidationError({'id_token': 'This field is required'})

        # Verify with Google tokeninfo endpoint
        try:
            resp = requests.get(
                'https://oauth2.googleapis.com/tokeninfo',
                params={'id_token': id_token},
                timeout=5,
            )
        except requests.RequestException:
            raise serializers.ValidationError({'id_token': 'Failed to verify token with Google'})

        if resp.status_code != 200:
            raise serializers.ValidationError({'id_token': 'Invalid Google token'})

        data = resp.json()
        email = data.get('email')
        email_verified = data.get('email_verified') in (True, 'true', 'True', '1', 1)
        name = data.get('name') or ''
        aud = data.get('aud') or data.get('azp')

        # Check audience against configured client id if present
        google_cfg = settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('APP', {})
        client_id = google_cfg.get('client_id')
        if client_id and aud != client_id:
            raise serializers.ValidationError({'id_token': 'Token audience mismatch'})

        if not email or not email_verified:
            raise serializers.ValidationError({'id_token': 'Email not verified by Google'})

        attrs['email'] = email
        attrs['name'] = name
        attrs['google_sub'] = data.get('sub')
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get('email').lower()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Do not reveal whether the email exists
            attrs['user'] = None
            return attrs
        attrs['user'] = user
        return attrs

    def create_reset_payload(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return {"uid": uid, "token": token}


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': "Password fields didn't match."})
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            raise serializers.ValidationError({'uid': 'Invalid user id'})

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({'token': 'Invalid or expired token'})
        attrs['user'] = user
        return attrs


# ============ MULTI-TENANT PERMISSION SERIALIZERS ============


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model."""
    
    class Meta:
        model = Permission
        fields = ('id', 'key', 'name', 'description', 'created_at')
        read_only_fields = ('id', 'created_at')


class OrganisationSerializer(serializers.ModelSerializer):
    """Serializer for Organisation model."""
    agent = serializers.SerializerMethodField()
    user_can_manage = serializers.SerializerMethodField()
    
    class Meta:
        model = Organisation
        fields = (
            'id', 'name', 'description', 'address', 'city', 
            'state', 'country', 'pincode', 'is_active',
            'agent', 'user_can_manage'
        )
        read_only_fields = ('id',)
    
    def get_agent(self, obj):
        """Get the agent for this organisation."""
        agent = Agent.get_agent_for_organisation(obj)
        if agent:
            return {
                'id': str(agent.user.id),
                'email': agent.user.email,
                'name': agent.user.name,
            }
        return None
    
    def get_user_can_manage(self, obj):
        """Check if current user can manage this organisation."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        from .utils import can_user_manage_organisation
        return can_user_manage_organisation(request.user, obj)


class AgentSerializer(serializers.ModelSerializer):
    """Serializer for Agent model."""
    user = UserSerializer(read_only=True)
    organisation = OrganisationSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True, required=False)
    organisation_id = serializers.IntegerField(write_only=True, required=False)
    assigned_by_email = serializers.EmailField(source='assigned_by.email', read_only=True)
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = Agent
        fields = (
            'id', 'user', 'organisation', 'user_id', 'organisation_id',
            'is_active', 'assigned_at', 'assigned_by_email',
            'revoked_at', 'permissions'
        )
        read_only_fields = ('id', 'assigned_at', 'revoked_at')
    
    def get_permissions(self, obj):
        """Get all permissions for this agent."""
        perms = obj.get_permissions()
        return PermissionSerializer(perms, many=True).data


class AssignAgentSerializer(serializers.Serializer):
    """Serializer for assigning an agent to an organisation."""
    user_id = serializers.UUIDField()
    organisation_id = serializers.IntegerField()
    
    def validate(self, attrs):
        """Validate user and organisation exist."""
        try:
            user = User.objects.get(id=attrs['user_id'])
            attrs['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError({'user_id': 'User not found'})
        
        try:
            org = Organisation.objects.get(id=attrs['organisation_id'])
            attrs['organisation'] = org
        except Organisation.DoesNotExist:
            raise serializers.ValidationError({'organisation_id': 'Organisation not found'})
        
        # Check if user is already an agent elsewhere
        existing_agent = Agent.get_agent_for_user(user)
        if existing_agent and existing_agent.is_active:
            if existing_agent.organisation.id != org.id:
                raise serializers.ValidationError({
                    'user_id': f'User is already an agent for {existing_agent.organisation.name}'
                })
        
        return attrs


class GrantAgentPermissionSerializer(serializers.Serializer):
    """Serializer for granting permissions to an agent."""
    permission_key = serializers.CharField()
    
    def validate_permission_key(self, value):
        """Validate permission exists."""
        try:
            permission = Permission.objects.get(key=value)
            return permission
        except Permission.DoesNotExist:
            raise serializers.ValidationError('Permission not found')


class UserPermissionSerializer(serializers.ModelSerializer):
    """Serializer for user permissions."""
    permission = PermissionSerializer(read_only=True)
    permission_key = serializers.CharField(write_only=True, required=False)
    granted_by_email = serializers.EmailField(source='granted_by.email', read_only=True)
    
    class Meta:
        model = UserPermissionAccess
        fields = (
            'id', 'permission', 'permission_key',
            'granted_at', 'granted_by_email'
        )
        read_only_fields = ('id', 'granted_at')


class UserDetailSerializer(UserSerializer):
    """Extended user serializer with full permission details."""
    direct_permissions = serializers.SerializerMethodField()
    agent_permissions = serializers.SerializerMethodField()
    all_permissions = serializers.SerializerMethodField()
    accessible_organisations = serializers.SerializerMethodField()
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'direct_permissions', 'agent_permissions', 
            'all_permissions', 'accessible_organisations'
        )
    
    def get_direct_permissions(self, obj):
        """Get direct permissions."""
        perms = obj.get_direct_permissions()
        return PermissionSerializer(perms, many=True).data
    
    def get_agent_permissions(self, obj):
        """Get agent permissions."""
        if not obj.is_agent():
            return []
        perms = obj.get_agent_permissions()
        return PermissionSerializer(perms, many=True).data
    
    def get_all_permissions(self, obj):
        """Get all permissions combined."""
        perms = obj.get_all_permissions()
        return PermissionSerializer(perms, many=True).data
    
    def get_accessible_organisations(self, obj):
        """Get organisations user can access."""
        from .utils import get_user_accessible_organisations
        orgs = get_user_accessible_organisations(obj)
        return OrganisationSerializer(orgs, many=True, context=self.context).data
