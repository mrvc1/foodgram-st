from django.contrib import admin

from recipes.models import (Ingredient, Recipe,
                            RecipeIngredientValue, Favourite)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'measurement_unit'
    )
    search_fields = ('name',)


class RecipeIngredientValueAdmin(admin.TabularInline):
    model = RecipeIngredientValue


class FavouriteInline(admin.TabularInline):
    model = Favourite


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'author', 'get_favorite_count'
    )
    inlines = [RecipeIngredientValueAdmin]
    list_filter = ('name', 'author__username')
    search_fields = ('name', 'author__username')

    @admin.display(description='В избранном')
    def get_favorite_count(self, obj):
        return obj.fav_recipes.count()
