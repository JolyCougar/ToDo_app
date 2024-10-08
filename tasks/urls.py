from django.urls import path
from .views import TaskView, UpdateTaskView, DeleteTaskView

urlpatterns = [
    path('', TaskView.as_view(), name="task_view"),
    path('update-task/<int:task_id>/', UpdateTaskView.as_view(), name='update_task'),
    path('delete-task/<int:task_id>/', DeleteTaskView.as_view(), name='delete_task'),

]
