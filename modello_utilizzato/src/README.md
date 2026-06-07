# modello_utilizzato/src/

Codice di inferenza del modello. Contiene un solo modulo: `inference.py`.

## `inference.py`

Espone due funzioni pubbliche per usare il modello senza conoscere i dettagli interni:

### `load_model() -> CatBoostRegressor`
Carica il modello da `assets/catboost_dengue_2026.cbm`. Da chiamare una volta sola
e passare il risultato alle funzioni di predizione per evitare ricaricamenti ripetuti.

### `predict_log(df, model=None) -> np.ndarray`
Restituisce le predizioni in scala logaritmica (`log_cases_per_100k = log1p(casi/100k)`).

- **Input:** DataFrame con le 39 colonne definite in `assets/feature_columns.json`
- **Output:** array NumPy di shape `(n_righe,)`

### `predict_cases(df, model=None) -> np.ndarray`
Restituisce i casi assoluti stimati (non normalizzati per popolazione).

- **Input:** stesso DataFrame di `predict_log`, più la colonna `population`
- **Output:** array NumPy -- casi assoluti calcolati come `expm1(log_pred) * population / 100_000`
- I valori negativi fisicamente impossibili sono clippati a zero

## Utilizzo

```python
import pandas as pd
from modello_utilizzato.src.inference import predict_log, predict_cases

df = pd.read_csv("DatasetFinale/test.csv")

log_preds  = predict_log(df)    # log_cases_per_100k
case_preds = predict_cases(df)  # casi assoluti
```
