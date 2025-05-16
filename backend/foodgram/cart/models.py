from django.contrib.auth import get_user_model
from django.db import models

from recipes.models import Recipe

User = get_user_model()


class Cart(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = '-id',
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_cart_user')
        ]
        indexes = [
            models.Index(fields=['user'], name='cart_user_idx'),
            models.Index(fields=['recipe'], name='cart_recipe_idx'),
        ]

    def __str__(self):
        return (
            f'Пользователь {self.user} добавил рецепт "{self.recipe}" '
            'в корзину'
        )
