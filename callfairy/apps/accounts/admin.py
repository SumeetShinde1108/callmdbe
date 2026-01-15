from django.contrib import admin
from .models import User, AllowedEmailDomain, GoogleSignInAudit
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _


class UserAdmin(BaseUserAdmin):
    """Define admin model for custom User model."""
    
    list_display = ('email', 'name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('email', 'name', 'company')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'company', 'job_title', 'phone')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                     'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )


admin.site.register(User, UserAdmin)


@admin.register(AllowedEmailDomain)
class AllowedEmailDomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "is_active")
    list_filter = ("is_active",)
    search_fields = ("domain",)


@admin.register(GoogleSignInAudit)
class GoogleSignInAuditAdmin(admin.ModelAdmin):
    list_display = ("email", "domain", "success", "created_at")
    list_filter = ("success", "domain")
    search_fields = ("email", "domain", "provider_sub")
    readonly_fields = ("user", "email", "domain", "provider_sub", "success", "reason", "ip", "user_agent", "created_at")
