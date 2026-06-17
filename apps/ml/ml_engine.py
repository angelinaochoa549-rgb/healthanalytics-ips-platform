import json
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


def entrenar_modelos():
    from apps.etl.models import Paciente
    qs = Paciente.objects.all().values(*FEATURES, TARGET)
    if not qs.exists():
        raise ValueError("No hay datos. Ejecuta el ETL primero.")

    df = pd.DataFrame(list(qs)).dropna()

    le = LabelEncoder()
    y = le.fit_transform(df[TARGET])
    X = df[FEATURES].copy()

    for col in ['fumador', 'antecedentes_familiares', 'consumo_alcohol']:
        X[col] = X[col].astype(int)

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

    with open(d / 'metricas.json', 'w') as f:
        json.dump(resultados, f, indent=2)

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
    d = _get_dir()
    path = d / 'metricas.json'
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)