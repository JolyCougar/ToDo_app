import django_filters
from tasks.models import Task


class TaskFilter(django_filters.FilterSet):
    """
    Этот класс используется для фильтрации задач по различным полям,
    таким как статус выполнения. Он позволяет пользователям
    получать только те задачи, которые соответствуют заданным критериям.
    """

    class Meta:
        model = Task
        fields = {
            'complete': ['exact'],  # Фильтрация по полю complete
        }
