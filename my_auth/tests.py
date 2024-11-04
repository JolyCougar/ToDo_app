import json
import string
import uuid
from decouple import config
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock, call
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Profile, EmailVerification
from .services import EmailService, PasswordGenerator, TaskScheduler
from .tasks import send_verification_email_task, send_new_password_email_task, delete_completed_tasks

User = get_user_model()


class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_profile_creation(self):
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.user.username, 'testuser')
        self.assertEqual(profile.bio, '')
        self.assertFalse(profile.agreement_accepted)
        self.assertFalse(profile.email_verified)
        self.assertFalse(profile.cookies_accepted)
        self.assertEqual(profile.delete_frequency, 'never')

    def test_profile_str(self):
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(str(profile), 'testuser')

    def test_delete_frequency_choices(self):
        profile = Profile.objects.get(user=self.user)
        valid_choices = dict(Profile._meta.get_field('delete_frequency').choices)
        self.assertIn(profile.delete_frequency, valid_choices)

    def test_profile_update(self):
        profile = Profile.objects.get(user=self.user)
        profile.bio = 'Updated bio.'
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.bio, 'Updated bio.')

    def test_profile_avatar_upload_path(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        profile = Profile.objects.get(user=self.user)
        avatar_file = SimpleUploadedFile("test_avatar.jpg", b"file_content", content_type="image/jpeg")
        profile.avatar = avatar_file
        profile.save()
        expected_path_prefix = f"profile_{profile.pk}/test_avatar"
        self.assertTrue(profile.avatar.name.startswith(expected_path_prefix))

    def test_profile_agreement_default(self):
        new_user = User.objects.create_user(username='newuser', password='newpassword')
        new_profile = Profile.objects.get(user=new_user)
        self.assertFalse(new_profile.agreement_accepted)

    def test_profile_email_verified_default(self):
        new_user = User.objects.create_user(username='anotheruser', password='anotherpassword')
        new_profile = Profile.objects.get(user=new_user)
        self.assertFalse(new_profile.email_verified)

    def test_profile_cookies_accepted_default(self):
        new_user = User.objects.create_user(username='thirduser', password='thirdpassword')
        new_profile = Profile.objects.get(user=new_user)
        self.assertFalse(new_profile.cookies_accepted)

    def test_profile_delete_frequency_default(self):
        new_user = User.objects.create_user(username='fourthuser', password='fourthpassword')
        new_profile = Profile.objects.get(user=new_user)
        self.assertEqual(new_profile.delete_frequency, 'never')


class CustomLoginViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_login_redirect_authenticated_user(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('my_auth:login'))
        self.assertRedirects(response, reverse('task:task_view'))

    def test_login_form_invalid(self):
        response = self.client.post(reverse('my_auth:login'), {'username': 'wronguser', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)

        context = response.context
        login_error = context.get('login_error', None)

        self.assertIsNotNone(login_error, "Ожидалось сообщение об ошибке, но его нет.")
        self.assertEqual(login_error, "Неправильное имя пользователя или пароль.")


class RegisterViewTests(TestCase):

    @patch('my_auth.services.EmailService.send_verification_email')
    def test_register_user(self, mock_send_verification_email):
        response = self.client.post(reverse('my_auth:register'), {
            'username': 'newuser',
            'password': 'newpassword',
            'confirm_password': 'newpassword',
            'email': 'test@test.com',
            'agreement_accepted': True,
        })

        self.assertRedirects(response, reverse('my_auth:login'))

        self.assertTrue(User.objects.filter(username='newuser').exists())

        new_user = User.objects.get(username='newuser')
        mock_send_verification_email.assert_called_once_with(response.wsgi_request, new_user)

    @patch('my_auth.services.EmailService.send_verification_email')
    def test_register_invalid_data(self, mock_send_verification_email):
        response = self.client.post(reverse('my_auth:register'), {
            'username': '',
            'password': 'newpassword',
            'confirm_password': 'newpassword',
            'email': 'test@test.com',
            'agreement_accepted': True,
        })

        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('username', form.errors)
        self.assertEqual(form.errors['username'], ['Обязательное поле.'])

        mock_send_verification_email.assert_not_called()


class ProfileViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.profile, created = Profile.objects.get_or_create(user=self.user)

    def test_profile_view(self):
        response = self.client.get(reverse('my_auth:profile', kwargs={'pk': self.user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')

    def test_update_profile(self):
        response = self.client.post(reverse('my_auth:profile', kwargs={'pk': self.user.pk}), {
            'bio': 'my test bio',
        })
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'my test bio')


class ChangePasswordViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

    def test_change_password_success(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('my_auth:change_password'),
                                    data=json.dumps({
                                        'old_password': 'testpass',
                                        'new_password': 'newtestpass',
                                    }),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_change_password_invalid(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('my_auth:change_password'),
                                    data=json.dumps({
                                        'old_password': 'wrongpass',
                                        'new_password': 'newtestpass',
                                    }),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], False)
        self.assertIn('old_password', response.json()['errors'])


class ResetAvatarViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.profile, created = Profile.objects.get_or_create(user=self.user)
        self.profile.avatar = 'old_avatar.png'

    def test_reset_avatar(self):
        response = self.client.post(reverse('my_auth:reset_avatar'))
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.avatar, '')


class VerifyEmailViewTests(TestCase):

    def setUp(self):
        self.user, created = User.objects.get_or_create(username='testuser', email='test@example.com')
        self.profile, created = Profile.objects.get_or_create(user=self.user)
        self.token = uuid.uuid4()
        EmailVerification.objects.create(profile=self.profile, token=self.token)

    @patch('my_auth.services.EmailService.send_verification_email')
    def test_verify_email_success(self, mock_send_verification_email):
        response = self.client.get(reverse('my_auth:verify_email', kwargs={'token': str(self.token)}))

        self.profile.refresh_from_db()
        self.assertTrue(self.profile.email_verified)

        mock_send_verification_email.assert_not_called()

    @patch('my_auth.services.EmailService.send_verification_email')
    def test_verify_email_invalid_token(self, mock_send_verification_email):
        response = self.client.get(reverse('my_auth:verify_email', kwargs={'token': str(uuid.uuid4())}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'verification_failed.html')
        self.assertContains(response, "Не удалось подтвердить ваш адрес электронной почты")

        mock_send_verification_email.assert_not_called()


class ResendVerificationTokenViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            email='test@test.com',
            is_active=True
        )
        self.profile, created = Profile.objects.get_or_create(user=self.user)
        self.client.login(username='testuser', password='testpassword')

    @patch('my_auth.services.EmailService.send_verification_email')
    def test_resend_verification_token(self, mock_send_verification_email):
        self.profile.email_verified = False
        self.profile.save()

        response = self.client.post(reverse('my_auth:resend_verification_token'))
        mock_send_verification_email.assert_called_once_with(
            response.wsgi_request,
            self.user
        )
        self.assertRedirects(response, reverse('task:task_view'))
        self.assertFalse(self.profile.email_verified)


class ChangeEmailViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

    @patch('my_auth.services.EmailService.send_verification_email')  # Замокируйте метод отправки email
    def test_change_email_success(self, mock_send_verification_email):
        # Отправляем POST-запрос для изменения email
        response = self.client.post(reverse('my_auth:change_email'), {'new_email': 'newemail@example.com'})

        # Проверяем, что произошел редирект
        self.assertRedirects(response, reverse('task:task_view'))

        # Проверяем, что email пользователя обновился
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')

        # Проверяем, что метод отправки email был вызван с правильным аргументом
        mock_send_verification_email.assert_called_once_with(
            response.wsgi_request,
            self.user
        )


class AcceptCookiesViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.profile, created = Profile.objects.get_or_create(user=self.user)
        self.profile.cookies_accepted = False

    def test_accept_cookies(self):
        response = self.client.post(reverse('my_auth:accept_cookies'))
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.cookies_accepted)


class CheckUsernameViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_check_username_exists(self):
        response = self.client.get(reverse('my_auth:check_username'), {'username': 'testuser'})
        self.assertJSONEqual(response.content, {'exists': True})

    def test_check_username_does_not_exist(self):
        response = self.client.get(reverse('my_auth:check_username'), {'username': 'nonexistentuser'})
        self.assertJSONEqual(response.content, {'exists': False})


class CheckEmailViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')

    def test_check_email_exists(self):
        response = self.client.get(reverse('my_auth:check_email'), {'email': 'test@example.com'})
        self.assertJSONEqual(response.content, {'exists': True})

    def test_check_email_does_not_exist(self):
        response = self.client.get(reverse('my_auth:check_email'), {'email': 'nonexistent@example.com'})
        self.assertJSONEqual(response.content, {'exists': False})


class PasswordResetViewTests(TestCase):

    def setUp(self):
        self.url = reverse('my_auth:password_reset')
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com')

    def test_authenticated_user_redirect(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('task:task_view'))

    def test_get_password_reset_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'password_reset.html')
        self.assertContains(response, 'form')

    @patch('my_auth.views.EmailService.send_new_password_email')
    @patch('my_auth.views.PasswordGenerator.generate_random_password', return_value='new_random_password')
    def test_post_valid_username(self, mock_generate_password, mock_send_email):
        response = self.client.post(self.url, {'username': 'testuser'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new_random_password'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('my_auth:login'))

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Новый пароль был установлен и отправлен вам на почту.')
        mock_send_email.assert_called_once_with(self.user, 'new_random_password')

    def test_post_invalid_username(self):
        response = self.client.post(self.url, {'username': 'invalid_username'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('username', form.errors)
        self.assertEqual(form.errors['username'], ['Пользователь с таким именем не найден.'])


class UpdateProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.profile, created = Profile.objects.get_or_create(user=self.user)
        self.profile.delete_frequency = 'never'
        self.profile.save()
        self.url = reverse('my_auth:update_profile')

    def test_update_profile_success(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'delete_frequency': 'week'}),
            content_type='application/json'
        )
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.delete_frequency, 'week')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'success',
                                                'message': 'Частота удаления задач успешно обновлена!'})

    def test_update_profile_invalid_data(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'delete_frequency': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'status': 'error',
                                                'message': 'Частота удаления задач не указана!'})


