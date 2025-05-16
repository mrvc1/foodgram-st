from recipes.models import RecipeIngredientValue


def create_relation_ingredient_and_value(ingredients, recipe):
    """Создает связи между рецептом и ингредиентами."""

    objects = []
    for item in ingredients:
        ingredient = item['id']
        objects.append(RecipeIngredientValue(
            recipe=recipe,
            ingredient=ingredient,
            amount=item['amount']
        ))
    RecipeIngredientValue.objects.bulk_create(objects)
