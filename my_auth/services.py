from django.urls import reverse
from .models import EmailVerification
from .tasks import send_verification_email_task


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
