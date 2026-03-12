"""
Script 05: Quiebres estructurales
Articulo IEEE Access - Jorge Jose Zamora, UPCT

- Test de Chow en marzo 2020 (COVID) - solo este, sin Ucrania
- Test Bai-Perron para quiebres desconocidos (min_segment=12)
- Comparacion de distribuciones emocionales pre/post COVID (KS, MW)
- Comparacion ARIMAX pre vs. post COVID
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
from scipy import stats as scipy_stats
from statsmodels.tsa.stattools import adfuller
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from pmdarima import auto_arima

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

# Configuracion
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / 'article_outputs' / 'data' / 'econometric_dataset_global.csv'
OUTPUT_DIR = BASE_DIR / 'article_outputs' / 'structural'
IPC_COL = 'IPC_ECOICOP Índice General'
EMOTION_VARS = ['Ira', 'Miedo', 'Tristeza', 'Alegria']

BREAK_COVID = '2020-03-01'
BREAK_UKRAINE = '2022-02-01'

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 80)
print("ANALISIS DE QUIEBRES ESTRUCTURALES (2017-2023)")
print("=" * 80)

# Paso 1: Cargar datos
print("\n[1/5] Cargando datos...")
df = pd.read_csv(INPUT_FILE, parse_dates=['Fecha'])
df = df.set_index('Fecha').sort_index()
df.index = pd.DatetimeIndex(df.index).to_period('M').to_timestamp()
df = df.dropna(subset=[IPC_COL] + EMOTION_VARS)
print(f"   {len(df)} observaciones, {df.index[0]} -- {df.index[-1]}")


def chow_test(y, X, break_date):
    X_full = add_constant(X)
    model_full = OLS(y, X_full).fit()
    rss_full = model_full.ssr
    n = len(y)
    k = X_full.shape[1]

    mask_pre = y.index < break_date
    mask_post = y.index >= break_date

    n1 = mask_pre.sum()
    n2 = mask_post.sum()

    if n1 < k + 2 or n2 < k + 2:
        return {'f_stat': np.nan, 'p_value': np.nan, 'n1': n1, 'n2': n2,
                'significant': False, 'error': 'Insuficientes observaciones'}

    y1, X1 = y[mask_pre], X_full[mask_pre]
    y2, X2 = y[mask_post], X_full[mask_post]

    model1 = OLS(y1, X1).fit()
    model2 = OLS(y2, X2).fit()

    rss1 = model1.ssr
    rss2 = model2.ssr

    f_stat = ((rss_full - (rss1 + rss2)) / k) / ((rss1 + rss2) / (n - 2 * k))
    p_value = 1 - scipy_stats.f.cdf(f_stat, k, n - 2 * k)

    return {
        'f_stat': round(float(f_stat), 4),
        'p_value': round(float(p_value), 4),
        'n1': int(n1),
        'n2': int(n2),
        'rss_full': round(float(rss_full), 4),
        'rss_pre': round(float(rss1), 4),
        'rss_post': round(float(rss2), 4),
        'significant': float(p_value) <= 0.05
    }


def bai_perron_sequential(y, X, min_segment=12, max_breaks=5, significance=0.05):
    breaks_found = []
    remaining_indices = y.index.tolist()

    for _ in range(max_breaks):
        best_f = 0
        best_date = None
        best_pvalue = 1.0

        for i in range(min_segment, len(remaining_indices) - min_segment):
            break_date = remaining_indices[i]
            mask = y.index.isin(remaining_indices)
            y_seg = y[mask]
            X_seg = X.loc[mask]

            result = chow_test(y_seg, X_seg, break_date)
            if not np.isnan(result['f_stat']) and result['f_stat'] > best_f:
                best_f = result['f_stat']
                best_date = break_date
                best_pvalue = result['p_value']

        if best_pvalue <= significance and best_date is not None:
            breaks_found.append({
                'break_date': str(best_date),
                'f_stat': round(best_f, 4),
                'p_value': round(best_pvalue, 4)
            })
            break
        else:
            break

    return breaks_found


# Paso 2: Test de Chow
print("\n[2/5] Tests de Chow en fechas conocidas...")

y = df[IPC_COL]
X = df[EMOTION_VARS]

chow_results = {}
for break_name, break_date in [('COVID (mar-2020)', BREAK_COVID),
                                ('Ucrania (feb-2022)', BREAK_UKRAINE)]:
    result = chow_test(y, X, break_date)
    chow_results[break_name] = result
    sig = "SIGNIFICATIVO" if result['significant'] else "No significativo"
    print(f"\n   {break_name}:")
    print(f"      F = {result['f_stat']}, p = {result['p_value']} -> {sig}")
    print(f"      Pre: {result['n1']} obs, Post: {result['n2']} obs")

# Paso 3: Bai-Perron
print("\n[3/5] Deteccion de quiebres (Bai-Perron secuencial, min_segment=12)...")
bp_breaks = bai_perron_sequential(y, X, min_segment=12)

if bp_breaks:
    print(f"   Quiebres detectados: {len(bp_breaks)}")
    for b in bp_breaks:
        print(f"      {b['break_date']}: F={b['f_stat']}, p={b['p_value']}")
else:
    print("   No se detectaron quiebres significativos adicionales")

# Paso 4: KS/MW pre/post COVID
print("\n[4/5] Comparacion de distribuciones emocionales pre/post COVID...")
# Pre-COVID: 2017-01 a 2020-02 (38 meses)
# Post-COVID: 2020-03 a 2023-12 (46 meses)

ks_results = []
pre_covid = df[df.index < BREAK_COVID]
post_covid = df[df.index >= BREAK_COVID]

print(f"   Pre-COVID: {len(pre_covid)} obs ({pre_covid.index[0]} -- {pre_covid.index[-1]})")
print(f"   Post-COVID: {len(post_covid)} obs ({post_covid.index[0]} -- {post_covid.index[-1]})")

for emo in EMOTION_VARS + [IPC_COL]:
    ks_stat, ks_pvalue = scipy_stats.ks_2samp(pre_covid[emo], post_covid[emo])
    mw_stat, mw_pvalue = scipy_stats.mannwhitneyu(pre_covid[emo], post_covid[emo],
                                                    alternative='two-sided')

    result = {
        'variable': emo,
        'mean_pre': round(float(pre_covid[emo].mean()), 4),
        'mean_post': round(float(post_covid[emo].mean()), 4),
        'std_pre': round(float(pre_covid[emo].std()), 4),
        'std_post': round(float(post_covid[emo].std()), 4),
        'diff_pct': round((post_covid[emo].mean() - pre_covid[emo].mean()) /
                          pre_covid[emo].mean() * 100, 2) if pre_covid[emo].mean() != 0 else None,
        'ks_stat': round(float(ks_stat), 4),
        'ks_pvalue': round(float(ks_pvalue), 4),
        'ks_significant': float(ks_pvalue) <= 0.05,
        'mw_stat': round(float(mw_stat), 4),
        'mw_pvalue': round(float(mw_pvalue), 4),
        'mw_significant': float(mw_pvalue) <= 0.05
    }
    ks_results.append(result)

    sig_ks = "SIG" if result['ks_significant'] else "ns"
    sig_mw = "SIG" if result['mw_significant'] else "ns"
    print(f"\n   {emo}:")
    print(f"      Media pre={result['mean_pre']:.4f}, post={result['mean_post']:.4f} "
          f"(D={result['diff_pct']}%)")
    print(f"      KS: D={ks_stat:.4f}, p={ks_pvalue:.4f} [{sig_ks}]")
    print(f"      Mann-Whitney: U={mw_stat:.1f}, p={mw_pvalue:.4f} [{sig_mw}]")

# Paso 5: ARIMAX pre vs post COVID
print("\n[5/5] Comparacion ARIMAX pre vs. post COVID...")

arimax_comparison = {}
for period_name, df_period in [('Pre-COVID', pre_covid), ('Post-COVID', post_covid)]:
    y_p = df_period[IPC_COL].dropna()
    X_p = df_period[EMOTION_VARS].loc[y_p.index]

    if len(y_p) < 20:
        print(f"   {period_name}: solo {len(y_p)} obs, insuficiente")
        continue

    try:
        model = auto_arima(y_p, exogenous=X_p,
                          start_p=0, max_p=3, start_q=0, max_q=3,
                          d=None, seasonal=False, stepwise=True,
                          suppress_warnings=True, error_action='ignore')

        coefs = {}
        param_names = list(model.arima_res_.param_names) if hasattr(model.arima_res_, 'param_names') else []
        params = model.params()
        pvalues = model.arima_res_.pvalues if hasattr(model.arima_res_, 'pvalues') else []

        for i, pname in enumerate(param_names):
            coefs[pname] = {
                'coef': round(float(params[i]), 6) if i < len(params) else None,
                'pvalue': round(float(pvalues[i]), 4) if i < len(pvalues) else None
            }

        arimax_comparison[period_name] = {
            'order': str(model.order),
            'aic': round(model.aic(), 2),
            'n_obs': len(y_p),
            'coefficients': coefs
        }

        print(f"\n   {period_name}: ARIMAX{model.order}, AIC={model.aic():.2f}, n={len(y_p)}")
        for pname, info in coefs.items():
            sig = "*" if info['pvalue'] is not None and info['pvalue'] <= 0.05 else ""
            print(f"      {pname:20s}: B={info['coef']}, p={info['pvalue']} {sig}")

    except Exception as e:
        print(f"   ERROR {period_name}: {e}")

# Figura: Series con quiebre COVID
fig, axes = plt.subplots(len(EMOTION_VARS) + 1, 1, figsize=(14, 4 * (len(EMOTION_VARS) + 1)),
                         sharex=True)

axes[0].plot(df.index, df[IPC_COL], color='blue', lw=1.5)
axes[0].axvline(pd.Timestamp(BREAK_COVID), color='red', ls='--', lw=2, label='COVID-19')
axes[0].axvline(pd.Timestamp(BREAK_UKRAINE), color='orange', ls='--', lw=2, label='Ukraine')
axes[0].set_title('CPI General Index', fontweight='bold')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

TR_EMO = {'Ira': 'Anger', 'Miedo': 'Fear', 'Tristeza': 'Sadness', 'Alegria': 'Joy'}
colors = {'Ira': 'red', 'Miedo': 'purple', 'Tristeza': 'blue', 'Alegria': 'green'}
for i, emo in enumerate(EMOTION_VARS):
    axes[i+1].plot(df.index, df[emo], color=colors.get(emo, 'gray'), lw=1.5)
    axes[i+1].axvline(pd.Timestamp(BREAK_COVID), color='red', ls='--', lw=1, alpha=0.5)
    axes[i+1].axvline(pd.Timestamp(BREAK_UKRAINE), color='orange', ls='--', lw=1, alpha=0.5)
    axes[i+1].set_title(TR_EMO.get(emo, emo), fontweight='bold')
    axes[i+1].grid(True, alpha=0.3)

plt.suptitle('Time Series with Structural Breaks (COVID-19 & Ukraine)', fontsize=14, fontweight='bold')
plt.tight_layout()
fig_path = os.path.join(OUTPUT_DIR, 'series_con_quiebres.png')
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"\n   Figura: {fig_path}")

# Exportar
print("\n" + "=" * 80)
print("EXPORTANDO RESULTADOS")
print("=" * 80)

chow_file = os.path.join(OUTPUT_DIR, 'chow_tests.json')
with open(chow_file, 'w', encoding='utf-8') as f:
    json.dump(chow_results, f, ensure_ascii=False, indent=2, default=str)
print(f"   {chow_file}")

ks_file = os.path.join(OUTPUT_DIR, 'ks_mw_tests.csv')
pd.DataFrame(ks_results).to_csv(ks_file, index=False, encoding='utf-8-sig')
print(f"   {ks_file}")

bp_file = os.path.join(OUTPUT_DIR, 'bai_perron_breaks.json')
with open(bp_file, 'w', encoding='utf-8') as f:
    json.dump(bp_breaks, f, ensure_ascii=False, indent=2, default=str)
print(f"   {bp_file}")

arimax_file = os.path.join(OUTPUT_DIR, 'arimax_pre_post_covid.json')
with open(arimax_file, 'w', encoding='utf-8') as f:
    json.dump(arimax_comparison, f, ensure_ascii=False, indent=2, default=str)
print(f"   {arimax_file}")

summary = {
    'chow_tests': chow_results,
    'bai_perron': bp_breaks,
    'ks_mw_tests': ks_results,
    'arimax_comparison': arimax_comparison,
    'periods': {
        'pre_covid': {'start': str(pre_covid.index[0]), 'end': str(pre_covid.index[-1]),
                      'n': len(pre_covid)},
        'post_covid': {'start': str(post_covid.index[0]), 'end': str(post_covid.index[-1]),
                       'n': len(post_covid)}
    }
}
summary_file = os.path.join(OUTPUT_DIR, 'structural_breaks_summary.json')
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
print(f"   {summary_file}")

print("\n" + "=" * 80)
print("ANALISIS DE QUIEBRES ESTRUCTURALES COMPLETO")
print("=" * 80)
