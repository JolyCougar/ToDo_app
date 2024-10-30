from django.db import models
from django.contrib.auth.models import User


class Task(models.Model):
    """ Модель задачи """
    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(null=False, blank=True, db_index=True)
    create_at = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return self.name
