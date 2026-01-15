"""
URL configuration for callfairy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="CallFairy API",
      default_version='v1',
      description="CallFairy Voice AI Platform API",
      terms_of_service="https://www.callfairy.com/terms/",
      contact=openapi.Contact(email="support@callfairy.com"),
      license=openapi.License(name="Proprietary"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

api_patterns = [
    path('auth/', include('callfairy.apps.accounts.urls')),
    path('calls/', include('callfairy.apps.calls.urls')),
]

# Import template views
from callfairy.apps.accounts.template_views import (
    login_view, register_view, logout_view, 
    password_reset_request_view, password_reset_confirm_view
)
from callfairy.apps.accounts.user_management_views import (
    organisations_list_view, organisation_detail_view, organisation_edit_view,
    organisation_create_view, agents_list_view, agent_assign_view,
    agent_revoke_view, agent_permissions_view, system_users_list_view,
    user_profile_view, permissions_list_view
)
from callfairy.apps.calls.template_views import (
    dashboard_view, make_call_view, contacts_list_view, calls_list_view,
    batches_list_view, batch_detail_view, create_campaign_view, import_csv_view, users_list_view
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API URLs
    path('api/v1/', include(api_patterns)),
    
    # Authentication URLs
    path('', login_view, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('password-reset/', password_reset_request_view, name='password_reset_request'),
    path('password-reset-confirm/<uidb64>/<token>/', password_reset_confirm_view, name='password_reset_confirm'),
    
    # Dashboard & Calls URLs
    path('dashboard/', dashboard_view, name='dashboard'),
    path('make-call/', make_call_view, name='make_call'),
    path('contacts/', contacts_list_view, name='contacts_list'),
    path('calls/', calls_list_view, name='calls_list'),
    path('campaigns/', batches_list_view, name='batches_list'),
    path('campaigns/<uuid:batch_id>/', batch_detail_view, name='batch_detail'),
    path('campaigns/create/', create_campaign_view, name='create_campaign'),
    path('import-csv/', import_csv_view, name='import_csv'),
    path('users/', users_list_view, name='users_list'),
    
    # User Management URLs
    path('management/organisations/', organisations_list_view, name='organisations_list'),
    path('management/organisations/create/', organisation_create_view, name='organisation_create'),
    path('management/organisations/<int:org_id>/', organisation_detail_view, name='organisation_detail'),
    path('management/organisations/<int:org_id>/edit/', organisation_edit_view, name='organisation_edit'),
    
    path('management/agents/', agents_list_view, name='agents_list'),
    path('management/agents/assign/', agent_assign_view, name='agent_assign'),
    path('management/agents/<uuid:agent_id>/revoke/', agent_revoke_view, name='agent_revoke'),
    path('management/agents/<uuid:agent_id>/permissions/', agent_permissions_view, name='agent_permissions'),
    
    path('management/system-users/', system_users_list_view, name='system_users_list'),
    path('management/users/<uuid:user_id>/profile/', user_profile_view, name='user_profile'),
    path('management/permissions/', permissions_list_view, name='permissions_list'),
    
    # Django AllAuth
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
