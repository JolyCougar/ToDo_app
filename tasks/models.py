from django.db import models
from django.contrib.auth.models import User


class Task(models.Model):
    """
    Модель задачи

    Эта модель представляет задачу, связанную с пользователем.
    Она содержит информацию о названии, описании, времени создания
    и статусе выполнения задачи.

    Атрибуты:
        user (ForeignKey): Ссылка на пользователя, которому принадлежит задача.
        name (CharField): Название задачи, максимальная длина 100 символов.
        description (TextField): Описание задачи, может быть пустым.
        create_at (DateTimeField): Время создания задачи, автоматически устанавливается при создании.
        complete (BooleanField): Статус выполнения задачи (выполнена/не выполнена), по умолчанию False.
    """

    class Meta:
        """
        verbose_name (str): Человекочитаемое имя модели в единственном числе.
        verbose_name_plural (str): Человекочитаемое имя модели во множественном числе.
        """

        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(null=False, blank=True, db_index=True)
    create_at = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False, db_index=True)

    def __str__(self) -> str:
        return self.name
