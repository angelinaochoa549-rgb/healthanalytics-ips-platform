import threading
from pathlib import Path

from django.conf import settings
from rest_framework import generics, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import ETLLog, Paciente
from .pipeline import ETLPipeline


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_etl(request):
    log = ETLLog.objects.create(usuario=request.user)
    pipeline = ETLPipeline(log)

    def _run():
        pipeline.run()

    thread = threading.Thread(target=_run)
    thread.start()

    return Response({
        'message': 'ETL iniciado',
        'log_id': log.id,
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_csv(request):
    try:
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({'error': 'No se recibió archivo'}, status=status.HTTP_400_BAD_REQUEST)
        if not archivo.name.endswith('.csv'):
            return Response({'error': 'Solo se aceptan archivos CSV'}, status=status.HTTP_400_BAD_REQUEST)

        datasets_dir = Path(settings.DATASETS_DIR)
        datasets_dir.mkdir(parents=True, exist_ok=True)
        dest = datasets_dir / 'upload_manual.csv'

        with open(dest, 'wb') as f:
            for chunk in archivo.chunks():
                f.write(chunk)

        log = ETLLog.objects.create(usuario=request.user, archivo_fuente=str(dest))
        pipeline = ETLPipeline(log)

        def _run():
            pipeline.run(archivo=str(dest))

        thread = threading.Thread(target=_run)
        thread.start()

        return Response({
            'message': 'Archivo recibido. ETL ejecutándose.',
            'log_id': log.id,
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def etl_log_detail(request, log_id):
    try:
        log = ETLLog.objects.get(id=log_id)
        return Response({
            'id': log.id,
            'estado': log.estado,
            'registros_extraidos': log.registros_extraidos,
            'registros_transformados': log.registros_transformados,
            'registros_cargados': log.registros_cargados,
            'registros_duplicados': log.registros_duplicados,
            'registros_invalidos': log.registros_invalidos,
            'tiempo_ejecucion': log.tiempo_ejecucion,
            'archivo_fuente': log.archivo_fuente,
            'log_detalle': log.log_detalle,
            'error_mensaje': log.error_mensaje,
            'fecha_inicio': log.fecha_inicio,
            'fecha_fin': log.fecha_fin,
            'duracion': f"{log.tiempo_ejecucion:.2f}s" if log.tiempo_ejecucion else None,
            'usuario_nombre': log.usuario.username if log.usuario else None,
        })
    except ETLLog.DoesNotExist:
        return Response({'error': 'Log no encontrado'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def etl_logs(request):
    logs = ETLLog.objects.all()[:20]
    data = []
    for log in logs:
        data.append({
            'id': log.id,
            'estado': log.estado,
            'registros_extraidos': log.registros_extraidos,
            'registros_cargados': log.registros_cargados,
            'registros_duplicados': log.registros_duplicados,
            'tiempo_ejecucion': log.tiempo_ejecucion,
            'duracion': f"{log.tiempo_ejecucion:.2f}s" if log.tiempo_ejecucion else None,
            'fecha_inicio': log.fecha_inicio,
            'usuario_nombre': log.usuario.username if log.usuario else None,
        })
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pacientes_list(request):
    search = request.GET.get('search', '')
    riesgo = request.GET.get('riesgo', '')
    page = int(request.GET.get('page', 1))
    page_size = 50

    qs = Paciente.objects.all()

    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(nombres__icontains=search) |
            Q(apellidos__icontains=search) |
            Q(diagnostico_preliminar__icontains=search)
        )
    if riesgo:
        qs = qs.filter(riesgo_enfermedad=riesgo)

    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size
    qs = qs[start:end]

    data = []
    for p in qs:
        data.append({
            'id': p.id,
            'id_paciente': p.id_paciente,
            'nombres': p.nombres,
            'apellidos': p.apellidos,
            'edad': p.edad,
            'sexo': p.sexo,
            'imc': p.imc,
            'clasificacion_imc': p.clasificacion_imc,
            'presion_sistolica': p.presion_sistolica,
            'glucosa': p.glucosa,
            'riesgo_enfermedad': p.riesgo_enfermedad,
            'diagnostico_preliminar': p.diagnostico_preliminar,
            'es_critico': p.es_critico,
            'fecha_consulta': p.fecha_consulta,
        })

    return Response({
        'count': total,
        'results': data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def paciente_detail(request, pk):
    try:
        p = Paciente.objects.get(pk=pk)
        return Response({
            'id': p.id,
            'id_paciente': p.id_paciente,
            'nombres': p.nombres,
            'apellidos': p.apellidos,
            'edad': p.edad,
            'sexo': p.sexo,
            'peso': p.peso,
            'altura': p.altura,
            'imc': p.imc,
            'clasificacion_imc': p.clasificacion_imc,
            'presion_sistolica': p.presion_sistolica,
            'presion_diastolica': p.presion_diastolica,
            'frecuencia_cardiaca': p.frecuencia_cardiaca,
            'glucosa': p.glucosa,
            'colesterol': p.colesterol,
            'saturacion_oxigeno': p.saturacion_oxigeno,
            'temperatura': p.temperatura,
            'antecedentes_familiares': p.antecedentes_familiares,
            'fumador': p.fumador,
            'consumo_alcohol': p.consumo_alcohol,
            'actividad_fisica': p.actividad_fisica,
            'diagnostico_preliminar': p.diagnostico_preliminar,
            'riesgo_enfermedad': p.riesgo_enfermedad,
            'es_critico': p.es_critico,
            'fecha_consulta': p.fecha_consulta,
        })
    except Paciente.DoesNotExist:
        return Response({'error': 'Paciente no encontrado'}, status=status.HTTP_404_NOT_FOUND)