from django.contrib import admin
from .models import User


@admin.register(User)
class UserModel(admin.ModelAdmin):
    list_filter = ("username", "email", "password")
    list_display = ("username", "email", "password")
