import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, ValidationError
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.reverse import reverse
from api.utils import create_relation_ingredient_and_value
from recipes.models import Favourite, Ingredient, Recipe, RecipeIngredientValue
from cart.models import Cart
from shortener.models import LinkMapped


MIN_COOKING_TIME = MIN_AMOUNT = 1
MAX_COOKING_TIME = MAX_AMOUNT = 32_000


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            if data.startswith('data:image'):
                try:
                    format, imgstr = data.split(';base64,')
                    ext = format.split('/')[-1]
                    data = ContentFile(base64.b64decode(imgstr),
                                       name=f'temp.{ext}')
                except Exception:
                    raise serializers.ValidationError('Invalid image format.')
            elif data.startswith('data:'):
                raise serializers.ValidationError(
                    'Only image uploads are supported.'
                )
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = 'id', 'name', 'measurement_unit'
        read_only_fields = ('__all__',)


class IngredientCreateSerializer(serializers.Serializer):
    """Сериализатор для ингредиентов при создании рецепта."""

    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        max_value=MAX_AMOUNT, min_value=MIN_AMOUNT
    )


class RecipeForUserSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов эндпоинта подписок."""

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'cooking_time'
        )
        read_only_fields = ('__all__',)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода автора-владельца рецепта."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed', 'avatar'
        )
        read_only_fields = ('__all__',)

    def get_is_subscribed(self, obj):
        """Возвращает True, если текущий пользователь подписан на obj."""
        user = self.context['request'].user
        if user.is_anonymous or user == obj:
            return False
        return user.following.filter(following=obj).exists()


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра списка рецептов или рецепта."""

    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )
        read_only_fields = ('__all__',)

    def get_ingredients(self, obj):
        """Получение поля ингредиентов с количеством."""
        ingredients = RecipeIngredientValue.objects.filter(
            recipe=obj
        ).select_related('ingredient')

        return [
            {
                'id': item.ingredient.id,
                'name': item.ingredient.name,
                'measurement_unit': item.ingredient.measurement_unit,
                'amount': item.amount
            }
            for item in ingredients
        ]

    def get_is_favorited(self, obj):
        """Проверка, находится ли рецепт в избранном."""
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favourite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверка, находится ли рецепт в корзине."""
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Cart.objects.filter(user=user, recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""

    image = Base64ImageField()
    ingredients = IngredientCreateSerializer(many=True,)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME, max_value=MAX_COOKING_TIME
    )
    text = serializers.CharField(required=True, allow_blank=False)
    name = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=('name', 'ingredients')
            )
        ]

    def validate(self, attrs):
        ingredients = self.initial_data.get('ingredients', [])

        if not ingredients:
            raise ValidationError(
                'Необходимо указать хотя бы один ингредиент!')

        ingredient_ids = {ingredient['id'] for ingredient in ingredients}
        if len(ingredient_ids) != len(ingredients):
            raise ValidationError('Ингредиенты не должны повторяться!')

        unknown_fields = set(self.initial_data.keys()) - set(self.fields.keys()
                                                             )
        if unknown_fields:
            raise ValidationError(
                f"Недопустимые поля: {', '.join(unknown_fields)}"
            )

        return attrs

    def validate_name(self, value):
        if len(value) > 256:
            raise ValidationError(
                'Длина поля "name" не должна превышать 256 символов.'
            )
        return value

    def create(self, validated_data):
        """Создание рецепта."""
        return self._save_recipe(validated_data)

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        return self._save_recipe(validated_data, instance)

    def _save_recipe(self, validated_data, instance=None):
        ingredients = validated_data.pop('ingredients', [])

        if instance:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.ingredients.clear()
            instance.save()
        else:
            instance = Recipe.objects.create(**validated_data)

        create_relation_ingredient_and_value(ingredients,
                                             recipe=instance)
        return instance


class FavouriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных рецептов."""

    id = serializers.IntegerField(source='recipe.id')
    name = serializers.CharField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image')
    cooking_time = serializers.IntegerField(source='recipe.cooking_time')

    class Meta:
        model = Favourite
        fields = (
            'id', 'name', 'image', 'cooking_time',
        )
        read_only_fields = ('__all__',)


class ShortenerSerializer(serializers.ModelSerializer):
    """Сериализатор коротких ссылок"""

    class Meta:
        model = LinkMapped
        fields = ('original_url',)
        write_only_fields = ('original_url',)

    def get_short_link(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(
            reverse('shortener:load_url', args=[obj.url_hash])
        )

    def create(self, validated_data):
        instance, _ = LinkMapped.objects.get_or_create(**validated_data)
        return instance

    def to_representation(self, instance):
        return {'short-link': self.get_short_link(instance)}
