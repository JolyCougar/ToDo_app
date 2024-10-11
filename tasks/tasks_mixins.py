from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin


class EmailVerifiedMixin(LoginRequiredMixin):
    """Mixin для проверки, подтверждена ли электронная почта пользователя."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.profile.email_verified:
            return HttpResponseForbidden("Пожалуйста, подтвердите вашу электронную почту.")
        return super().dispatch(request, *args, **kwargs)