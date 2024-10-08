from django.urls import path
from .views import TaskView, UpdateTaskView, DeleteTaskView, AddTaskView

urlpatterns = [
    path('', TaskView.as_view(), name="task_view"),
    path('update-task/<int:task_id>/', UpdateTaskView.as_view(), name='update_task'),
    path('delete-task/<int:task_id>/', DeleteTaskView.as_view(), name='delete_task'),
    path('add-task/', AddTaskView.as_view(), name='add_task'),

]
