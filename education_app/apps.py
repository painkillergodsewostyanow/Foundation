from django.apps import AppConfig


class EducationAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'education_app'
    verbose_name = 'Обучение'

    def ready(self):
        from .signals import simple_task_solved, lesson_solved, course_part_solved
