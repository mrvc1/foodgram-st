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
        self.user_client = Client()
        self.user_client.login(username='testuser', password='pass')
        self.ingredient = Ingredient.objects.create(name='Соль',
                                                    measurement_unit='г')
        self.recipe = Recipe.objects.create(
            name='Тестовый рецепт',
            text='Описание',
            cooking_time=10,
            author=self.user
        )
        self.recipe.ingredients.add(self.ingredient)

    def test_recipe_list_exists(self):
        response = self.guest_client.get('/api/recipes/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_recipe_detail_exists(self):
        response = self.guest_client.get(f'/api/recipes/{self.recipe.id}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_recipe_creation(self):
        data = {
            'name': 'Новый рецепт',
            'text': 'Описание',
            'cooking_time': 5,
            'ingredients': [{'id': self.ingredient.id, 'amount': 1}],
        }
        response = self.user_client.post('/api/recipes/', data,
                                         content_type='application/json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertTrue(Recipe.objects.filter(name='Новый рецепт').exists())

    def test_recipe_creation_unauth(self):
        data = {
            'name': 'Неавторизованный рецепт',
            'text': 'Описание',
            'cooking_time': 5,
            'ingredients': [{'id': self.ingredient.id, 'amount': 1}],
        }
        response = self.guest_client.post('/api/recipes/', data,
                                          content_type='application/json')
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_recipe_partial_update(self):
        data = {'name': 'Обновленный рецепт'}
        response = self.user_client.patch(
            f'/api/recipes/{self.recipe.id}/', data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.name, 'Обновленный рецепт')

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

    def test_download_shopping_cart_auth(self):
        self.recipe.cart_items.create(user=self.user)
        RecipeIngredientValue.objects.create(
            recipe=self.recipe, ingredient=self.ingredient, amount=2
        )
        response = self.user_client.get('/api/recipes/download_shopping_cart/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('Соль', response.content.decode())
