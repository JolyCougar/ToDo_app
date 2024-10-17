from django.urls import path
from .views import TaskListView,TaskCreateView

app_name = 'api'

urlpatterns = [
    path('tasks/', TaskListView.as_view(), name='task-list'),
    path('tasks/create/', TaskCreateView.as_view(), name='task-create'),

]
