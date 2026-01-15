from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    # Authentication views
    RegisterView,
    LoginView,
    MeView,
    EmailVerifyView,
    TOTPEnableView,
    TOTPVerifyView,
    TOTPDisableView,
    GoogleLoginView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    # Multi-tenant permission views
    OrganisationListView,
    OrganisationDetailView,
    OrganisationUpdateView,
    AssignAgentView,
    RevokeAgentView,
    AgentListView,
    GrantAgentPermissionView,
    RevokeAgentPermissionView,
    PermissionListView,
    MyPermissionsView,
    MyOrganisationsView,
)

app_name = 'accounts'

urlpatterns = [
    # ============ AUTHENTICATION ============
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('login/google/', GoogleLoginView.as_view(), name='login_google'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email/', EmailVerifyView.as_view(), name='verify_email'),
    
    # Password Reset
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # 2FA
    path('2fa/totp/enable/', TOTPEnableView.as_view(), name='totp_enable'),
    path('2fa/totp/verify/', TOTPVerifyView.as_view(), name='totp_verify'),
    path('2fa/totp/disable/', TOTPDisableView.as_view(), name='totp_disable'),
    
    # ============ USER PROFILE ============
    path('me/', MeView.as_view(), name='me'),
    path('me/permissions/', MyPermissionsView.as_view(), name='my-permissions'),
    path('me/organisations/', MyOrganisationsView.as_view(), name='my-organisations'),
    
    # ============ ORGANISATIONS ============
    path('organisations/', OrganisationListView.as_view(), name='organisation-list'),
    path('organisations/<int:pk>/', OrganisationDetailView.as_view(), name='organisation-detail'),
    path('organisations/<int:pk>/update/', OrganisationUpdateView.as_view(), name='organisation-update'),
    
    # ============ AGENT MANAGEMENT ============
    path('agents/', AgentListView.as_view(), name='agent-list'),
    path('agents/assign/', AssignAgentView.as_view(), name='assign-agent'),
    path('agents/<uuid:agent_id>/revoke/', RevokeAgentView.as_view(), name='revoke-agent'),
    path('agents/<uuid:agent_id>/permissions/grant/', GrantAgentPermissionView.as_view(), name='grant-agent-permission'),
    path('agents/<uuid:agent_id>/permissions/<str:permission_key>/', RevokeAgentPermissionView.as_view(), name='revoke-agent-permission'),
    
    # ============ PERMISSIONS ============
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
]
