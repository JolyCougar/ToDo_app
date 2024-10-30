from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """ Отоброжение модели задачи в админке """

    list_display = "pk", "name", "description_short", "complete"
    list_display_links = "pk", "name"
    search_fields = "name", "description", "user"

    def description_short(self, obj: Task) -> str:
        if len(obj.description) < 48:
            return obj.description
        return obj.description[:48] + "..."
