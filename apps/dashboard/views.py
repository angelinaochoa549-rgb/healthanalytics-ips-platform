from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.etl.models import Paciente, ETLLog
from apps.ml.ml_engine import obtener_metricas


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    total_pacientes = Paciente.objects.count()
    ultimo_etl = ETLLog.objects.order_by('-fecha_inicio').first()
    metricas = obtener_metricas()

    return Response({
        'total_pacientes': total_pacientes,
        'etl_ejecutados': ETLLog.objects.filter(estado='completado').count(),
        'ultimo_etl': {
            'fecha': str(ultimo_etl.fecha_inicio) if ultimo_etl else None,
            'estado': ultimo_etl.estado if ultimo_etl else None,
            'registros_cargados': ultimo_etl.registros_cargados if ultimo_etl else 0,
        },
        'modelos_entrenados': list(metricas.keys()) if metricas else [],
        'mejor_accuracy': max(
            (v['accuracy'] for v in metricas.values()), default=None
        ) if metricas else None,
    })