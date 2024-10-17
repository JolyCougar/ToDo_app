from rest_framework.generics import (ListAPIView, CreateAPIView, UpdateAPIView,
                                     RetrieveAPIView, DestroyAPIView)
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from tasks.models import Task
from .filters import TaskFilter
from .serializers import (TaskSerializer, CreateTaskSerializer, TaskDetailSerializer,
                          UserRegistrationSerializer)
from rest_framework.permissions import IsAuthenticated
from my_auth.services import EmailService
from django.contrib import messages
from rest_framework.response import Response
from my_auth.models import Profile


class TaskListView(ListAPIView):
    serializer_class = TaskSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskFilter
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


class TaskCreateView(CreateAPIView):
    serializer_class = CreateTaskSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskUpdateView(UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save()


class TaskDetailView(RetrieveAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


class TaskDeleteView(DestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


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
