from rest_framework import permissions


class IsEmailVerified(permissions.BasePermission):
    """
    Разрешение, которое позволяет доступ только пользователям с подтвержденным адресом электронной почты.
    """

    def has_permission(self, request, view):
        # Проверяем, аутентифицирован ли пользователь
        if request.user and request.user.is_authenticated:
            # Проверяем, подтвержден ли email
            return request.user.profile.email_verified  # Предполагается, что у вас есть поле is_email_verified
        return False
   