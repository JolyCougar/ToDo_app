from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Отображение модели задачи в админке.

    Этот класс настраивает отображение модели задачи в административном
    интерфейсе Django. Он определяет, какие поля будут отображаться в
    списке задач, а также позволяет выполнять поиск по определенным полям.

    Атрибуты:
        list_display (tuple): Поля, которые будут отображаться в списке задач.
        list_display_links (tuple): Поля, по которым можно кликнуть для
        перехода к редактированию задачи.
        search_fields (tuple): Поля, по которым будет выполняться поиск
        в списке задач.
    """

    list_display = "pk", "name", "description_short", "complete"
    list_display_links = "pk", "name"
    search_fields = "name", "description", "user"

    def description_short(self, obj: Task) -> str:
        """
        Возвращает укороченное описание задачи для отображения в админке.

        :param obj: Объект задачи.
        :return: Укороченное описание задачи (до 48 символов) с добавлением
                 многоточия, если описание длиннее.
        """

        if len(obj.description) < 48:
            return obj.description
        return obj.description[:48] + "..."
