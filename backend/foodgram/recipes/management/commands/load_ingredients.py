import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient  # Импорт модели ингредиентов

class Command(BaseCommand):
    help = 'Load ingredients from JSON file'

    def handle(self, *args, **kwargs):
        with open('ingredients.json', 'r', encoding='utf-8') as file:
            data = json.load(file)  # загружаем список словарей

        for item in data:
            ingredient, created = Ingredient.objects.get_or_create(
                name=item['name'],
                defaults={'measurement_unit': item['measurement_unit']}
            )
            if created:
                self.stdout.write(f"Added ingredient: {ingredient.name}")
            else:
                self.stdout.write(f"Ingredient already exists: {ingredient.name}")

