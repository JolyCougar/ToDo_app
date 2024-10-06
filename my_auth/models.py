from django.db import models
from django.contrib.auth.models import User


def product_preview_directory_path(instance: "Profile", filename: str) -> str:
    return "profile_{pk}/{filename}".format(
        pk=instance.pk,
        filename=filename,
    )


class Profile(models.Model):
    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    agreement_accepted = models.BooleanField(default=False)
    avatar = models.ImageField(null=True, blank=True, upload_to=product_preview_directory_path)
