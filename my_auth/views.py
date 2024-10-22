from django.shortcuts import get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from .models import Profile, EmailVerification
from .services import PasswordGenerator, EmailService, TaskScheduler
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import json
from django.contrib.auth import login
from django.http import JsonResponse
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
from django.views.decorators.csrf import csrf_exempt
import hashlib
import hmac


class CustomLoginView(LoginView):
    template_name = 'login.html'

    def dispatch(self, request, *args, **kwargs):
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

    def get_context_data(self, **kwargs):
        # Получаем контекст из родительского класса
        context = super().get_context_data(**kwargs)
        # Объединяем контекст с дополнительными данными
        context.update(self.extra_context)
        return context

    def form_invalid(self, form):
        # Если форма недействительна, добавляем сообщение об ошибке
        self.extra_context['login_error'] = "Неправильное имя пользователя или пароль."
        return self.render_to_response(self.get_context_data(form=form))


class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return response


class RegisterView(CreateView):
    template_name = 'registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('my_auth:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse_lazy('task:task_view'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()

        # Создание или получение профиля
        profile, created = Profile.objects.get_or_create(user=user)
        profile.agreement_accepted = form.cleaned_data['agreement_accepted']
        profile.save()

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


@method_decorator(login_required, name='dispatch')
class ProfileView(DetailView):
    model = User
    template_name = 'profile.html'
    context_object_name = "user"

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.request.user.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ProfileForm(instance=self.object.profile, user=self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ProfileForm(request.POST, request.FILES, instance=self.object.profile, user=self.object)

        if form.is_valid():
            # Сохраняем старый email для сравнения
            old_email = self.object.email
            form.save()

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
            messages.error(request, 'Ошибка при обновлении профиля. Пожалуйста, проверьте введенные данные.')

        return self.get(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ChangePasswordView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)  # Разбираем JSON из тела запроса
        form = PasswordChangeForm(request.user, data)  # Передаем данные в форму
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Обновляем сессию, чтобы пользователь не вышел
            return JsonResponse({'success': True, 'message': 'Пароль успешно изменен!'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})


@method_decorator(login_required, name='dispatch')
class ResetAvatarView(View):
    def post(self, request, *args, **kwargs):
        profile = request.user.profile
        profile.avatar = ''
        profile.save()
        return JsonResponse({'success': True})


class VerifyEmailView(View):
    def get(self, request, token):
        try:
            verification = EmailVerification.objects.get(token=token)
            profile = verification.profile
            profile.email_verified = True  # Устанавливаем статус подтверждения
            profile.user.is_active = True  # Активируем пользователя
            profile.user.save()
            profile.save()
            verification.delete()  # Удаляем токен после подтверждения
            login(request, profile.user)  # Вход пользователя
            return redirect('task:task_view')  # Перенаправление на главную страницу
        except EmailVerification.DoesNotExist:
            return render(request, 'verification_failed.html')


class ResendVerificationTokenView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            messages.error(request, 'Вы должны быть авторизованы для отправки токена.')
            return redirect('my_auth:login')
        try:
            user = request.user
            EmailService.send_verification_email(request, user)
            messages.success(request, 'Токен подтверждения был отправлен на ваш email.')
        except Exception as e:
            messages.error(request, 'Произошла ошибка при отправке токена. Пожалуйста, попробуйте еще раз.')

        return redirect('task:task_view')


class ChangeEmailView(View):
    def post(self, request):
        new_email = request.POST.get('new_email')
        # Получаем объект User
        user = request.user
        # Обновляем адрес электронной почты у объекта User
        user.email = new_email
        user.save()  # Сохраняем изменения
        # Отправляем новый код подтверждения
        EmailService.send_verification_email(request, user)

        messages.success(request,
                         'Новый адрес электронной почты был установлен. '
                         'Проверьте ваш почтовый ящик для подтверждения.')
        return redirect('task:task_view')  # Перенаправляем на страницу с сообщением


class AcceptCookiesView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        profile = Profile.objects.get(user=request.user)
        profile.cookies_accepted = True
        profile.save()
        return JsonResponse({'status': 'success'})


class CheckUsernameView(View):
    def get(self, request):
        username = request.GET.get('username', None)
        if username:
            exists = User.objects.filter(username=username).exists()
            return JsonResponse({'exists': exists})
        return JsonResponse({'exists': False})


class CheckEmailView(View):
    def get(self, request):
        email = request.GET.get('email', None)
        if email:
            exists = User.objects.filter(email=email).exists()
            return JsonResponse({'exists': exists})
        return JsonResponse({'exists': False})


class PasswordResetView(View):
    template_name = 'password_reset.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse_lazy('task:task_view'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = UsernameForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
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

                return redirect('my_auth:login')  # Путь к странице с сообщением об успешной отправке
            except User.DoesNotExist:
                form.add_error('username', 'Пользователь с таким именем не найден.')

        return render(request, self.template_name, {'form': form})


class UpdateProfileView(LoginRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body)
        profile = Profile.objects.get(user=request.user)

        if 'delete_frequency' in data:
            profile.delete_frequency = data['delete_frequency']
            profile.save()

            # Создайте экземпляр TaskScheduler и обновите расписание
            scheduler = TaskScheduler(profile)
            scheduler.schedule_deletion_tasks()

            return JsonResponse({'status': 'success', 'message': 'Частота удаления задач успешно обновлена!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Частота удаления задач не указана!'}, status=400)


class TelegramAuthView(View):
    def post(self, request):
        # Получаем данные из POST-запроса
        user_id = request.POST.get('user_id')
        telegram_id = request.POST.get('telegram_id')
        telegram_username = request.POST.get('telegram_username')

        if user_id and telegram_id:
            try:
                # Обновите профиль пользователя
                profile = Profile.objects.get(id=user_id)
                profile.telegram_user_id = telegram_id
                profile.telegram_username = telegram_username
                profile.save()

                return JsonResponse({'status': 'success', 'message': 'Профиль успешно обновлен.'})
            except Profile.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Профиль не найден.'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': 'Недостаточно данных.'}, status=400)


class CSRFTokenView(View):
    def get(self, request):
        token = get_token(request)
        return JsonResponse({'csrfToken': token})


class UnsubscribeView(View):
    def post(self, request, *args, **kwargs):
        profile = get_object_or_404(Profile, user=request.user)

        # Очищаем поля
        profile.telegram_user_id = None
        profile.telegram_username = None
        profile.save()

        return JsonResponse({'message': 'Вы успешно отписались!'})
