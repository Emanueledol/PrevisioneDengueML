# build_panel_splits -- Pipeline di costruzione del dataset finale

Script numerati da eseguire **in sequenza** (01 -> 07). Partono dal dataset grezzo
unificato e producono `train.csv` / `test.csv` pronti per il training del modello CatBoost.
`check_leak.py` è uno script di verifica indipendente, da eseguire dopo il passo 04.

---

## Script in sequenza

### `01_build_clean_panel.py`
Carica il dataset grezzo con pivot e lag climatici, seleziona i paesi del campione
(11 nazioni), rimuove righe con valori mancanti critici e salva `panel_clean.csv`.
È il primo punto di ingresso della pipeline panel.

### `02_add_population_and_targets.py`
Aggiunge la colonna `population` (dati World Bank) a `panel_clean.csv` e calcola
le variabili target derivate:
- `cases_per_100k` = casi / popolazione x 100.000
- `log_cases_per_100k` = log1p(cases_per_100k)

Output: `panel_targets.csv`.

### `03_add_temporal_features.py`
Aggiunge all'intero panel le feature temporali e autoregressiva:
- Lag epidemiologici: `cases_lag1/2/3/12`, `cases_per_100k_lag1/2/3/12`, `log_cases_per_100k_lag1/2/3/12`
- Rolling mean: `cases_per_100k_roll3/6/12_mean`, `log_cases_per_100k_roll3/6/12_mean`
- Stagionalità: `sin_month`, `cos_month`

Output: `panel_features.csv` (dataset completo con tutte le 39 feature).

### `04_make_splits.py`
Divide il panel in train (2014-2021) e test (2022-2023) -- **Scenario B**.
Rimuove le righe prive di `log_cases_per_100k_lag12` (i primi 12 mesi di ciascun paese).
Produce quattro file:
- `train_main_catboost.csv` / `test_main_catboost.csv` -- con `economy` come categoriale
- `train_main_mlp.csv` / `test_main_mlp.csv` -- con feature numeriche scalate e `economy` one-hot

Salva anche `feature_columns.json` (specifica delle 39 feature) e `folds_rolling.json`.

### `05_baselines.py`
Calcola i modelli baseline da usare come riferimento comparativo:
- **Naive lag-1**: predice il valore del mese precedente
- **Naive lag-12**: predice il valore dello stesso mese dell'anno precedente
- **Media storica per mese**: media per paese e mese calcolata sul training

Output: metriche e predizioni baseline in `results/`.

### `06_train_models.py`
Addestra tre modelli sul training set e li valuta sul test:
- Regressione lineare (baseline parametrico)
- MLP con sklearn (`MLPRegressor`)
- **CatBoost** -- il modello selezionato come finale

Salva i risultati in `results/models_results.json` e gli artefatti del modello.
Il modello CatBoost prodotto qui (dopo tuning nelle fasi successive) è quello
conservato in `modello_utilizzato/assets/catboost_dengue_2026.cbm`.

### `07_integrate_baselines_and_plots.py`
Consolida i risultati di baseline e modelli in tabelle comparative, calcola
metriche per paese e genera i grafici di confronto usati nell'analisi esplorativa.

---

## Script di verifica

### `check_leak.py`
Verifica l'assenza di leakage nel dataset di training. Controlla:
1. Che nessuna colonna con il nome del target (`log_cases_per_100k`, `cases_per_100k`, ecc.) sia presente tra le feature
2. Che nessuna feature non-lag abbia correlazione di Pearson >= 0.90 o Spearman >= 0.95 con il target

Le feature `_lag` e `_roll` sono **escluse intenzionalmente** dal controllo di correlazione:
rappresentano valori storici legittimi, non informazione futura. Esce con codice 0 se
non rileva problemi, con codice 2 se trova anomalie.

```bash
py check_leak.py
```

---

## Output finali della pipeline

I file effettivamente usati per il modello in produzione sono in `DatasetFinale/`:

| File | Prodotto da |
|------|-------------|
| `train.csv` | `04_make_splits.py` (train_main_catboost.csv) |
| `test.csv` | `04_make_splits.py` (test_main_catboost.csv) |
| `feature_columns.json` | `04_make_splits.py` |
