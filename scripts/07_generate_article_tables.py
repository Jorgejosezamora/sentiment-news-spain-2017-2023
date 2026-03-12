"""
Script 07: Generacion de tablas para articulo IEEE Access
Articulo IEEE Access - Jorge Jose Zamora, UPCT

Genera CSVs con datos de tablas para insertar en el Word.
"""

import pandas as pd
import numpy as np
import sys
import os
import json
import warnings
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'article_outputs' / 'data'
ARIMAX_DIR = BASE_DIR / 'article_outputs' / 'arimax'
VAR_DIR = BASE_DIR / 'article_outputs' / 'var_granger'
STRUCT_DIR = BASE_DIR / 'article_outputs' / 'structural'
OUTPUT_DIR = BASE_DIR / 'article_outputs' / 'tables'

os.makedirs(OUTPUT_DIR, exist_ok=True)

EMOTION_EN = {
    'anger': 'Anger', 'fear': 'Fear', 'joy': 'Joy',
    'sadness': 'Sadness', 'surprise': 'Surprise',
    'disgust': 'Disgust', 'others': 'Others'
}
TR_EMO = {
    'Ira': 'Anger', 'Miedo': 'Fear', 'Tristeza': 'Sadness',
    'Alegria': 'Joy', 'Sorpresa': 'Surprise', 'Asco': 'Disgust',
    'Otros': 'Others',
}
TR_CAT = {
    'cultura': 'Culture', 'deporte': 'Sports', 'economia': 'Economy',
    'medioambiente': 'Environment', 'politica': 'Politics', 'sociedad': 'Society',
}

print("=" * 80)
print("GENERACION DE TABLAS - ARTICULO IEEE ACCESS")
print("=" * 80)

# ═══ TABLE I: Corpus por anio (2017-2023) ═══
print("\n[Table I] Corpus por anio...")
emotions_file = DATA_DIR / 'dataset_emociones_2017_2023.parquet'
if emotions_file.exists():
    df_emo = pd.read_parquet(emotions_file)

    # By year
    year_counts = df_emo.groupby('anio').size().reset_index(name='Headlines')
    year_counts = year_counts.rename(columns={'anio': 'Year'})

    # By year and category
    year_cat = df_emo.groupby(['anio', 'categoria']).size().unstack(fill_value=0)
    year_cat = year_cat.rename(columns=TR_CAT)
    year_cat = year_cat.reset_index().rename(columns={'anio': 'Year'})

    # Merge
    table_i = year_counts.merge(year_cat, on='Year')

    # Add total row
    total_row = {'Year': 'Total', 'Headlines': len(df_emo)}
    for col in table_i.columns[2:]:
        total_row[col] = table_i[col].sum()
    table_i = pd.concat([table_i, pd.DataFrame([total_row])], ignore_index=True)

    table_i.to_csv(OUTPUT_DIR / 'table_I_corpus_by_year.csv', index=False, encoding='utf-8-sig')
    print(f"   -> table_I_corpus_by_year.csv")
    print(table_i.to_string(index=False))

# ═══ TABLE II: Variables del modelo ═══
print("\n[Table II] Variables del modelo...")
variables = [
    {'Variable': 'CPI General Index', 'Type': 'Dependent', 'Source': 'INE', 'Frequency': 'Monthly'},
    {'Variable': 'Anger (Ira)', 'Type': 'Independent', 'Source': 'RoBERTa-BNE', 'Frequency': 'Monthly'},
    {'Variable': 'Fear (Miedo)', 'Type': 'Independent', 'Source': 'RoBERTa-BNE', 'Frequency': 'Monthly'},
    {'Variable': 'Sadness (Tristeza)', 'Type': 'Independent', 'Source': 'RoBERTa-BNE', 'Frequency': 'Monthly'},
    {'Variable': 'Joy (Alegria)', 'Type': 'Independent', 'Source': 'RoBERTa-BNE', 'Frequency': 'Monthly'},
    {'Variable': 'D_COVID', 'Type': 'Dummy', 'Source': 'Manual', 'Frequency': 'Monthly'},
    {'Variable': '12 ECOICOP sub-indices', 'Type': 'Dependent (Model B)', 'Source': 'INE', 'Frequency': 'Monthly'},
    {'Variable': 'ICM (Consumer Confidence)', 'Type': 'Dependent (Model B)', 'Source': 'CIS', 'Frequency': 'Monthly'},
    {'Variable': 'ICC (Consumer Confidence Index)', 'Type': 'Dependent (Model B)', 'Source': 'CIS', 'Frequency': 'Monthly'},
    {'Variable': 'IPI (Industrial Production)', 'Type': 'Dependent (Model B)', 'Source': 'INE', 'Frequency': 'Monthly'},
]
table_ii = pd.DataFrame(variables)
table_ii.to_csv(OUTPUT_DIR / 'table_II_variables.csv', index=False, encoding='utf-8-sig')
print(f"   -> table_II_variables.csv")

