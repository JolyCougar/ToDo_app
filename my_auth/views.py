from django.shortcuts import get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from .models import Profile
from django.urls import reverse
from django.contrib.auth import login
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
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
            messages.success(self.request, 'Регистрация успешна! Проверьте вашу почту для подтверждения.')
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