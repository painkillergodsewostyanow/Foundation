from django.urls import path
from .views import *
from .video import get_stream_video
from .decorators import teacher_required
from django.contrib.auth.decorators import login_required

app_name = 'education_app'

urlpatterns = [

    # DASHBOARD
    path('dashboard', login_required(dashboard), name='dashboard'),
    path('teacher-dashboard', teacher_required(TeacherDashboard.as_view()), name='teacher_dashboard'),
    path('student-dashboard', StudentDashboard.as_view(), name='student_dashboard'),
    # DASHBOARD

    # COURSE
    path('add-course', teacher_required(CourseCreateView.as_view()), name='create_course'),

    path('update-course/<int:course_id>', teacher_required(CourseUpdateView.as_view()),
         name='update_course'),
    # COURSE

    # COURSE PART
    path('course/<int:course_id>/add-course-part', teacher_required(CoursePartCreateView.as_view()),
         name='create_course_part'),

    path('update-course-part/<int:course_part_id>', teacher_required(CoursePartUpdateView.as_view()),
         name='update_course_part'),

    path('delete-course-part/<int:pk>', teacher_required(CoursePartDeleteView.as_view()),
         name='delete_course_part'),
    # COURSE PART

    # LESSON
    path('lesson/<int:lesson_id>/stream-video', get_stream_video, name='video_stream'),
    path('course-part/<int:course_part_id>/add-lesson', teacher_required(LessonCreateView.as_view()),
         name='create_lesson'),

    path('update-lesson/<int:lesson_id>', teacher_required(LessonUpdateView.as_view()),
         name='update_lesson'),

    path('delete-lesson/<int:pk>', teacher_required(LessonDeleteView.as_view()),
         name='delete_lesson'),
    # LESSON

    # SIMPLE TASK
    path('lesson/<int:lesson_id>/add-task', teacher_required(SimpleTaskCreateView.as_view()),
         name='create_simple_task'),
    path('update-simple-task/<int:simple_task_id>', teacher_required(SimpleTaskUpdateView.as_view()),
         name='update_simple_task'),
    path('simple-task/answer', answer_to_simple_task, name='answer_to_simple_task'),
    path('delete-simple-task/<int:pk>', teacher_required(SimpleTaskDeleteView.as_view()), name='delete_simple_task'),
    # SIMPLE TASK

    # TASK WITH FILES
    path('lesson/<int:lesson_id>/add-task-with-file', TaskWithFileCreateView.as_view(), name='create_task_with_file'),
    path('task-with-file/<int:pk>/update', TaskWithFileUpdateView.as_view(), name='update_task_with_file'),
    path('task_with_file/answer', answer_to_task_with_file, name='answer_to_task_w_file'),
    # TASK WITH FILES

    # QUIZ TASK
    path('lesson/<int:lesson_id>/add-quiz', teacher_required(QuizCreateView.as_view()),
         name='create_quiz'),
    path('update-quiz/<int:quiz_id>', teacher_required(QuizUpdateView.as_view()),
         name='update_quiz'),

    path('quiz/answer', answer_to_quiz, name='answer_to_quiz'),
    # QUIZ TASK

    # ANSWER TO QUIZ
    path('quiz/<int:quiz_pk>/add-answer', teacher_required(AnswerToQuizCreateView.as_view()),
         name='create_answer_to_quiz'),

    path('update-quiz-answer/<int:quiz_answer_id>', teacher_required(AnswerToQuizUpdateView.as_view()),
         name='update_answer_to_quiz'),
    # ANSWER TO QUIZ

    # MANUAL TEST
    path('reject', RejectAnswerView.as_view(), name='reject'),
    path('confirm', ConfirmAnswerView.as_view(), name='confirm'),
    # MANUAL TEST

    # CODE TASK
    path('lesson/<int:lesson_id>/execute-code', CheckCodeTaskAnswerView.as_view(), name='check_code_task'),
    path('lesson/<int:lesson_id>/add-code-task', CodeTaskCreateView.as_view(), name='create_code_task'),
    path('code-task/<int:pk>/update', CodeTaskUpdateView.as_view(), name='update_code_task'),
    # CODE TASK

    path('catalog', CatalogListView.as_view(), name='catalog'),
    path('lesson/<int:pk>', login_required(LessonDetailView.as_view()), name='lesson'),
    path('course-preview/<int:pk>', login_required(CourseDetailView.as_view()), name='course_preview'),
    path('sing_up', login_required(signup_for_course), name='sing_up')

]
