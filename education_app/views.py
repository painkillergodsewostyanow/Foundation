from django.db.models import Count, Q, Max, OuterRef, Subquery, IntegerField, F, Case, When
from django.db.models.functions import Coalesce
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, reverse, redirect
from django.views.generic import UpdateView, DetailView, CreateView, DeleteView, ListView, View
from .forms import CourseForm, CoursePartForm, LessonForm, AnswerToSimpleTaskForm, SimpleTaskForm, QuizForm, AnswerForm, \
    TaskWithFileForm, AnswerToTaskWFileForm
from .models import (Course, CoursePart, Lesson, SimpleTask, StudentThatSolvedLessonM2M, StudentThatSolvedCoursePartM2M,
                     StudentThatSolvedSimpleTaskM2M, SimpleTaskToManualTest, QuizQuestion, Answer,
                     StudentThatSolvedQuizM2M, TaskWithFile, AnswerToTaskWithFile, StudentThatSolvedTaskWithFileM2M,
                     StudentThatSolvedCourseM2M)
from django.contrib import messages


def dashboard(request):
    if request.user.is_teacher():
        return redirect(reverse('education_app:teacher_dashboard'))
    return redirect(reverse('education_app:student_dashboard'))


class TeacherDashboard(View):

    def get(self, request, *args, **kwargs):
        simple_task_manual_test = list(
            SimpleTaskToManualTest.objects
            .filter(simple_task__lesson__course_part__course__author=request.user.teacher, status__isnull=True)
            .select_related('simple_task')
            .select_related('student')
        ) + list(
            AnswerToTaskWithFile.objects.filter(
                task__lesson__course_part__course__author=request.user.teacher, status__isnull=True
            )
            .select_related('task')
            .select_related('student')
        )
        manual_test_objs = simple_task_manual_test

        return render(
            request,
            'education_app/teacher_dashboard.html',
            context={'manual_test_objs': manual_test_objs}
        )


class StudentDashboard(View):
    def get(self, request, *args, **kwargs):
        student = self.request.user

        solved_courses = StudentThatSolvedCourseM2M.objects.filter(student=student).select_related(
            'course')[:5]
        solved_course_parts = StudentThatSolvedCoursePartM2M.objects.filter(student=student).select_related(
            'course_part')[:5]
        solved_lessons = StudentThatSolvedLessonM2M.objects.filter(student=student).select_related('lesson')[:5]
        solved_simpletask = StudentThatSolvedSimpleTaskM2M.objects.filter(student=student).select_related(
            'simple_task')[:5]

        solved_quiz = StudentThatSolvedQuizM2M.objects.filter(student=student).select_related(
            'quiz')[:5]

        solved_task_w_file = StudentThatSolvedTaskWithFileM2M.objects.filter(student=student).select_related('task')

        activity_list = sorted(
            list(solved_quiz) + list(solved_course_parts) + list(solved_lessons) + list(solved_simpletask) +
            list(solved_task_w_file) + list(solved_courses),
            key=lambda x: x.time, reverse=True
        )

        manual_test_result = list(
            SimpleTaskToManualTest.objects
            .filter(student=student)
            .select_related('simple_task')
            .select_related('simple_task__lesson')
        ) + list(
            AnswerToTaskWithFile.objects.filter(
                student=student
            )
            .select_related('task')
            .select_related('student')
        )

        sub_query_get_last_solved_lesson = Lesson.objects.filter(
            course_part__course=OuterRef('pk'),
            students_that_solved=student,
        ).values('order')[:1]

        sub_query_get_next_lesson_pk = Lesson.objects.filter(
            course_part__course=OuterRef('pk'),
            order__gt=OuterRef('last_solved_lesson_order'),  # ORDER ИЗ last_solved_lesson_order
        ).values('pk')[:1]

        sub_query_get_next_lesson_pk_if_no_one_solved = Lesson.objects.filter(
            course_part__course=OuterRef('pk'),
        ).values('pk')[:1]

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

        return render(
            request, 'education_app/student_dashboard.html',
            {
                'courses': courses, 'activity_list': activity_list,
                'manual_test_result': manual_test_result
            }
        )


def signup_for_course(request):
    if request.method == "POST":
        course_id = request.POST.get('course_id', None)
        course = get_object_or_404(Course, id=course_id)
        course.sing_up(request.user)
        return redirect(reverse('education_app:course_preview', args=(course_id,)))
    raise Http404


