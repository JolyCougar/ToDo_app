from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import AnonymousUser
from tasks.models import Task
from .permissions import IsEmailVerified
from my_auth.models import Profile
from .serializers import (
    TaskSerializer,
    CreateTaskSerializer,
    UserRegistrationSerializer,
    ProfileSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)
from rest_framework.exceptions import ValidationError


class TaskSerializerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_task_serializer(self):
        task = Task.objects.create(name='Test Task', description='Test Description', complete=False, user=self.user)
        serializer = TaskSerializer(task)
        self.assertEqual(serializer.data, {
            'id': task.id,
            'name': 'Test Task',
            'description': 'Test Description',
            'complete': False,
        })

    def test_create_task_serializer(self):
        data = {
            'name': 'New Task',
            'description': 'New Task Description',
            'complete': False,
        }
        serializer = CreateTaskSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        task = serializer.save(user=self.user)
        self.assertEqual(task.name, 'New Task')
        self.assertEqual(task.user, self.user)


class UserRegistrationSerializerTests(TestCase):

    def test_user_registration_serializer(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword',
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('newpassword'))

    def test_validate_email_unique(self):
        User.objects.create(username='existinguser', email='existing@example.com', password='password')
        data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'newpassword',
        }
        serializer = UserRegistrationSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn('Пользователь с таким e-mail уже существует.', str(context.exception))


class ProfileSerializerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.profile, created = Profile.objects.get_or_create(user=self.user, defaults={'bio': 'Test Bio'})

    def test_profile_serializer(self):
        data = {'bio': 'Updated Bio'}
        serializer = ProfileSerializer(instance=self.profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_profile = serializer.save()
        self.assertEqual(updated_profile.bio, 'Updated Bio')


class PasswordResetSerializerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')

    def test_get_user(self):
        data = {'email': 'test@example.com'}
        serializer = PasswordResetSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.get_user(), self.user)

    def test_get_user_invalid_email(self):
        data = {'email': 'invalid@example.com'}
        serializer = PasswordResetSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
            serializer.get_user()
        self.assertIn('Пользователь с таким email не найден.', str(context.exception))


class PasswordResetConfirmSerializerTests(TestCase):

    def test_validate_passwords_match(self):
        data = {
            'new_password': 'newpassword',
            'confirm_password': 'newpassword',
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_validate_passwords_do_not_match(self):
        data = {
            'new_password': 'newpassword',
            'confirm_password': 'differentpassword',
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn('Пароли не совпадают.', str(context.exception))


class IsEmailVerifiedTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.profile = self.user.profile

    def test_permission_denied_if_not_authenticated(self):
        request = self.factory.get('/api/v1/tasks/')
        request.user = AnonymousUser()
        permission = IsEmailVerified()
        self.assertFalse(permission.has_permission(request, None))

    def test_permission_denied_if_email_not_verified(self):
        self.profile.email_verified = False
        self.profile.save()
        request = self.factory.get('/api/v1/tasks/')
        request.user = self.user
        permission = IsEmailVerified()
        self.assertFalse(permission.has_permission(request, None))

    def test_permission_granted_if_email_verified(self):
        self.profile.email_verified = True
        self.profile.save()
        request = self.factory.get('/api/v1/tasks/')
        request.user = self.user
        permission = IsEmailVerified()
        self.assertTrue(permission.has_permission(request, None))

    def test_permission_denied_if_no_profile(self):
        self.profile.delete()
        request = self.factory.get('/api/v1/tasks/')
        request.user = self.user
        permission = IsEmailVerified()
        self.assertFalse(permission.has_permission(request, None))


class TaskListViewTests(APITestCase):

    def setUp(self):
        self.user_with_verified_email = User.objects.create_user(
            username='verifieduser', password='testpassword'
        )
        self.profile_verified = Profile.objects.get(user=self.user_with_verified_email)
        self.profile_verified.email_verified = True
        self.profile_verified.save()

        self.user_without_verified_email = User.objects.create_user(
            username='unverifieduser', password='testpassword'
        )
        self.profile_unverified = Profile.objects.get(user=self.user_without_verified_email)
        self.profile_unverified.email_verified = False
        self.profile_unverified.save()

        Task.objects.create(name='Task 1', description='Description 1', user=self.user_with_verified_email)
        Task.objects.create(name='Task 2', description='Description 2', user=self.user_with_verified_email)

        self.token_verified = Token.objects.create(user=self.user_with_verified_email)
        self.token_unverified = Token.objects.create(user=self.user_without_verified_email)

    def test_list_tasks_verified_user(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_verified.key)
        url = reverse('api:task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_tasks_unverified_user(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_unverified.key)
        url = reverse('api:task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': 'Пожалуйста, подтвердите адрес электронной почты.'})

    def test_list_tasks_unauthenticated_user(self):
        url = reverse('api:task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskCreateViewTests(APITestCase):

    def setUp(self):
        self.user_with_verified_email = User.objects.create_user(
            username='verifieduser', password='testpassword'
        )
        self.profile_verified = Profile.objects.get(user=self.user_with_verified_email)
        self.profile_verified.email_verified = True
        self.profile_verified.save()

        self.user_without_verified_email = User.objects.create_user(
            username='unverifieduser', password='testpassword'
        )
        self.profile_unverified = Profile.objects.get(user=self.user_without_verified_email)
        self.profile_unverified.email_verified = False
        self.profile_unverified.save()

        self.token_verified = Token.objects.create(user=self.user_with_verified_email)
        self.token_unverified = Token.objects.create(user=self.user_without_verified_email)

    def test_create_task_verified_user(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_verified.key)
        url = reverse('api:task-create')
        data = {'name': 'New Task', 'description': 'Task Description'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(Task.objects.get().name, 'New Task')

    def test_create_task_unverified_user(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_unverified.key)
        url = reverse('api:task-create')
        data = {'name': 'New Task', 'description': 'Task Description'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': 'Пожалуйста, подтвердите адрес электронной почты.'})

    def test_create_task_unauthenticated_user(self):
        url = reverse('api:task-create')
        data = {'name': 'New Task', 'description': 'Task Description'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskDetailUpdateViewTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@example.com')
        self.profile = Profile.objects.get(user=self.user)
        self.profile.email_verified = True
        self.profile.save()
        self.task = Task.objects.create(name='Test Task', user=self.user)
        self.token = Token.objects.create(user=self.user)

    def test_get_task_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(f'/api/v1/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Task')

    def test_get_task_detail_unverified_user(self):
        self.profile.email_verified = False
        self.profile.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Пожалуйста, подтвердите адрес электронной почты.')


class TaskDeleteViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@example.com')
        self.profile = Profile.objects.get(user=self.user)
        self.profile.email_verified = True
        self.profile.save()
        self.token = Token.objects.create(user=self.user)

        self.task = Task.objects.create(name='Test Task', user=self.user)

        self.url = reverse('api:task-delete', kwargs={'pk': self.task.pk})

    def test_delete_task_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_delete_task_permission_denied(self):
        self.profile.email_verified = False
        self.profile.save()

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': 'Пожалуйста, подтвердите адрес электронной почты.'})

    def test_delete_task_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        url_not_found = reverse('api:task-delete', kwargs={'pk': 999})
        response = self.client.delete(url_not_found)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
