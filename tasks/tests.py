from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Task
from my_auth.models import Profile
import json


class TaskModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', email='testuser@example.com')
        self.profile, created = Profile.objects.get_or_create(user=self.user)
        self.profile.email_verified = True
        self.profile.save()

    def test_create_task(self):
        task = Task.objects.create(user=self.user, name='Test Task', description='Test Description')
        self.assertEqual(task.name, 'Test Task')
        self.assertEqual(task.description, 'Test Description')
        self.assertFalse(task.complete)
        self.assertIsNotNone(task.create_at)

    def test_non_unique_task_name_per_user(self):
        Task.objects.create(user=self.user, name='Non-Unique Task')
        task = Task.objects.create(user=self.user, name='Non-Unique Task')
        self.assertEqual(task.name, 'Non-Unique Task')

    def test_str_method(self):
        task = Task.objects.create(user=self.user, name='Test Task')
        self.assertEqual(str(task), 'Test Task')


class TaskViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.profile, created = Profile.objects.get_or_create(user=self.user)
        self.profile.email_verified = True
        self.profile.save()
        self.client.login(username='testuser', password='testpass')

    def test_task_list_view(self):
        Task.objects.create(user=self.user, name='Test Task 1', description='Description 1')
        Task.objects.create(user=self.user, name='Test Task 2', description='Description 2')

        response = self.client.get(reverse('task:task_view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertEqual(len(response.context['task_list']), 2)

    def test_add_task_view(self):
        response = self.client.post(reverse('task:add_task'), data=json.dumps({
            'name': 'New Task',
            'description': 'New Task Description'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Task.objects.filter(name='New Task').exists())

    def test_update_task_view(self):
        task = Task.objects.create(user=self.user, name='Task to Update', complete=False)
        response = self.client.post(reverse('task:update_task', args=[task.id]),
                                    data=json.dumps({'complete': True}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertTrue(task.complete)

    def test_delete_task_view(self):
        task = Task.objects.create(user=self.user, name='Task to Delete')
        response = self.client.delete(reverse('task:delete_task', args=[task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_main_page_redirect_authenticated(self):
        response = self.client.get(reverse('task:main_page'))
        self.assertRedirects(response, reverse('task:task_view'))

    def test_main_page_display_for_anonymous_user(self):
        self.client.logout()
        response = self.client.get(reverse('task:main_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')


class EmailVerifiedMixinTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.profile, created = Profile.objects.get_or_create(user=self.user)
        self.profile.email_verified = False
        self.profile.save()

    def test_redirect_if_email_not_verified(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('task:task_view'))
        self.assertTemplateUsed(response, 'email_verification_required.html')
        self.assertEqual(response.status_code, 200)
