import django_filters
from tasks.models import Task


class TaskFilter(django_filters.FilterSet):
    class Meta:
        model = Task
        fields = {
            'complete': ['exact'],  # Фильтрация по полю complete
        }
