"""
Script 03: Modelos ARIMAX para articulo IEEE Access
Articulo IEEE Access - Jorge Jose Zamora, UPCT

Modelo A: ARIMAX Global (84 obs, IPC General ~ emociones + D_COVID)
Modelo B: ARIMAX por variable dependiente (13 ECOICOP + ICM + ICC + IPI)
Modelo C: ARIMAX por categoria tematica (6 modelos)

Sin D_UCRANIA. Solo D_COVID.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
import os
import json
import warnings
from pathlib import Path
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.diagnostic import acorr_ljungbox
from pmdarima import auto_arima
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy import stats

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

# Configuracion
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_GLOBAL = BASE_DIR / 'article_outputs' / 'data' / 'econometric_dataset_global.csv'
INPUT_BY_CAT = BASE_DIR / 'article_outputs' / 'data' / 'econometric_dataset_by_category.csv'
OUTPUT_DIR = BASE_DIR / 'article_outputs' / 'arimax'

EMOTION_VARS = ['Ira', 'Miedo', 'Tristeza', 'Alegria']
DUMMY_VARS = ['D_COVID', 'D_UCRANIA']
EXOG_VARS = EMOTION_VARS + DUMMY_VARS

IPC_GENERAL = 'IPC_ECOICOP Índice General'
ECOICOP_COLS = [
    'ECOICOP_Alimentos y bebidas no alcohólicas',
    'ECOICOP_Bebidas alcohólicas y tabaco',
    'ECOICOP_Vestido y calzado',
    'ECOICOP_Vivienda, agua, electricidad, gas y otros combustibles',
    'ECOICOP_Muebles, artículos del hogar y artículos para el mantenimiento corriente del hogar',
    'ECOICOP_Sanidad',
    'ECOICOP_Transporte',
    'ECOICOP_Comunicaciones',
    'ECOICOP_Ocio y cultura',
    'ECOICOP_Enseñanza',
    'ECOICOP_Restaurantes y hoteles',
    'ECOICOP_Otros bienes y servicios'
]
OTHER_DEP = ['ICM', 'ICC', 'IPI']
ALL_DEP_VARS = [IPC_GENERAL] + ECOICOP_COLS + OTHER_DEP

CAT_TO_INDICATOR = {
    'economia': 'IPC_ECOICOP Índice General',
    'politica': 'ICC',
    'sociedad': 'ICC',
    'deporte': 'ECOICOP_Ocio y cultura',
    'cultura': 'ECOICOP_Ocio y cultura',
    'medioambiente': 'ECOICOP_Vivienda, agua, electricidad, gas y otros combustibles'
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 80)
print("MODELOS ARIMAX — ARTICULO IEEE ACCESS (2017-2023)")
print("=" * 80)


def run_adf_test(series, name):
    result = adfuller(series.dropna(), autolag='AIC')
    return {
        'variable': name,
        'adf_statistic': round(result[0], 4),
        'p_value': round(result[1], 4),
        'lags_used': result[2],
        'nobs': result[3],
        'critical_1pct': round(result[4]['1%'], 4),
        'critical_5pct': round(result[4]['5%'], 4),
        'critical_10pct': round(result[4]['10%'], 4),
        'stationary': result[1] <= 0.05
    }


def fit_arimax(y, X, name, output_dir):
    adf = run_adf_test(y, name)
    d_param = 0 if adf['stationary'] else 1

    # Step 1: auto_arima to find optimal (p,d,q) order
    auto_model = auto_arima(
        y, exogenous=X,
        start_p=0, max_p=5, start_q=0, max_q=5,
        d=d_param, seasonal=False, stepwise=True,
        trace=False, error_action='ignore',
        suppress_warnings=True, information_criterion='aic'
    )
    order = auto_model.order

    # Step 2: Re-fit with statsmodels SARIMAX for full exogenous coefficients
    sm_model = SARIMAX(y, exog=X, order=order, trend='c').fit(disp=False)

    y_pred = sm_model.fittedvalues
    residuals = sm_model.resid

    rmse = np.sqrt(mean_squared_error(y, y_pred))
    mae = mean_absolute_error(y, y_pred)
    mape = np.mean(np.abs((y - y_pred) / y)) * 100 if (y != 0).all() else np.nan

    lb = acorr_ljungbox(residuals, lags=10, return_df=True)
    lb_ok = bool((lb['lb_pvalue'] > 0.05).all())

    summary = sm_model.summary()
    param_names = list(sm_model.param_names)
    params = sm_model.params
    pvalues = sm_model.pvalues

    coefs = {}
    for i, pname in enumerate(param_names):
        coefs[pname] = {
            'coefficient': round(float(params.iloc[i]), 6),
            'p_value': round(float(pvalues.iloc[i]), 4),
            'significant_5pct': bool(float(pvalues.iloc[i]) <= 0.05)
        }

    # Figura diagnostica
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    safe_name = name.replace('/', '-').replace(' ', '_').replace('->', '_to_').replace(',', '').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('Í', 'I')[:50]

    axes[0, 0].plot(y.index, y, label='Actual', color='blue', lw=1.5)
    axes[0, 0].plot(y.index, y_pred, label='Predicted', color='red', ls='--', lw=1.5)
    axes[0, 0].set_title(f'Actual vs Predicted - {name[:40]}', fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].plot(y.index, residuals, color='green', lw=1)
    axes[0, 1].axhline(0, color='red', ls='--', lw=1)
    axes[0, 1].set_title('Residuals', fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].hist(residuals, bins=20, color='purple', alpha=0.7, edgecolor='black')
    axes[1, 0].set_title('Residual Distribution', fontweight='bold')

    stats.probplot(residuals, dist="norm", plot=axes[1, 1])
    axes[1, 1].set_title('Q-Q Plot', fontweight='bold')

    plt.suptitle(f'ARIMAX{order} - {name}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig_path = os.path.join(output_dir, f'arimax_{safe_name}.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'variable': name,
        'order': str(order),
        'aic': round(sm_model.aic, 2),
        'bic': round(sm_model.bic, 2),
        'rmse': round(rmse, 4),
        'mae': round(mae, 4),
        'mape': round(mape, 2) if not np.isnan(mape) else None,
        'ljung_box_ok': lb_ok,
        'adf': adf,
        'coefficients': coefs,
        'n_obs': len(y),
        'figure': fig_path,
        'summary_text': str(summary)
    }


# Cargar datos
print("\n[1/4] Cargando datos...")
df_global = pd.read_csv(INPUT_GLOBAL, parse_dates=['Fecha'])
df_global = df_global.set_index('Fecha').sort_index()
df_global.index = pd.DatetimeIndex(df_global.index).to_period('M').to_timestamp()
print(f"   Dataset global: {len(df_global)} obs ({df_global.index[0]} -- {df_global.index[-1]})")

df_by_cat = pd.read_csv(INPUT_BY_CAT, parse_dates=['Fecha'])
print(f"   Dataset por categoria: {len(df_by_cat)} filas")

for v in EXOG_VARS:
    if v not in df_global.columns:
        print(f"   FALTA columna: {v}")

all_results = []

# MODELO A: ARIMAX Global
print("\n" + "=" * 80)
print("MODELO A: ARIMAX GLOBAL")
print("=" * 80)

mask_a = df_global[IPC_GENERAL].notna() & df_global[EXOG_VARS].notna().all(axis=1)
y_a = df_global.loc[mask_a, IPC_GENERAL]
X_a = df_global.loc[mask_a, EXOG_VARS]

print(f"   Obs: {len(y_a)} | Periodo: {y_a.index[0]} -- {y_a.index[-1]}")
result_a = fit_arimax(y_a, X_a, 'IPC_ECOICOP Indice General (Global)', str(OUTPUT_DIR))
all_results.append(result_a)

print(f"   ARIMAX{result_a['order']}, AIC={result_a['aic']}, RMSE={result_a['rmse']}")
print(f"   Coeficientes significativos:")
for pname, info in result_a['coefficients'].items():
    if info.get('significant_5pct'):
        print(f"      {pname}: {info['coefficient']} (p={info['p_value']})")

# MODELO B: ARIMAX por variable dependiente
print("\n" + "=" * 80)
print("MODELO B: ARIMAX POR VARIABLE DEPENDIENTE")
print("=" * 80)

results_b = []
for dep_var in ALL_DEP_VARS:
    if dep_var not in df_global.columns:
        print(f"   Saltando {dep_var} (no encontrada)")
        continue

    mask_b = df_global[dep_var].notna() & df_global[EXOG_VARS].notna().all(axis=1)
    y_b = df_global.loc[mask_b, dep_var]
    X_b = df_global.loc[mask_b, EXOG_VARS]

    if len(y_b) < 30:
        print(f"   Saltando {dep_var} (solo {len(y_b)} obs)")
        continue

    try:
        result_b = fit_arimax(y_b, X_b, dep_var, str(OUTPUT_DIR))
        results_b.append(result_b)
        all_results.append(result_b)

        sig_vars = [p for p, info in result_b['coefficients'].items() if info.get('significant_5pct')]
        print(f"   {dep_var[:50]:50s} -> ARIMAX{result_b['order']}, "
              f"RMSE={result_b['rmse']:.4f}, Sig: {sig_vars}")
    except Exception as e:
        print(f"   ERROR {dep_var[:50]}: {e}")

print(f"\n   Total modelos ajustados: {len(results_b)}")

# MODELO C: ARIMAX por categoria tematica
print("\n" + "=" * 80)
print("MODELO C: ARIMAX POR CATEGORIA TEMATICA")
print("=" * 80)

results_c = []
for cat, indicator in CAT_TO_INDICATOR.items():
    print(f"\n   Categoria: {cat} -> {indicator}")

    df_cat = df_by_cat[df_by_cat['categoria'] == cat].copy()
    if df_cat.empty:
        print(f"   Sin datos para categoria {cat}")
        continue

    df_cat = df_cat.set_index('Fecha').sort_index()
    df_cat.index = pd.DatetimeIndex(df_cat.index).to_period('M').to_timestamp()

    exog_cat = EMOTION_VARS.copy()
    missing_exog = [v for v in exog_cat if v not in df_cat.columns]
    if missing_exog:
        print(f"   Faltan: {missing_exog}")
        continue

    if indicator not in df_global.columns:
        print(f"   Indicador {indicator} no encontrado")
        continue

    df_cat_merged = df_cat[exog_cat].join(
        df_global[[indicator] + DUMMY_VARS], how='inner'
    )
    df_cat_merged = df_cat_merged.dropna()

    if len(df_cat_merged) < 30:
        print(f"   Solo {len(df_cat_merged)} obs -- saltando")
        continue

    y_c = df_cat_merged[indicator]
    X_c = df_cat_merged[exog_cat + DUMMY_VARS]

    try:
        result_c = fit_arimax(y_c, X_c, f'{cat} -> {indicator}', str(OUTPUT_DIR))
        results_c.append(result_c)
        all_results.append(result_c)

        sig_vars = [p for p, info in result_c['coefficients'].items() if info.get('significant_5pct')]
        print(f"   ARIMAX{result_c['order']}, RMSE={result_c['rmse']:.4f}, Sig: {sig_vars}")
    except Exception as e:
        print(f"   ERROR: {e}")

# Exportar
print("\n" + "=" * 80)
print("EXPORTANDO RESULTADOS")
print("=" * 80)

summary_rows = []
for r in all_results:
    row = {
        'Variable': r['variable'],
        'ARIMAX Order': r['order'],
        'N obs': r['n_obs'],
        'AIC': r['aic'],
        'BIC': r['bic'],
        'RMSE': r['rmse'],
        'MAE': r['mae'],
        'MAPE': r['mape'],
        'Ljung-Box OK': r['ljung_box_ok'],
        'ADF p-value': r['adf']['p_value'],
        'Stationary': r['adf']['stationary']
    }
    for emo in EMOTION_VARS:
        for pname, info in r['coefficients'].items():
            if emo.lower() in pname.lower() or emo in pname:
                row[f'B_{emo}'] = info['coefficient']
                row[f'p_{emo}'] = info['p_value']
                row[f'sig_{emo}'] = info['significant_5pct']
                break
    summary_rows.append(row)

df_summary = pd.DataFrame(summary_rows)
excel_file = str(OUTPUT_DIR / 'arimax_results_full.xlsx')
df_summary.to_excel(excel_file, index=False)
print(f"   {excel_file}")

adf_rows = [r['adf'] for r in all_results]
df_adf = pd.DataFrame(adf_rows)
adf_file = str(OUTPUT_DIR / 'adf_tests.csv')
df_adf.to_csv(adf_file, index=False)
print(f"   {adf_file}")

json_file = str(OUTPUT_DIR / 'all_results.json')
json_results = [{k: v for k, v in r.items() if k != 'summary_text'} for r in all_results]
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(json_results, f, ensure_ascii=False, indent=2, default=str)
print(f"   {json_file}")

print("\n" + "=" * 80)
print(f"{len(all_results)} MODELOS ARIMAX COMPLETADOS")
print(f"   Modelo A (Global): 1 modelo")
print(f"   Modelo B (Por VD): {len(results_b)} modelos")
print(f"   Modelo C (Por categoria): {len(results_c)} modelos")
print("=" * 80)
