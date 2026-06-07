# risultati/metrics/

Metriche di valutazione del modello CatBoost sul test set 2022-2023.
Tutte le metriche in spazio logaritmico (`log_cases_per_100k`) salvo dove indicato.

## File

### `metrics_global.csv`
Metriche aggregate sull'intero dataset, separate per split:

| Subset | Descrizione |
|--------|-------------|
| `train_global_log` | Metriche train in log-space |
| `train_global_cases` | Metriche train su casi assoluti |
| `test_global_log` | Metriche test in log-space |
| `test_global_cases` | Metriche test su casi assoluti |

Colonne: `MAE`, `RMSE`, `R^2`, `sMAPE_%`

### `metrics_per_country.csv`
Metriche sul test set per ciascuno degli 11 paesi, ordinate per R^2 decrescente.
Colonne: `iso3`, `country`, `MAE`, `RMSE`, `R^2`, `sMAPE_%`, `n_months`

### `metrics_per_year.csv`
Metriche sul test set aggregate per anno (2022 e 2023 separatamente).
Utile per vedere se le performance degradano nel secondo anno di test.

### `feature_importance.csv`
Importanza delle feature secondo CatBoost (metrica: gain), ordinata per importanza decrescente.
Colonne: `feature`, `importance`