class EmailTasksTests(TestCase):

    @patch('my_auth.tasks.send_mail')
    @patch('my_auth.tasks.render_to_string')
    @patch('my_auth.tasks.strip_tags')
    def test_send_verification_email_task(self, mock_strip_tags, mock_render_to_string, mock_send_mail):
        mock_render_to_string.return_value = '<html>Verification Link</html>'
        mock_strip_tags.return_value = 'Verification Link'

        verification_link = 'http://example.com/verify?token=123'
        user_email = 'test@example.com'

        send_verification_email_task(verification_link, user_email)

        mock_render_to_string.assert_called_once_with('messages_to_verification.html', {
            'verification_link': verification_link,
        })
        mock_send_mail.assert_called_once_with(
            'toDo app: Добро пожаловать!',
            'Verification Link',
            config('EMAIL_HOST_USER'),  # Замените на ваш EMAIL_HOST_USER
            [user_email],
            fail_silently=False,
            html_message='<html>Verification Link</html>',
        )

    @patch('my_auth.tasks.send_mail')
    @patch('my_auth.tasks.render_to_string')
    @patch('my_auth.tasks.strip_tags')
    def test_send_new_password_email_task(self, mock_strip_tags, mock_render_to_string, mock_send_mail):
        mock_render_to_string.return_value = '<html>New Password</html>'
        mock_strip_tags.return_value = 'New Password'

        user_email = 'test@example.com'
        new_password = 'new_password123'

        send_new_password_email_task(user_email, new_password)

        mock_render_to_string.assert_called_once_with('messages_to_new_password.html', {
            'new_password': new_password,
        })
        mock_send_mail.assert_called_once_with(
            'toDo app: Ваш новый пароль',
            'New Password',
            config('EMAIL_HOST_USER'),  # Замените на ваш EMAIL_HOST_USER
            [user_email],
            fail_silently=False,
            html_message='<html>New Password</html>',
        )


