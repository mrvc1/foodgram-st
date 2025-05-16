from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from api.views import RedirectToRecipeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:hashed_id>/', RedirectToRecipeView.as_view(),
         name='short-link'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
