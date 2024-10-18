from django.urls import reverse
from .models import EmailVerification
from .tasks import send_verification_email_task, send_new_password_email_task
import random
import string


class EmailService:
    @staticmethod
    def send_verification_email(request, user):
        # Получаем профиль пользователя
        profile = user.profile  # Здесь вы получаете профиль пользователя
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
        # Отправка нового пароля асинхронно
        send_new_password_email_task.delay(user.email, new_password)


class PasswordGenerator:
    @staticmethod
    def generate_random_password(length=8):
        """Генерация случайного пароля заданной длины."""
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(characters) for _ in range(length))
