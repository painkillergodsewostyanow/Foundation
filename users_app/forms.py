from django import forms
from django.contrib.auth import authenticate
from .models import *
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm, PasswordChangeForm
from django.http import Http404


class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'style': "font-size:24px; text-align: center; font-weight: bold;",
        'class': "form-control", 'placeholder': "Введите старый пароль"
    }))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'style': "font-size:24px; text-align: center; font-weight: bold;",
        'class': "form-control", 'placeholder': "Введите новый пароль"
    }))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'style': "font-size:24px; text-align: center; font-weight: bold;",
        'class': "form-control", 'placeholder': "Повторите пароль"
    }))


class UpdateUserForm(UserChangeForm):

    username = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'style': "font-size:24px; text-align: center; font-weight: bold;",
        'class': "form-control", 'placeholder': "Username",
    }))
    link_to_tg = forms.URLField(required=False, widget=forms.TextInput(attrs={
        'style': "font-size:24px; text-align: center; font-weight: bold;",
        'class': "form-control", 'placeholder': "ссылка на tg"
    }))
    link_to_vk = forms.URLField(required=False, widget=forms.TextInput(attrs={
        'style': "font-size:24px; text-align: center; font-weight: bold;",
        'class': "form-control", 'placeholder': "ссылка на vk"
    }))
    link_to_github = forms.URLField(required=False, widget=forms.TextInput(attrs={
        'style': "font-size:24px; text-align: center; font-weight: bold;",
        'class': "form-control", 'placeholder': "ссылка на github"
    }))
    link_to_site = forms.URLField(required=False, widget=forms.TextInput(attrs={
        'style': "font-size:24px; text-align: center; font-weight: bold;",
        'class': "form-control", 'placeholder': "ссылка на сайт"
    }))
    image = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': "input-file", 'onchange': "previewImage()"
    }))
    about = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'w-100', 'style': 'font-size: 24px;'
    }))

    class Meta:
        model = User
        fields = (
            'username', 'image', 'about', 'link_to_vk', 'link_to_tg',
            'link_to_github', 'link_to_site'
        )


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

