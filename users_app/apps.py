from django.apps import AppConfig


class UsersAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users_app'
    verbose_name = 'Пользователи'

    def ready(self):
        from .signals import crop_user_image
