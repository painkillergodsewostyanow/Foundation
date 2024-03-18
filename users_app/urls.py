from django.urls import path, include, reverse_lazy
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
)
from .views import *

app_name = 'users_app'

urlpatterns = [

    # auth block
    path('auth-reg', auth_reg_page, name='reg_auth_form'),
    path('registration', registration, name='registration'),
    path('authorization', authorization, name='authorization'),
    path('logout', LogoutView.as_view(), name='logout'),
    # auth block

    # reset pwd block
    path('pwd-reset-request', pwd_reset_request, name='pwd_reset_request'),
    path(
        'pwd-reset-done',
        PasswordResetDoneView.as_view(template_name='users_app/alerts/pwd_reset_done.html'),
        name='pwd_reset_done'
    ),

    path(
        'pwd-reset-confirm/<uidb64>/<token>',
        PasswordResetConfirmView.as_view(
            template_name='users_app/pwd_reset_confirm.html',
            success_url=reverse_lazy("users_app:pwd_reset_complete")
        ),
        name='pwd_reset_confirm'
    ),

    path('pwd-reset-complete', auth_reg_page, name='pwd_reset_complete'),
    # reset pwd block

    # verify email block
    path('email-verify/<uidb64>/<token>', EmailVerify.as_view(), name='verify_email')
    # verify email block
]
