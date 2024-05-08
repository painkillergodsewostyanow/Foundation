from django.db.models import OuterRef, Count, Q, Subquery, IntegerField
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect, reverse
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.generic import DetailView, UpdateView

from education_app.models import StudentThatSolvedCoursePartM2M, StudentThatSolvedLessonM2M, \
    StudentThatSolvedSimpleTaskM2M, Lesson, Course, StudentThatSolvedQuizM2M
from .forms import *
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.conf import settings


class ChangePwdView(View):
    form_class = ChangePasswordForm
    template_name = 'users_app/profile/update_profile.html'

    def post(self, *args, **kwargs):
        pwd_change_form = self.form_class(user=self.request.user, data=self.request.POST)
        if pwd_change_form.is_valid():
            pwd_change_form.save()
            return redirect(settings.LOGOUT_REDIRECT_URL)

        form = UpdateUserForm(instance=self.request.user)

        return render(
            self.request, self.template_name, {
                'pwd_change_form': pwd_change_form,
                'form': form
            }
        )


class UpdateUser(UpdateView):
    form_class = UpdateUserForm
    pwd_change_form = ChangePasswordForm
    template_name = 'users_app/profile/update_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'pwd_change_form': self.pwd_change_form(user=self.get_object())
            }
        )
        return context

    def get_success_url(self):
        return reverse('users_app:profile', kwargs={'pk': self.get_object().pk})

    def get_object(self, **kwargs):
        return self.request.user


class ProfileView(DetailView):
    model = User
    template_name = 'users_app/profile/profile.html'

    def get_context_data(self, **kwargs):
        student = self.get_object()

        context = super().get_context_data(**kwargs)
        solved_course_parts = StudentThatSolvedCoursePartM2M.objects.filter(student=student).select_related(
            'course_part')[:5]
        solved_lessons = StudentThatSolvedLessonM2M.objects.filter(student=student).select_related('lesson')[:5]
        solved_simpletask = StudentThatSolvedSimpleTaskM2M.objects.filter(student=student).select_related(
            'simple_task')[:5]

        solved_quiz = StudentThatSolvedQuizM2M.objects.filter(student=student).select_related(
            'quiz')[:5]

        activity_list = sorted(list(solved_quiz) + list(solved_course_parts) + list(solved_lessons) + list(solved_simpletask),
                               key=lambda x: x.time, reverse=True)

        sub_query_get_last_solved_lesson = Lesson.objects.filter(
            course_part__course=OuterRef('pk'),
            students_that_solved=student,
        ).values('order')[:1]

        sub_query_get_next_lesson_pk = Lesson.objects.filter(
            course_part__course=OuterRef('pk'),
            order__gt=OuterRef('last_solved_lesson_order'),  # ORDER ИЗ last_solved_lesson_order
        ).values('pk')

        sub_query_get_next_lesson_pk_if_no_one_solved = Lesson.objects.filter(
            course_part__course=OuterRef('pk'),
        ).values('pk')[0:1]

        courses = Course.objects.filter(students=student).select_related('author__user').annotate(
            percent_ready=(
                    Count('coursepart__lesson', filter=Q(coursepart__lesson__students_that_solved=student)) /
                    Count('coursepart__lesson', distinct=True) * 100
            ),

            last_solved_lesson_order=Subquery(
                sub_query_get_last_solved_lesson, output_field=IntegerField()
            ),

            next_lesson_pk=Coalesce(
                Subquery(sub_query_get_next_lesson_pk, output_field=IntegerField()),
                Subquery(sub_query_get_next_lesson_pk_if_no_one_solved, output_field=IntegerField())
            ),
        )

        context.update({'activity_list': activity_list, 'courses': courses})
        return context


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
                    'msg': 'Для завершения регистрации подтвердите почту, письмо высланно автоматически'
                }
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