class DeleteCompletedTasksTests(TestCase):

    @patch('tasks.models.Task.objects.filter')
    def test_delete_completed_tasks(self, mock_filter):
        user_id = 1
        mock_filter.return_value.delete.return_value = None  # Эмулируем успешное удаление

        delete_completed_tasks(user_id)

        mock_filter.assert_called_once_with(user_id=user_id, complete=True)
        mock_filter.return_value.delete.assert_called_once()


class EmailServiceTests(TestCase):

    @patch('my_auth.services.send_verification_email_task.delay')
    @patch('my_auth.services.EmailVerification.objects.get_or_create')
    def test_send_verification_email(self, mock_get_or_create, mock_send_verification_email_task):
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        profile, created = Profile.objects.get_or_create(user=user)

        mock_get_or_create.return_value = (EmailVerification(profile=profile), True)
        request = MagicMock()
        request.build_absolute_uri.return_value = 'http://example.com/verify?token=123'

        EmailService.send_verification_email(request, user)

        mock_get_or_create.assert_called_once_with(profile=profile)
        mock_send_verification_email_task.assert_called_once_with('http://example.com/verify?token=123', user.email)

    @patch('my_auth.services.send_new_password_email_task.delay')
    def test_send_new_password_email(self, mock_send_new_password_email_task):
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        new_password = 'new_password123'

        EmailService.send_new_password_email(user, new_password)

        mock_send_new_password_email_task.assert_called_once_with(user.email, new_password)


