from typing import Type
from django.db.models import QuerySet
from rest_framework.generics import (ListAPIView, CreateAPIView, GenericAPIView,
                                     UpdateAPIView, DestroyAPIView, RetrieveUpdateAPIView)
from rest_framework import status
import logging
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import Serializer

from my_auth.services import PasswordGenerator
from django_filters.rest_framework import DjangoFilterBackend
from tasks.models import Task
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from .filters import TaskFilter
from .serializers import (TaskSerializer, CreateTaskSerializer, TaskDetailSerializer,
                          UserRegistrationSerializer, ProfileSerializer, UserSerializer,
                          PasswordResetSerializer)
from rest_framework.permissions import IsAuthenticated
from my_auth.services import EmailService
from django.contrib import messages
from rest_framework.response import Response
from my_auth.models import Profile
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from .permissions import IsEmailVerified
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class TaskListView(ListAPIView):
    """
    Этот класс предоставляет API для получения списка задач,
    связанных с текущим пользователем. Доступ к этому представлению
    разрешен только для пользователей с подтвержденным адресом электронной почты.
    """

    serializer_class = TaskSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskFilter
    permission_classes = [IsEmailVerified]

    def get_queryset(self) -> QuerySet[Task]:
        """
        Возвращает набор задач, связанных с текущим пользователем.

        :return: QuerySet задач пользователя.
        """

        return Task.objects.filter(user=self.request.user)

    def handle_exception(self, exc: Exception) -> Response:
        """
        Обрабатывает исключения, возникающие при выполнении запроса.
        Если возникло исключение PermissionDenied, возвращает
        сообщение с просьбой подтвердить адрес электронной почты.

        :param exc: Исключение, возникшее при выполнении запроса.
        :return: Response с сообщением об ошибке или результатом
        обработки исключения.
        """

        if isinstance(exc, PermissionDenied):
            return Response({'detail': 'Пожалуйста, подтвердите адрес электронной почты.'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().handle_exception(exc)


class TaskCreateView(CreateAPIView):
    """
    Этот класс предоставляет API для создания новой задачи,
    связанной с текущим пользователем. Доступ к этому представлению
    разрешен только для пользователей с подтвержденным адресом электронной почты.
    """

    serializer_class = CreateTaskSerializer
    permission_classes = [IsEmailVerified]

    def perform_create(self, serializer) -> None:
        """
        Сохраняет новую задачу, связывая её с текущим пользователем.

        :param serializer: Сериализатор, содержащий данные для создания задачи.
        """

        serializer.save(user=self.request.user)
        logger.info(f"Пользователь {self.request.user.username} создал новую задачу.")

    def handle_exception(self, exc: Exception) -> Response:
        """
        Обрабатывает исключения, возникающие при выполнении запроса.

        Если возникло исключение PermissionDenied, возвращает
        сообщение с просьбой подтвердить адрес электронной почты.

        :param exc: Исключение, возникшее при выполнении запроса.
        :return: Response с сообщением об ошибке или результатом
        обработки исключения.
        """

        if isinstance(exc, PermissionDenied):
            return Response({'detail': 'Пожалуйста, подтвердите адрес электронной почты.'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().handle_exception(exc)


class TaskDetailUpdateView(RetrieveUpdateAPIView):
    """
    Этот класс предоставляет API для получения и обновления
    информации о задаче, связанной с текущим пользователем.
    Доступ к этому представлению разрешен только для пользователей
    с подтвержденным адресом электронной почты.
    """

    permission_classes = [IsEmailVerified]

    def get_queryset(self) -> QuerySet[Task]:
        """
        Возвращает только задачи, принадлежащие текущему пользователю.

        :return: QuerySet задач пользователя.
        """

        return Task.objects.filter(user=self.request.user)

    def get_serializer_class(self) -> Type[Serializer]:
        """
        Возвращает сериализатор в зависимости от метода запроса.

        :return: Сериализатор для получения или обновления задачи.
        """

        if self.request.method == 'PUT':
            return TaskSerializer
        return TaskDetailSerializer

    def handle_exception(self, exc: Exception) -> Response:
        """
        Обрабатывает исключения, возникающие при выполнении запроса.

        Если возникло исключение PermissionDenied, возвращает
        сообщение с просьбой подтвердить адрес электронной почты.

        :param exc: Исключение, возникшее при выполнении запроса.
        :return: Response с сообщением об ошибке или результатом
        обработки исключения.
        """

        if isinstance(exc, PermissionDenied):
            return Response({'detail': 'Пожалуйста, подтвердите адрес электронной почты.'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().handle_exception(exc)


class TaskDeleteView(DestroyAPIView):
    """
    Этот класс предоставляет API для удаления задачи,
    связанной с текущим пользователем.
    Доступ к этому представлению разрешен только для пользователей
    с подтвержденным адресом электронной почты.
    """

    queryset = Task.objects.all()
    serializer_class = TaskDetailSerializer
    permission_classes = [IsEmailVerified]

    def get_queryset(self) -> QuerySet[Task]:
        """
        Возвращает только задачи, принадлежащие текущему пользователю.

        :return: QuerySet задач пользователя.
        """

        logger.info(f"Пользователь {self.request.user.username} удалил задачу.")
        return Task.objects.filter(user=self.request.user)

    def handle_exception(self, exc: Exception) -> Response:
        """
        Обрабатывает исключения, возникающие при выполнении запроса.
        Если возникло исключение PermissionDenied, возвращает
        сообщение с просьбой подтвердить адрес электронной почты.

        :param exc: Исключение, возникшее при выполнении запроса.
        :return: Response с сообщением об ошибке или результатом
        обработки исключения.
        """

        if isinstance(exc, PermissionDenied):
            return Response({'detail': 'Пожалуйста, подтвердите адрес электронной почты.'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().handle_exception(exc)


class RegisterView(CreateAPIView):
    """
    Этот класс предоставляет API для регистрации новых пользователей.
    """

    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs) -> Response:
        """
        Обрабатывает создание нового пользователя.

        :param request: HTTP запрос с данными для регистрации.
        :return: Response с результатом регистрации.
        """

        user_serializer = self.get_serializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)  # Проверяем валидность данных

        # Получаем пароль из сериализатора
        password = user_serializer.validated_data.get('password')

        # Проверка сложности пароля
        try:
            validate_password(password=password)
        except ValidationError as e:
            if 'This password is too short.' in e.messages or 'This password is too common.' in e.messages:
                return Response({'password': ['Пароль слишком легкий. Пожалуйста, выберите более сложный пароль.']},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response({'password': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        # Сохраняем пользователя
        user = user_serializer.save()
        logger.info(f"Зарегистрирован пользователь: {user.username}")

        # Создаем или обновляем профиль
        profile, created = Profile.objects.get_or_create(user=user)
        profile.agreement_accepted = True
        profile.save()
        logger.info(f"Создан профиль для пользователя: {user.username}")

        # Отправляем электронное письмо для подтверждения
        try:
            EmailService.send_verification_email(request, user)  # Отправляем письмо
            messages.success(request, 'Регистрация прошла успешна! Проверьте вашу почту для подтверждения.')
        except Exception as e:
            logger.error(f"Не удалось отправить письмо с подтверждением для пользователя {user.username}: {str(e)}")
            messages.warning(request, 'Регистрация успешна, но не удалось отправить письмо с подтверждением. '
                                      'Пожалуйста, проверьте вашу почту позже.')

        return Response({'message': 'Регистрация прошла успешно! Проверьте вашу почту для подтверждения.'},
                        status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """
    Этот класс предоставляет API для выхода пользователя из системы.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        """
        Обрабатывает выход пользователя из системы.

        :param request: HTTP запрос.
        :return: Response с результатом выхода.
        """

        request.user.auth_token.delete()
        logger.info(f"Пользователь успешно вышел: {request.user.username}")
        return Response(status=status.HTTP_200_OK)


class LoginView(APIView):
    """
    Этот класс предоставляет API для входа пользователей в систему.
    """

    def post(self, request) -> Response:
        """
        Обрабатывает вход пользователя в систему.

        :param request: HTTP запрос с данными для авторизации.
        :return: Response с токеном или сообщением об ошибке.
        """

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
            logger.info(f"Авторизовался пользователь: {username}")
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        else:
            logger.warning(f"Неудачная попытка авторизации для пользователя: {username}")
            return Response({'error': 'Неверные учетные данные'}, status=status.HTTP_401_UNAUTHORIZED)


class ProfileView(RetrieveUpdateAPIView):
    """
    Этот класс предоставляет API для получения и обновления
    информации о профиле текущего пользователя.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        """
        Возвращает информацию о пользователе и его профиле.

        :param request: HTTP запрос.
        :return: Response с данными пользователя и профиля.
        """

        profile = request.user.profile
        user_data = UserSerializer(request.user).data
        profile_data = ProfileSerializer(profile).data
        return Response({'user': user_data, 'profile': profile_data})

    def put(self, request, *args, **kwargs) -> Response:
        """
        Обрабатывает обновление информации о пользователе и профиле.

        :param request: HTTP запрос с данными для обновления.
        :return: Response с обновленными данными или ошибками.
        """

        user_serializer = UserSerializer(request.user, data=request.data.get('user'), partial=True)
        profile_serializer = ProfileSerializer(request.user.profile, data=request.data.get('profile'), partial=True)

        if user_serializer.is_valid() and profile_serializer.is_valid():
            # Проверяем, изменился ли email
            if 'email' in user_serializer.validated_data:
                new_email = user_serializer.validated_data['email']
                if new_email != request.user.email:
                    # Отправляем письмо для подтверждения нового email
                    EmailService.send_verification_email(request, request.user)
                    request.user.profile.email_verified = False
                    request.user.profile.save()

            user_serializer.save()
            profile_serializer.save()
            logger.info(f"Пользователь {request.user.username} обновил свой профиль.")
            return Response({'user': user_serializer.data, 'profile': profile_serializer.data})

        logger.info(f"Пользователь {request.user.username} ошибка обновления профиля.")
        return Response({'user_errors': user_serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(GenericAPIView):
    """
    Этот класс предоставляет API для сброса пароля пользователя.
    """

    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs) -> Response:
        """
        Обрабатывает запрос на сброс пароля.

        :param request: HTTP запрос с данными для сброса пароля.
        :return: Response с результатом сброса пароля.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()  # Убедитесь, что это объект User

        # Проверка, что user - это объект User
        if not isinstance(user, User):
            return Response({"detail": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND)

        # Генерация нового пароля
        new_password = PasswordGenerator.generate_random_password()

        # Установка нового пароля для пользователя
        user.set_password(new_password)
        user.save()

        # Отправка нового пароля пользователю
        EmailService.send_new_password_email(user, new_password)
        logger.info(f"Пользователь {request.user.username} сбросил свой пароль.")
        return Response({"detail": "Новый пароль отправлен на ваш email."}, status=status.HTTP_200_OK)


class TaskConfirmView(UpdateAPIView):
    """
    Этот класс предоставляет API для подтверждения задачи,
    связанной с текущим пользователем.
    """

    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def patch(self, request, *args, **kwargs) -> Response:
        """
        Обрабатывает запрос на подтверждение задачи.

        :param request: HTTP запрос.
        :return: Response с результатом подтверждения задачи.
        """

        task = self.get_object()

        # Проверка прав пользователя
        if task.user != request.user:
            return Response({"detail": "У вас нет прав на подтверждение этой задачи."},
                            status=status.HTTP_403_FORBIDDEN)

        # Обновление поля complete
        task.complete = True
        task.save()  # Сохраняем изменения в базе данных
        logger.info(f"Пользователь {request.user.username} подтвердил задачу.")
        return Response({"detail": "Задача успешно подтверждена."}, status=status.HTTP_200_OK)
