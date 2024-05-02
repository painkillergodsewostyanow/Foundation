from django.db.models import Count, Q, Max, OuterRef, Subquery, IntegerField, F
from django.db.models.functions import Coalesce
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, reverse, redirect
from django.views.generic import UpdateView, DetailView, CreateView, DeleteView, ListView, View
from .forms import CourseForm, CoursePartForm, LessonForm, AnswerToSimpleTaskForm, SimpleTaskForm
from .models import (Course, CoursePart, Lesson, SimpleTask, StudentThatSolvedLessonM2M, StudentThatSolvedCoursePartM2M,
                     StudentThatSolvedSimpleTaskM2M)


def dashboard(request):
    if request.user.is_teacher():
        return redirect(reverse('education_app:teacher_dashboard'))
    return redirect(reverse('education_app:student_dashboard'))


class TeacherDashboard(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'education_app/teacher_dashboard.html')


class StudentDashboard(View):
    def get(self, request, *args, **kwargs):
        student = self.request.user
        solved_course_parts = StudentThatSolvedCoursePartM2M.objects.filter(student=student).select_related(
            'course_part')[:5]
        solved_lessons = StudentThatSolvedLessonM2M.objects.filter(student=student).select_related('lesson')[:5]
        solved_simpletask = StudentThatSolvedSimpleTaskM2M.objects.filter(student=student).select_related(
            'simple_task')[:5]

        activity_list = sorted(list(solved_course_parts) + list(solved_lessons) + list(solved_simpletask),
                               key=lambda x: x.time)

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

        return render(
            request, 'education_app/student_dashboard.html',
            {
                'courses': courses, 'activity_list': activity_list
            }
        )


def signup_for_course(request):
    if request.method == "POST":
        course_id = request.POST.get('course_id', None)
        course = get_object_or_404(Course, id=course_id)
        course.sing_up(request.user)
        return HttpResponse('Успешно')
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
            count_simple_task=Count('simpletask'),
        ).values('pk', 'video', 'students_that_solved', 'order', 'count_simple_task')

        count_simple_task = sum(lesson['count_simple_task'] for lesson in lessons)
        count_video = sum(1 for lesson in lessons if lesson['video'])
        # TODO(я не могу в аннотации подсчитать количество видео, ибо он считает что у каждого урока есть видео)
        student_on_course = self.request.user in course.students.all()

        added_context = {
            'count_simple_task': count_simple_task,
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
        return CoursePart.objects.select_related('course').prefetch_related('lesson_set').select_related('course__author')


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
        self.success_url = reverse('education_app:update_course_part', kwargs={'course_part_id': course_part.pk})
        if not course_part.course.is_owner(request.user.teacher):
            raise Http404
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        course_part = get_object_or_404(CoursePart, id=self.kwargs.get('course_part_id'))
        form.instance.course_part = course_part
        form.save()
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
            raise Http404()

        simple_tasks = lesson.simpletask_set.all()

        theory_task = list(filter(lambda x: x.place == 1, simple_tasks))
        practice_task = list(filter(lambda x: x.place == 2, simple_tasks))
        video_task = list(filter(lambda x: x.place == 3, simple_tasks))

        course_parts = lesson.course_part.course.coursepart_set.prefetch_related('lesson_set').all()

        if not simple_tasks:
            lesson.students_that_solved.add(request.user)

        return render(request, self.template_name,
                      context={
                          'theory_task': theory_task, 'practice_task': practice_task,
                          'video_task': video_task, 'object': lesson,
                          'lesson_count': lesson.lessons_count,
                          'course_parts': course_parts
                      })

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
        pk = self.kwargs.get('pk', None)
        lesson = get_object_or_404(self.get_queryset(), pk=pk)

        return lesson


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


def answer_to_simple_task(request):
    if request.method == 'POST':
        form = AnswerToSimpleTaskForm(data=request.POST, student=request.user)
        if form.is_valid():
            simple_task = get_object_or_404(SimpleTask, id=int(form.data['simple_task']))
            simple_task.students_that_solved.add(request.user)
            return HttpResponse('Правильно!')

    raise Http404()