class PasswordGeneratorTests(TestCase):

    def test_generate_random_password_length(self):
        password = PasswordGenerator.generate_random_password(length=12)
        self.assertEqual(len(password), 12)

    def test_generate_random_password_characters(self):
        password = PasswordGenerator.generate_random_password(length=12)
        self.assertTrue(any(c.isdigit() for c in password))
        self.assertTrue(any(c.isalpha() for c in password))
        self.assertTrue(any(c in string.punctuation for c in password))


class TaskSchedulerTests(TestCase):

    @patch('my_auth.services.PeriodicTask.objects.create')
    @patch('my_auth.services.PeriodicTask.objects.filter')
    @patch('my_auth.services.IntervalSchedule.objects.get_or_create')
    def test_schedule_deletion_tasks(self, mock_get_or_create, mock_filter, mock_create):
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        profile, created = Profile.objects.get_or_create(user=user)
        profile.delete_frequency = 'hour'
        profile.save()
        scheduler = TaskScheduler(profile)

        mock_get_or_create.return_value = (MagicMock(), True)

        scheduler.schedule_deletion_tasks()

        mock_filter.assert_called_once_with(name=scheduler.task_name)
        mock_create.assert_called_once()
        self.assertEqual(mock_create.call_args[1]['args'], json.dumps([profile.user.id]))

    @patch('my_auth.services.IntervalSchedule.objects.get_or_create')
    def test_get_schedule(self, mock_get_or_create):
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        profile, created = Profile.objects.get_or_create(user=user)
        profile.delete_frequency = 'hours'
        profile.save()
        scheduler = TaskScheduler(profile)

        scheduler.get_schedule()

        expected_calls = [
            call(every=1, period='minutes'),
            call(every=1, period='hours'),
            call(every=1, period='days'),
            call(every=7, period='days'),
        ]
        mock_get_or_create.assert_has_calls(expected_calls, any_order=True)
