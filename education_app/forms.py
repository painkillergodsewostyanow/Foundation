from django.shortcuts import get_object_or_404

from .models import Course, CoursePart, Lesson, SimpleTask
from django import forms


class CourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['image'].required = False

    image = forms.ImageField(widget=forms.FileInput(attrs={
        'class': "input-file", 'id': "inputPhoto", 'placeholder': "Фото курса", 'onchange': "previewImage()"
    }))

    title = forms.CharField(widget=forms.TextInput(attrs={
        'style': "font-size:32px; text-align: center; font-weight: bold;",
        'class': "form-control", 'id': "inputName", 'placeholder': "Введите название курса"
    }))

    class Meta:
        model = Course
        fields = ('image', 'title', 'description')


class CoursePartForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={
        'style': "font-size:32px; text-align: center; font-weight: bold;",
        'class': "form-control", 'placeholder': "Название раздела"
    }))

    order = forms.IntegerField(widget=forms.NumberInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'placeholder': "Порядок"
    }))

    class Meta:
        model = CoursePart
        fields = ('title', 'order')


class LessonForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={
        'style': "font-size:32px; text-align: center; font-weight: bold;",
        'class': "form-control", 'placeholder': "Название раздела"
    }))

    video = forms.FileField(required=False, widget=forms.FileInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'id': "inputPhoto", 'placeholder': "Видео"
    }))

    order = forms.IntegerField(widget=forms.NumberInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'placeholder': "Порядок"
    }))

    class Meta:
        model = Lesson
        fields = ('title', 'theory', 'practice', 'video', 'order')


class SimpleTaskForm(forms.ModelForm):
    place = forms.ChoiceField(
        widget=forms.Select(
            attrs={'style': "font-size:32px;", 'class': "form-select",
                   'aria-label': "Выберите раздел где будет размещена задача"
                   }
        ),
        choices=(
          (1, "Раздел теории"),
          (2, "Раздел практики"),
          (3, "Раздел видео")
        )
    )
    title = forms.CharField(widget=forms.TextInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'placeholder': "Название"
    }))

    description = forms.CharField(widget=forms.TextInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'placeholder': "Описание"
    }))

    hint = forms.CharField(widget=forms.TextInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'placeholder': "Подсказка"
    }))

    right_answer = forms.CharField(widget=forms.TextInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'placeholder': "Правильный ответ"
    }))

    order = forms.IntegerField(widget=forms.NumberInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'placeholder': "Порядок"
    }))

    class Meta:
        model = SimpleTask
        fields = ('place', 'title', 'description', 'hint', 'right_answer', 'order')


class AnswerToSimpleTaskForm(forms.Form):
    def __init__(self, student, *args, **kwargs):
        self.student = student
        super().__init__(*args, **kwargs)

    answer = forms.CharField(max_length=255)
    simple_task = forms.HiddenInput()

    def get_object(self):
        return get_object_or_404(SimpleTask, id=int(self.data['simple_task']))

    def is_valid(self):
        simple_task = self.get_object()
        if not simple_task.lesson.student_has_access(self.student):
            return False
        return super().is_valid()
