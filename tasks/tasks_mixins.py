from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin


class EmailVerifiedMixin(LoginRequiredMixin):
    """Mixin для проверки, подтверждена ли электронная почта пользователя."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Проверяем, подтверждена ли электронная почта
            if not request.user.profile.email_verified:
                # Если не подтверждена, рендерим страницу с сообщением
                return self.handle_email_not_verified(request)
        return super().dispatch(request, *args, **kwargs)

    def handle_email_not_verified(self, request):
        # Отображаем страницу с сообщением о необходимости подтверждения электронной почты
        return render(request, 'email_verification_required.html')
