from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from api.pagination import CustomPagination

from api.serializers import UserSerializer
from users.serializers import (ChangePasswordSerializer, UserCreateSerializer,
                               UserSubscriptionsSerializer, AvatarSerializer,
                               SubscriptionCreateSerializer)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'subscriptions':
            return UserSubscriptionsSerializer
        if self.action == 'set_password':
            return ChangePasswordSerializer
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    @action(
        methods=('get',),
        detail=False,
        serializer_class=UserSubscriptionsSerializer,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Возвращает подписки с рецептами."""

        subscriptions = User.objects.filter(followers__user=request.user)
        page = self.paginate_queryset(subscriptions)
        recipes_limit = request.query_params.get('recipes_limit')
        serializer = self.get_serializer(
            page,
            many=True,
            context={
                'request': request,
                'recipes_limit': recipes_limit
            }
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, pk=None):
        """Подписаться на пользователя или отписаться."""
        return Response(
            {'detail': 'Метод GET не поддерживается для этого эндпоинта.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @subscribe.mapping.post
    def subscribe_post(self, request, pk=None):
        author = get_object_or_404(User, id=pk)
        serializer = SubscriptionCreateSerializer(
            data={'following': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        recipes_limit = request.query_params.get('recipes_limit')
        response_serializer = UserSubscriptionsSerializer(
            author,
            context={
                'request': request,
                'recipes_limit': recipes_limit
            }
        )
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def subscribe_delete(self, request, pk=None):
        """Отписаться от пользователя."""
        user = request.user
        author = get_object_or_404(User, id=pk)

        deleted, _ = user.following.filter(following=author).delete()
        if not deleted:
            return Response({'detail': 'Подписка не найдена.'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def me(self, request):
        """Возвращает текущего пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['put', 'delete'],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Обновление или удаление аватара текущего пользователя."""
        user = request.user

        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user, data=request.data, partial=False,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': serializer.data.get('avatar')},
                status=status.HTTP_200_OK
            )

        if request.method == 'DELETE':
            if not user.avatar:
                return Response(
                    {'detail': 'У пользователя нет аватара для удаления.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user.avatar.name.startswith('data:image'):
                user.avatar = ''
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post'],
        detail=False,
        serializer_class=ChangePasswordSerializer,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def set_password(self, request):
        """Изменение пароля текущего пользователя."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(
                serializer.validated_data['current_password']):
            return Response({'detail': 'Текущий пароль неверен.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if serializer.validated_data['current_password'] == \
                serializer.validated_data['new_password']:
            return Response(
                {'detail': 'Новый пароль не может совпадать с текущим.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