# ═══ TABLE III: Distribucion de emociones ═══
print("\n[Table III] Distribucion de emociones...")
if emotions_file.exists():
    emotion_cols = ['anger', 'fear', 'joy', 'sadness', 'surprise', 'disgust', 'others']
    stats_rows = []
    for col in emotion_cols:
        if col in df_emo.columns:
            stats_rows.append({
                'Emotion': EMOTION_EN.get(col, col),
                'Mean': round(df_emo[col].mean(), 6),
                'Std': round(df_emo[col].std(), 6),
                'Min': round(df_emo[col].min(), 6),
                'Max': round(df_emo[col].max(), 6),
                'Median': round(df_emo[col].median(), 6),
            })

    # Dominant emotion distribution
    if 'dominant_emotion' in df_emo.columns:
        dom_counts = df_emo['dominant_emotion'].value_counts()
        for col in emotion_cols:
            for row in stats_rows:
                if row['Emotion'] == EMOTION_EN.get(col, col):
                    count = dom_counts.get(col, 0)
                    row['Dominant_N'] = count
                    row['Dominant_Pct'] = round(count / len(df_emo) * 100, 2)

    table_iii = pd.DataFrame(stats_rows)
    table_iii.to_csv(OUTPUT_DIR / 'table_III_emotion_distribution.csv', index=False, encoding='utf-8-sig')
    print(f"   -> table_III_emotion_distribution.csv")
    print(table_iii.to_string(index=False))

# ═══ TABLE IV: ADF tests ═══
print("\n[Table IV] ADF tests...")
adf_file = ARIMAX_DIR / 'adf_tests.csv'
if adf_file.exists():
    df_adf = pd.read_csv(adf_file)
    # Keep unique variables
    df_adf_unique = df_adf.drop_duplicates(subset='variable')
    df_adf_unique.to_csv(OUTPUT_DIR / 'table_IV_adf_tests.csv', index=False, encoding='utf-8-sig')
    print(f"   -> table_IV_adf_tests.csv ({len(df_adf_unique)} variables)")
else:
    print("   ADF data not yet available. Run script 03 first.")

# ═══ TABLE V: ARIMAX Global ═══
print("\n[Table V] ARIMAX Global...")
arimax_json = ARIMAX_DIR / 'all_results.json'
if arimax_json.exists():
    with open(arimax_json, 'r', encoding='utf-8') as f:
        arimax_results = json.load(f)

    global_model = None
    for r in arimax_results:
        if 'Global' in r.get('variable', ''):
            global_model = r
            break

    if global_model:
        coef_rows = []
        for pname, info in global_model['coefficients'].items():
            coef_rows.append({
                'Parameter': pname,
                'Coefficient': info['coefficient'],
                'p-value': info['p_value'],
                'Significant (5%)': 'Yes' if info.get('significant_5pct') else 'No'
            })
        table_v = pd.DataFrame(coef_rows)

        # Add model stats
        model_stats = pd.DataFrame([{
            'Parameter': '---',
            'Coefficient': None,
            'p-value': None,
            'Significant (5%)': None
        }, {
            'Parameter': f"Order: ARIMAX{global_model['order']}",
            'Coefficient': None,
            'p-value': None,
            'Significant (5%)': None
        }, {
            'Parameter': f"AIC: {global_model['aic']}",
            'Coefficient': None,
            'p-value': None,
            'Significant (5%)': None
        }, {
            'Parameter': f"RMSE: {global_model['rmse']}",
            'Coefficient': None,
            'p-value': None,
            'Significant (5%)': None
        }, {
            'Parameter': f"Ljung-Box OK: {global_model['ljung_box_ok']}",
            'Coefficient': None,
            'p-value': None,
            'Significant (5%)': None
        }])

        table_v = pd.concat([table_v, model_stats], ignore_index=True)
        table_v.to_csv(OUTPUT_DIR / 'table_V_arimax_global.csv', index=False, encoding='utf-8-sig')
        print(f"   -> table_V_arimax_global.csv")
else:
    print("   ARIMAX data not yet available. Run script 03 first.")

# ═══ TABLE VI: ARIMAX por variable ═══
print("\n[Table VI] ARIMAX por variable dependiente...")
arimax_excel = ARIMAX_DIR / 'arimax_results_full.xlsx'
if arimax_excel.exists():
    df_arimax = pd.read_excel(arimax_excel)
    cols_keep = ['Variable', 'ARIMAX Order', 'N obs', 'AIC', 'BIC', 'RMSE', 'MAE',
                 'Ljung-Box OK', 'ADF p-value', 'Stationary']
    # Add emotion coefficients if available
    for emo in ['Ira', 'Miedo', 'Tristeza', 'Alegria']:
        if f'B_{emo}' in df_arimax.columns:
            cols_keep.extend([f'B_{emo}', f'p_{emo}', f'sig_{emo}'])

    available_cols = [c for c in cols_keep if c in df_arimax.columns]
    table_vi = df_arimax[available_cols]
    table_vi.to_csv(OUTPUT_DIR / 'table_VI_arimax_all_models.csv', index=False, encoding='utf-8-sig')
    print(f"   -> table_VI_arimax_all_models.csv ({len(table_vi)} models)")
