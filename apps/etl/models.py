from django.db import models
from apps.authentication.models import User


class Paciente(models.Model):
    RIESGO_CHOICES = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('critico', 'Crítico'),
    ]
    SEXO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino')]
    ACTIVIDAD_CHOICES = [
        ('sedentario', 'Sedentario'),
        ('leve', 'Leve'),
        ('moderado', 'Moderado'),
        ('intenso', 'Intenso'),
    ]

    id_paciente = models.IntegerField(unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    edad = models.IntegerField()
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    peso = models.FloatField()
    altura = models.FloatField()
    imc = models.FloatField()
    presion_sistolica = models.IntegerField()
    presion_diastolica = models.IntegerField()
    frecuencia_cardiaca = models.IntegerField()
    glucosa = models.FloatField()
    colesterol = models.FloatField()
    saturacion_oxigeno = models.FloatField()
    temperatura = models.FloatField()
    antecedentes_familiares = models.BooleanField(default=False)
    fumador = models.BooleanField(default=False)
    consumo_alcohol = models.BooleanField(default=False)
    actividad_fisica = models.CharField(max_length=20, choices=ACTIVIDAD_CHOICES, default='sedentario')
    diagnostico_preliminar = models.CharField(max_length=200)
    riesgo_enfermedad = models.CharField(max_length=10, choices=RIESGO_CHOICES, default='bajo')
    fecha_consulta = models.DateField()
    es_critico = models.BooleanField(default=False)
    clasificacion_imc = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_consulta']

    def __str__(self):
        return f"{self.nombres} {self.apellidos} (ID: {self.id_paciente})"


class ETLLog(models.Model):
    ESTADO_CHOICES = [
        ('iniciado', 'Iniciado'),
        ('en_proceso', 'En proceso'),
        ('completado', 'Completado'),
        ('error', 'Error'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='iniciado')
    registros_extraidos = models.IntegerField(default=0)
    registros_transformados = models.IntegerField(default=0)
    registros_cargados = models.IntegerField(default=0)
    registros_duplicados = models.IntegerField(default=0)
    registros_invalidos = models.IntegerField(default=0)
    tiempo_ejecucion = models.FloatField(null=True, blank=True)
    archivo_fuente = models.CharField(max_length=255, blank=True)
    log_detalle = models.TextField(blank=True)
    error_mensaje = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"ETL #{self.id} - {self.estado}"