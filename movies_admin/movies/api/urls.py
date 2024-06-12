from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('v1/', include('movies.api.v1.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
