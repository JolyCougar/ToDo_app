from django.db import models
from django.contrib.auth.models import User
import uuid


def profile_preview_directory_path(instance: "Profile", filename: str) -> str:
    """
    Генерирует путь для сохранения аватара профиля пользователя.

    instance (Profile): Экземпляр профиля пользователя.
    filename (str): Имя файла загружаемого изображения.

    Returns: str: Путь для сохранения изображения.
    """

    return "profile_{pk}/{filename}".format(
        pk=instance.pk,
        filename=filename,
    )


class Profile(models.Model):
    """
    Модель профиля пользователя.

    Хранит информацию о пользователе, включая биографию, аватар,
    статус подтверждения email и согласие на использование cookies.

    Атрибуты:
        user (OneToOneField): Ссылка на пользователя, которому создается профиль.
        bio (TextField): Небольшая информация о себе(максимум 500 символов).
        agreement_accepted (BooleanField): Статус принял ли пользователь лицензионное соглашение
        (согласен/не согласен), по умолчанию False.
        avatar (ImageField): Аватарка пользователя.
        email_verified (BooleanField): Статус подтвержден E-mail (выполнена/не выполнена), по умолчанию False.
        cookies_accepted (BooleanField): Статус согласие на использования Cookies (согласен/не согласен),
         по умолчанию False.
        delete_frequency (CharField): Частота удаления выполненых задач, по умолчанию ('never','Никогда')


    """

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    agreement_accepted = models.BooleanField(default=False)
    avatar = models.ImageField(null=True, blank=True, upload_to=profile_preview_directory_path)
    email_verified = models.BooleanField(default=False)
    cookies_accepted = models.BooleanField(default=False)
    delete_frequency = models.CharField(max_length=20, choices=[
        ('never', 'Никогда'),
        ('minute', 'Раз в минуту'),
        ('hour', 'Раз в час'),
        ('day', 'Раз в день'),
        ('week', 'Раз в неделю'),
        ('month', 'Раз в месяц'),
    ], default='never')

    def __str__(self) -> str:
        """
        Возвращает строковое представление профиля пользователя.
        """

        return self.user.username


class EmailVerification(models.Model):
    """
    Модель создания токена для подтверждения E-mail.

    Хранит информацию о профиле и токене для подтверждения адреса электронной почты.

     Атрибуты:
        profile (OneToOneField): Ссылка на пользователя, которому был отправлен токен.
        token (UUIDField): Токен пользователя для подтверждения E-mail
    """

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
