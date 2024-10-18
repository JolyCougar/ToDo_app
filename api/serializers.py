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
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}  # Пароль только для записи

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])  # Хешируем пароль
        user.save()
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar', 'agreement_accepted', 'cookies_accepted']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def get_user(self):
        email = self.validated_data['email']
        try:
            return User.objects.get(email=email)
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
            if not default_token_generator.check_token(user, token):
                raise serializers.ValidationError("Недействительный токен.")
            return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Недействительный токен.")


class TaskConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['complete']
