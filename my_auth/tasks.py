from celery import shared_task
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from decouple import config
from tasks.models import Task

""" Задачи Celery  для отправки писем """

logger = logging.getLogger(__name__)


@shared_task
def send_verification_email_task(verification_link, user_email):
    try:
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
        logger.info(f'Письмо с подтверждением было отправлено на {user_email}')
    except Exception as e:
        logger.error(f'Неудачная попытка отправить письмо пользователю на E-mail: {user_email}: {str(e)}')


@shared_task
def send_new_password_email_task(user_email, new_password):
    subject = 'toDo app: Ваш новый пароль'
    try:
        # Генерируем HTML-содержимое письма
        html_message = render_to_string('messages_to_new_password.html', {
            'new_password': new_password,
        })

        text_message = strip_tags(html_message)

        send_mail(
            subject,
            text_message,
            config('EMAIL_HOST_USER'),
            [user_email],
            fail_silently=False,
            html_message=html_message,
        )
        logger.info(f'Новый пароль был отправлен пользователю на почту {user_email}')
    except Exception as e:
        logger.error(f'Неудачная попытка отправки пароля пользователю на почту {user_email}: {str(e)}')


"""
Задача Celery удаления всех выполненых задач
"""


@shared_task
def delete_completed_tasks(user_id):
    try:
        # Удаляем все выполненные задачи для данного пользователя
        Task.objects.filter(user_id=user_id, complete=True).delete()
        logger.info(f'Удалены выполненые задачи у пользователя {user_id}')
    except Exception as e:
        logger.error(f'Неудачная попытка удаления выполненнх задач у пользователя {user_id}: {str(e)}')
