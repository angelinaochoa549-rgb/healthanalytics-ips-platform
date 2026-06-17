from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # APIs
    path('api/auth/', include('apps.authentication.urls')),
    path('api/etl/', include('apps.etl.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/ml/', include('apps.ml.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/reports/', include('apps.reports.urls')),
    # Frontend
    path('', include('apps.dashboard.frontend_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)