class CatalogListView(ListView):
    template_name = 'education_app/course_catalog.html'
    model = Course
    paginate_by = 6

    def get_queryset(self):
        return self.model.objects.filter(is_published=True)


class CourseCreateView(CreateView):
    form_class = CourseForm
    template_name = 'education_app/course/create.html'

    def form_valid(self, form):
        author = self.request.user.teacher
        form.instance.author = author
        form.save()
        return super().form_valid(form)


class CourseUpdateView(UpdateView):
    form_class = CourseForm
    template_name = 'education_app/course/update.html'

    def get_context_data(self, **kwargs):
        context = super(CourseUpdateView, self).get_context_data(**kwargs)
        context['add_course_part_form'] = CoursePartForm()
        return context

    def get(self, request, *args, **kwargs):
        course = self.get_object()
        if not course.is_owner(request.user.teacher):
            raise Http404()

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        course = self.get_object()
        if not course.is_owner(request.user.teacher):
            raise Http404()

        return super().post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            pk = self.kwargs.get('course_id', None)
            self.object = get_object_or_404(self.get_queryset(), id=pk)

        return self.object

    def get_queryset(self):
        return (
            Course.objects.prefetch_related('coursepart_set')
            .prefetch_related('coursepart_set__lesson_set')
            .select_related('author')
        )


class CourseDetailView(DetailView):
    queryset = Course.objects.all().select_related('author').prefetch_related('students').annotate(
        course_part_count=Count('coursepart'),
    )
    template_name = 'education_app/course/view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = context['object']

        lessons = Lesson.objects.filter(course_part__course=course).annotate(
            count_simple_task=Count('simpletask', distinct=True),
            count_quiz=Count('quizquestion', distinct=True),
        ).values('pk', 'video', 'students_that_solved', 'order', 'count_quiz', 'count_simple_task', 'video')

        count_task = sum(lesson['count_quiz'] + lesson['count_simple_task'] for lesson in lessons)
        count_video = sum(1 for lesson in lessons if lesson['video'])

        student_on_course = self.request.user in course.students.all()

        added_context = {
            'count_simple_task': count_task,
            'count_video': count_video,
            'count_lesson': lessons.count(),
            'count_course_part': course.course_part_count,
            'student_on_course': student_on_course,
        }

        if not course.is_owner(self.request.user.related_teacher):
            added_context.update({
                'next_unsolved_lesson_pk': self.request.user.get_last_unsolved_lesson_pk(lessons)
            })

        context.update(added_context)

        return context


class CoursePartCreateView(CreateView):
    form_class = CoursePartForm
    template_name = 'education_app/course_part/create.html'

    def post(self, request, *args, **kwargs):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        self.success_url = reverse('education_app:update_course', kwargs={'course_id': course.pk})
        if not course.is_owner(request.user.teacher):
            raise Http404
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        course = Course.objects.get(pk=self.kwargs.get('course_id'))
        form.instance.course = course
        form.save()
        return super().form_valid(form)


class CoursePartUpdateView(UpdateView):
    form_class = CoursePartForm
    template_name = 'education_app/course_part/update.html'

    def get(self, request, *args, **kwargs):
        course_part = self.get_object()
        if not course_part.course.is_owner(request.user.teacher):
            raise Http404
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        course_part = self.get_object()
        self.success_url = reverse('education_app:update_course', kwargs={'course_id': course_part.course.pk})
        if not course_part.course.is_owner(request.user.teacher):
            raise Http404
        return super().post(request, *args, **kwargs)

    def get_object(self, **kwargs):
        if not hasattr(self, 'object'):
            course_part_id = self.kwargs.get('course_part_id')
            self.object = get_object_or_404(self.get_queryset(), id=course_part_id)

        return self.object

    def get_queryset(self):
        return CoursePart.objects.select_related('course').prefetch_related('lesson_set').select_related(
            'course__author')


class CoursePartDeleteView(DeleteView):
    model = CoursePart
    template_name = 'education_app/course_part/confirm_delete.html'

    def post(self, request, *args, **kwargs):
        course_part = self.get_object()
        self.success_url = reverse('education_app:update_course', kwargs={'course_id': course_part.course.id})
        if not course_part.course.is_owner(self.request.user.teacher):
            raise Http404()
        return super().post(request, args, kwargs)

    def get(self, request, *args, **kwargs):
        course_part = self.get_object()
        if not course_part.course.is_owner(self.request.user.teacher):
            raise Http404()
        return super().get(request, args, kwargs)


