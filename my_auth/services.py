from django.urls import reverse
from .models import EmailVerification
from .tasks import send_verification_email_task, send_new_password_email_task
import random
import string
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
import json


class EmailService:
    """
    Класс который взаимодействует с задачей Celery на отправку E-mail
    """

    @staticmethod
    def send_verification_email(request, user):
        """
        Отправляет письмо с кодом проверки для подтверждения E-mail.
        """

        # Получаем профиль пользователя
        profile = user.profile
        # Создаем или получаем токен верификации
        email_verification, created = EmailVerification.objects.get_or_create(profile=profile)
        # Генерируем ссылку для подтверждения
        verification_link = request.build_absolute_uri(
            reverse('my_auth:verify_email', args=[email_verification.token])
        )
        # Отправляем электронное письмо асинхронно
        send_verification_email_task.delay(verification_link, user.email)

    @staticmethod
    def send_new_password_email(user, new_password):
        """
        Отправляет новый пароль
        """
        # Отправка нового пароля асинхронно
        send_new_password_email_task.delay(user.email, new_password)


class PasswordGenerator:
    """
    Генератор паролей
     """

    @staticmethod
    def generate_random_password(length=8):
        """
        Генерация случайного пароля заданной длины.
        """
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(characters) for _ in range(length))


class TaskScheduler:
    """
    Класс создания и применения рассписания на удаление выполненных задач
    """
    def __init__(self, profile):
        self.profile = profile
        self.task_name = f'delete_tasks_{self.profile.user.username}'

    def schedule_deletion_tasks(self):
        """
        Создаем расписание
        """

        # Удаляем старую задачу, если она существует
        PeriodicTask.objects.filter(name=self.task_name).delete()

        schedule = self.get_schedule()
        if schedule:
            PeriodicTask.objects.create(
                interval=schedule if isinstance(schedule, IntervalSchedule) else None,
                crontab=schedule if isinstance(schedule, CrontabSchedule) else None,
                name=self.task_name,
                task='my_auth.tasks.delete_completed_tasks',
                args=json.dumps([self.profile.user.id]),  # Передаем user_id в качестве аргумента
            )

    def get_schedule(self):
        """
        Устанавливаем рассписание в зависимости от выбора пользователя
        """

        if self.profile.delete_frequency == 'minute':
            return IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.MINUTES)[0]
        elif self.profile.delete_frequency == 'hour':
            return IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.HOURS)[0]
        elif self.profile.delete_frequency == 'day':
            return IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.DAYS)[0]
        elif self.profile.delete_frequency == 'week':
            return IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.WEEKS)[0]
        elif self.profile.delete_frequency == 'month':
            return CrontabSchedule.objects.get_or_create(minute=0, hour=0, day=1)[0]
        return None
