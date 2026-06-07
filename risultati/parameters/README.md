# risultati/parameters/

Parametri e metadati del modello CatBoost in produzione.

## File

### `catboost_params.json`
Tutti i parametri dell'oggetto CatBoost estratti con `model.get_all_params()`.
Include iperparametri di training (learning rate, depth, iterazioni, loss function, ecc.)
e impostazioni interne. Utile per replicare il training o confrontare versioni del modello.

### `feature_spec.json`
Copia di `modello_utilizzato/assets/feature_columns.json` al momento della generazione
dei risultati. Documenta esattamente quali feature erano attive nel modello valutato:
- `catboost.feature_columns` -- lista ordinata delle 39 feature di input
- `catboost.categorical` -- feature categoriali (`economy`)
- `target` -- colonna target (`log_cases_per_100k`)
- `id_cols` -- colonne identificative escluse dall'input

### `metadata_production.json`
Metadati del modello: versione, data di deployment, metriche sul test set,
percorsi dei dati e del file modello, specifica input/output.
Copia di `modello_utilizzato/assets/metadata_production.json`.
