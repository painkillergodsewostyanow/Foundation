from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'date_joined', 'is_teacher')

    def is_teacher(self, obj):
        return mark_safe('<img src="/static/admin/img/icon-yes.svg" alt="True">') if obj.is_teacher() else \
            mark_safe('<img src="/static/admin/img/icon-no.svg" alt="True">')

    is_teacher.allow_tags = True
    is_teacher.short_description = 'Преподаватель'


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user',)




