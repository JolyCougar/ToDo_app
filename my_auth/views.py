from django.shortcuts import get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from .models import Profile
from django.contrib.auth import login
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, DetailView
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import UserRegistrationForm, ProfileForm
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from .models import EmailVerification
from .services import EmailService


class CustomLoginView(LoginView):
    template_name = 'login.html'


class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return response



class RegisterView(CreateView):
    template_name = 'registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('my_auth:login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()

        # Создание или получение профиля
        profile, created = Profile.objects.get_or_create(user=user)

        # Отправка письма с подтверждением
        EmailService.send_verification_email(self.request, user)  # Передаем user, а не profile

        messages.success(self.request, 'Регистрация успешна! Проверьте вашу почту для подтверждения.')
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
            form.save()
            messages.success(request, 'Информация о профиле успешно обновлена!')
            return redirect('my_auth:profile', pk=self.object.pk)
        else:
            messages.error(request, 'Ошибка при обновлении профиля. Пожалуйста, проверьте введенные данные.')
        return self.get(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ChangePasswordView(View):
    def post(self, request, *args, **kwargs):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Обновляем сессию, чтобы пользователь не вышел
            return JsonResponse({'success': True, 'message': 'Пароль успешно изменен!'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})


@method_decorator(login_required, name='dispatch')
class ResetAvatarView(View):
    def post(self, request, *args, **kwargs):
        profile = request.user.profile  # Получаем профиль текущего пользователя
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
            return redirect('/')  # Перенаправление на главную страницу
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
            logger.error(f'Ошибка при отправке токена: {e}')  # Логируем ошибку
            messages.error(request, 'Произошла ошибка при отправке токена. Пожалуйста, попробуйте еще раз.')

        return redirect('task:task_view')

class ChangeEmailView(View):
    def post(self, request):
        new_email = request.POST.get('new_email')
        profile = request.user.profile  # Предполагается, что у пользователя есть профиль

        # Обновляем адрес электронной почты в профиле
        profile.user.email = new_email
        profile.user.save()

        # Отправляем новый код подтверждения
        EmailService.send_verification_email(request, profile)

        messages.success(request, 'Новый адрес электронной почты был установлен. Проверьте ваш почтовый ящик для подтверждения.')
        return redirect('task:task_view')  # Перенаправляем на страницу с сообщением