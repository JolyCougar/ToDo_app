from django.core.mail import send_mail
from decouple import config
from celery import shared_task

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from decouple import config


@shared_task
def send_verification_email_task(verification_link, user_email):
    # Генерируем HTML-содержимое письма
    html_message = render_to_string('messages_to_verification.html', {
        'verification_link': verification_link,
    })

    # Создаем текстовую версию письма (для почтовых клиентов, которые не поддерживают HTML)
    text_message = strip_tags(html_message)

    send_mail(
        'toDo app: Добро пожаловать!',
        text_message,
        config('EMAIL_HOST_USER'),
        [user_email],
        fail_silently=False,
        html_message=html_message,  # Добавляем HTML-содержимое
    )


@shared_task
def send_new_password_email_task(user_email, new_password):
    subject = 'toDo app: Ваш новый пароль'
    # Генерируем HTML-содержимое письма
    html_message = render_to_string('messages_to_new_password.html', {
        'new_password': new_password,
    })

    # Создаем текстовую версию письма (для почтовых клиентов, которые не поддерживают HTML)
    text_message = strip_tags(html_message)

    send_mail(
        subject,
        text_message,
        config('EMAIL_HOST_USER'),
        [user_email],
        fail_silently=False,
        html_message=html_message,  # Добавляем HTML-содержимое
    )
