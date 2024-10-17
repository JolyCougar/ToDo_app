from django.urls import path
from .views import TaskListView, TaskCreateView, TaskUpdateView, TaskDetailView

app_name = 'api'

urlpatterns = [
    path('tasks/', TaskListView.as_view(), name='task-list'),
    path('tasks/create/', TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:pk>/update/', TaskUpdateView.as_view(), name='task-update'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),

]
