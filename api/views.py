from rest_framework.generics import (ListAPIView, CreateAPIView, GenericAPIView,
                                     RetrieveAPIView, DestroyAPIView, RetrieveUpdateAPIView)
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.shortcuts import reverse
from django_filters.rest_framework import DjangoFilterBackend
from tasks.models import Task
from rest_framework.views import APIView
from .filters import TaskFilter
from .serializers import (TaskSerializer, CreateTaskSerializer, TaskDetailSerializer,
                          UserRegistrationSerializer, ProfileSerializer, UserSerializer,
                          PasswordResetSerializer, PasswordResetConfirmSerializer)
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.tokens import default_token_generator
from my_auth.services import EmailService
from django.contrib import messages
from rest_framework.response import Response
from my_auth.models import Profile
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from .permissions import IsEmailVerified


class TaskListView(ListAPIView):
    serializer_class = TaskSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskFilter
    permission_classes = [IsEmailVerified]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def handle_exception(self, exc):
        if isinstance(exc, PermissionDenied):
            return Response({'detail': 'Пожалуйста, подтвердите адрес электронной почты.'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().handle_exception(exc)


class TaskCreateView(CreateAPIView):
    serializer_class = CreateTaskSerializer
    permission_classes = [IsEmailVerified]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def handle_exception(self, exc):
        if isinstance(exc, PermissionDenied):
            return Response({'detail': 'Пожалуйста, подтвердите адрес электронной почты.'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().handle_exception(exc)


class TaskDetailUpdateView(RetrieveUpdateAPIView):
    permission_classes = [IsEmailVerified]

    def get_queryset(self):
        # Возвращаем только задачи, принадлежащие текущему пользователю
        return Task.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        # Используем разные сериализаторы для получения и обновления
        if self.request.method == 'PUT':
            return TaskSerializer
        return TaskDetailSerializer

    def handle_exception(self, exc):
        if isinstance(exc, PermissionDenied):
            return Response({'detail': 'Пожалуйста, подтвердите адрес электронной почты.'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().handle_exception(exc)


class TaskDeleteView(DestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskDetailSerializer
    permission_classes = [IsEmailVerified]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def handle_exception(self, exc):
        if isinstance(exc, PermissionDenied):
            return Response({'detail': 'Пожалуйста, подтвердите адрес электронной почты.'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().handle_exception(exc)


class RegisterView(CreateAPIView):
    serializer_class = UserRegistrationSerializer  # Используем наш сериализатор

    def create(self, request, *args, **kwargs):
        user_serializer = self.get_serializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)  # Проверяем валидность данных

        # Сохраняем пользователя
        user = user_serializer.save()

        # Создаем или обновляем профиль
        profile, created = Profile.objects.get_or_create(user=user)
        profile.agreement_accepted = True
        profile.save()

        # Отправляем электронное письмо для подтверждения
        try:
            EmailService.send_verification_email(request, user)  # Отправляем письмо
            messages.success(request, 'Регистрация прошла успешна! Проверьте вашу почту для подтверждения.')
        except Exception as e:
            messages.warning(request, 'Регистрация успешна, но не удалось отправить письмо с подтверждением. '
                                      'Пожалуйста, проверьте вашу почту позже.')

        return Response(user_serializer.data, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)


class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # Проверка, что имя пользователя и пароль предоставлены
        if not username or not password:
            return Response({'error': 'Имя пользователя и пароль обязательны.'}, status=status.HTTP_400_BAD_REQUEST)

        # Аутентификация пользователя
        user = authenticate(username=username, password=password)

        if user is not None:
            # Если аутентификация успешна, получаем или создаем токен
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Неверные учетные данные'}, status=status.HTTP_401_UNAUTHORIZED)


class ProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        profile = request.user.profile
        user_data = UserSerializer(request.user).data
        profile_data = ProfileSerializer(profile).data
        return Response({'user': user_data, 'profile': profile_data})

    def put(self, request, *args, **kwargs):
        user_serializer = UserSerializer(request.user, data=request.data.get('user'), partial=True)
        profile_serializer = ProfileSerializer(request.user.profile, data=request.data.get('profile'), partial=True)

        if user_serializer.is_valid() and profile_serializer.is_valid():
            user_serializer.save()
            profile_serializer.save()
            return Response({'user': user_serializer.data, 'profile': profile_serializer.data})
        return Response({'user_errors': user_serializer.errors, 'profile_errors': profile_serializer.errors},
                        status=400)


class PasswordResetView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()

        # Генерация токена и UID
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Создание ссылки для сброса пароля
        verification_link = request.build_absolute_uri(
            reverse('password_reset_confirm', args=[uid, token])
        )

        # Отправка письма с ссылкой для сброса пароля
        EmailService.send_verification_email(verification_link, user.email)

        return Response({"detail": "Ссылка для сброса пароля отправлена на ваш email."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, uidb64, token, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Получение пользователя
        user = serializer.get_user(uidb64, token)
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({"detail": "Пароль успешно сброшен."}, status=status.HTTP_200_OK)
