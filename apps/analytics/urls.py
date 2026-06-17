from django.urls import path
from .views import (
    kpis, estadisticas, segmentacion_riesgo,
    segmentacion_sexo, segmentacion_imc,
    segmentacion_diagnostico, segmentacion_edad,
    pacientes_criticos, tendencia_consultas,
)

urlpatterns = [
    path('kpis/', kpis, name='kpis'),
    path('estadisticas/', estadisticas, name='estadisticas'),
    path('riesgo/', segmentacion_riesgo, name='riesgo'),
    path('sexo/', segmentacion_sexo, name='sexo'),
    path('imc/', segmentacion_imc, name='imc'),
    path('diagnostico/', segmentacion_diagnostico, name='diagnostico'),
    path('edad/', segmentacion_edad, name='edad'),
    path('criticos/', pacientes_criticos, name='criticos'),
    path('tendencia/', tendencia_consultas, name='tendencia'),
]