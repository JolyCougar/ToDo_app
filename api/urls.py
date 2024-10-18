from django.urls import path
from .views import (TaskListView, TaskCreateView, TaskDetailUpdateView,
                    TaskDeleteView, RegisterView, LogoutView,
                    LoginView, ProfileView)

app_name = 'api'

urlpatterns = [
    path('tasks/', TaskListView.as_view(), name='task-list'),
    path('tasks/create/', TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:pk>/', TaskDetailUpdateView.as_view(), name='task-detail-update'),
    path('tasks/<int:pk>/delete/', TaskDeleteView.as_view(), name='task-delete'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),

]
