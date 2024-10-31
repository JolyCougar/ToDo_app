from rest_framework import permissions


class IsEmailVerified(permissions.BasePermission):
    """
    Это разрешение проверяет, аутентифицирован ли пользователь и
    подтвержден ли его адрес электронной почты. Если оба условия
    выполнены, доступ разрешен.
    """

    def has_permission(self, request, view) -> bool:
        """
        Проверяет, есть ли у пользователя разрешение на доступ к представлению.

        :param request: HTTP запрос.
        :param view: Представление, к которому осуществляется доступ.
        :return: True, если доступ разрешен; иначе False.
        """

        # Проверяем, аутентифицирован ли пользователь
        if request.user and request.user.is_authenticated:
            # Проверяем, подтвержден ли email
            return request.user.profile.email_verified  # Предполагается, что у вас есть поле is_email_verified
        return False
