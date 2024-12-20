from django.urls import path
from .views import (CustomLoginView, CustomLogoutView, RegisterView,
                    ProfileView, ChangePasswordView, ResetAvatarView,
                    VerifyEmailView, ResendVerificationTokenView, ChangeEmailView,
                    AcceptCookiesView, CheckUsernameView, CheckEmailView,
                    PasswordResetView, UpdateProfileView, SetLanguageView)

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
    path('check-username/', CheckUsernameView.as_view(), name='check_username'),
    path('check-email/', CheckEmailView.as_view(), name='check_email'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('update-profile/', UpdateProfileView.as_view(), name='update_profile'),
    path('set_language/<str:language>/', SetLanguageView.as_view(), name='set_language'),

]
