from http import HTTPStatus
from django.test import Client, TestCase
from django.contrib.auth import get_user_model

from recipes.models import Recipe, Ingredient, RecipeIngredientValue

User = get_user_model()


class RecipeViewSetTestCase(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='testuser',
                                             password='pass')
        self.auth_client = Client()
        self.auth_client.login(username='testuser', password='pass')
        self.ingredient = Ingredient.objects.create(name='Тестовый ингредиент',
                                                    measurement_unit='г')
        self.recipe = Recipe.objects.create(name='Тестовый рецепт',
                                            author=self.user,
                                            cooking_time=10)
        RecipeIngredientValue.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            amount=1
        )

    def test_recipe_list_exists(self):
        response = self.guest_client.get('/api/recipes/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_recipe_detail_exists(self):
        response = self.guest_client.get(f'/api/recipes/{self.recipe.id}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_recipe_creation_unauth(self):
        data = {'name': 'NoAuth Recipe'}
        response = self.guest_client.post('/api/recipes/', data)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_get_link(self):
        response = self.guest_client.get(
            f'/api/recipes/{self.recipe.id}/get-link/'
            )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('short-link', response.json())

    def test_download_shopping_cart_unauth(self):
        response = self.guest_client.get(
            '/api/recipes/download_shopping_cart/'
        )
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


class IngredientViewSetTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.ingredient = Ingredient.objects.create(name='сахар',
                                                    measurement_unit='г')

    def test_ingredient_list(self):
        response = self.client.get('/api/ingredients/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_ingredient_search(self):
        response = self.client.get('/api/ingredients/?name=сах')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('сахар', response.content.decode())
