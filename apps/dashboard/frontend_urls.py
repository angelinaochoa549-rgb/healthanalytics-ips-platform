from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='dashboard/index.html'), name='home'),
    path('login/', TemplateView.as_view(template_name='authentication/login.html'), name='frontend-login'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard/index.html'), name='frontend-dashboard'),
    path('etl/', TemplateView.as_view(template_name='etl/index.html'), name='frontend-etl'),
    path('pacientes/', TemplateView.as_view(template_name='etl/pacientes.html'), name='frontend-pacientes'),
    path('ml/', TemplateView.as_view(template_name='dashboard/ml.html'), name='frontend-ml'),
    path('reportes/', TemplateView.as_view(template_name='reports/index.html'), name='frontend-reportes'),
    path('docs/', TemplateView.as_view(template_name='dashboard/docs.html'), name='frontend-docs'),
]