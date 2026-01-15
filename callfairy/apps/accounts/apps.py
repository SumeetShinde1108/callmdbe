from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'callfairy.apps.accounts'
    label = 'accounts'

    def ready(self):
        """Import tasks and signals when app is ready."""
        # Import tasks to ensure Celery auto-discovers them
        try:
            from . import tasks  # noqa: F401
        except ImportError:
            # Tasks module might not exist in certain contexts; ignore if missing
            pass
        
        # Import signals for automatic role synchronization
        try:
            from . import signals  # noqa: F401
        except ImportError:
            pass
