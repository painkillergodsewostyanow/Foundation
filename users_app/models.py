from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


class User(AbstractUser):
    is_email_verified = models.BooleanField(default=False, verbose_name='Подтверждение почты')
    image = models.ImageField(upload_to='media/users/users-image/', blank=True, null=True)
    about = models.CharField(max_length=350, blank=True, null=True)
    email = models.EmailField(unique=True)
    link_to_vk = models.URLField(blank=True, null=True)
    link_to_tg = models.URLField(blank=True, null=True)
    link_to_github = models.URLField(blank=True, null=True)
    link_to_site = models.URLField(blank=True, null=True)

    MAX_IMAGE_WIDTH = 600
    MAX_IMAGE_HEIGHT = 900

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def send_verified_email(self):
        user = self
        context = {
            'user': user,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user)
        }

        message = render_to_string('users_app/email/verify_email_msg.html', context)

        send_mail(
            subject='Подтверждение почты',
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email]
        )

    def get_last_unsolved_lesson_pk(self, lessons_query):
        """Получение pk урока на котором остановился ученик"""
        last_solved_lesson_order = lessons_query.filter(students_that_solved=self).values_list(
            'order', flat=True
        ).last()

        if last_solved_lesson_order is not None:
            next_unsolved_lesson = lessons_query.filter(order__gt=last_solved_lesson_order).order_by(
                'order').values_list('pk', flat=True).first()

            return next_unsolved_lesson if next_unsolved_lesson else lessons_query.values_list('pk', flat=True).last()

        return lessons_query.order_by('order').values_list('pk', flat=True).first()

    def is_teacher(self):
        """ Проверка на то учитель ли пользователь """
        return hasattr(self, 'teacher')

    @property
    def related_teacher(self):
        """ Получение учителя без ошибки если у пользователя такового нет """
        return self.teacher if self.is_teacher() else None


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')

    class Meta:
        verbose_name = 'Преподаватель'
        verbose_name_plural = 'Преподаватели'

    def __str__(self):
        return self.user.username


