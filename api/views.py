from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from tasks.models import Task
from .filters import TaskFilter
from .serializers import TaskSerializer


class TaskListView(generics.ListAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskFilter

