from django.contrib import admin

from .models import Course, CoursePart, Lesson, StudentThatSolvedCourseM2M, StudentThatSolvedCoursePartM2M, \
    StudentThatSolvedLessonM2M, StudentOnCourseM2M, SimpleTask, StudentThatSolvedSimpleTaskM2M, SimpleTaskToManualTest


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'enrolled_students', 'number_students_completed')

    def enrolled_students(self, obj):
        return obj.students.count()

    def number_students_completed(self, obj):
        return obj.students_that_solved.count()

    enrolled_students.short_description = 'Записано студентов'
    number_students_completed.short_description = 'Студентов окончивших курс'


@admin.register(CoursePart)
class CoursePartAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_part', 'order')


@admin.register(StudentThatSolvedCourseM2M)
class StudentThatSolvedCourseAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'time')


@admin.register(StudentThatSolvedCoursePartM2M)
class StudentThatSolvedCoursePartAdmin(admin.ModelAdmin):
    list_display = ('student', 'course_part', 'time')


@admin.register(StudentThatSolvedLessonM2M)
class StudentThatSolvedCoursePartAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'time')


@admin.register(SimpleTaskToManualTest)
class SimpleTaskToManualTestAdmin(admin.ModelAdmin):
    list_display = ('student', 'simple_task', 'time')


@admin.register(Course.students.through)
class StudentOnCourseM2MAdmin(admin.ModelAdmin):
    list_display = ('user', 'course')


@admin.register(SimpleTask)
class SimpleTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson')


@admin.register(StudentThatSolvedSimpleTaskM2M)
class StudentThatSolvedSimpleTaskM2MAdmin(admin.ModelAdmin):
    list_display = ('student', 'simple_task', 'time')
