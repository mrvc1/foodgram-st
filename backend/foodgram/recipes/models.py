from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.forms import ValidationError

MIN_COOKING_TIME = MIN_AMOUNT = 1
MAX_COOKING_TIME = MAX_AMOUNT = 32_000

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        'Название ингредиента',
        max_length=128,
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=64,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        indexes = [
            models.Index(fields=['name'], name='ingredient_name_idx'),
        ]
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit',
            ),
        )

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='author_recipes',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиент',
        related_name='ingredients_recipes',
        through='RecipeIngredientValue',
    )
    image = models.ImageField(
        upload_to='recipes/',
        blank=True
    )
    name = models.CharField(
        'Название рецепта',
        max_length=256,
    )
    text = models.TextField(
        'Описание рецепта',
        blank=True
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время проготовления',
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME)
        ]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name

    def get_ingredients_list(self):
        return [
            f"{iv.ingredient.name} ({iv.amount} "
            f"{iv.ingredient.measurement_unit})"
            for iv in self.ingredient_values.select_related('ingredient')
        ]


class RecipeIngredientValue(models.Model):
    """Модель рецепта-ингредиентов."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Id ингредиента',
        related_name='recipe',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Id рецепта',
        related_name='ingredient_values',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество продукта',
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ]
    )

    def clean(self):
        if self.amount < MIN_AMOUNT or self.amount > MAX_AMOUNT:
            raise ValidationError(
                f'Количество должно быть от {MIN_AMOUNT} до {MAX_AMOUNT}.'
            )
        super().clean()

    class Meta:
        verbose_name = 'Рецепты - ингредиенты'
        verbose_name_plural = 'Рецепты - ингредиенты'
        ordering = ('recipe',)
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='not_uniq_ingredient_in_recipe'
            ),
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} – {self.amount} '
            f'{self.ingredient.measurement_unit}'
        )


class Favourite(models.Model):
    """Модель избранного."""

    user = models.ForeignKey(
        User,
        related_name='fav_recipes',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='fav_recipes',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='recipe_has_already_been_in_fav'
            ),
        ]

    def __str__(self):
        return (
            f'Пользователь {self.user} добавил рецепт '
            f'"{self.recipe}" в избранное'
        )
