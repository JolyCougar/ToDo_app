from django.contrib.auth import views as auth_views
from django.urls import path
from .views import CustomLoginView, CustomLogoutView, RegisterView

app_name = 'my_auth'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register')

]
