from rest_framework import serializers
from tasks.models import Task
from django.contrib.auth.models import User
from my_auth.models import Profile
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode


class TaskSerializer(serializers.ModelSerializer):
    """
    Сериалайзер задач.

    Этот сериализатор используется для представления задач.
    Он позволяет сериализовать и десериализовать данные задач.
    """

    class Meta:
        model = Task
        fields = ['id', 'name', 'description', 'complete']


class CreateTaskSerializer(serializers.ModelSerializer):
    """
    Сериалайзер создания задачи.

    Этот сериализатор используется для создания новой задачи.
    Поля 'user' и 'create_at' являются только для чтения.
    """

    class Meta:
        model = Task
        fields = ['id', 'user', 'name', 'description', 'create_at', 'complete']
        read_only_fields = ['user', 'create_at']


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Сериалайзер деталей задачи.

    Этот сериализатор используется для получения всех деталей задачи.
    """

    class Meta:
        model = Task
        fields = '__all__'


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для регистрации нового пользователя.

    Этот сериализатор используется для регистрации новых пользователей.
    Он проверяет уникальность email и устанавливает пароль.
    """

    email = serializers.EmailField(required=True)  # Делаем поле e-mail обязательным

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        """
        Создает нового пользователя с заданными данными.

        :param validated_data: Данные для создания пользователя.
        :return: Созданный объект User.
        """

        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])  # Устанавливаем пароль
        user.save()
        return user

    def validate_email(self, value):
        """
        Проверяет, существует ли пользователь с таким email.

        :param value: Email для проверки.
        :return: Email, если он уникален.
        :raises serializers.ValidationError: Если email уже существует.
        """

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким e-mail уже существует.")
        return value


class ProfileSerializer(serializers.ModelSerializer):
    """
    Сериалайзер профиля.

    Этот сериализатор используется для получения и обновления профиля пользователя.
    """

    class Meta:
        model = Profile
        fields = ['bio', 'avatar']

    def update(self, instance, validated_data):
        """
        Обновляет профиль пользователя.

        :param instance: Экземпляр профиля для обновления.
        :param validated_data: Данные для обновления профиля.
        :return: Обновленный экземпляр профиля.
        """

        # Удаляем поля, которые не должны изменяться
        validated_data.pop('agreement_accepted', None)
        validated_data.pop('cookies_accepted', None)

        # Обновляем остальные поля
        return super().update(instance, validated_data)


class UserSerializer(serializers.ModelSerializer):
    """
    Сериалайзер юзера.

    Этот сериализатор используется для представления данных пользователя.
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class PasswordResetSerializer(serializers.Serializer):
    """
    Сериалайзер для сброса пароля.

    Этот сериализатор используется для обработки запросов на сброс пароля.
    """

    email = serializers.EmailField()

    def get_user(self):
        """
        Получает пользователя по email.

        :return: Объект User, если он существует.
        :raises serializers.ValidationError: Если пользователь не найден.
        """

        email = self.validated_data['email']
        try:
            user = User.objects.get(email=email)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь с таким email не найден.")


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Сериалайзер подтверждения сброса пароля.

    Этот сериализатор используется для подтверждения сброса пароля
    и установки нового пароля.
    """

    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Проверяет, совпадают ли новые пароли.

        :param attrs: Атрибуты, переданные для валидации.
        :return: Атрибуты, если пароли совпадают.
        :raises serializers.ValidationError: Если пароли не совпадают.
        """

        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Пароли не совпадают.")
        return attrs

    def get_user(self, uidb64, token):
        """
        Получает пользователя по uid и токену.

        :param uidb64: Закодированный идентификатор пользователя.
        :param token: Токен для подтверждения сброса пароля.
        :return: Объект User, если токен действителен.
        :raises serializers.ValidationError: Если токен недействителен.
        """

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
            if not default_token_generator.check_token(user, token):
                raise serializers.ValidationError("Недействительный токен.")
            return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Недействительный токен.")


class TaskConfirmSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для подтверждения задачи.

    Этот сериализатор используется для обновления статуса задачи
    на "подтверждено".
    """

    class Meta:
        model = Task
        fields = ['complete']
