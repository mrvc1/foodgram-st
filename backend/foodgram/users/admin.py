from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from recipes.admin import FavouriteInline
from users.models import User, UserFollow


class UserFollowAdmin(admin.TabularInline):
    model = UserFollow
    fk_name = 'user'


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        'username', 'id', 'email', 'first_name',
        'last_name'
    )
    list_filter = ('email', 'username')
    search_fields = ('email', 'username')
    inlines = (FavouriteInline, UserFollowAdmin)
