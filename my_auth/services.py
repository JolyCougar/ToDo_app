# services.py
from django.core.mail import send_mail
from django.urls import reverse
from .models import EmailVerification


class EmailService:
    @staticmethod
    def send_verification_email(request, profile):
        verification = EmailVerification.objects.create(profile=profile)
        verification_link = request.build_absolute_uri(reverse('my_auth:verify_email', args=[verification.token]))

        try:
            send_mail(
                'Подтверждение электронной почты',
                f'Пожалуйста, подтвердите вашу электронную почту, перейдя по следующей ссылке: {verification_link}',
                'danero95@yandex.ru',
                [profile.user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Ошибка при отправке письма: {e}")
