from django.urls import path
from .views import *
from .decorators import teacher_required
from django.contrib.auth.decorators import login_required

app_name = 'education_app'

urlpatterns = [
    path('dashboard', login_required(dashboard), name='dashboard'),
    path('teacher-dashboard', teacher_required(TeacherDashboard.as_view()), name='teacher_dashboard'),
    path('student-dashboard', StudentDashboard.as_view(), name='student_dashboard'),

    path('add-course', teacher_required(CourseCreateView.as_view()), name='create_course'),

    path('update-course/<int:course_id>', teacher_required(CourseUpdateView.as_view()),
         name='update_course'),

    # TODO(DELETE COURSE)

    path('course/<int:course_id>/add-course-part', teacher_required(CoursePartCreateView.as_view()),
         name='create_course_part'),

    path('update-course-part/<int:course_part_id>', teacher_required(CoursePartUpdateView.as_view()),
         name='update_course_part'),

    path('delete-course-part/<int:pk>', teacher_required(CoursePartDeleteView.as_view()),
         name='delete_course_part'),

    path('course-part/<int:course_part_id>/add-lesson', teacher_required(LessonCreateView.as_view()),
         name='create_lesson'),

    path('update-lesson/<int:lesson_id>', teacher_required(LessonUpdateView.as_view()),
         name='update_lesson'),

    path('delete-lesson/<int:pk>', teacher_required(LessonDeleteView.as_view()),
         name='delete_lesson'),

    # SIMPLE TASK
    path('lesson/<int:lesson_id>/add-task', teacher_required(SimpleTaskCreateView.as_view()), name='create_simple_task'),
    path('update-simple-task/<int:simple_task_id>', teacher_required(SimpleTaskUpdateView.as_view()),
         name='update_simple_task'),
    path('simple-task/answer', answer_to_simple_task, name='answer_to_simple_task'),
    # SIMPLE TASK

    # MANUAL TEST
    path('reject', manual_reject_answer, name='reject'),
    path('confirm', manual_confirm_answer, name='confirm'),
    # MANUAL TEST

    path('catalog', CatalogListView.as_view(), name='catalog'),
    path('lesson/<int:pk>', login_required(LessonDetailView.as_view()), name='lesson'),
    path('course-preview/<int:pk>', login_required(CourseDetailView.as_view()), name='course_preview'),
    path('sing_up', login_required(signup_for_course), name='sing_up')
]
