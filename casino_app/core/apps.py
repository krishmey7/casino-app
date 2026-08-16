from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'casino_app.core'
    # Keep the original app label so existing migrations and db state remain valid
    label = 'casino_app'
