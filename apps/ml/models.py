from django.db import models

class MLMetrica(models.Model):
    nombre_modelo = models.CharField(max_length=50)
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    confusion_matrix = models.JSONField()
    clases = models.JSONField()
    fecha_entrenamiento = models.DateTimeField(auto_now=True)

    class Meta:
        get_latest_by = 'fecha_entrenamiento'

    def __str__(self):
        return f"{self.nombre_modelo} - {self.accuracy}"