from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from users_app.models import User
from .models import SimpleTask, Lesson, CoursePart


@receiver(m2m_changed, sender=SimpleTask.students_that_solved.through)
def simple_task_solved(*args, **kwargs):
    if kwargs['action'] == 'post_add':
        simple_task = kwargs['instance']

        # Проверка на случай если запись о прохождении уже создана
        try:
            student = User.objects.get(pk=list(kwargs['pk_set'])[0])
        except IndexError:
            return

        # Если пользователь уже решил, урок и задача была добавлена после этого,
        # просто засчитываем ее решение, не проверяя дальше
        if student in kwargs['instance'].lesson.students_that_solved.all():
            return

        lesson_simple_task = simple_task.lesson.simpletask_set
        # Если количество решенных пользователем задач равно количеству задач урока - урок пройден
        if lesson_simple_task.filter(
                students_that_solved=student).count() == lesson_simple_task.count():
            simple_task.lesson.students_that_solved.add(student)


@receiver(m2m_changed, sender=Lesson.students_that_solved.through)
def lesson_solved(*args, **kwargs):
    if kwargs['action'] == 'post_add':
        lesson = kwargs['instance']

        # Проверка на случай если запись о прохождении уже создана
        try:
            student = User.objects.get(pk=list(kwargs['pk_set'])[0])
        except IndexError:
            return

        # Если пользователь уже решил урок, и задача была добавлена после этого,
        # просто засчитываем ее решение, не проверяя дальше
        if student in kwargs['instance'].course_part.students_that_solved.all():
            return

        course_part_lesson_set = lesson.course_part.lesson_set

        # Если количество решенных пользователем задач равно количеству задач урока - урок пройден
        if course_part_lesson_set.filter(
                students_that_solved=student).count() == course_part_lesson_set.count():
            lesson.course_part.students_that_solved.add(student)


@receiver(m2m_changed, sender=CoursePart.students_that_solved.through)
def course_part_solved(*args, **kwargs):
    if kwargs['action'] == 'post_add':
        course_part = kwargs['instance']

        # Проверка на случай если запись о прохождении уже создана
        try:
            student = User.objects.get(pk=list(kwargs['pk_set'])[0])
        except IndexError:
            return

        # Если пользователь уже решил курс, и раздел был добавлен после этого,
        # просто засчитываем его решение, не проверяя дальше
        if student in kwargs['instance'].course.students_that_solved.all():
            return

        course_course_part_set = course_part.course.coursepart_set

        # Если количество решенных пользователем задач равно количеству задач урока - урок пройден
        if course_course_part_set.filter(
                students_that_solved=student).count() == course_course_part_set.count():
            course_part.course.students_that_solved.add(student)
