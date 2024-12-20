from django.urls import reverse
from .models import EmailVerification
from .tasks import send_verification_email_task, send_new_password_email_task
from django.core.exceptions import ObjectDoesNotExist
import random
import logging
import string
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
import json

logger = logging.getLogger(__name__)


class EmailService:
    """
    Класс который взаимодействует с задачей Celery на отправку E-mail
    """

    @staticmethod
    def send_verification_email(request, user):
        """
        Отправляет письмо с кодом проверки для подтверждения E-mail.
        """
        try:
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
        except ObjectDoesNotExist:
            logger.error(f"Не найден профиль для пользователя: {user.id}")

        except Exception as e:
            logger.error(f"Ошибка отправки письма подтверждения E-mail: {str(e)}")

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
        if length < 1:
            raise ValueError("Длина пароля должна быть больше 0")

        password = [random.choice(string.digits)]
        characters = string.ascii_letters + string.digits + string.punctuation
        password += random.choices(characters, k=length - 1)
        random.shuffle(password)

        return ''.join(password)


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

        schedule_map = {
            'minute': IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.MINUTES)[0],
            'hour': IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.HOURS)[0],
            'day': IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.DAYS)[0],
            'week': IntervalSchedule.objects.get_or_create(every=7, period=IntervalSchedule.DAYS)[0],
            'month': CrontabSchedule.objects.get_or_create(minute=0, hour=0, day_of_month=1)[0],
        }
        return schedule_map.get(self.profile.delete_frequency)
