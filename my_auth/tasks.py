from django.core.mail import send_mail
from decouple import config
from celery import shared_task


@shared_task
def send_verification_email_task(verification_link, user_email):
    send_mail(
        'Подтверждение электронной почты',
        f'Пожалуйста, подтвердите вашу электронную почту, перейдя по следующей ссылке: {verification_link}',
        config('EMAIL_HOST_USER'),
        [user_email],
        fail_silently=False,
    )
