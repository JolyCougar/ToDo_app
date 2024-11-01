from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProductAdmin(admin.ModelAdmin):
    """
    Отображение Профиля в админке

    Этот класс настраивает отображение модели задачи в административном
    интерфейсе Django. Он определяет, какие поля будут отображаться в
    списке задач, а также позволяет выполнять поиск по определенным полям.

    Атрибуты:
        list_display (tuple): Поля, которые будут отображаться в списке задач.
    """

    list_display = "user", "bio", "avatar", "agreement_accepted"
