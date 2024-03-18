from django import forms
from django.contrib.auth import authenticate

from .models import *
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import Http404


class ResetPasswordRequestForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': "form__input", 'placeholder': 'Введите почту'}
    ))

    def clean(self):
        email = self.data['email']

        try:
            user = get_object_or_404(User, email=email)
        except Http404:
            user = None

        if not user:
            self.add_error('email', 'Пользователь с данной почтой не зарегистрирован')

        self.cleaned_data['email'] = email
        self.cleaned_data['user'] = user

        return self.cleaned_data


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=65,
        label='',
        widget=forms.TextInput(
            attrs={'class': "form__input", 'placeholder': 'Введите имя пользователя'}
        )
    )
    password = forms.CharField(
        max_length=65,
        label='',
        widget=forms.PasswordInput(
            attrs={'class': "form__input", 'placeholder': 'Введите пароль'}
        )
    )

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )

            if self.user_cache is None:
                raise self.get_invalid_login_error()

            if not self.user_cache.is_email_verified:
                self.user_cache.send_verified_email()
                self.add_error('username', 'Подтвердите почту.\nПисьмо отправлено автоматически')

            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class RegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.pop("autofocus", None)

    CHOICES = [
        ('0', 'Студент'),
        ('1', 'Преподаватель'),
    ]

    student_or_teacher = forms.ChoiceField(
        label='',
        widget=forms.RadioSelect,
        choices=CHOICES,
    )

    username = forms.CharField(
        label='',
        widget=forms.TextInput(
            attrs={
                'class': "form__input",
                'placeholder': 'Введите имя пользователя',
            }
        )
    )

    email = forms.EmailField(
        label='',
        widget=forms.EmailInput(attrs={'class': "form__input", 'placeholder': 'Введите почту'})
    )

    password1 = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'class': "form__input", 'placeholder': 'Введите пароль'}),
    )

    password2 = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'class': "form__input", 'placeholder': 'Подтвердите пароль'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'student_or_teacher', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(self)
        if self.cleaned_data['student_or_teacher'] == '1':
            Teacher.objects.create(user=user)
            return user

        Student.objects.create(user=user)
        return user

