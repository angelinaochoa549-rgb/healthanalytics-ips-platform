import threading
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .ml_engine import entrenar_modelos, predecir, obtener_metricas, FEATURES


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train(request):
    def _train():
        try:
            entrenar_modelos()
        except Exception as e:
            pass

    thread = threading.Thread(target=_train)
    thread.start()
    return Response(
        {'message': 'Entrenamiento iniciado. Espera ~30 segundos.'},
        status=status.HTTP_202_ACCEPTED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict(request):
    datos = dict(request.data)
    modelo = datos.pop('modelo', 'random_forest')
    if isinstance(modelo, list):
        modelo = modelo[0]

    requeridos = ['imc', 'edad', 'glucosa', 'colesterol',
                  'presion_sistolica', 'presion_diastolica',
                  'frecuencia_cardiaca']
    faltantes = [f for f in requeridos if f not in datos]
    if faltantes:
        return Response(
            {'error': f'Faltan campos: {faltantes}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        resultado = predecir(datos, modelo)
        return Response(resultado)
    except FileNotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def metricas(request):
    data = obtener_metricas()
    if data is None:
        return Response(
            {'error': 'No hay modelos entrenados aún.'},
            status=status.HTTP_404_NOT_FOUND
        )
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def features_info(request):
    return Response({'features': FEATURES})