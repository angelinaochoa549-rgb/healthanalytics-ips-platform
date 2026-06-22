import time
import logging
from datetime import datetime, date
from pathlib import Path
 
import numpy as np
import pandas as pd
from django.conf import settings
from django.utils import timezone
 
logger = logging.getLogger(__name__)
 
RANGOS_CLINICOS = {
    'edad':              (0, 120),
    'peso':              (10, 300),
    'altura':            (0.5, 2.5),
    'presion_sistolica': (60, 300),
    'presion_diastolica':(40, 200),
    'frecuencia_cardiaca':(20, 300),
    'glucosa':           (20, 1000),
    'colesterol':        (50, 600),
    'saturacion_oxigeno':(50, 100),
    'temperatura':       (30, 45),
}
 
MAP_DIAGNOSTICOS = {
    'hipertencion':          'Hipertensión',
    'hipertensíon':          'Hipertensión',
    'hipertension':          'Hipertensión',
    'diabetes tipo2':        'Diabetes tipo 2',
    'insuficiencia cardiaca':'Insuficiencia cardíaca',
    'sin diagnóstico':       'Sano',
}
 
MAP_ACTIVIDAD = {
    'sedentario': 'sedentario', 'sédentario': 'sedentario',
    'leve': 'leve', 'levee': 'leve',
    'moderado': 'moderado', 'moderadoo': 'moderado',
    'intenso': 'intenso', 'intensoo': 'intenso',
}
 
