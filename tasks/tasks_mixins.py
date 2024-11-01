from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin


class EmailVerifiedMixin(LoginRequiredMixin):
    """
    Mixin для проверки, подтверждена ли электронная почта пользователя.

    Этот миксин используется для защиты представлений, требующих
    подтверждения электронной почты. Если электронная почта
    пользователя не подтверждена, он будет перенаправлен на
    страницу с сообщением о необходимости подтверждения.
    """

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
        Обрабатывает входящие запросы и проверяет, подтверждена ли
        электронная почта пользователя.

        :param request: HTTP запрос.
        :return: HttpResponse с перенаправлением на страницу
                 подтверждения электронной почты или ответом
                 для дальнейшей обработки запроса.
        """

        if request.user.is_authenticated:
            # Проверяем, подтверждена ли электронная почта
            if not request.user.profile.email_verified:
                # Если не подтверждена, рендерим страницу с сообщением
                return self.handle_email_not_verified(request)
        return super().dispatch(request, *args, **kwargs)

    def handle_email_not_verified(self, request) -> HttpResponse:
        """
        Отображает страницу с сообщением о необходимости
        подтверждения электронной почты.

        :param request: HTTP запрос.
        :return: HttpResponse с рендерингом страницы
                 подтверждения электронной почты.
        """

        return render(request, 'email_verification_required.html')
