from django.urls import path
from .views import run_etl, etl_log_detail, etl_logs, pacientes_list, paciente_detail, upload_csv

urlpatterns = [
    path('run/', run_etl, name='etl-run'),
    path('upload/', upload_csv, name='etl-upload'),
    path('logs/', etl_logs, name='etl-logs'),
    path('logs/<int:log_id>/', etl_log_detail, name='etl-log-detail'),
    path('pacientes/', pacientes_list, name='pacientes-list'),
    path('pacientes/<int:pk>/', paciente_detail, name='paciente-detail'),
]