class LessonCreateView(CreateView):
    form_class = LessonForm
    template_name = 'education_app/lesson/create.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_part = None

    def get(self, request, *args, **kwargs):
        course_part = get_object_or_404(CoursePart, id=self.kwargs.get('course_part_id'))
        if course_part.course.is_owner(request.user.teacher):
            form = self.form_class(initial={'order': course_part.get_auto_order_for_lesson()})
            return render(request, self.template_name, context={'form': form})
        raise Http404

    def post(self, request, *args, **kwargs):
        course_part = get_object_or_404(CoursePart, id=self.kwargs.get('course_part_id'))
        if not course_part.course.is_owner(request.user.teacher):
            raise Http404
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        course_part = get_object_or_404(CoursePart, id=self.kwargs.get('course_part_id'))
        form.instance.course_part = course_part
        lesson = form.save()
        self.success_url = reverse('education_app:update_lesson', kwargs={'lesson_id': lesson.pk})
        return super().form_valid(form)


class LessonUpdateView(UpdateView):
    form_class = LessonForm
    template_name = 'education_app/lesson/update.html'

    def get(self, request, *args, **kwargs):
        lesson = self.get_object()
        if not lesson.course_part.course.author == request.user.teacher:
            raise Http404()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        lesson = self.get_object()
        if not lesson.course_part.course.author == request.user.teacher:
            raise Http404()
        self.success_url = reverse('education_app:update_course_part', kwargs={'course_part_id': lesson.course_part.pk})
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Lesson.objects
            .select_related('course_part')
            .prefetch_related('course_part__course')
            .prefetch_related('course_part__course__author')
            .prefetch_related('simpletask_set')
            .filter(course_part__course__author=self.request.user.teacher)
        )

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            lesson_id = self.kwargs.get('lesson_id', None)
            self.object = get_object_or_404(self.get_queryset(), id=lesson_id)

        return self.object


class LessonDetailView(DetailView):
    model = Lesson
    template_name = 'education_app/lesson/view.html'

    def get(self, request, *args, **kwargs):

        lesson = self.get_object()
        if not lesson.student_has_access(self.request.user):
            return render(request, 'users_app/alerts/alert.html', context={
                'title': 'Урок не доступен', 'msg': 'Запишитесь на курс, или решите все предыдущие уроки'
            })

        simple_tasks = lesson.simpletask_set.all().prefetch_related('students_that_solved')
        quizs = lesson.quizquestion_set.all().prefetch_related('answer_set').prefetch_related('students_that_solved')
        task_w_file = lesson.taskwithfile_set.all().prefetch_related('students_that_solved')

        theory_task_w_file = list(filter(lambda x: x.place == 1, task_w_file))
        practice_task_w_file = list(filter(lambda x: x.place == 2, task_w_file))
        video_task_w_file = list(filter(lambda x: x.place == 3, task_w_file))

        theory_quiz = list(filter(lambda x: x.place == 1, quizs))
        practice_quiz = list(filter(lambda x: x.place == 2, quizs))
        video_quiz = list(filter(lambda x: x.place == 3, quizs))

        theory_task = list(filter(lambda x: x.place == 1, simple_tasks))
        practice_task = list(filter(lambda x: x.place == 2, simple_tasks))
        video_task = list(filter(lambda x: x.place == 3, simple_tasks))

        course_parts = lesson.course_part.course.coursepart_set.prefetch_related('lesson_set').all()

        if not simple_tasks and not quizs:
            lesson.students_that_solved.add(request.user)

        request_user_is_teacher = self.request.user.related_teacher
        request_user_is_owner = False

        if request_user_is_teacher:
            if request_user_is_teacher == self.get_object().course_part.course.author:
                request_user_is_owner = True

        answer_to_task_w_file_form = AnswerToTaskWFileForm(student=self.request.user)

        return render(
            request,
            self.template_name,
            context={
                'answer_to_task_w_file_form': answer_to_task_w_file_form,
                'theory_task_w_file': theory_task_w_file,
                'practice_task_w_file': practice_task_w_file,
                'video_task_w_file': video_task_w_file,
                'theory_task': theory_task, 'practice_task': practice_task,
                'video_task': video_task, 'object': lesson,
                'lesson_count': lesson.lessons_count,
                'course_parts': course_parts,
                'theory_quiz': theory_quiz, 'practice_quiz': practice_quiz,
                'video_quiz': video_quiz,
                'request_user_is_owner': request_user_is_owner
            }
        )

    def get_queryset(self):
        return (
            Lesson.objects
            .select_related('course_part')
            .select_related('course_part__course')
            .select_related('course_part__course__author')
            .prefetch_related('simpletask_set')
            .annotate(lessons_count=Count('course_part__lesson'))
        )

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            pk = self.kwargs.get('pk', None)
            self.object = get_object_or_404(self.get_queryset(), pk=pk)

        return self.object


