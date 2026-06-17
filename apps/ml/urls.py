from django.urls import path
from .views import train, predict, metricas, features_info

urlpatterns = [
    path('train/', train, name='ml-train'),
    path('predict/', predict, name='ml-predict'),
    path('metricas/', metricas, name='ml-metricas'),
    path('features/', features_info, name='ml-features'),
]