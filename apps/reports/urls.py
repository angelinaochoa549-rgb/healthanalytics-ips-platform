from django.urls import path
from .views import exportar_csv, exportar_excel, exportar_pdf

urlpatterns = [
    path('csv/', exportar_csv, name='export-csv'),
    path('excel/', exportar_excel, name='export-excel'),
    path('pdf/', exportar_pdf, name='export-pdf'),
]