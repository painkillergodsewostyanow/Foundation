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

    def is_teacher(self):
        return hasattr(self, 'teacher')


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')

    class Meta:
        verbose_name = 'Преподаватель'
        verbose_name_plural = 'Преподаватели'

    def __str__(self):
        return self.user.username


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'

    def __str__(self):
        return self.user.username

