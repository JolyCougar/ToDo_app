from django.test import TestCase
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
