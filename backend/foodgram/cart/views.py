from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import RecipeForUserSerializer
from cart.models import Cart
from recipes.models import Recipe


class CartAPI(APIView):

    permission_classes = permissions.IsAuthenticated,
    serializer_class = RecipeForUserSerializer

    def post(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if user.cart.filter(recipe=recipe).exists():
            return Response(
                {'message': 'Рецепт уже в корзине!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Cart.objects.create(user=user, recipe=recipe)
        serializer = self.serializer_class(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        cart_item = request.user.cart.filter(recipe=recipe)
        if cart_item.exists():
            cart_item.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'message': 'Рецепта в корзине нет!'},
            status=status.HTTP_400_BAD_REQUEST
        )
