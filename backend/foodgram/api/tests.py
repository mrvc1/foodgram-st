from http import HTTPStatus
from django.test import Client, TestCase
from django.contrib.auth import get_user_model

from recipes.models import Recipe, Ingredient, Favourite, RecipeIngredientValue

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

    def test_recipe_partial_update(self):
        data = {'name': 'Updated name'}
        response = self.auth_client.patch(
            f'/api/recipes/{self.recipe.id}/', data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.name, 'Updated name')

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
        response = self.auth_client.get('/api/recipes/download_shopping_cart/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('Test Ingredient', response.content.decode())


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


class FavouritesViewSetTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='favuser',
                                             password='pass')
        self.auth_client = Client()
        self.auth_client.login(username='favuser', password='pass')
        self.ingredient = Ingredient.objects.create(name='соль',
                                                    measurement_unit='г')
        self.recipe = Recipe.objects.create(name='Fav Recipe',
                                            author=self.user,
                                            cooking_time=10,
                                            )
        RecipeIngredientValue.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            amount=1
        )

    def test_add_to_favourites(self):
        url = f'/api/recipes/{self.recipe.id}/favourite/'
        response = self.auth_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertTrue(Favourite.objects.filter(recipe=self.recipe,
                                                 user=self.user).exists())

    def test_add_to_favourites_twice(self):
        url = f'/api/recipes/{self.recipe.id}/favourite/'
        self.auth_client.post(url)
        response = self.auth_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_remove_from_favourites(self):
        url = f'/api/recipes/{self.recipe.id}/favourite/'
        self.auth_client.post(url)
        response = self.auth_client.delete(url)
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(Favourite.objects.filter(recipe=self.recipe,
                                                  user=self.user).exists())

    def test_remove_nonexistent_from_favourites(self):
        url = f'/api/recipes/{self.recipe.id}/favourite/'
        response = self.auth_client.delete(url)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