EDADES_TEXTO = {
    'treinta': 30, 'cuarenta y cinco': 45,
    'veinte': 20, 'cincuenta': 50, 'sesenta y dos': 62,
}
 
 
class ETLPipeline:
 
    def __init__(self, log_instance):
        self.log = log_instance
        self.detalles = []
        self.df_raw = None
        self.df_clean = None
 
    # ── EXTRACT ──
    def extract(self, archivo=None):
        self._log("=== FASE EXTRACT ===")
        start = time.time()
 
        datasets_dir = Path(settings.DATASETS_DIR)
 
        if archivo and Path(archivo).exists():
            ruta = Path(archivo)
        else:
            # Buscar Excel o CSV en la carpeta datasets
            excels = list(datasets_dir.glob('*.xlsx'))
            csvs = list(datasets_dir.glob('*.csv'))
            if excels:
                ruta = excels[0]
            elif csvs:
                ruta = csvs[0]
            else:
                raise FileNotFoundError("No se encontró dataset en la carpeta datasets/")
 
        self._log(f"Leyendo archivo: {ruta.name}")
 
        if ruta.suffix == '.xlsx':
            self.df_raw = pd.read_excel(ruta)
        else:
            self.df_raw = pd.read_csv(ruta, encoding='utf-8-sig')
 
        total = len(self.df_raw)
        self.log.registros_extraidos = total
        self.log.archivo_fuente = ruta.name
        self.log.save(update_fields=['registros_extraidos', 'archivo_fuente'])
 
        elapsed = round(time.time() - start, 2)
        self._log(f"Extraídos: {total} registros en {elapsed}s")
        return self.df_raw
 
    # ── TRANSFORM ──
    def transform(self):
        self._log("=== FASE TRANSFORM ===")
        df = self.df_raw.copy()
 
        # Normalizar nombres de columnas
        df.columns = (df.columns
                      .str.lower()
                      .str.strip()
                      .str.replace('á','a').str.replace('é','e')
                      .str.replace('í','i').str.replace('ó','o')
                      .str.replace('ú','u')
                      .str.replace(' ','_')
                      .str.replace('presion_sistolica','presion_sistolica')
                      )
 
        # Renombres específicos
        renombres = {
            'presion_sistolica': 'presion_sistolica',
            'presion_diastolica': 'presion_diastolica',
            'saturacion_oxigeno': 'saturacion_oxigeno',
            'actividad_fisica': 'actividad_fisica',
            'diagnostico_preliminar': 'diagnostico_preliminar',
            'imc': 'imc',
            'frecuencia_cardiaca': 'frecuencia_cardiaca',
        }
 
        # Eliminar duplicados
        antes = len(df)
        df.drop_duplicates(subset=['id_paciente'], keep='first', inplace=True)
        duplicados = antes - len(df)
        self.log.registros_duplicados = duplicados
        self._log(f"Duplicados eliminados: {duplicados}")
 
        # Convertir edad (puede venir como texto)
        df['edad'] = df['edad'].apply(self._convertir_edad)
 
        # Convertir columnas numéricas
        nums = ['presion_sistolica','presion_diastolica','frecuencia_cardiaca',
                'peso','altura','imc','glucosa','colesterol',
                'saturacion_oxigeno','temperatura']
        for col in nums:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
 
        # Reemplazar outliers con NaN
        invalidos = 0
        for col, (mn, mx) in RANGOS_CLINICOS.items():
            if col in df.columns:
                mask = (df[col] < mn) | (df[col] > mx)
                invalidos += mask.sum()
                df.loc[mask, col] = np.nan
        self.log.registros_invalidos = invalidos
        self._log(f"Valores fuera de rango: {invalidos}")
 
        # Imputar nulos con mediana
        for col in nums:
            if col in df.columns:
                df[col].fillna(df[col].median(), inplace=True)
 
        # Convertir enteros
        for col in ['edad','presion_sistolica','presion_diastolica','frecuencia_cardiaca']:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(int)
 
        # Recalcular IMC
        df['imc'] = (df['peso'] / (df['altura'] ** 2)).round(2)
 
        # Normalizar sexo
        if 'sexo' in df.columns:
            df['sexo'] = df['sexo'].str.upper().str.strip()
            df['sexo'] = df['sexo'].map(
                {'M':'M','F':'F','MASCULINO':'M','FEMENINO':'F'}
            ).fillna('M')
 
        # Normalizar actividad física
        if 'actividad_fisica' in df.columns:
            df['actividad_fisica'] = (df['actividad_fisica']
                .str.lower().str.strip()
                .map(MAP_ACTIVIDAD)
                .fillna('sedentario'))
 
        # Normalizar diagnóstico
        if 'diagnostico_preliminar' in df.columns:
            df['diagnostico_preliminar'] = df['diagnostico_preliminar'].apply(
                lambda x: MAP_DIAGNOSTICOS.get(str(x).lower().strip(), str(x).strip())
            )
 
        # Asegurar booleanos antes de calcular riesgo
        for col in ['fumador', 'antecedentes_familiares']:
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool)
            else:
                df[col] = False
 
        # Calcular riesgo con reglas clínicas reales (no confiar en el Excel original)
        from apps.ml.ml_engine import calcular_riesgo
        df['riesgo_enfermedad'] = df.apply(calcular_riesgo, axis=1)
 
        # Clasificación IMC
        df['clasificacion_imc'] = df['imc'].apply(self._clasificar_imc)
 
        # Detectar críticos (coherente con riesgo_enfermedad)
        df['es_critico'] = (
            (df['riesgo_enfermedad'] == 'critico') |
            (df['presion_sistolica'] > 180) |
            (df['glucosa'] > 300) |
            (df['saturacion_oxigeno'] < 85)
        )
 
        # Fechas
        if 'fecha_consulta' in df.columns:
            df['fecha_consulta'] = pd.to_datetime(
                df['fecha_consulta'], errors='coerce'
            ).dt.date
            df['fecha_consulta'] = df['fecha_consulta'].fillna(date.today())
 
        # Texto nulo
        for col in ['nombres','apellidos','diagnostico_preliminar']:
            if col in df.columns:
                df[col] = df[col].fillna('Sin información')
 
        self.df_clean = df
        self.log.registros_transformados = len(df)
        self.log.save(update_fields=[
            'registros_transformados','registros_duplicados','registros_invalidos'
        ])
        self._log(f"Transformación completa: {len(df)} registros")
        return df
 
    # ── LOAD ──
    def load(self):
        from apps.etl.models import Paciente
        self._log("=== FASE LOAD ===")
        df = self.df_clean
 
        Paciente.objects.all().delete()
 
        bulk = []
        cargados = 0
        for _, row in df.iterrows():
            try:
                p = Paciente(
                    id_paciente=int(row['id_paciente']),
                    nombres=str(row.get('nombres',''))[:100],
                    apellidos=str(row.get('apellidos',''))[:100],
                    edad=int(row['edad']),
                    sexo=str(row['sexo']),
                    peso=float(row['peso']),
                    altura=float(row['altura']),
                    imc=float(row['imc']),
                    presion_sistolica=int(row['presion_sistolica']),
                    presion_diastolica=int(row['presion_diastolica']),
                    frecuencia_cardiaca=int(row['frecuencia_cardiaca']),
                    glucosa=float(row['glucosa']),
                    colesterol=float(row['colesterol']),
                    saturacion_oxigeno=float(row['saturacion_oxigeno']),
                    temperatura=float(row['temperatura']),
                    antecedentes_familiares=bool(row.get('antecedentes_familiares', False)),
                    fumador=bool(row.get('fumador', False)),
                    consumo_alcohol=bool(row.get('consumo_alcohol', False)),
                    actividad_fisica=str(row.get('actividad_fisica','sedentario')),
                    diagnostico_preliminar=str(row.get('diagnostico_preliminar',''))[:200],
                    riesgo_enfermedad=str(row['riesgo_enfermedad']),
                    fecha_consulta=row['fecha_consulta'],
                    es_critico=bool(row.get('es_critico', False)),
                    clasificacion_imc=str(row.get('clasificacion_imc','')),
                )
                bulk.append(p)
                cargados += 1
            except Exception as e:
                self._log(f"Error en fila: {e}")
 
        Paciente.objects.bulk_create(bulk, batch_size=200)
        self.log.registros_cargados = cargados
        self.log.save(update_fields=['registros_cargados'])
        self._log(f"Cargados en BD: {cargados}")
        return cargados
 
    # ── RUN ──
    def run(self, archivo=None):
        start = time.time()
        try:
            self.log.estado = 'en_proceso'
            self.log.save(update_fields=['estado'])
            self.extract(archivo)
            self.transform()
            self.load()
            elapsed = round(time.time() - start, 2)
            self.log.estado = 'completado'
            self.log.fecha_fin = timezone.now()
            self.log.tiempo_ejecucion = elapsed
            self.log.log_detalle = '\n'.join(self.detalles)
            self.log.save()
            self._log(f"ETL completado en {elapsed}s")
        except Exception as e:
            self.log.estado = 'error'
            self.log.error_mensaje = str(e)
            self.log.fecha_fin = timezone.now()
            self.log.log_detalle = '\n'.join(self.detalles)
            self.log.save()
            raise
 
    # ── HELPERS ──
    def _convertir_edad(self, val):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return EDADES_TEXTO.get(str(val).lower().strip(), 0)
 
    def _clasificar_imc(self, imc):
        if pd.isna(imc):
            return 'Sin datos'
        if imc < 18.5:
            return 'Bajo peso'
        elif imc < 25:
            return 'Normal'
        elif imc < 30:
            return 'Sobrepeso'
        return 'Obesidad'
 
    def _log(self, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        entry = f"[{ts}] {msg}"
        self.detalles.append(entry)
        logger.info(entry)