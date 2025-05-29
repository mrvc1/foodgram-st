from django.contrib.auth import get_user_model
from django.core.validators import MaxLengthValidator, RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from api.serializers import RecipeForUserSerializer, Base64ImageField
from users.models import UserFollow

EMAIL_MAX_LENGTH = 254
USER_MAX_LENGTH = 150
MESSAGE = 'Длина имени не должна превышать 150 символов.'

User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'password'
        )
        extra_kwargs = {
            'email': {
                'required': True,
                'validators': [
                    UniqueValidator(queryset=User.objects.all()),
                    MaxLengthValidator(
                        EMAIL_MAX_LENGTH,
                        message='Длина почты не должна превышать 254 символов.'
                    ),
                ]
            },
            'username': {
                'required': True,
                'validators': [
                    UniqueValidator(queryset=User.objects.all()),
                    MaxLengthValidator(
                        USER_MAX_LENGTH,
                        message=MESSAGE
                    ),
                    RegexValidator(
                        regex=r'^[\w.@+-]+\Z',
                        message='Неверный формат имени.'
                    )
                ]
            },
            'first_name': {
                'required': True,
                'validators': [
                    MaxLengthValidator(
                        USER_MAX_LENGTH,
                        message=MESSAGE
                    )
                ]
            },
            'last_name': {
                'required': True,
                'validators': [
                    MaxLengthValidator(
                        USER_MAX_LENGTH,
                        message=(
                            'Длина фамилии не должна превышать 150 символов.'
                        )
                    )
                ]
            },
            'password': {
                'required': True,
                'write_only': True,
            }
        }

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserSubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок пользователя"""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )
        read_only_fields = ('__all__',)

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.author_recipes.all()
        limit = request.query_params.get('recipes_limit')

        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]

        return RecipeForUserSerializer(recipes, many=True,
                                       context={'request': request}).data

    def get_recipes_count(self, obj):
        return obj.author_recipes.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user if request else None

        if user and not user.is_anonymous:
            return user.following.filter(following=obj).exists()
        return False


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFollow
        fields = ('user', 'following')
        read_only_fields = ('user',)

    def validate(self, data):
        user = self.context['request'].user
        following = data['following']
        if user == following:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!'
            )
        if user.following.filter(following=following).exists():
            raise serializers.ValidationError('Подписка уже оформлена!')
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ChangePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(
        required=True,
        validators=[
            MaxLengthValidator(
                USER_MAX_LENGTH,
                message='Длина пароля не должна превышать 150 символов.'
            ),
        ]
    )
    current_password = serializers.CharField(
        required=True,
        validators=[
            MaxLengthValidator(
                USER_MAX_LENGTH,
                message='Длина пароля не должна превышать 150 символов.'
            ),
        ]
    )

    class Meta:
        model = User
        fields = (
            'new_password', 'current_password'
        )

    def validate(self, data):
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError(
                'Новый пароль не может совпадать с текущим.')
        return data
