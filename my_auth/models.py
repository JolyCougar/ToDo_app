from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


def profile_preview_directory_path(instance: "Profile", filename: str) -> str:
    return "profile_{pk}/{filename}".format(
        pk=instance.pk,
        filename=filename,
    )


class Profile(models.Model):
    """ Модель профиля пользователя"""

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

    def __str__(self):
        return self.user.username


class EmailVerification(models.Model):
    """ Модель создания токена для подтверждения E-mail """

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
