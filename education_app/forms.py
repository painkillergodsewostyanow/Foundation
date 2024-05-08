from django.utils import timezone
from pathlib import Path
from django.shortcuts import get_object_or_404
import re
from .models import Course, CoursePart, Lesson, SimpleTask, SimpleTaskToManualTest, QuizQuestion, Answer, TaskWithFile, \
    AnswerToTaskWithFile, FileExtends
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
        'class': "form-control", 'placeholder': "Название урока"
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
    re_answer = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': "form-check-input", 'id': "re_answer"}))
    manual_test = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': "form-check-input", 'id': "manual_test"}))

    class Meta:
        model = SimpleTask
        fields = ('place', 'title', 'description', 'hint', 'right_answer', 'order', 're_answer', 'manual_test')


class QuizForm(forms.ModelForm):
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

    hint = forms.CharField(widget=forms.TextInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'placeholder': "Подсказка"
    }))

    question = forms.CharField(widget=forms.TextInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'placeholder': "Описание"
    }))

    class Meta:
        model = QuizQuestion
        fields = ('place', 'title', 'question', 'hint')


class TaskWithFileForm(forms.ModelForm):
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

    hint = forms.CharField(widget=forms.TextInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'placeholder': "Подсказка"
    }))
    description = forms.CharField(widget=forms.TextInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'placeholder': "Описание"
    }))

    class Meta:
        model = TaskWithFile
        fields = ('place', 'title', 'hint', 'description', 'allowed_extends')
        widgets = {
            'allowed_extends': forms.SelectMultiple(
                attrs={'class': "form-select", 'aria-label': "multiple select example", 'style': 'font-size:32px;'}
            ),
        }


class AnswerForm(forms.ModelForm):
    text = forms.CharField(widget=forms.TextInput(attrs={
        'style': "font-size:32px;", 'class': "form-control", 'placeholder': "Ответ"
    }))

    is_correct = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': "form-check-input"}))

    class Meta:
        model = Answer
        fields = ('text', 'is_correct')


class AnswerToSimpleTaskForm(forms.Form):
    def __init__(self, student, *args, **kwargs):
        self.student = student
        self.object = None
        super().__init__(*args, **kwargs)

    answer = forms.CharField(max_length=255)
    simple_task = forms.HiddenInput()

    def get_object(self):
        if not self.object:
            self.object = get_object_or_404(SimpleTask, id=int(self.data['simple_task']))
        return self.object

    def is_valid(self):
        simple_task = self.get_object()
        if not simple_task.lesson.student_has_access(self.student):
            return False
        return super().is_valid()

    def check_answer(self):
        simple_task = self.get_object()

        if simple_task.re_answer:
            pattern = re.compile(simple_task.right_answer, re.IGNORECASE)
            if pattern.fullmatch(self.cleaned_data['answer']):
                self.__mark_solved()
                return True

        if simple_task.right_answer == self.cleaned_data['answer']:
            self.__mark_solved()
            return True

        return False

    def __mark_solved(self):
        self.object.students_that_solved.add(self.student)

    def send_to_manual_test(self) -> bool or str:
        """
        Возвращает True если все верно, и задача отправлена на проверку
        Иначе возвращает строку с ошибкой
        """

        if self.student in self.object.students_that_solved.all():
            return "Вы уже решили задачу, не балуйтесь !"

        count_today_tries = SimpleTaskToManualTest.objects.filter(
                student=self.student,
                simple_task=self.object,
                time__date=timezone.now()
        ).count()

        if count_today_tries > 4:
            return "Вы превысили число попыток на сегодня"

        SimpleTaskToManualTest.objects.create(
            student=self.student,
            simple_task=self.object,
            answer=self.cleaned_data['answer']
        )
        return True


class AnswerToTaskWFileForm(forms.ModelForm):
    def __init__(self, student, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_obj = None
        self.student = student

    task = forms.IntegerField(widget=forms.HiddenInput())
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control mb-4', 'style': 'font-size:24px;'}))

    class Meta:
        model = AnswerToTaskWithFile
        fields = ('task', 'file')

    def clean(self):
        self.task_obj = get_object_or_404(TaskWithFile, id=int(self.data['task']))

        if not self.task_obj.lesson.student_has_access(self.student):
            self.add_error('file', 'Вам не доступен данный урок')

        answers_before = AnswerToTaskWithFile.objects.filter(task=self.task_obj, student=self.student, time__date=timezone.now())

        if answers_before.count() > 5:
            self.add_error('file', 'Вы превысили лимит ответов на сегодня')

        allowed_extends = list((ex.extend for ex in self.task_obj.allowed_extends.all()))

        if allowed_extends:
            file = self.files['file']
            filename = file.name

            if Path(filename).suffix not in allowed_extends:
                self.add_error('file', f'Не допустимое расширение файла, допустимые расширения: {allowed_extends}')

        return {'task': self.task_obj, 'file': self.files['file']}

    def save(self, commit=True):
        self.instance.student = self.student
        # return super().save()