class LessonDeleteView(DeleteView):
    model = Lesson
    template_name = 'education_app/lesson/confirm_delete.html'

    def post(self, request, *args, **kwargs):
        lesson = self.get_object()
        self.success_url = reverse('education_app:update_course_part', kwargs={'course_part_id': lesson.course_part.pk})
        if not lesson.course_part.course.is_owner(self.request.user.teacher):
            raise Http404()
        return super().post(request, args, kwargs)


class SimpleTaskCreateView(CreateView):
    form_class = SimpleTaskForm
    template_name = 'education_app/simple_task/create.html'

    def get(self, request, *args, **kwargs):
        lesson = get_object_or_404(Lesson, id=self.kwargs.get('lesson_id'))
        if lesson.course_part.course.is_owner(request.user.teacher):
            return super().get(request, args, kwargs)
        raise Http404()

    def post(self, request, *args, **kwargs):
        lesson = get_object_or_404(Lesson, id=self.kwargs.get('lesson_id'))
        self.success_url = self.success_url = reverse('education_app:update_lesson', kwargs={'lesson_id': lesson.pk})

        if lesson.course_part.course.is_owner(request.user.teacher):
            return super().post(request, args, kwargs)
        raise Http404()

    def form_valid(self, form):
        lesson = get_object_or_404(Lesson, id=self.kwargs.get('lesson_id'))
        form.instance.lesson = lesson
        form.save()
        return super().form_valid(form)


class SimpleTaskUpdateView(UpdateView):
    form_class = SimpleTaskForm
    template_name = 'education_app/simple_task/create.html'

    def get(self, request, *args, **kwargs):
        simple_task = self.get_object()
        if not simple_task.lesson.course_part.course.is_owner(request.user.teacher):
            raise Http404
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        simple_task = self.get_object()
        self.success_url = self.success_url = reverse('education_app:update_lesson',
                                                      kwargs={'lesson_id': simple_task.lesson.pk})
        if not simple_task.lesson.course_part.course.is_owner(request.user.teacher):
            raise Http404
        return super().post(request, *args, **kwargs)

    def get_object(self, **kwargs):
        if not hasattr(self, 'object'):
            simple_task_id = self.kwargs.get('simple_task_id')
            self.object = get_object_or_404(SimpleTask, id=simple_task_id)
        return self.object


class SimpleTaskDeleteView(DeleteView):
    model = SimpleTask
    template_name = 'education_app/lesson/confirm_delete.html'

    def post(self, request, *args, **kwargs):
        simple_task = self.get_object()
        self.success_url = reverse('education_app:update_course_part',
                                   kwargs={'course_part_id': simple_task.lesson.course_part.pk})
        if not simple_task.lesson.course_part.course.is_owner(self.request.user.teacher):
            raise Http404()
        return super().post(request, args, kwargs)


class QuizCreateView(CreateView):
    form_class = QuizForm
    template_name = 'education_app/quiz/create.html'

    def get(self, request, *args, **kwargs):
        lesson = get_object_or_404(Lesson, id=self.kwargs.get('lesson_id'))
        if lesson.course_part.course.is_owner(request.user.teacher):
            return super().get(request, args, kwargs)
        raise Http404()

    def post(self, request, *args, **kwargs):
        lesson = get_object_or_404(Lesson, id=self.kwargs.get('lesson_id'))

        if lesson.course_part.course.is_owner(request.user.teacher):
            return super().post(request, args, kwargs)
        raise Http404()

    def form_valid(self, form):
        lesson = get_object_or_404(Lesson, id=self.kwargs.get('lesson_id'))
        form.instance.lesson = lesson
        quiz = form.save()
        self.success_url = self.success_url = reverse('education_app:update_quiz', kwargs={'quiz_id': quiz.pk})
        return super().form_valid(form)


