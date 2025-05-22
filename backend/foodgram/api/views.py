from django.contrib.auth import get_user_model
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from hashids import Hashids

from .pagination import CustomPagination
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (FavouriteSerializer, IngredientSerializer,
                             RecipeReadSerializer, RecipeWriteSerializer)
from recipes.models import (Favourite, Ingredient, Recipe,
                            RecipeIngredientValue)

User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    """Получить список или рецепт с возможностью редактирования и удаления."""

    queryset = Recipe.objects.prefetch_related('ingredients')
    serializer_class = RecipeWriteSerializer
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = CustomPagination

    def get_queryset(self):
        filters = {}

        author = self.request.query_params.get('author')
        if author:
            filters['author'] = author

        if not self.request.user.is_anonymous:
            if self.request.query_params.get('is_favorited') == '1':
                filters['fav_recipes__user'] = self.request.user
            if self.request.query_params.get('is_in_shopping_cart') == '1':
                filters['cart_items__user'] = self.request.user

        return self.queryset.filter(**filters).distinct()

    def get_serializer_class(self):
        """Получить сериализатор в зафисимости от метода запроса."""

        if self.action == 'list' or self.action == 'retrieve':
            return RecipeReadSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        """Создать рецепт."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save(author=self.request.user)
        return Response(
            RecipeReadSerializer(result, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def partial_update(self, request, *args, **kwargs):
        """Редактировать рецепт."""

        recipe = self.get_object()
        self.check_object_permissions(request, recipe)
        serializer = self.get_serializer(instance=recipe, data=request.data,
                                         partial=True)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(
            RecipeReadSerializer(result, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[permissions.AllowAny],
    )
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""

        recipe = self.get_object()
        hashids = Hashids(salt="your_secret_salt", min_length=6)
        hashed_id = hashids.encode(recipe.id)

        base_url = request.build_absolute_uri('/')
        short_link = f"{base_url}s/{hashed_id}"

        return Response(
            {"short-link": short_link},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
        methods=['get'],
    )
    def download_shopping_cart(self, request):
        """Загрузить файл со списком покупок."""
        user = request.user

        ingredients = RecipeIngredientValue.objects.filter(
            recipe__in=Recipe.objects.filter(cart_items__user=user)
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

        shopping_list = [
            (
                f"• {ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) — "
                f"{ingredient['total_amount']}"
            )
            for ingredient in ingredients
        ]

        filename = f'{user.username}_shopping_list.txt'
        response = HttpResponse(
            '\n'.join(shopping_list), content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Возвращает ингредиент или список ингредиентов. """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        name = self.request.query_params.get('name')
        queryset = super().get_queryset()
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset.distinct()


class FavouritesViewSet(generics.CreateAPIView, generics.DestroyAPIView):
    """Получить рецепт, добавленный в избранное или удалить его."""

    queryset = Favourite.objects.all()
    serializer_class = FavouriteSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = None

    def post(self, request, *args, **kwargs):
        """Добавить рецепт в избранное."""
        recipe = get_object_or_404(Recipe, pk=self.kwargs['pk'])
        user = request.user

        if user.fav_recipes.filter(recipe=recipe).exists():
            return Response({'message': 'Рецепт уже добавлен!'},
                            status=status.HTTP_400_BAD_REQUEST)

        favourite = Favourite.objects.create(recipe=recipe, user=user)
        serializer = FavouriteSerializer(favourite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """Удалить рецепт из избранного."""

        recipe = get_object_or_404(Recipe, pk=self.kwargs['pk'])
        deleted, _ = request.user.fav_recipes.filter(recipe=recipe).delete()

        if not deleted:
            return Response({'message': 'Рецепта нет!'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)
