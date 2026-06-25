import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

logger = logging.getLogger(__name__)

FEATURES = [
    'imc', 'edad', 'glucosa', 'colesterol',
    'presion_sistolica', 'presion_diastolica',
    'frecuencia_cardiaca', 'fumador',
    'antecedentes_familiares', 'consumo_alcohol',
]
TARGET = 'riesgo_enfermedad'
MODELS_DIR = Path(settings.BASE_DIR) / 'ml_models'


def _get_dir():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR


def calcular_riesgo(row):
    score = 0
    if row['presion_sistolica'] > 160: score += 2
    if row['glucosa'] > 200: score += 2
    if row['imc'] > 35: score += 1
    if row['fumador']: score += 1
    if row['antecedentes_familiares']: score += 1
    if row['colesterol'] > 240: score += 1
    if row['frecuencia_cardiaca'] > 110: score += 1
    if score >= 6: return 'critico'
    if score >= 4: return 'alto'
    if score >= 2: return 'medio'
    return 'bajo'

    if score >= 5: return 'critico'
    if score >= 3: return 'alto'
    if score >= 1: return 'medio'
    return 'bajo'


def entrenar_modelos():
    from apps.etl.models import Paciente
    from apps.ml.models import MLMetrica

    qs = Paciente.objects.all().values(*FEATURES, TARGET)
    if not qs.exists():
        raise ValueError("No hay datos. Ejecuta el ETL primero.")

    df = pd.DataFrame(list(qs)).dropna()

    # Calcular riesgo con reglas clínicas para mejor accuracy
    for col in ['fumador', 'antecedentes_familiares', 'consumo_alcohol']:
        df[col] = df[col].astype(int)

    y_series = df.apply(calcular_riesgo, axis=1)

    le = LabelEncoder()
    y = le.fit_transform(y_series)
    X = df[FEATURES].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    modelos = {
        'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'decision_tree': DecisionTreeClassifier(max_depth=8, random_state=42),
        'logistic_regression': LogisticRegression(max_iter=500, random_state=42),
    }

    resultados = {}
    d = _get_dir()

    for nombre, modelo in modelos.items():
        modelo.fit(X_train, y_train)
        y_pred = modelo.predict(X_test)

        resultados[nombre] = {
            'accuracy': round(accuracy_score(y_test, y_pred), 4),
            'precision': round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
            'recall': round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
            'f1_score': round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'clases': list(le.classes_),
        }
        joblib.dump(modelo, d / f'{nombre}.pkl')
        logger.info(f"{nombre}: accuracy={resultados[nombre]['accuracy']}")

    joblib.dump(scaler, d / 'scaler.pkl')
    joblib.dump(le, d / 'label_encoder.pkl')

    # Guardar métricas en base de datos
    MLMetrica.objects.all().delete()
    for nombre, metricas in resultados.items():
        MLMetrica.objects.create(
            nombre_modelo=nombre,
            accuracy=metricas['accuracy'],
            precision=metricas['precision'],
            recall=metricas['recall'],
            f1_score=metricas['f1_score'],
            confusion_matrix=metricas['confusion_matrix'],
            clases=metricas['clases'],
        )

    return resultados


def predecir(datos: dict, modelo_nombre='random_forest'):
    d = _get_dir()
    modelo_path = d / f'{modelo_nombre}.pkl'
    if not modelo_path.exists():
        raise FileNotFoundError(f"Modelo '{modelo_nombre}' no entrenado aún.")

    modelo = joblib.load(modelo_path)
    scaler = joblib.load(d / 'scaler.pkl')
    le = joblib.load(d / 'label_encoder.pkl')

    valores = [float(datos.get(f, 0)) for f in FEATURES]
    X = np.array(valores).reshape(1, -1)
    X_scaled = scaler.transform(X)

    pred_idx = modelo.predict(X_scaled)[0]
    probas = modelo.predict_proba(X_scaled)[0]

    return {
        'riesgo_predicho': le.inverse_transform([pred_idx])[0],
        'probabilidades': {
            le.classes_[i]: round(float(p), 4)
            for i, p in enumerate(probas)
        },
        'modelo_usado': modelo_nombre,
    }


def obtener_metricas():
    from apps.ml.models import MLMetrica
    qs = MLMetrica.objects.all()
    if not qs.exists():
        return None
    data = {}
    for m in qs:
        data[m.nombre_modelo] = {
            'accuracy': m.accuracy,
            'precision': m.precision,
            'recall': m.recall,
            'f1_score': m.f1_score,
            'confusion_matrix': m.confusion_matrix,
            'clases': m.clases,
        }
    return data