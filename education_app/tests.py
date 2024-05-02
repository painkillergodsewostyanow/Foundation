from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from education_app.forms import CourseForm
from education_app.models import Course, CoursePart, Lesson
from users_app.forms import RegistrationForm
from users_app.models import User


class EducationAppTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        # reg student
        registration_form_data = RegistrationForm(data={
            'username': 'student',
            'password1': '123321password',
            'password2': '123321password',
            'email': 'student@gmail.com',
            'student_or_teacher': '0'
        })

        registration_form_data.save()

        # reg teacher
        registration_form_data = RegistrationForm(data={
            'username': 'teacher',
            'password1': '123321password',
            'password2': '123321password',
            'email': 'teacher@gmail.com',
            'student_or_teacher': '1'
        })

        registration_form_data.save()

        # reg other_student
        registration_form_data = RegistrationForm(data={
            'username': 'other_teacher',
            'password1': '123321password',
            'password2': '123321password',
            'email': 'other_teacher@gmail.com',
            'student_or_teacher': '1'
        })

        registration_form_data.save()

        cls.user_student = User.objects.get(pk=1)
        cls.user_teacher = User.objects.get(username='teacher')
        cls.other_teacher = User.objects.get(username='other_teacher')

        # В ручную верифицировали почту
        User.objects.all().update(is_email_verified=True)

        cls.course_for_test = Course.objects.create(
            title='Курс для тестов',
            description='Курс созданный для тестов',
            author=cls.user_teacher.teacher
        )

        cls.course_part_for_test = CoursePart.objects.create(
            course=cls.course_for_test,
            title='Раздел для тестов',
            order=1
        )

        cls.lesson_for_test = Lesson.objects.create(
            course_part=cls.course_part_for_test,
            title='Урок для тестов',
            order=1
        )

    def test_dashboard_student(self):
        # TODO()
        self.client.force_login(self.user_student)
        dashboard_url = reverse('education_app:dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302)

    def test_dashboard_teacher(self):
        # TODO()
        self.client.force_login(self.user_student)
        dashboard_url = reverse('education_app:dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302)

    def test_dashboard_anonym(self):
        dashboard_url = reverse('education_app:dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302)

    # Тесты курсов

    def test_teacher_try_add_course_GET(self):
        self.client.force_login(self.user_teacher)
        add_course_url = reverse('education_app:create_course')
        response = self.client.get(add_course_url)
        self.assertEqual(response.status_code, 200)

    def test_teacher_try_add_course_POST(self):
        self.client.force_login(self.user_teacher)
        add_course_url = reverse('education_app:create_course')

        # Автора специально не передаем, тк должен вставиться из request'а
        post_data = CourseForm(data={
            'title': 'Тест создания курса',
            'description': 'Курс был создан тестом',
        }).data

        response = self.client.post(add_course_url, data=post_data)

        # Обработчик отработал
        self.assertEqual(response.status_code, 302)
        course = Course.objects.filter(title='Тест создания курса').first()

        # Автор задался автоматически
        self.assertEqual(course.author, self.user_teacher.teacher)

    def test_student_try_add_course_GET(self):
        self.client.force_login(self.user_student)
        add_course_url = reverse('education_app:create_course')
        response = self.client.get(add_course_url)
        self.assertEqual(response.status_code, 404)

    def test_student_try_add_course_POST(self):
        self.client.force_login(self.user_student)
        add_course_url = reverse('education_app:create_course')

        # Автора специально не передаем, тк должен вставиться из request'а
        post_data = CourseForm(data={
            'title': 'Тест создания курса',
            'description': 'Курс был создан тестом',
        }).data

        response = self.client.post(add_course_url, data=post_data)
        # Обработчик отработал
        self.assertEqual(response.status_code, 404)

    def test_anonym_try_add_course_GET(self):
        add_course_url = reverse('education_app:create_course')
        response = self.client.get(add_course_url)
        self.assertEqual(response.status_code, 404)

    def test_anonym_try_add_course_POST(self):
        self.client.force_login(self.user_student)
        add_course_url = reverse('education_app:create_course')

        # Автора специально не передаем, тк должен вставиться из request'а
        post_data = CourseForm(data={
            'title': 'Тест создания курса',
            'description': 'Курс был создан тестом',
        }).data

        response = self.client.post(add_course_url, data=post_data)

        # Отработала обманка в виде 404
        self.assertEqual(response.status_code, 404)

    def test_update_course_by_author_GET(self):
        self.client.force_login(self.user_teacher)
        course = self.course_for_test
        update_course = reverse('education_app:update_course', kwargs={'course_id': course.pk})
        response = self.client.get(update_course)
        self.assertEqual(response.status_code, 200)

    def test_update_course_by_author_POST(self):
        self.client.force_login(self.user_teacher)
        course = self.course_for_test
        update_course = reverse('education_app:update_course', kwargs={'course_id': course.pk})

        data = {
            'title': 'new_title',
            'description': 'new_description',
        }

        response = self.client.post(update_course, data)
        course.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(course.title, 'new_title', msg='Данные не поменялись')
        self.assertEqual(course.description, 'new_description', msg='Данные не поменялись')

    def test_update_course_by_other_teacher_GET(self):
        self.client.force_login(self.other_teacher)
        course = self.course_for_test
        update_course = reverse('education_app:update_course', kwargs={'course_id': course.pk})
        response = self.client.get(update_course)
        self.assertEqual(response.status_code, 404)

    def test_update_course_by_other_teacher_POST(self):
        self.client.force_login(self.other_teacher)
        course = self.course_for_test
        update_course = reverse('education_app:update_course', kwargs={'course_id': course.pk})

        data = {
            'title': 'new_title',
            'description': 'new_description',
        }

        response = self.client.post(update_course, data)
        course.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertNotEquals(course.title, 'new_title', msg='Данные не поменялись')
        self.assertNotEquals(course.description, 'new_description', msg='Данные не поменялись')

    def test_update_course_by_student_GET(self):
        self.client.force_login(self.user_student)
        course = self.course_for_test
        update_course = reverse('education_app:update_course', kwargs={'course_id': course.pk})
        response = self.client.get(update_course)
        self.assertEqual(response.status_code, 404)

    def test_update_course_by_student_POST(self):
        self.client.force_login(self.user_student)
        course = self.course_for_test
        update_course = reverse('education_app:update_course', kwargs={'course_id': course.pk})

        data = {
            'title': 'new_title',
            'description': 'new_description',
        }

        response = self.client.post(update_course, data)
        course.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertNotEquals(course.title, 'new_title', msg='Данные не поменялись')
        self.assertNotEquals(course.description, 'new_description', msg='Данные не поменялись')

    def test_update_course_by_anonym_GET(self):
        course = self.course_for_test
        update_course = reverse('education_app:update_course', kwargs={'course_id': course.pk})
        response = self.client.get(update_course)
        self.assertEqual(response.status_code, 404)

    def test_update_course_by_anonym_POST(self):
        course = self.course_for_test
        update_course = reverse('education_app:update_course', kwargs={'course_id': course.pk})

        data = {
            'title': 'new_title',
            'description': 'new_description',
        }

        response = self.client.post(update_course, data)
        course.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertNotEquals(course.title, 'new_title', msg='Данные не поменялись')
        self.assertNotEquals(course.description, 'new_description', msg='Данные не поменялись')

    # Тесты разделов
    def test_course_author_try_add_course_part_GET(self):
        self.client.force_login(self.user_teacher)
        course = self.course_for_test
        update_course = reverse('education_app:create_course_part', kwargs={'course_id': course.pk})
        response = self.client.get(update_course)
        self.assertEqual(response.status_code, 200)

    def test_course_author_try_add_course_part_POST(self):
        self.client.force_login(self.user_teacher)
        course = self.course_for_test
        update_course = reverse('education_app:create_course_part', kwargs={'course_id': course.pk})

        data = {
            'title': 'title',
            'course': self.course_for_test,
            'order': 2
        }

        response = self.client.post(update_course, data)
        course.refresh_from_db()

        self.assertEqual(response.status_code, 302)

        created_course_part = course.coursepart_set.last()
        self.assertEqual(created_course_part.title, 'title', msg='Раздел не создался')

    def test_other_teacher_try_add_course_part_GET(self):
        self.client.force_login(self.other_teacher)
        course = self.course_for_test
        update_course = reverse('education_app:create_course_part', kwargs={'course_id': course.pk})
        response = self.client.get(update_course)
        self.assertEqual(response.status_code, 404)

    def test_other_teacher_try_add_course_part_POST(self):
        self.client.force_login(self.other_teacher)
        course = self.course_for_test
        update_course = reverse('education_app:create_course_part', kwargs={'course_id': course.pk})

        data = {
            'title': 'title',
            'course': self.course_for_test,
            'order': 2
        }

        response = self.client.post(update_course, data)
        course.refresh_from_db()

        self.assertEqual(response.status_code, 404)

    def test_student_try_add_course_part_GET(self):
        self.client.force_login(self.user_student)
        course = self.course_for_test
        update_course = reverse('education_app:create_course_part', kwargs={'course_id': course.pk})
        response = self.client.get(update_course)
        self.assertEqual(response.status_code, 404)

    def test_student_try_add_course_part_POST(self):
        self.client.force_login(self.user_student)
        course = self.course_for_test
        update_course = reverse('education_app:create_course_part', kwargs={'course_id': course.pk})

        data = {
            'title': 'title',
            'course': self.course_for_test,
            'order': 2
        }

        response = self.client.post(update_course, data)
        self.assertEqual(response.status_code, 404)

    def test_anonym_try_add_course_part_GET(self):
        course = self.course_for_test
        update_course = reverse('education_app:create_course_part', kwargs={'course_id': course.pk})
        response = self.client.get(update_course)
        self.assertEqual(response.status_code, 404)

    def test_anonym_try_add_course_part_POST(self):
        course = self.course_for_test
        update_course = reverse('education_app:create_course_part', kwargs={'course_id': course.pk})

        data = {
            'title': 'title',
            'course': self.course_for_test,
            'order': 2
        }

        response = self.client.post(update_course, data)
        self.assertEqual(response.status_code, 404)

    def test_course_author_try_update_course_part_GET(self):
        self.client.force_login(self.user_teacher)
        course_part = self.course_part_for_test
        update_course = reverse('education_app:update_course_part', kwargs={'course_part_id': course_part.pk})
        response = self.client.get(update_course)
        self.assertEqual(response.status_code, 200)

    def test_course_author_try_update_course_part_POST(self):
        self.client.force_login(self.user_teacher)
        course_part = self.course_part_for_test
        update_course = reverse('education_app:update_course_part', kwargs={'course_part_id': course_part.pk})

        data = {
            'title': 'new_title',
            'course': self.course_for_test,
            'order': 2
        }

        response = self.client.post(update_course, data)
        course_part.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(course_part.title, 'new_title')
        self.assertEqual(course_part.order, 2)

    def test_other_teacher_try_update_course_part_GET(self):
        self.client.force_login(self.other_teacher)
        course_part = self.course_part_for_test
        update_course = reverse('education_app:update_course_part', kwargs={'course_part_id': course_part.pk})
        response = self.client.get(update_course)
        self.assertEqual(response.status_code, 404)

    def test_other_teacher_try_update_course_part_POST(self):
        self.client.force_login(self.other_teacher)
        course_part = self.course_part_for_test
        update_course = reverse('education_app:update_course_part', kwargs={'course_part_id': course_part.pk})

        data = {
            'title': 'new_title',
            'course': self.course_for_test,
            'order': 2
        }

        response = self.client.post(update_course, data)
        self.assertEqual(response.status_code, 404)

    def test_student_try_update_course_part_GET(self):
        self.client.force_login(self.user_student)
        course_part = self.course_part_for_test
        update_course = reverse('education_app:update_course_part', kwargs={'course_part_id': course_part.pk})
        response = self.client.get(update_course)
        self.assertEqual(response.status_code, 404)

    def test_student_try_update_course_part_POST(self):
        self.client.force_login(self.user_student)
        course_part = self.course_part_for_test
        update_course = reverse('education_app:update_course_part', kwargs={'course_part_id': course_part.pk})

        data = {
            'title': 'new_title',
            'course': self.course_for_test,
            'order': 2
        }

        response = self.client.post(update_course, data)
        self.assertEqual(response.status_code, 404)

    def test_anonym_teacher_try_update_course_part_GET(self):
        course_part = self.course_part_for_test
        update_course = reverse('education_app:update_course_part', kwargs={'course_part_id': course_part.pk})
        response = self.client.get(update_course)
        self.assertEqual(response.status_code, 404)

    def test_anonym_teacher_try_update_course_part_POST(self):
        course_part = self.course_part_for_test
        update_course = reverse('education_app:update_course_part', kwargs={'course_part_id': course_part.pk})

        data = {
            'title': 'new_title',
            'course': self.course_for_test,
            'order': 2
        }

        response = self.client.post(update_course, data)
        self.assertEqual(response.status_code, 404)

    def test_course_author_try_delete_course_part_GET(self):
        self.client.force_login(self.user_teacher)
        course_part = self.course_part_for_test
        delete_course_url = reverse('education_app:delete_course_part', kwargs={'pk': course_part.pk})
        response = self.client.get(delete_course_url)
        self.assertEqual(response.status_code, 200)

    def test_course_author_try_delete_course_part_POST(self):
        self.client.force_login(self.user_teacher)
        course_part = self.course_part_for_test
        delete_course_url = reverse('education_app:delete_course_part', kwargs={'pk': course_part.pk})

        # Потому что есть добавленные уроки со связью PROTECTED
        with self.assertRaises(ProtectedError):
            response = self.client.post(delete_course_url)

        # TODO()
        # response = self.client.post(delete_course_url)
        # self.assertEqual(response.status_code, 404)
        # self.assertEqual(self.course_for_test.coursepart_set.count(), 0)

    def test_other_teacher_try_delete_course_part_GET(self):
        self.client.force_login(self.other_teacher)
        course_part = self.course_part_for_test
        delete_course_url = reverse('education_app:delete_course_part', kwargs={'pk': course_part.pk})
        response = self.client.get(delete_course_url)
        self.assertEqual(response.status_code, 404)

    def test_other_teacher_try_delete_course_part_POST(self):
        self.client.force_login(self.other_teacher)
        course_part = self.course_part_for_test
        delete_course_url = reverse('education_app:delete_course_part', kwargs={'pk': course_part.pk})
        response = self.client.post(delete_course_url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.course_for_test.coursepart_set.count(), 1)

    def test_student_try_delete_course_part_GET(self):
        self.client.force_login(self.user_student)
        course_part = self.course_part_for_test
        delete_course_url = reverse('education_app:delete_course_part', kwargs={'pk': course_part.pk})
        response = self.client.get(delete_course_url)
        self.assertEqual(response.status_code, 404)

    def test_student_try_delete_course_part_POST(self):
        self.client.force_login(self.user_student)
        course_part = self.course_part_for_test
        delete_course_url = reverse('education_app:delete_course_part', kwargs={'pk': course_part.pk})
        response = self.client.post(delete_course_url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.course_for_test.coursepart_set.count(), 1)

    def test_anonym_try_delete_course_part_GET(self):
        course_part = self.course_part_for_test
        delete_course_url = reverse('education_app:delete_course_part', kwargs={'pk': course_part.pk})
        response = self.client.get(delete_course_url)
        self.assertEqual(response.status_code, 404)

    def test_anonym_try_delete_course_part_POST(self):
        course_part = self.course_part_for_test
        delete_course_url = reverse('education_app:delete_course_part', kwargs={'pk': course_part.pk})
        response = self.client.post(delete_course_url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.course_for_test.coursepart_set.count(), 1)

    # Тесты уроков

    # TODO(test delete viewwithoutsub, singup)

    def test_course_author_try_add_lesson_GET(self):
        self.client.force_login(self.user_teacher)
        add_lesson_url = reverse('education_app:create_lesson', kwargs={'course_part_id': self.course_part_for_test.pk})
        response = self.client.get(add_lesson_url)
        self.assertEqual(response.status_code, 200)

    def test_course_author_try_add_lesson_POST(self):
        self.client.force_login(self.user_teacher)
        add_lesson_url = reverse('education_app:create_lesson', kwargs={'course_part_id': self.course_part_for_test.pk})
        data = {
            'title': 'title',
            'course_part': self.course_part_for_test,
            'order': 2
        }
        response = self.client.post(add_lesson_url, data)
        created_lesson = self.course_part_for_test.lesson_set.last()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(created_lesson.title, 'title')

    def test_other_teacher_try_add_lesson_GET(self):
        self.client.force_login(self.other_teacher)
        add_lesson_url = reverse('education_app:create_lesson', kwargs={'course_part_id': self.course_part_for_test.pk})
        response = self.client.get(add_lesson_url)
        self.assertEqual(response.status_code, 404)

    def test_other_teacher_try_add_lesson_POST(self):
        self.client.force_login(self.other_teacher)
        add_lesson_url = reverse('education_app:create_lesson', kwargs={'course_part_id': self.course_part_for_test.pk})
        data = {
            'title': 'title',
            'course_part': self.course_part_for_test,
            'order': 2
        }
        response = self.client.post(add_lesson_url, data)
        self.assertEqual(response.status_code, 404)

    def test_student_try_add_lesson_GET(self):
        self.client.force_login(self.user_student)
        add_lesson_url = reverse('education_app:create_lesson', kwargs={'course_part_id': self.course_part_for_test.pk})
        response = self.client.get(add_lesson_url)
        self.assertEqual(response.status_code, 404)

    def test_student_try_add_lesson_POST(self):
        self.client.force_login(self.user_student)
        add_lesson_url = reverse('education_app:create_lesson', kwargs={'course_part_id': self.course_part_for_test.pk})
        data = {
            'title': 'title',
            'course_part': self.course_part_for_test,
            'order': 2
        }
        response = self.client.post(add_lesson_url, data)
        self.assertEqual(response.status_code, 404)

    def test_anonym_try_add_lesson_GET(self):
        add_lesson_url = reverse('education_app:create_lesson', kwargs={'course_part_id': self.course_part_for_test.pk})
        response = self.client.get(add_lesson_url)
        self.assertEqual(response.status_code, 404)

    def test_anonym_try_add_lesson_POST(self):
        add_lesson_url = reverse('education_app:create_lesson', kwargs={'course_part_id': self.course_part_for_test.pk})
        data = {
            'title': 'title',
            'course_part': self.course_part_for_test,
            'order': 2
        }
        response = self.client.post(add_lesson_url, data)
        self.assertEqual(response.status_code, 404)

    def test_update_lesson_by_author_GET(self):
        self.client.force_login(self.user_teacher)
        lesson = self.lesson_for_test
        update_lesson_url = reverse('education_app:update_lesson', kwargs={'lesson_id': lesson.pk})
        response = self.client.get(update_lesson_url)
        self.assertEqual(response.status_code, 200)

    def test_update_lesson_by_author_POST(self):
        self.client.force_login(self.user_teacher)
        lesson = self.lesson_for_test
        update_lesson = reverse('education_app:update_lesson', kwargs={'lesson_id': lesson.pk})

        data = {
            'title': 'new_title',
            'order': 2
        }

        response = self.client.post(update_lesson, data)
        lesson.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(lesson.title, 'new_title')
        self.assertEqual(lesson.order, 2)

    def test_update_lesson_by_other_teacher_GET(self):
        self.client.force_login(self.other_teacher)
        lesson = self.lesson_for_test
        update_lesson_url = reverse('education_app:update_lesson', kwargs={'lesson_id': lesson.pk})
        response = self.client.get(update_lesson_url)
        self.assertEqual(response.status_code, 404)

    def test_update_lesson_by_other_teacher_POST(self):
        self.client.force_login(self.other_teacher)
        lesson = self.lesson_for_test
        update_lesson = reverse('education_app:update_lesson', kwargs={'lesson_id': lesson.pk})

        data = {
            'title': 'new_title',
            'order': 2
        }

        response = self.client.post(update_lesson, data)
        lesson.refresh_from_db()

        self.assertEqual(response.status_code, 404)

    def test_update_lesson_by_student_GET(self):
        self.client.force_login(self.user_student)
        lesson = self.lesson_for_test
        update_lesson_url = reverse('education_app:update_lesson', kwargs={'lesson_id': lesson.pk})
        response = self.client.get(update_lesson_url)
        self.assertEqual(response.status_code, 404)

    def test_update_lesson_by_student_POST(self):
        self.client.force_login(self.user_student)
        lesson = self.lesson_for_test
        update_lesson = reverse('education_app:update_lesson', kwargs={'lesson_id': lesson.pk})

        data = {
            'title': 'new_title',
            'order': 2
        }

        response = self.client.post(update_lesson, data)
        lesson.refresh_from_db()

        self.assertEqual(response.status_code, 404)

    def test_update_lesson_by_anonym_GET(self):
        lesson = self.lesson_for_test
        update_lesson_url = reverse('education_app:update_lesson', kwargs={'lesson_id': lesson.pk})
        response = self.client.get(update_lesson_url)
        self.assertEqual(response.status_code, 404)

    def test_update_lesson_by_anonym_POST(self):
        lesson = self.lesson_for_test
        update_lesson = reverse('education_app:update_lesson', kwargs={'lesson_id': lesson.pk})

        data = {
            'title': 'new_title',
            'order': 2
        }

        response = self.client.post(update_lesson, data)
        lesson.refresh_from_db()

        self.assertEqual(response.status_code, 404)
