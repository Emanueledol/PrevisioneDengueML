# modello_utilizzato/assets/

Artefatti del modello CatBoost in produzione. Tutti i file in questa cartella
sono necessari per eseguire l'inferenza.

## File

### `catboost_dengue_2026.cbm`
Pesi del modello CatBoost addestrato. Formato binario nativo CatBoost (`.cbm`).
Caricato da `src/inference.py` tramite `CatBoostRegressor().load_model()`.
- Training: 2014-2021, 11 paesi
- Target: `log_cases_per_100k`
- R^2 test: 0.876

### `feature_columns.json`
Specifica completa delle feature richieste dal modello in input:
- `catboost.feature_columns` -- lista ordinata delle 39 feature (+ `economy` categoriale)
- `mlp.numerical` / `mlp.categorical_dummies` -- spec equivalente per MLP
- `id_cols` -- colonne identificative non usate come feature
- `target` -- nome della colonna target

**Il dataframe passato a `predict_log()` deve contenere esattamente queste colonne, in qualsiasi ordine.**

### `metadata_production.json`
Metadati del modello: versione, data di deployment, metriche sul test set (MAE, RMSE, R^2),
specifica input/output, percorsi dei dati di riferimento.

### `test_reference.csv`
Copia del test set 2022-2023 usata dallo smoke test (`tests/smoke_inference.py`)
per verificare che il modello produca predizioni nei range attesi senza dipendere
dal percorso di `DatasetFinale/`.
