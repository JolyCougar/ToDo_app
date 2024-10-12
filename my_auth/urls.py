from django.contrib.auth import views as auth_views
from django.urls import path
from .views import (CustomLoginView, CustomLogoutView, RegisterView,
                    ProfileView, ChangePasswordView, ResetAvatarView,
                    VerifyEmailView, ResendVerificationTokenView, ChangeEmailView,
                    AcceptCookiesView)

app_name = 'my_auth'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification-token/', ResendVerificationTokenView.as_view(), name='resend_verification_token'),
    path('profile/<int:pk>/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('reset-avatar/', ResetAvatarView.as_view(), name='reset_avatar'),
    path('change-email/', ChangeEmailView.as_view(), name='change_email'),
    path('accept-cookies/', AcceptCookiesView.as_view(), name='accept_cookies'),

]
