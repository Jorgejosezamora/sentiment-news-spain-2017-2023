# Sentiment Monitoring in Spanish Media via Multi-Model Econometric Design (2017-2023)

This repository contains the reproducibility materials for the article:

> **Sentiment Monitoring in Spanish Media via Multi-Model Econometric Design: Emotional Signals, Inflation Dynamics, and Structural Breaks (2017-2023)**
>
> Zamora Canovas, Jorge Jose; Martinez Maria-Dolores, Soledad Maria
>
> *IEEE Access* (submitted)

## Overview

This study investigates the longitudinal relationship between emotional signals embedded in 175,869 Spanish digital news headlines and macroeconomic indicators over the 2017-2023 period (84 monthly observations). Emotional features are extracted using RoBERTa-BNE, a transformer-based model fine-tuned for Spanish emotion classification, producing seven-dimensional probability vectors (anger, fear, joy, sadness, surprise, disgust, and neutral).

### Key Findings

- **Bidirectional Granger causality** between headline emotions and Spain's Consumer Price Index (CPI)
- **Structural breaks** confirmed at COVID-19 onset (March 2020) and Ukraine conflict (February 2022)
- **Joy declined 11.8%** and **anger increased 5.4%** post-COVID, indicating a semi-permanent emotional shift in media coverage
- **FEVD analysis** shows emotional signals explain substantial long-run CPI forecast error variance

## Repository Structure

```
sentiment-news-spain-2017-2023/
  scripts/               # Numbered analysis pipeline (01-08)
    01_filter_dataset.py          # Filter corpus to 2017-2023
    02_monthly_aggregation.py     # Monthly emotion aggregation + merge with macro data
    03_arimax_models.py           # ARIMAX models (Global, by variable, by category)
    04_var_granger_analysis.py    # VAR model, Granger causality, IRF, FEVD
    05_structural_breaks.py       # Chow, Bai-Perron, KS/MW tests
    06_generate_article_figures.py # IEEE Access format figures
    07_generate_article_tables.py  # Article tables (CSV)
    08_rewrite_article.py          # Word document generation
  data/                  # Aggregated monthly datasets (CSV)
    econometric_dataset_global.csv       # 84 monthly obs, all variables
    econometric_dataset_by_category.csv  # 504 rows (84 months x 6 categories)
    volume_dataset.csv                   # Monthly headline counts
    README_DATA.md                       # Data dictionary
  results/               # Analysis outputs
    arimax/              # ARIMAX model results (JSON, CSV, XLSX)
    var_granger/         # VAR, Granger, IRF, FEVD results
    structural_breaks/   # Chow, Bai-Perron, KS/MW results
  figures/               # Publication-quality figures (300 dpi PNG)
  requirements.txt
  CITATION.cff
  LICENSE
```

## Data

Raw headline data are not shared due to copyright restrictions. Only **monthly aggregated** emotion probabilities and macroeconomic indicators are provided. See `data/README_DATA.md` for the full data dictionary.

### Key Variables

| Variable | Description | Source |
|----------|-------------|--------|
| Anger, Fear, Joy, Sadness | Monthly mean emotion probabilities | RoBERTa-BNE |
| IPC General Index | Consumer Price Index (ECOICOP) | INE (Spain) |
| 12 ECOICOP sub-indices | Disaggregated price indices | INE |
| ICM, ICC | Consumer confidence indicators | CIS |
| IPI | Industrial Production Index | INE |
| D_COVID | Dummy (=1 from March 2020) | Manual |
| D_UKRAINE | Dummy (=1 from February 2022) | Manual |

## Methodology

1. **Emotion Classification**: RoBERTa-BNE (pysentimiento) produces 7-dimensional probability vectors for each headline
2. **ARIMAX Models**: Auto-selected orders via AIC (pmdarima) + re-estimated with statsmodels SARIMAX for full coefficient inference
3. **VAR(6) Model**: Five-variable system (CPI + 4 emotions), Granger causality, orthogonalized IRF (12 months), FEVD
4. **Structural Breaks**: Chow tests (COVID, Ukraine), Bai-Perron sequential, KS/Mann-Whitney distribution comparisons

## Requirements

```bash
pip install -r requirements.txt
```

Python 3.10+ required. See `requirements.txt` for full dependency list.

## Execution

Scripts are numbered and should be run sequentially:

```bash
python scripts/01_filter_dataset.py
python scripts/02_monthly_aggregation.py
python scripts/03_arimax_models.py
python scripts/04_var_granger_analysis.py
python scripts/05_structural_breaks.py
python scripts/06_generate_article_figures.py
python scripts/07_generate_article_tables.py
```

> **Note**: Script 01 requires the raw headline parquet file (`dataset_emociones.parquet`) which is not included in this repository. Scripts 02-08 can be run using the provided aggregated CSV data.

## Citation

If you use this code or data, please cite:

```bibtex
@article{zamora2025sentiment,
  title={Sentiment Monitoring in Spanish Media via Multi-Model Econometric Design: Emotional Signals, Inflation Dynamics, and Structural Breaks (2017--2023)},
  author={Zamora C{\'a}novas, Jorge Jos{\'e} and Mart{\'i}nez Mar{\'i}a-Dolores, Soledad Maria},
  journal={IEEE Access},
  year={2025},
  publisher={IEEE}
}
```

## License

MIT License. See [LICENSE](LICENSE).

## Contact

- Jorge Jose Zamora Canovas - jjzamora.canovas@gmail.com
- Polytechnic University of Cartagena (UPCT), Spain
