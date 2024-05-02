from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import F, Count, Q
from users_app.models import Teacher, User
from django_ckeditor_5.fields import CKEditor5Field
from django.urls import reverse


class Course(models.Model):
    author = models.ForeignKey(Teacher, on_delete=models.PROTECT, verbose_name='Автор')
    title = models.CharField(max_length=255, verbose_name='Название')
    image = models.ImageField(blank=True, null=True, upload_to='media/education_app/courses_img',
                              verbose_name='Изображение')
    is_private = models.BooleanField(default=False)
    description = CKEditor5Field('description', config_name='extends')

    students = models.ManyToManyField(
        blank=True, null=True,
        to=User, related_name='course_student_m2m',
        verbose_name='Зачисленные студенты'
    )

    students_that_solved = models.ManyToManyField(
        blank=True, null=True,
        to=User, through='StudentThatSolvedCourseM2M', related_name='students_that_solved_course_m2m',
        verbose_name='Студенты которые прошли курс'
    )
    is_published = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['title']

    def get_absolute_url(self):
        return reverse('education_app:course_preview', kwargs={'pk': self.pk})

    def __str__(self):
        return self.title

    def get_auto_order_for_course_part(self):
        course_parts = self.coursepart_set
        course_part_count = course_parts.count()
        if course_part_count > 0:
            return course_parts.last().order + 1
        return 1

    def is_owner(self, user):
        return self.author == user

    def sing_up(self, student):
        self.students.add(student)

    def student_has_access(self, student):
        if student.is_teacher():
            return self.author == student.teacher
        return student in self.students.all()


class StudentThatSolvedCourseM2M(models.Model):
    student = models.ForeignKey(User, on_delete=models.PROTECT)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Решенный студентом курс'
        verbose_name_plural = 'Решенные студентами курсы'


class StudentOnCourseM2M(models.Model):
    student = models.ForeignKey(User, on_delete=models.PROTECT)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Студент записанный на курс'
        verbose_name_plural = 'Студенты записанные на курсы'


