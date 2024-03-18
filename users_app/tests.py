from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .forms import RegistrationForm, LoginForm
from .models import Teacher, User, Student


class UserTestCase(TestCase):

    def test_student_reg(self):
        # Регистрация
        registration_url = reverse('users_app:registration')

        registration_form_data = RegistrationForm(data={
            'username': 'root123',
            'password1': '123321password',
            'password2': '123321password',
            'email': 'roottest123@gmail.com',
            'student_or_teacher': '0'
        }).data

        # Проверка, что пользователь создался
        self.client.post(registration_url, data=registration_form_data)
        user = User.objects.last()
        self.assertIsNotNone(user, 'Пользователь не был зарегистрирован')

    def test_user_related_with_student(self):
        user = RegistrationForm(data={
            'username': 'root123',
            'password1': '123321password',
            'password2': '123321password',
            'email': 'roottest123@gmail.com',
            'student_or_teacher': '0'
        }).save()

        try:
            student = Student.objects.get(user=user)
        except Student.DoesNotExist:
            student = None

        self.assertIsNotNone(student, 'Пользователь не был связан с объектом студента')

    def test_user_related_with_teacher(self):
        user = RegistrationForm(data={
            'username': 'root123',
            'password1': '123321password',
            'password2': '123321password',
            'email': 'roottest123@gmail.com',
            'student_or_teacher': '1'
        }).save()

        try:
            teacher = Teacher.objects.get(user=user)
        except Student.DoesNotExist:
            teacher = None

        self.assertIsNotNone(teacher, 'Пользователь не был связан с объектом преподавателя')

    def test_signin_without_verified_email(self):
        # Регистрация
        registration_url = reverse('users_app:registration')

        registration_form_data = RegistrationForm(data={
            'username': 'root123',
            'password1': '123321password',
            'password2': '123321password',
            'email': 'roottest123@gmail.com',
            'student_or_teacher': '1'
        }).data

        self.client.post(registration_url, data=registration_form_data)

        # Проверка на возможность входа в аккаунт без верифицированной почты
        login_url = reverse('users_app:authorization')

        login_form_data = LoginForm(data={
            'username': 'root123',
            'password': '123321password'
        }).data

        response = self.client.post(login_url, data=login_form_data)
        self.assertEqual(response.status_code, 200, msg='Пользователь смог войти без подтвержденной почты')

    def test_email_verify(self):
        # Регистрация пользователя
        registration_url = reverse('users_app:registration')

        registration_form_data = RegistrationForm(data={
            'username': 'root123',
            'password1': '123321password',
            'password2': '123321password',
            'email': 'roottest123@gmail.com',
            'student_or_teacher': '1'
        }).data

        self.client.post(registration_url, data=registration_form_data)
        user = User.objects.last()

        # Верификация почты
        verify_url = reverse('users_app:verify_email', kwargs={
            'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user)
        })

        full_verify_url = f"http://127.0.0.1:8000{verify_url}"

        self.client.get(full_verify_url)
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified, msg='Почта не подтвердилась')

    def test_signin_with_verified_email(self):
        # Регистрация пользователя
        registration_url = reverse('users_app:registration')

        registration_form_data = RegistrationForm(data={
            'username': 'root123',
            'password1': '123321password',
            'password2': '123321password',
            'email': 'roottest123@gmail.com',
            'student_or_teacher': '1'
        }).data

        self.client.post(registration_url, data=registration_form_data)
        user = User.objects.last()

        # Верификация почты
        verify_url = reverse('users_app:verify_email', kwargs={
            'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user)
        })

        full_verify_url = f"http://127.0.0.1:8000{verify_url}"

        self.client.get(full_verify_url)
        user.refresh_from_db()

        login_url = reverse('users_app:authorization')

        login_form_data = LoginForm(data={
            'username': user.username,
            'password': '123321password'
        }).data

        response = self.client.post(login_url, data=login_form_data)

        self.assertEqual(response.status_code, 302, msg='Пользователь не смог войти с подтвержденной почтой')
