from django.urls import path
from .views import (TaskListView, TaskCreateView, TaskUpdateView,
                    TaskDetailView, TaskDeleteView, RegisterView,
                    LogoutView, LoginView)
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

app_name = 'api'

urlpatterns = [
    path('tasks/', TaskListView.as_view(), name='task-list'),
    path('tasks/create/', TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('tasks/<int:pk>/delete/', TaskDeleteView.as_view(), name='task-delete'),
    path('tasks/<int:pk>/update/', TaskUpdateView.as_view(), name='task-update'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

]
