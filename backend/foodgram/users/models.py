from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

ADMIN = 'admin'
USER = 'user'
ROLE_CHOICES = [
    (USER, 'User'),
    (ADMIN, 'Admin'),
]
ROLE_MAX_LENGTH = 10


class UserManager(BaseUserManager):

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('Поле "username" обязательно для заполнения.')
        if not email:
            raise ValueError('Поле "email" обязательно для заполнения.')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            raise ValueError('Поле "password" обязательно для заполнения.')
        user.save(using=self._db)
        return user

    def create_superuser(
        self, username, email=None, password=None, **extra_fields
    ):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(username, email, password, **extra_fields)

    def __str__(self):
        return f'UserManager for {self.model.__name__}'


class User(AbstractUser):

    avatar = models.ImageField(
        'Аватар', upload_to='users/', blank=True, null=True
    )

    role = models.CharField(
        max_length=ROLE_MAX_LENGTH,
        choices=ROLE_CHOICES,
        default=USER,
    )

    @property
    def is_admin(self):
        return (
            self.role == ADMIN
            or self.is_superuser
            or self.is_staff
        )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        indexes = [
            models.Index(fields=['email'], name='email_idx'),
            models.Index(fields=['username'], name='username_idx'),
        ]
        ordering = ['id']

    def __str__(self):
        return self.username

    def clean(self):
        if not self.email:
            raise ValidationError('Поле "email" обязательно для заполнения.')
        if not self.username:
            raise ValidationError(
                'Поле "username" обязательно для заполнения.')
        super().clean()


class UserFollow(models.Model):

    user = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        User,
        related_name='followers',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписки'
        verbose_name_plural = 'Подписки'
        ordering = ['user', 'following']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='subscription_has_already_been_issued'
            ),
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.following}'

    def save(self, *args, **kwargs):
        if self.user == self.following:
            raise ValidationError('Нельзя подписываться на самого себя!')
        if self.user.following.filter(following=self.following).exists():
            raise ValidationError('Подписка уже существует.')
        super().save(*args, **kwargs)
