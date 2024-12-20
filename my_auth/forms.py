from .models import Profile
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class UserRegistrationForm(forms.ModelForm):
    """
    Форма регистрации нового пользователя.

    Позволяет пользователю ввести данные для регистрации, включая имя,
    email, пароль и согласие с лицензионным соглашением.
    """

    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Подтвердите пароль")
    agreement_accepted = forms.BooleanField(required=True, label="Я согласен с лицензионным соглашением")

    class Meta:
        model = User
        fields = ['first_name', 'username', 'email', 'password', 'confirm_password', 'agreement_accepted']

    def clean_username(self) -> str:
        """
        Проверяет уникальность имени пользователя.

        Raises:
            ValidationError: Если имя пользователя уже существует.
        """

        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Пользователь с таким именем уже существует.")
        return username

    def clean_email(self) -> str:
        """
        Проверяет уникальность email.

        Raises:
            ValidationError: Если email уже существует.
        """

        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean(self) -> dict:
        """
        Проверяет, совпадают ли пароли.

        Raises:
            ValidationError: Если пароли не совпадают.
        """

        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Пароли не совпадают!")

        return cleaned_data

    def save(self, commit=True) -> User:
        """
        Сохраняет пользователя и профиль.

        Args:
            commit (bool): Если True, сохраняет изменения в базе данных.

        Returns:
            User: Сохраненный объект пользователя.
        """

        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Устанавливаем зашифрованный пароль
        if commit:
            user.save()
            # Сохранение согласия с лицензионным соглашением в профиле
            profile, created = Profile.objects.get_or_create(user=user)
            profile.agreement_accepted = self.cleaned_data['agreement_accepted']
            profile.save()
        return user


class ProfileForm(forms.ModelForm):
    """
    Форма профиля.

    Позволяет пользователю редактировать информацию о своем профиле,
    включая биографию и аватар.
    """

    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = Profile
        fields = ['bio', 'avatar']  # Поля из модели Profile

    def __init__(self, *args, **kwargs) -> None:
        """
        Инициализирует форму, устанавливая начальные значения для полей имени,
        фамилии и email из объекта пользователя.
        """
        user = kwargs.pop('user', None)  # Получаем пользователя из аргументов
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True) -> User:
        """
        Сохраняет изменения в объекте пользователя и профиля.

        Args:
            commit (bool): Если True, сохраняет изменения в базе данных.

        Returns:
            User: Сохраненный объект пользователя.
        """

        user = self.instance.user  # Получаем объект User
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()  # Сохраняем объект User
            self.instance.save()  # Сохраняем объект Profile
        return user


class UsernameForm(forms.Form):
    """
    Форма для ввода имени пользователя.

    Используется для сброса пароля.
    """

    username = forms.CharField(
        max_length=150,
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите ваше имя пользователя',
            'class': 'form-control'
        })
    )
