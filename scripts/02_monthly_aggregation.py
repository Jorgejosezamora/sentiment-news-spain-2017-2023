"""
Script 02: Agregacion mensual de emociones + merge con variables economicas
Articulo IEEE Access - Jorge Jose Zamora, UPCT

Genera 3 datasets:
  1. Global: media mensual de cada emocion (84 meses x 7 emociones)
  2. Por categoria: media mensual por categoria (84 x 6 x 7)
  3. Volumen: conteo mensual total y por categoria
Merge con Modelo_reg.xlsx (filtrado a 2017-2023).
Sin D_UCRANIA, solo D_COVID.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Rutas
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_EMOTIONS = BASE_DIR / 'article_outputs' / 'data' / 'dataset_emociones_2017_2023.parquet'
INPUT_MODELO = BASE_DIR / 'Metodología del estudio y resultados' / 'Modelo_reg.xlsx'
OUTPUT_DIR = BASE_DIR / 'article_outputs' / 'data'

OUTPUT_GLOBAL = OUTPUT_DIR / 'econometric_dataset_global.csv'
OUTPUT_BY_CAT = OUTPUT_DIR / 'econometric_dataset_by_category.csv'
OUTPUT_VOLUME = OUTPUT_DIR / 'volume_dataset.csv'

EMOTION_COLS = ['anger', 'fear', 'joy', 'sadness', 'surprise', 'disgust', 'others']
EMOTION_ES = {
    'anger': 'Ira', 'fear': 'Miedo', 'joy': 'Alegria',
    'sadness': 'Tristeza', 'surprise': 'Sorpresa',
    'disgust': 'Asco', 'others': 'Otros'
}

print("=" * 80)
print("AGREGACION MENSUAL DE EMOCIONES (2017-2023)")
print("=" * 80)

# Paso 1: Cargar datos
print("\n[1/5] Cargando datos...")
df = pd.read_parquet(INPUT_EMOTIONS)
print(f"   {len(df):,} titulares cargados")

df['fecha_mes'] = pd.to_datetime(
    df['anio'].astype(str) + '-' + df['mes_pub'].astype(str).str.zfill(2) + '-01'
)

# Paso 2: Agregacion global
print("\n[2/5] Agregacion mensual global...")

monthly_mean = df.groupby('fecha_mes')[EMOTION_COLS].mean().reset_index()
monthly_mean = monthly_mean.rename(columns=EMOTION_ES)
monthly_mean = monthly_mean.rename(columns={'fecha_mes': 'Fecha'})

monthly_dominant = df.groupby(['fecha_mes', 'dominant_emotion']).size().unstack(fill_value=0)
monthly_dominant_pct = monthly_dominant.div(monthly_dominant.sum(axis=1), axis=0)
monthly_dominant_pct = monthly_dominant_pct.add_prefix('pct_')
monthly_dominant_pct = monthly_dominant_pct.reset_index().rename(columns={'fecha_mes': 'Fecha'})

monthly_volume = df.groupby('fecha_mes').size().reset_index(name='n_titulares')
monthly_volume = monthly_volume.rename(columns={'fecha_mes': 'Fecha'})

monthly_global = monthly_mean.merge(monthly_volume, on='Fecha')
monthly_global = monthly_global.merge(monthly_dominant_pct, on='Fecha', how='left')

monthly_global['Negatividad'] = (
    monthly_global['Ira'] + monthly_global['Miedo'] + monthly_global['Tristeza']
)

print(f"   {len(monthly_global)} meses agregados")
print(f"   Rango: {monthly_global['Fecha'].min()} -- {monthly_global['Fecha'].max()}")

# Paso 3: Agregacion por categoria
print("\n[3/5] Agregacion mensual por categoria...")

monthly_by_cat_list = []
categories = sorted(df['categoria'].unique())
print(f"   Categorias: {list(categories)}")

for cat in categories:
    df_cat = df[df['categoria'] == cat]
    cat_mean = df_cat.groupby('fecha_mes')[EMOTION_COLS].mean().reset_index()
    cat_mean = cat_mean.rename(columns=EMOTION_ES)
    cat_mean['categoria'] = cat
    cat_mean = cat_mean.rename(columns={'fecha_mes': 'Fecha'})

    cat_vol = df_cat.groupby('fecha_mes').size().reset_index(name='n_titulares')
    cat_vol = cat_vol.rename(columns={'fecha_mes': 'Fecha'})

    cat_merged = cat_mean.merge(cat_vol, on='Fecha')
    monthly_by_cat_list.append(cat_merged)

monthly_by_cat = pd.concat(monthly_by_cat_list, ignore_index=True)
print(f"   {len(monthly_by_cat)} filas (meses x categorias)")

# Paso 4: Merge con variables economicas
print("\n[4/5] Merge con Modelo_reg.xlsx (filtrado a 2017-2023)...")

df_reg = pd.read_excel(INPUT_MODELO, sheet_name='Reg_model')
df_reg['Fecha'] = pd.to_datetime(df_reg['Fecha'])

df_dum = pd.read_excel(INPUT_MODELO, sheet_name='Dummies')
df_dum['Fecha'] = pd.to_datetime(df_dum['Fecha'])

# D_COVID y D_UCRANIA
dummy_cols = ['D_COVID', 'D_UCRANIA']
for dcol in dummy_cols:
    if dcol not in df_reg.columns and dcol in df_dum.columns:
        df_reg = df_reg.merge(df_dum[['Fecha', dcol]], on='Fecha', how='left')

# Eliminar SentNeg (AFINN)
if 'SentNeg' in df_reg.columns:
    df_reg = df_reg.drop(columns=['SentNeg'])
    print("   Columna SentNeg (AFINN) eliminada")

# Filtrar a 2017-2023
df_reg = df_reg[(df_reg['Fecha'] >= '2017-01-01') & (df_reg['Fecha'] <= '2023-12-31')]
print(f"   Modelo_reg filtrado: {len(df_reg)} filas")

# Merge
econometric_global = monthly_global.merge(df_reg, on='Fecha', how='outer')
econometric_global = econometric_global.sort_values('Fecha').reset_index(drop=True)
# Mantener solo 2017-2023
econometric_global = econometric_global[
    (econometric_global['Fecha'] >= '2017-01-01') &
    (econometric_global['Fecha'] <= '2023-12-31')
]

econometric_by_cat = monthly_by_cat.merge(df_reg, on='Fecha', how='left')
econometric_by_cat = econometric_by_cat.sort_values(['categoria', 'Fecha']).reset_index(drop=True)

print(f"   Dataset global: {len(econometric_global)} filas x {len(econometric_global.columns)} columnas")
print(f"   Dataset por categoria: {len(econometric_by_cat)} filas x {len(econometric_by_cat.columns)} columnas")

# Paso 5: Exportar
print(f"\n[5/5] Exportando...")

econometric_global.to_csv(OUTPUT_GLOBAL, index=False, encoding='utf-8-sig')
econometric_by_cat.to_csv(OUTPUT_BY_CAT, index=False, encoding='utf-8-sig')

vol_total = monthly_volume.copy()
vol_by_cat = df.groupby(['fecha_mes', 'categoria']).size().reset_index(name='n_titulares')
vol_by_cat = vol_by_cat.rename(columns={'fecha_mes': 'Fecha'})
vol_combined = vol_total.merge(
    vol_by_cat.pivot_table(index='Fecha', columns='categoria', values='n_titulares', fill_value=0),
    on='Fecha', how='left'
)
vol_combined.to_csv(OUTPUT_VOLUME, index=False, encoding='utf-8-sig')

print(f"   {OUTPUT_GLOBAL}")
print(f"   {OUTPUT_BY_CAT}")
print(f"   {OUTPUT_VOLUME}")

# Resumen
print("\n" + "=" * 80)
print("RESUMEN DE AGREGACION")
print("=" * 80)

print("\nMedias globales de emociones (2017-2023):")
for col_es in ['Ira', 'Miedo', 'Alegria', 'Tristeza', 'Sorpresa', 'Asco']:
    if col_es in monthly_global.columns:
        vals = monthly_global[col_es].dropna()
        print(f"   {col_es:12s}: media={vals.mean():.4f}, std={vals.std():.4f}")

print(f"\nVolumen mensual medio: {monthly_global['n_titulares'].mean():,.0f} titulares/mes")
print(f"Negatividad media: {monthly_global['Negatividad'].mean():.4f}")

econ_cols = [c for c in df_reg.columns if c != 'Fecha']
print(f"\nVariables economicas ({len(econ_cols)}):")
for c in econ_cols:
    print(f"   - {c}")

print("\n" + "=" * 80)
print("AGREGACION COMPLETA")
print("=" * 80)
