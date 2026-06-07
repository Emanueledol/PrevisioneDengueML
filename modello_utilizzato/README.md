# modello_utilizzato/

Contiene il modello CatBoost in produzione per il forecasting mensile del dengue,
il codice di inferenza e i test di verifica.

## Struttura

```
modello_utilizzato/
|-- assets/
|   |-- catboost_dengue_2026.cbm     # Pesi del modello (CatBoost)
|   |-- feature_columns.json         # Specifica delle 39 feature + categoriale economy
|   |-- test_reference.csv           # Test set 2022-2023 (11 paesi) per smoke test
|   +-- metadata_production.json     # Versione, metriche, specifica input/output
|
|-- src/
|   +-- inference.py                 # predict_log() e predict_cases()
|
+-- tests/
    +-- smoke_inference.py           # Smoke test eseguibile
```

## Utilizzo

### Smoke test
```bash
python modello_utilizzato/tests/smoke_inference.py
```

### Inferenza
```python
from modello_utilizzato.src.inference import predict_log, predict_cases

# df deve contenere le 39 colonne definite in assets/feature_columns.json
log_preds  = predict_log(df)    # log_cases_per_100k
case_preds = predict_cases(df)  # casi assoluti (richiede colonna 'population')
```

## Specifica del modello

- **Framework**: CatBoost (catboost >= 1.2)
- **Target**: `log_cases_per_100k` -- log1p-trasformazione di casi/100k residenti
- **Feature**: 39 colonne (climatiche, socioeconomiche, lag temporali, rolling means)
- **Categoriale**: `economy` (codice ISO3: ARG, BOL, BRA, CRI, GTM, HND, MEX, PER, PRY, THA, URY)
- **Addestramento**: 2014-2021 | **Test**: 2022-2023
- **R^2 test (log-space)**: 0.876

## Conversione output

```python
import numpy as np
cases_per_100k  = np.expm1(log_pred)
absolute_cases  = cases_per_100k * population / 100_000
```

## Dati di riferimento

- Training/test completi: `DatasetFinale/train.csv` e `DatasetFinale/test.csv`
- Risultati completi (metriche, plot, predizioni): `risultati/`
- Conclusioni: `risultati/conclusioni.md`
