from django.db import models
from django.contrib.auth.models import UserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone

class CustomUserManager(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError('You have not provided a valid e-mail address')

        if not username:
             raise ValueError('You have not provided a valid username')

        if not password:
            raise ValueError('You have not provided a valid password address')
     
               

        email = self.normalize_email(email)
        user = self.model(email=email, username = username, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)

        return user

    def create_user(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_super_user(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(blank=True, default = '', unique = True)
    username = models.CharField(max_length = 255, blank = True, default = '', unique = True)

    is_active = models.BooleanField(default = True)
    is_staff = models.BooleanField(default = False)
    is_superuser = models.BooleanField(default = False)

    date_joined = models.DateTimeField(default = timezone.now)
    last_login = models.DateTimeField(blank = True, null = True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def get_full_name(self):
        return self.name