from django.apps import AppConfig


class MyAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_auth'
    verbose_name = 'Аккаунт'

    def ready(self):
        import my_auth.signals