class CoursePart(models.Model):
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField()

    students_that_solved = models.ManyToManyField(
        blank=True, null=True,
        to=User, through='StudentThatSolvedCoursePartM2M',
    )

    class Meta:
        ordering = ["order"]
        verbose_name = 'Раздел'
        verbose_name_plural = 'Разделы'

    def __str__(self):
        return self.title

    def get_auto_order_for_lesson(self):

        lessons = self.lesson_set
        lessons_count = lessons.count()
        if lessons_count > 0:
            return lessons.last().order + 1
        return 1

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Если создается раздел с порядком который уже занят,
        или порядок раздела меняется на уже занятый, то порядки перестраиваются
        """

        course_part_w_same_order = self.course.coursepart_set.filter(order=self.order).first()

        if course_part_w_same_order and course_part_w_same_order != self:
            self.course.coursepart_set.filter(order__gte=self.order).update(order=F('order') + 1)

        return super().save(force_insert=False, force_update=False, using=None, update_fields=None)

    def delete(self, using=None, keep_parents=False):
        """
        При удалении раздела нужно перестроить порядки
        """

        self.course.coursepart_set.filter(order__gt=self.order).update(
            order=F('order') - 1
        )
        return super().delete(using, keep_parents)

    def student_has_access(self, student):
        # Если у пользователя есть доступ к курсу
        if self.course.student_has_access(student):
            # Если это первый раздел курса, то он доступен
            if self.course.coursepart_set.first() == self:
                return True

            # Если решены все разделы до этого, то раздел доступен
            prev_course_parts = self.course.coursepart_set.filter(order__lt=self.order).prefetch_related('students_that_solved')
            for prev_course_part in prev_course_parts:
                if student not in prev_course_part.students_that_solved.all():
                    return False
            return True
        # TODO()


class StudentThatSolvedCoursePartM2M(models.Model):
    student = models.ForeignKey(User, on_delete=models.PROTECT)
    course_part = models.ForeignKey(CoursePart, on_delete=models.PROTECT)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Решенный студентом раздел'
        verbose_name_plural = 'Решенные студентами разделы'


class Lesson(models.Model):
    course_part = models.ForeignKey(CoursePart, on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    theory = CKEditor5Field('lesson_theory', config_name='extends', null=True, blank=True)
    practice = CKEditor5Field('lesson_practice', config_name='extends', null=True, blank=True)
    video = models.FileField(
        blank=True, null=True,
        upload_to='media/education_app/lesson-video/',
        validators=[FileExtensionValidator(allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv'])]
    )
    order = models.PositiveSmallIntegerField()
    students_that_solved = models.ManyToManyField(
        blank=True, null=True,
        to=User, through='StudentThatSolvedLessonM2M'
    )

    class Meta:
        ordering = ["order"]
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'

    def __str__(self):
        return self.title

    def get_next_lesson(self):
        return self.course_part.lesson_set.filter(order__gt=self.order).first()

    def get_absolute_url(self):
        return reverse('education_app:lesson', kwargs={'pk': self.pk})

    def get_percent_ready(self, student):
        """Возвращает процент на сколько выполнен урок"""
        stat = self.simpletask_set.aggregate(
            total=Count('pk', distinct=True),
            solved=Count('pk', filter=Q(students_that_solved=student))
        )
        if stat['solved'] == 0:
            return 0

        return (stat['solved']/stat['total']) * 100

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Если создается урок с порядком который уже занят,
        или порядок раздела меняется на уже занятый, то порядки перестраиваются
        """

        lesson_w_same_order = self.course_part.lesson_set.filter(order=self.order).first()

        if lesson_w_same_order and lesson_w_same_order != self:
            self.course_part.lesson_set.filter(order__gte=self.order).update(order=F('order') + 1)

        return super().save(force_insert=False, force_update=False, using=None, update_fields=None)

    def delete(self, using=None, keep_parents=False):
        """
        При удалении урока нужно перестроить порядки
        """
        self.course_part.lesson_set.filter(order__gt=self.order).update(
            order=F('order') - 1
        )
        return super().delete(using, keep_parents)

    def student_has_access(self, student):
        # Если есть доступ к разделу
        if self.course_part.student_has_access(student):
            # Если урок первый, он доступен
            if self.course_part.lesson_set.first() == self:
                return True

            # Если решены все уроки до
            prev_lessons = self.course_part.lesson_set.filter(order__lt=self.order)
            for prev_lesson in prev_lessons:
                if student not in prev_lesson.students_that_solved.all():
                    return False
            return True
        return False


class StudentThatSolvedLessonM2M(models.Model):
    student = models.ForeignKey(User, on_delete=models.PROTECT)
    lesson = models.ForeignKey(Lesson, on_delete=models.PROTECT)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Решенный студентом урок'
        verbose_name_plural = 'Решенные студентами уроки'


class SimpleTask(models.Model):
    class Meta:
        ordering = ["order"]
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

    place = models.SmallIntegerField(
        choices=(
            (1, "Раздел теории"),
            (2, "Раздел практики"),
            (3, "Раздел видео")
        )
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=500)
    hint = models.CharField(max_length=255)
    right_answer = models.CharField(max_length=255)
    students_that_solved = models.ManyToManyField(
        blank=True, null=True,
        to=User, through='StudentThatSolvedSimpleTaskM2M'
    )
    order = models.PositiveSmallIntegerField()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Если создается простая задача с порядком который уже занят,
        или порядок раздела меняется на уже занятый, то порядки перестраиваются
        """

        simple_task_w_same_order = self.lesson.simpletask_set.filter(order=self.order).first()

        if simple_task_w_same_order and simple_task_w_same_order != self:
            self.lesson.simpletask_set.filter(order__gte=self.order).update(order=F('order') + 1)

        return super().save(force_insert=False, force_update=False, using=None, update_fields=None)

    def delete(self, using=None, keep_parents=False):
        # При удалении урока нужно поправить порядок
        self.lesson.simpletask_set.filter(order__gt=self.order).update(
            order=F('order') - 1
        )
        return super().delete(using, keep_parents)


class StudentThatSolvedSimpleTaskM2M(models.Model):
    student = models.ForeignKey(User, on_delete=models.PROTECT)
    simple_task = models.ForeignKey(SimpleTask, on_delete=models.PROTECT)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Решенная студентом задача'
        verbose_name_plural = 'Решенные студентами задачи'
