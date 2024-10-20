from rest_framework import serializers
from tasks.models import Task
from django.contrib.auth.models import User
from my_auth.models import Profile
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'name', 'description', 'complete']


class CreateTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'user', 'name', 'description', 'create_at']
        read_only_fields = ['user', 'create_at', 'complete']


class TaskDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)  # Делаем поле e-mail обязательным

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])  # Устанавливаем пароль
        user.save()
        return user

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким e-mail уже существует.")
        return value


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar']

    def update(self, instance, validated_data):
        # Удаляем поля, которые не должны изменяться
        validated_data.pop('agreement_accepted', None)
        validated_data.pop('cookies_accepted', None)

        # Обновляем остальные поля
        return super().update(instance, validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def get_user(self):
        email = self.validated_data['email']
        try:
            user = User.objects.get(email=email)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь с таким email не найден.")


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Пароли не совпадают.")
        return attrs

    def get_user(self, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
            print(user)
            if not default_token_generator.check_token(user, token):
                raise serializers.ValidationError("Недействительный токен.")
            return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Недействительный токен.")


class TaskConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['complete']
