"""
Script 01: Filtrar dataset de emociones a 2017-2023
Articulo IEEE Access - Jorge Jose Zamora, UPCT

Input: dataset_emociones.parquet (253.886 titulares, 2014-2024)
Output: dataset_emociones_2017_2023.parquet (~175.869 titulares)
"""

import pandas as pd
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Rutas
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / 'Metodología del estudio y resultados' / 'dataset_emociones.parquet'
OUTPUT_DIR = BASE_DIR / 'article_outputs' / 'data'
OUTPUT_FILE = OUTPUT_DIR / 'dataset_emociones_2017_2023.parquet'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EMOTION_COLS = ['anger', 'fear', 'joy', 'sadness', 'surprise', 'disgust', 'others']
EMOTION_ES = {
    'anger': 'Ira', 'fear': 'Miedo', 'joy': 'Alegria',
    'sadness': 'Tristeza', 'surprise': 'Sorpresa',
    'disgust': 'Asco', 'others': 'Otros'
}

print("=" * 80)
print("FILTRADO DE DATASET: 2017-2023")
print("=" * 80)

# Cargar
print("\n[1/3] Cargando dataset completo...")
df = pd.read_parquet(INPUT_FILE)
print(f"   Total original: {len(df):,} titulares")

# Filtrar
print("\n[2/3] Filtrando a 2017-2023...")
df_filtered = df[(df['anio'] >= 2017) & (df['anio'] <= 2023)].copy()
print(f"   Total filtrado: {len(df_filtered):,} titulares")

# Resumen
print("\n[3/3] Resumen del dataset filtrado:")

print("\n   Por anio:")
year_counts = df_filtered['anio'].value_counts().sort_index()
for year, count in year_counts.items():
    print(f"      {year}: {count:>8,}")
print(f"      {'TOTAL':>4s}: {len(df_filtered):>8,}")

if 'categoria' in df_filtered.columns:
    print("\n   Por categoria:")
    cat_counts = df_filtered['categoria'].value_counts().sort_index()
    for cat, count in cat_counts.items():
        print(f"      {cat:20s}: {count:>8,} ({count/len(df_filtered)*100:.1f}%)")

if 'dominant_emotion' in df_filtered.columns:
    print("\n   Por emocion dominante:")
    dom_counts = df_filtered['dominant_emotion'].value_counts()
    for emo, count in dom_counts.items():
        print(f"      {emo:12s}: {count:>8,} ({count/len(df_filtered)*100:.1f}%)")

# Estadisticas de probabilidades
print("\n   Probabilidades medias:")
for col in EMOTION_COLS:
    if col in df_filtered.columns:
        print(f"      {EMOTION_ES.get(col, col):12s}: {df_filtered[col].mean():.6f}")

# Guardar
df_filtered.to_parquet(OUTPUT_FILE, index=False)
print(f"\n   Guardado: {OUTPUT_FILE}")
print(f"   Tamano: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB")

print("\n" + "=" * 80)
print("FILTRADO COMPLETO")
print("=" * 80)
