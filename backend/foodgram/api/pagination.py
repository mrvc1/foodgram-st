from rest_framework import pagination


class CustomPagination(pagination.PageNumberPagination):
    """Кастомный класс пагинации."""

    page_size = 6
    page_size_query_param = 'limit'
