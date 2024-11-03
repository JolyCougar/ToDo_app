from django.shortcuts import get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from .models import Profile, EmailVerification
from .services import PasswordGenerator, EmailService, TaskScheduler
import json
import logging
from django.contrib.auth import login
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, DetailView
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import UserRegistrationForm, ProfileForm, UsernameForm
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    """
    Кастомный класс авторизации, который обрабатывает вход пользователей.

    Если пользователь уже аутентифицирован, он будет перенаправлен на главную страницу.
    Также добавляет сообщения об успешной регистрации и ошибках входа в контекст.
    """

    template_name = 'login.html'

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
        Обрабатывает запрос и проверяет, аутентифицирован ли пользователь.
        Если да, перенаправляет на главную страницу.
        """

        if request.user.is_authenticated:
            return redirect(reverse_lazy('task:task_view'))  # Перенаправление на главную страницу

        # Проверка параметров запроса для передачи сообщений
        registration_success = request.GET.get('registration_success', False)
        login_error = request.GET.get('login_error', False)

        # Добавление сообщений в контекст
        self.extra_context = {
            'registration_success': registration_success,
            'login_error': login_error,
        }

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        """
        Получает контекст для шаблона и добавляет дополнительные данные.
        """

        # Получаем контекст из родительского класса
        context = super().get_context_data(**kwargs)
        # Объединяем контекст с дополнительными данными
        context.update(self.extra_context)
        return context

    def form_invalid(self, form) -> HttpResponse:
        """
        Обрабатывает случай, когда форма входа недействительна,
        добавляя сообщение об ошибке в контекст.
        """

        logger.warning(f'Неудачная попытка авторизации для : {form.cleaned_data.get("username")}')
        # Если форма недействительна, добавляем сообщение об ошибке
        self.extra_context['login_error'] = "Неправильное имя пользователя или пароль."
        return self.render_to_response(self.get_context_data(form=form))


class CustomLogoutView(LogoutView):
    """
    Кастомный класс выхода из системы.
    Обрабатывает выход пользователя и перенаправляет на страницу входа.
    """

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """
        Обрабатывает GET-запрос для выхода из системы.
        """

        logger.info(f'User {request.user.username} вышел из системы.')
        response = super().get(request, *args, **kwargs)
        return response


class RegisterView(CreateView):
    """
    Класс Регистрации пользователя.

    Обрабатывает регистрацию нового пользователя и отправляет письмо с подтверждением.
    """

    template_name = 'registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('my_auth:login')

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
        Проверяет, аутентифицирован ли пользователь.
        Если да, перенаправляет на главную страницу.
        """

        if request.user.is_authenticated:
            return redirect(reverse_lazy('task:task_view'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form) -> HttpResponse:
        """
        Обрабатывает валидную форму регистрации, создавая пользователя и профиль.
        Отправляет письмо с подтверждением.
        """
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        logger.info(f'Зарегистрировался пользователь: {user.username}')

        # Создание или получение профиля
        profile, created = Profile.objects.get_or_create(user=user)
        profile.agreement_accepted = form.cleaned_data['agreement_accepted']
        profile.save()
        logger.info(f'Создан профиль для пользователя: {user.username}')

        # Отправка письма с подтверждением
        try:
            EmailService.send_verification_email(self.request, user)
            messages.success(self.request, 'Регистрация прошла успешна! '
                                           'Проверьте вашу почту для подтверждения.')
        except Exception as e:
            messages.warning(self.request,
                             'Регистрация успешна, но не удалось отправить письмо с подтверждением. '
                             'Пожалуйста, проверьте вашу почту позже.')

        return super().form_valid(form)

    def form_invalid(self, form) -> HttpResponse:
        logger.error('Неудачная попытка регистрации: введены некоректные данные.')
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
class ProfileView(DetailView):
    """
    Класс просмотра профиля пользователя.

    Позволяет пользователю просматривать и редактировать свой профиль.
    """

    model = User
    template_name = 'profile.html'
    context_object_name = "user"

    def get_object(self, queryset=None) -> User:
        """
        Получает объект пользователя по идентификатору текущего аутентифицированного пользователя.
        Если пользователь не найден, возвращает 404.
        """

        return get_object_or_404(User, pk=self.request.user.pk)

    def get_context_data(self, **kwargs) -> dict:
        """
        Получает контекст для шаблона и добавляет форму профиля в контекст.
        """

        context = super().get_context_data(**kwargs)
        context['form'] = ProfileForm(instance=self.object.profile, user=self.object)
        return context

    def post(self, request, *args, **kwargs) -> HttpResponse:
        """
        Обрабатывает POST-запрос для обновления профиля пользователя.
        Если email изменился, отправляет новое письмо для подтверждения.
        """

        self.object = self.get_object()
        form = ProfileForm(request.POST, request.FILES, instance=self.object.profile, user=self.object)

        if form.is_valid():
            # Сохраняем старый email для сравнения
            old_email = self.object.email
            form.save()
            logger.info(f'Пользователь {self.object.username} обновил свой профиль.')

            # Проверяем, изменился ли email
            if old_email != form.instance.user.email:
                # Устанавливаем email_verified в False
                self.object.profile.email_verified = False
                self.object.profile.save()
                # Отправляем новое письмо для подтверждения email
                EmailService.send_verification_email(request, self.object)

            messages.success(request, 'Информация о профиле успешно обновлена!')
            return redirect('my_auth:profile', pk=self.object.pk)
        else:
            logger.error(f'Ошибка при обновлении профиля. {self.object.username}: {form.errors}')
            messages.error(request, 'Ошибка при обновлении профиля. Пожалуйста, проверьте введенные данные.')

        return self.get(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ChangePasswordView(View):
    """
    Класс смены пароля.

    Позволяет пользователю изменить свой пароль через AJAX-запрос.
    """

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Обрабатывает POST-запрос для изменения пароля пользователя.
        Возвращает JSON-ответ с результатом операции.
        """

        data = json.loads(request.body)  # Разбираем JSON из тела запроса
        form = PasswordChangeForm(request.user, data)  # Передаем данные в форму
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Обновляем сессию, чтобы пользователь не вышел
            logger.info(f'Пользователь {request.user.username} успешно сменил свой пароль.')
            return JsonResponse({'success': True, 'message': 'Пароль успешно изменен!'})
        else:
            logger.info(f'Неудачная попытка смены пароля у пользователя {request.user.username}.')
            return JsonResponse({'success': False, 'errors': form.errors})


@method_decorator(login_required, name='dispatch')
class ResetAvatarView(View):
    """
    Класс сброса аватарки.

    Позволяет пользователю сбросить свой аватар.
    """

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Обрабатывает POST-запрос для сброса аватарки пользователя.
        Возвращает JSON-ответ с результатом операции.
        """

        profile = request.user.profile
        profile.avatar = ''
        profile.save()
        logger.info(f'Пользователь {profile.user.username} сбросил свой аватар.')
        return JsonResponse({'success': True})


class VerifyEmailView(View):
    """
    Класс подтверждения E-mail.

    Обрабатывает запрос на подтверждение адреса электронной почты пользователя.
    """

    def get(self, request, token) -> HttpResponse:
        """
        Обрабатывает GET-запрос для подтверждения email по токену.
        Если токен действителен, активирует пользователя и перенаправляет на главную страницу.
        """

        try:
            verification = EmailVerification.objects.get(token=token)
            profile = verification.profile
            profile.email_verified = True  # Устанавливаем статус подтверждения
            profile.user.is_active = True  # Активируем пользователя
            profile.user.save()
            profile.save()
            verification.delete()  # Удаляем токен после подтверждения
            login(request, profile.user)  # Вход пользователя
            logger.info(f'Пользователь {profile.user.username} подтвердил свой E-mail.')
            return redirect('task:task_view')  # Перенаправление на главную страницу
        except EmailVerification.DoesNotExist:
            logger.warning(f'Ошибка подтверждения E-mail: неверный токен.')
            return render(request, 'verification_failed.html')


class ResendVerificationTokenView(View):
    """
    Класс повторной отправки E-mail с подтверждением.

    Позволяет пользователю запросить повторную отправку токена подтверждения на его адрес электронной почты.
    """

    def post(self, request) -> HttpResponse:
        """
        Обрабатывает POST-запрос для повторной отправки токена подтверждения.
        Если пользователь не аутентифицирован, отображает сообщение об ошибке.
        """

        if not request.user.is_authenticated:
            messages.error(request, 'Вы должны быть авторизованы для отправки токена.')
            return redirect('my_auth:login')
        try:
            user = request.user
            EmailService.send_verification_email(request, user)
            logger.info(f'Пользователь {request.user.username} отправил токен подтверждения себе на E-mail.')
            messages.success(request, 'Токен подтверждения был отправлен на ваш email.')
        except Exception as e:
            logger.info(f'Пользователь {request.user.username} не смог отправить токен подтверждения себе на E-mail.')
            messages.error(request, 'Произошла ошибка при отправке токена. Пожалуйста, попробуйте еще раз.')

        return redirect('task:task_view')


class ChangeEmailView(View):
    """
    Класс смены E-mail.

    Позволяет пользователю изменить свой адрес электронной почты и отправляет новый код подтверждения.
    """

    def post(self, request) -> HttpResponse:
        """
        Обрабатывает POST-запрос для изменения адреса электронной почты пользователя.
        Отправляет новый код подтверждения на указанный email.
        """

        new_email = request.POST.get('new_email')
        # Получаем объект User
        user = request.user
        # Обновляем адрес электронной почты у объекта User
        user.email = new_email
        user.save()  # Сохраняем изменения
        # Отправляем новый код подтверждения
        EmailService.send_verification_email(request, user)
        logger.info(f'Пользователь {request.user.username} сменил E-mail.')

        messages.success(request,
                         'Новый адрес электронной почты был установлен. '
                         'Проверьте ваш почтовый ящик для подтверждения.')
        return redirect('task:task_view')  # Перенаправляем на страницу с сообщением


class AcceptCookiesView(LoginRequiredMixin, View):
    """
    Класс, который подтверждает согласие на работу cookies.

    Позволяет пользователю подтвердить использование cookies на сайте.
    """

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Обрабатывает POST-запрос для подтверждения согласия на использование cookies.
        Возвращает JSON-ответ с результатом операции.
        """

        profile = Profile.objects.get(user=request.user)
        profile.cookies_accepted = True
        profile.save()
        logger.info(f'Пользователь {request.user.username} подтвердил согласие на использования Cookies.')
        return JsonResponse({'status': 'success'})


class CheckUsernameView(View):
    """
    Проверка username на уникальность.

    Позволяет проверить, существует ли указанный username в базе данных.
    """

    def get(self, request) -> JsonResponse:
        """
        Обрабатывает GET-запрос для проверки уникальности username.
        Возвращает JSON-ответ с результатом проверки.
        """

        username = request.GET.get('username', None)
        if username:
            exists = User.objects.filter(username=username).exists()
            logger.info(f'Попытка регистрации пользователь {username} cуществует.')
            return JsonResponse({'exists': exists})
        return JsonResponse({'exists': False})


class CheckEmailView(View):
    """
    Проверка E-mail на уникальность.

    Позволяет проверить, существует ли указанный email в базе данных.
    """

    def get(self, request) -> JsonResponse:
        """
        Обрабатывает GET-запрос для проверки уникальности email.
        Возвращает JSON-ответ с результатом проверки.
        """

        email = request.GET.get('email', None)
        if email:
            exists = User.objects.filter(email=email).exists()
            logger.info(f'Попытка регистрации пользователь с данной почтой уже существует.')
            return JsonResponse({'exists': exists})
        return JsonResponse({'exists': False})


class PasswordResetView(View):
    """
    Класс сброса пароля.

    Позволяет пользователю сбросить пароль, отправляя новый пароль на его email.
    """

    template_name = 'password_reset.html'

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
        Проверяет, аутентифицирован ли пользователь.
        Если да, перенаправляет на главную страницу.
        """

        if request.user.is_authenticated:
            return redirect(reverse_lazy('task:task_view'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request) -> HttpResponse:
        """
        Отображает форму для сброса пароля.
        """

        form = UsernameForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request) -> HttpResponse:
        """
        Обрабатывает POST-запрос для сброса пароля пользователя.
        Генерирует новый пароль и отправляет его на email пользователя.
        Если пользователь с указанным именем не найден, добавляет ошибку в форму.
        """

        form = UsernameForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                user = User.objects.get(username=username)
                new_password = PasswordGenerator.generate_random_password()
                user.set_password(new_password)
                user.save()

                # Отправка нового пароля пользователю через EmailService
                EmailService.send_new_password_email(user, new_password)
                messages.success(request,
                                 'Новый пароль был установлен и отправлен вам на почту.')
                logger.info(f'Пароль сброшен для пользователя {user.username}. Новый пароль отправлен на E-mail.')

                return redirect('my_auth:login')
            except User.DoesNotExist:
                logger.error('Неудалось сбросить пароль: Пользователь с таким именем не найден.')
                form.add_error('username', 'Пользователь с таким именем не найден.')

        return render(request, self.template_name, {'form': form})


class UpdateProfileView(LoginRequiredMixin, View):
    """
    Класс обновления профиля пользователя.

    Позволяет пользователю обновлять настройки профиля, такие как частота удаления задач.
    """

    def post(self, request) -> JsonResponse:
        """
        Обрабатывает POST-запрос для обновления настроек профиля пользователя.
        Возвращает JSON-ответ с результатом операции.
        """

        data = json.loads(request.body)
        profile = Profile.objects.get(user=request.user)

        if 'delete_frequency' in data:
            profile.delete_frequency = data['delete_frequency']
            profile.save()

            scheduler = TaskScheduler(profile)
            scheduler.schedule_deletion_tasks()

            return JsonResponse({'status': 'success', 'message': 'Частота удаления задач успешно обновлена!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Частота удаления задач не указана!'}, status=400)
