# Data Dictionary

## econometric_dataset_global.csv

Monthly aggregated dataset with 84 observations (January 2017 - December 2023).

| Column | Description | Unit |
|--------|-------------|------|
| `Fecha` | Date (first day of month) | Date |
| `Ira` | Mean anger probability across all headlines in the month | [0, 1] |
| `Miedo` | Mean fear probability | [0, 1] |
| `Tristeza` | Mean sadness probability | [0, 1] |
| `Alegria` | Mean joy probability | [0, 1] |
| `Sorpresa` | Mean surprise probability | [0, 1] |
| `Asco` | Mean disgust probability | [0, 1] |
| `Otros` | Mean others/neutral probability | [0, 1] |
| `Negatividad` | Composite negativity index (Anger + Fear + Sadness) | [0, 1] |
| `IPC_ECOICOP Indice General` | Consumer Price Index (General, base 2021=100) | Index |
| `ECOICOP_*` | 12 ECOICOP sub-indices | Index |
| `ICM` | Consumer Confidence Indicator | Index |
| `ICC` | Consumer Confidence Index | Index |
| `IPI` | Industrial Production Index | Index |
| `D_COVID` | Dummy variable (=1 from March 2020 onward) | 0/1 |
| `D_UCRANIA` | Dummy variable (=1 from February 2022 onward) | 0/1 |

## econometric_dataset_by_category.csv

Monthly aggregated dataset by news category with 504 rows (84 months x 6 categories).

| Column | Description |
|--------|-------------|
| `Fecha` | Date |
| `categoria` | News category: cultura, deporte, economia, medioambiente, politica, sociedad |
| `Ira`, `Miedo`, `Tristeza`, `Alegria`, `Sorpresa`, `Asco`, `Otros` | Mean emotion probabilities per category per month |
| `n_titulares` | Number of headlines in that category-month |

## volume_dataset.csv

Monthly headline volume counts.

| Column | Description |
|--------|-------------|
| `Fecha` | Date |
| `n_titulares` | Total number of headlines in the month |
| `n_fuentes` | Number of distinct media sources |

## Notes

- Emotion probabilities are produced by RoBERTa-BNE (pysentimiento) and sum to 1.0 for each headline
- Variable names use Spanish labels (Ira=Anger, Miedo=Fear, Tristeza=Sadness, Alegria=Joy, Sorpresa=Surprise, Asco=Disgust, Otros=Others)
- Raw headline text is not included due to copyright restrictions
- Macroeconomic indicators sourced from INE (Spain's National Statistics Institute) and CIS (Center for Sociological Research)
