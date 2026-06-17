from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncMonth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.etl.models import Paciente


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kpis(request):
    import math
    qs = Paciente.objects.all()
    total = qs.count()
    if total == 0:
        return Response({'error': 'No hay datos. Ejecuta el ETL primero.'})

    def safe(val, decimals=1):
        if val is None:
            return 0
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return 0
        return round(f, decimals)

    return Response({
        'total_pacientes': total,
        'pacientes_criticos': qs.filter(es_critico=True).count(),
        'pacientes_hipertensos': qs.filter(presion_sistolica__gt=140).count(),
        'pacientes_diabeticos': qs.filter(glucosa__gt=126).count(),
        'pacientes_fumadores': qs.filter(fumador=True).count(),
        'pacientes_obesos': qs.filter(imc__gte=30).count(),
        'riesgo_bajo': qs.filter(riesgo_enfermedad='bajo').count(),
        'riesgo_medio': qs.filter(riesgo_enfermedad='medio').count(),
        'riesgo_alto': qs.filter(riesgo_enfermedad='alto').count(),
        'riesgo_critico': qs.filter(riesgo_enfermedad='critico').count(),
        'edad_promedio': safe(qs.aggregate(v=Avg('edad'))['v'], 1),
        'imc_promedio': safe(qs.aggregate(v=Avg('imc'))['v'], 2),
        'glucosa_promedio': safe(qs.aggregate(v=Avg('glucosa'))['v'], 1),
        'colesterol_promedio': safe(qs.aggregate(v=Avg('colesterol'))['v'], 1),
        'presion_sistolica_promedio': safe(qs.aggregate(v=Avg('presion_sistolica'))['v'], 1),
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estadisticas(request):
    qs = Paciente.objects.all()
    if not qs.exists():
        return Response({'error': 'Sin datos'})

    def stats(campo):
        vals = list(qs.values_list(campo, flat=True))
        vals = [v for v in vals if v is not None]
        if not vals:
            return {}
        return {
            'media': round(sum(vals) / len(vals), 2),
            'min': round(min(vals), 2),
            'max': round(max(vals), 2),
        }

    return Response({
        'edad': stats('edad'),
        'imc': stats('imc'),
        'glucosa': stats('glucosa'),
        'colesterol': stats('colesterol'),
        'presion_sistolica': stats('presion_sistolica'),
        'temperatura': stats('temperatura'),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def segmentacion_riesgo(request):
    qs = Paciente.objects.values('riesgo_enfermedad').annotate(
        total=Count('id')
    ).order_by('riesgo_enfermedad')
    return Response(list(qs))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def segmentacion_sexo(request):
    qs = Paciente.objects.values('sexo').annotate(total=Count('id'))
    return Response(list(qs))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def segmentacion_imc(request):
    qs = Paciente.objects.values('clasificacion_imc').annotate(
        total=Count('id')
    ).order_by('-total')
    return Response(list(qs))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def segmentacion_diagnostico(request):
    qs = Paciente.objects.values('diagnostico_preliminar').annotate(
        total=Count('id')
    ).order_by('-total')[:15]
    return Response(list(qs))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def segmentacion_edad(request):
    grupos = {
        '18-30': (18, 30),
        '31-45': (31, 45),
        '46-60': (46, 60),
        '61-75': (61, 75),
        '76+':   (76, 200),
    }
    resultado = []
    for label, (mn, mx) in grupos.items():
        count = Paciente.objects.filter(edad__gte=mn, edad__lte=mx).count()
        resultado.append({'grupo': label, 'total': count})
    return Response(resultado)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pacientes_criticos(request):
    criticos = Paciente.objects.filter(es_critico=True).values(
        'id_paciente', 'nombres', 'apellidos', 'edad', 'sexo',
        'presion_sistolica', 'glucosa', 'saturacion_oxigeno',
        'riesgo_enfermedad', 'diagnostico_preliminar', 'fecha_consulta'
    )[:100]
    return Response(list(criticos))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tendencia_consultas(request):
    qs = (Paciente.objects
          .annotate(mes=TruncMonth('fecha_consulta'))
          .values('mes')
          .annotate(total=Count('id'))
          .order_by('mes'))
    return Response([
        {'mes': str(r['mes'])[:7], 'total': r['total']}
        for r in qs if r['mes']
    ])