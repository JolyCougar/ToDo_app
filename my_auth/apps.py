from django.apps import AppConfig


class MyAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_auth'

    def ready(self):
        import my_auth.signals