else:
    print("   ARIMAX Excel not yet available. Run script 03 first.")

# ═══ TABLE VII: Granger causality ═══
print("\n[Table VII] Granger causality...")
granger_file = VAR_DIR / 'granger_tests.csv'
if granger_file.exists():
    df_gc = pd.read_csv(granger_file)
    # Summary: keep best lag per pair
    sig_gc = df_gc[df_gc['significant_5pct'] == True]
    if len(sig_gc) > 0:
        best_gc = sig_gc.loc[sig_gc.groupby(['cause', 'effect'])['f_pvalue'].idxmin()]
        best_gc = best_gc[['cause', 'effect', 'lag', 'f_stat', 'f_pvalue', 'significant_5pct']]
        best_gc.to_csv(OUTPUT_DIR / 'table_VII_granger_significant.csv', index=False, encoding='utf-8-sig')
        print(f"   -> table_VII_granger_significant.csv ({len(best_gc)} significant pairs)")
    else:
        print("   No significant Granger causalities found")

    # Full summary matrix
    pairs = df_gc.groupby(['cause', 'effect']).agg(
        min_pvalue=('f_pvalue', 'min'),
        best_lag=('f_pvalue', 'idxmin')
    ).reset_index()
    pairs['significant'] = pairs['min_pvalue'] <= 0.05
    pairs.to_csv(OUTPUT_DIR / 'table_VII_granger_matrix.csv', index=False, encoding='utf-8-sig')
else:
    print("   Granger data not yet available. Run script 04 first.")

# ═══ TABLE VIII: FEVD ═══
print("\n[Table VIII] FEVD...")
fevd_file = VAR_DIR / 'fevd_ipc.csv'
if fevd_file.exists():
    fevd = pd.read_csv(fevd_file, index_col=0)
    # Select horizons 1, 3, 6, 12
    horizons = [1, 3, 6, 12]
    available_h = [h for h in horizons if h in fevd.index]
    table_viii = fevd.loc[available_h].round(4)
    table_viii.to_csv(OUTPUT_DIR / 'table_VIII_fevd_selected.csv', encoding='utf-8-sig')
    print(f"   -> table_VIII_fevd_selected.csv")
    print(table_viii.to_string())
else:
    print("   FEVD data not yet available. Run script 04 first.")

# ═══ TABLE IX: Structural breaks ═══
print("\n[Table IX] Structural breaks...")
struct_summary = STRUCT_DIR / 'structural_breaks_summary.json'
if struct_summary.exists():
    with open(struct_summary, 'r', encoding='utf-8') as f:
        struct_data = json.load(f)

    # Chow test
    chow_rows = []
    for break_name, result in struct_data.get('chow_tests', {}).items():
        chow_rows.append({
            'Break': break_name,
            'F-statistic': result.get('f_stat'),
            'p-value': result.get('p_value'),
            'N pre': result.get('n1'),
            'N post': result.get('n2'),
            'Significant': 'Yes' if result.get('significant') else 'No'
        })

    # Bai-Perron
    for bp in struct_data.get('bai_perron', []):
        chow_rows.append({
            'Break': f"Bai-Perron: {bp['break_date']}",
            'F-statistic': bp.get('f_stat'),
            'p-value': bp.get('p_value'),
            'N pre': None,
            'N post': None,
            'Significant': 'Yes'
        })

    table_ix = pd.DataFrame(chow_rows)
    table_ix.to_csv(OUTPUT_DIR / 'table_IX_structural_breaks.csv', index=False, encoding='utf-8-sig')
    print(f"   -> table_IX_structural_breaks.csv")
else:
    print("   Structural breaks data not yet available. Run script 05 first.")

# ═══ TABLE X: KS/MW pre vs post COVID ═══
print("\n[Table X] KS/MW pre vs post COVID...")
ks_file = STRUCT_DIR / 'ks_mw_tests.csv'
if ks_file.exists():
    table_x = pd.read_csv(ks_file)
    table_x.to_csv(OUTPUT_DIR / 'table_X_ks_mw_tests.csv', index=False, encoding='utf-8-sig')
    print(f"   -> table_X_ks_mw_tests.csv")
    print(table_x.to_string(index=False))
else:
    print("   KS/MW data not yet available. Run script 05 first.")

print("\n" + "=" * 80)
tables = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.csv')]
print(f"{len(tables)} TABLAS GENERADAS EN {OUTPUT_DIR}/")
for f in sorted(tables):
    print(f"   - {f}")
print("=" * 80)
