import string
from random import choice, randint

from django.db import models

MIN_HASH_GEN = 8
MAX_HASH_GEN = 10
MAX_HASH_LENGTH = 15
URL_MAX_LENGTH = 256


def _generate_unique_hash():
    """Генерирует уникальный хеш для короткой ссылки."""
    from .models import LinkMapped
    while True:
        new_hash = ''.join(
            choice(string.ascii_letters + string.digits)
            for _ in range(randint(MIN_HASH_GEN, MAX_HASH_GEN))
        )
        if not LinkMapped.objects.filter(url_hash=new_hash).exists():
            return new_hash


class LinkMapped(models.Model):
    """Модель коротких ссылок"""

    url_hash = models.CharField(
        max_length=MAX_HASH_LENGTH, default=_generate_unique_hash, unique=True
    )
    original_url = models.URLField(max_length=URL_MAX_LENGTH)

    class Meta:
        verbose_name = 'Ссылка'
        verbose_name_plural = 'Ссылки'

    def __str__(self):
        return f'{self.original_url} -> {self.url_hash}'
