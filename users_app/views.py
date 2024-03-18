from django.shortcuts import render, redirect, reverse
from django.utils.http import urlsafe_base64_decode
from django.views import View

from .forms import *
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.conf import settings


def auth_reg_page(request):
    if request.method == 'GET':
        return render(
            request,
            'users_app/auth_reg_page.html',
            {
                'auth_form': LoginForm(),
                'reg_form': RegistrationForm(),
                'reset_pwd_request_form': ResetPasswordRequestForm()
            }
        )


def registration(request):
    if request.method == "POST":
        reg_form = RegistrationForm(data=request.POST)
        if reg_form.is_valid():
            user = reg_form.save()
            user.send_verified_email()
            return render(
                request,
                'users_app/alerts/alert.html',
                {
                    'title': 'Подтвердите почту',
                    'msg': 'Для завершения регистрации подтвердите почту, письмо высланно автоматически'}
            )

        return render(
            request,
            'users_app/auth_reg_page.html',
            {
                'reg_form': reg_form,
                'auth_form': LoginForm(),
                'reset_pwd_request_form': ResetPasswordRequestForm()
            }
        )


def authorization(request):
    if request.method == 'POST':
        auth_form = LoginForm(data=request.POST)
        if auth_form.is_valid():
            user = authenticate(username=auth_form.cleaned_data['username'], password=auth_form.cleaned_data['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect(settings.LOGIN_REDIRECT_URL)
                else:
                    return HttpResponse('Аккаунт заблокирован')

        return render(
            request,
            'users_app/auth_reg_page.html',
            {
                'auth_form': auth_form,
                'reg_form': RegistrationForm(),
                'reset_pwd_request_form': ResetPasswordRequestForm()
            }
        )


def pwd_reset_request(request):
    if request.method == "POST":
        reset_form = ResetPasswordRequestForm(request.POST)
        if reset_form.is_valid():
            email = reset_form.cleaned_data['email']
            user = reset_form.cleaned_data['user']

            subj = "Запрошен сброс пароля"
            email_template = "users_app/email/pwd_reset_msg.html"

            context = {
                'email': user.email,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'username': user.username,
                'token': default_token_generator.make_token(user)
            }

            msg_html = render_to_string(email_template, context)

            send_mail(
                subject=subj,
                from_email=settings.EMAIL_HOST_USER,
                message=msg_html,
                recipient_list=[email]
            )
            return redirect(reverse('users_app:pwd_reset_done'))

        reset_form.fields['email'].widget.attrs["autofocus"] = ''
        return render(
            request,
            'users_app/auth_reg_page.html',
            context={
                'reg_form': RegistrationForm(),
                'auth_form': LoginForm(),
                'reset_pwd_request_form': reset_form
            }
        )
    raise Http404()


class EmailVerify(View):
    def get(self, request, uidb64, token):
        user = self.get_user(uidb64)

        if user and default_token_generator.check_token(user, token):
            user.is_email_verified = True
            user.save()
            login(request=self.request, user=user)
            return redirect(settings.LOGIN_REDIRECT_URL)
        return render(
            self.request,
            'users_app/alerts/alert.html',
            {'title': 'Токен устарел', 'msg': 'Ссылка устарела, залогиньтесь снова, что бы получить новую'})

    @staticmethod
    def get_user(uidb64):
        try:
            user_pk = urlsafe_base64_decode(uidb64).decode()
            user = get_object_or_404(User, pk=user_pk)
        except Http404:
            user = None

        return user


