from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from tasks.models import Task
from .filters import TaskFilter
from .serializers import TaskSerializer
from rest_framework.permissions import IsAuthenticated


class TaskListView(ListAPIView):
    serializer_class = TaskSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskFilter
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