class QuizUpdateView(UpdateView):
    form_class = QuizForm
    template_name = 'education_app/quiz/update.html'

    def get_context_data(self, **kwargs):
        context = super(QuizUpdateView, self).get_context_data(**kwargs)
        context.update({
            'add_answer_form': AnswerForm()
        })
        return context

    def get(self, request, *args, **kwargs):
        quiz = self.get_object()
        if not quiz.lesson.course_part.course.is_owner(request.user.teacher):
            raise Http404
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        quiz = self.get_object()
        self.success_url = self.success_url = reverse('education_app:update_lesson',
                                                      kwargs={'lesson_id': quiz.lesson.pk})
        if not quiz.lesson.course_part.course.is_owner(request.user.teacher):
            raise Http404
        return super().post(request, *args, **kwargs)

    def get_object(self, **kwargs):
        if not hasattr(self, 'object'):
            simple_task_id = self.kwargs.get('quiz_id')
            self.object = get_object_or_404(QuizQuestion, id=simple_task_id)
        return self.object


class AnswerToQuizCreateView(CreateView):
    form_class = AnswerForm
    template_name = 'education_app/answer_to_quiz/create.html'

    def get(self, request, *args, **kwargs):
        quiz = get_object_or_404(QuizQuestion, id=self.kwargs.get('quiz_pk'))
        self.success_url = self.success_url = reverse('education_app:update_quiz', kwargs={'quiz_id': quiz.pk})

        if quiz.lesson.course_part.course.is_owner(request.user.teacher):
            return super().post(request, args, kwargs)
        raise Http404()

    def post(self, request, *args, **kwargs):
        quiz = get_object_or_404(QuizQuestion, id=self.kwargs.get('quiz_pk'))
        self.success_url = self.success_url = reverse('education_app:update_quiz', kwargs={'quiz_id': quiz.pk})

        if quiz.lesson.course_part.course.is_owner(request.user.teacher):
            return super().post(request, args, kwargs)
        raise Http404()

    def form_valid(self, form):
        quiz = get_object_or_404(QuizQuestion, id=self.kwargs.get('quiz_pk'))
        form.instance.question = quiz
        form.save()
        return super().form_valid(form)


class AnswerToQuizUpdateView(UpdateView):
    form_class = AnswerForm
    template_name = 'education_app/answer_to_quiz/update.html'

    def get(self, request, *args, **kwargs):
        quiz = self.get_object().question

        if quiz.lesson.course_part.course.is_owner(request.user.teacher):
            return super().post(request, args, kwargs)
        raise Http404()

    def post(self, request, *args, **kwargs):
        quiz = self.get_object().question
        self.success_url = self.success_url = reverse('education_app:update_quiz', kwargs={'quiz_id': quiz.pk})

        if quiz.lesson.course_part.course.is_owner(request.user.teacher):
            return super().post(request, args, kwargs)
        raise Http404()

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(Answer, id=self.kwargs.get('quiz_answer_id'))
        return self.object


class TaskWithFileCreateView(CreateView):
    form_class = TaskWithFileForm
    template_name = 'education_app/task_with_file/create.html'

    def get(self, request, *args, **kwargs):
        lesson = self.get_lesson()
        if lesson.course_part.course.is_owner(request.user.teacher):
            return super().get(request, args, kwargs)
        raise Http404()

    def post(self, request, *args, **kwargs):
        lesson = self.get_lesson()
        self.success_url = self.success_url = reverse('education_app:update_lesson', kwargs={'lesson_id': lesson.pk})

        if lesson.course_part.course.is_owner(request.user.teacher):
            return super().post(request, args, kwargs)
        raise Http404()

    def form_valid(self, form):
        lesson = self.get_lesson()
        form.instance.lesson = lesson
        form.save()
        return super().form_valid(form)

    def get_lesson(self):
        if not hasattr(self, 'lesson'):
            self.lesson = get_object_or_404(Lesson, id=self.kwargs.get('lesson_id'))
        return self.lesson


class TaskWithFileUpdateView(UpdateView):
    form_class = TaskWithFileForm
    template_name = 'education_app/task_with_file/create.html'

    def get(self, request, *args, **kwargs):
        task_w_file = self.get_object()

        if task_w_file.lesson.course_part.course.is_owner(request.user.teacher):
            return super().post(request, args, kwargs)
        raise Http404()

    def post(self, request, *args, **kwargs):
        task_w_file = self.get_object()

        self.success_url = self.success_url = reverse('education_app:update_lesson',
                                                      kwargs={'lesson_id': task_w_file.lesson.pk})

        if task_w_file.lesson.course_part.course.is_owner(request.user.teacher):
            return super().post(request, args, kwargs)
        raise Http404()

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(TaskWithFile, id=self.kwargs.get('pk'))
        return self.object


def answer_answer_to_task_with_file(request):
    if request.method == "POST":
        form = AnswerToTaskWFileForm(data=request.POST, files=request.FILES, student=request.user)
        is_form_valid = form.is_valid()
        redirect_to = redirect(reverse('education_app:lesson', args=(form.task_obj.lesson.pk,)))

        if is_form_valid:
            form.save()
            messages.info(request, 'Файл сохранен')
            return redirect_to
        messages.info(request, form.errors['file'])
        return redirect_to


def answer_to_quiz(request):
    if request.method == 'POST':
        quiz = get_object_or_404(QuizQuestion, id=request.POST.get('quiz', None))
        redirect_to = redirect(reverse('education_app:lesson', args=(quiz.lesson.pk,)))

        if quiz.lesson.student_has_access(request.user):
            answers_ids = list(map(int, request.POST.getlist('answers')))
            selected_answers = quiz.answer_set.filter(pk__in=answers_ids)
            right_answers = quiz.answer_set.filter(is_correct=True)

            if set(selected_answers) == set(right_answers):
                quiz.students_that_solved.add(request.user)
                messages.info(request, 'Верно')
                return redirect_to

            messages.info(request, 'Не верно')
            return redirect_to

    raise Http404()


def manual_reject_answer(request):
    if request.method == "POST":
        manual_test_info = request.POST['manual_test_id']

        if manual_test_info.startswith('task_w_file'):
            pk = int(manual_test_info[12:])
            manual_test = (
                AnswerToTaskWithFile.objects
                .select_related('task__lesson__course_part__course__author')
                .filter(pk=pk).first()
            )

        if manual_test_info.startswith('simple_task_'):
            pk = int(manual_test_info[12:])
            manual_test = (
                SimpleTaskToManualTest.objects
                .select_related('simple_task__lesson__course_part__course__author')
                .filter(pk=pk).first()
            )

        comment = request.POST.get('comment', '')
        manual_test.comment = comment
        manual_test.save()

        if manual_test.is_owner(request.user.teacher):
            manual_test.reject()
            return redirect(request.META['HTTP_REFERER'])
        raise Http404()
    raise Http404()


def manual_confirm_answer(request):
    if request.method == "POST":
        manual_test_info = request.POST['manual_test_id']

        if manual_test_info.startswith('task_w_file'):
            pk = int(manual_test_info[12:])
            manual_test = (
                AnswerToTaskWithFile.objects
                .select_related('task__lesson__course_part__course__author')
                .filter(pk=pk).first()
            )

        if manual_test_info.startswith('simple_task_'):
            pk = int(manual_test_info[12:])
            manual_test = (
                SimpleTaskToManualTest.objects
                .select_related('simple_task__lesson__course_part__course__author')
                .filter(pk=pk).first()
            )

        comment = request.POST.get('comment', '')
        manual_test.comment = comment
        manual_test.save()

        if manual_test.is_owner(request.user.teacher):
            manual_test.confirm()
            return redirect(request.META['HTTP_REFERER'])
        raise Http404()
    raise Http404()


def answer_to_simple_task(request):
    if request.method == 'POST':
        form = AnswerToSimpleTaskForm(data=request.POST, student=request.user)
        if form.is_valid():
            redirect_to = redirect(reverse('education_app:lesson', args=(form.object.lesson.pk,)))
            if not form.object.manual_test:
                if form.check_answer():

                    messages.info(request, 'Ответ верный')
                    return redirect_to

                messages.info(request, 'Ответ не верный')
                return redirect_to

            send_result = form.send_to_manual_test()
            if isinstance(send_result, (bool,)):
                messages.info(request, 'Ваш ответ отправлен на ручную проверку')
                return redirect_to

            messages.warning(request, send_result)
            return redirect_to

    raise Http404()
