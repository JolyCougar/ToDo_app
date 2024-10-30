from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProductAdmin(admin.ModelAdmin):
    """ Отображение Профиля в админке """

    list_display = "user", "bio", "avatar", "agreement_accepted"
