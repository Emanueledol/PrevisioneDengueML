# Previsione Mensile del Dengue -- Progetto di Tesi

Studio di forecasting mensile dei casi di dengue su 11 paesi (9 America Latina + Messico + Tailandia), periodo 2014-2023. Il modello finale è un CatBoost con target log-normalizzato per popolazione (`log_cases_per_100k`), addestrato con rolling cross-validation temporale.

**Paper di riferimento:** `2026_MED_Dengue.pdf`

---

## Struttura del repository

```
.
|-- DatiGeologici/          # Dati climatici Copernicus (NetCDF, ~1.6 GB, locali)
|-- DatiEpidemiologici/     # Dati dengue grezzi per paese (WHO/PAHO, .xlsx) + script raccolta
|-- DatiSocioEconomici/     # Indicatori World Bank (GDP, popolazione, ecc.) + script
|
|-- DatasetFinale/          # Dataset effettivamente usato per train/test
|   |-- dataset_raw.csv         # Dataset unificato grezzo (2014-2024, tutti i paesi)
|   |-- train.csv               # Split train 2014-2021 (feature ingegnerizzate)
|   |-- test.csv                # Split test 2022-2023
|   |-- feature_columns.json    # Specifica delle 39 feature + categoriale economy
|   +-- scripts/
|       |-- build_raw_dataset/  # Script ETL: merge climatico, unione epid., interpolazione
|       +-- build_panel_splits/ # Pipeline panel (01->07): clean, targets, features, splits
|
|-- modello_utilizzato/     # Modello CatBoost di produzione + codice inferenza
|   |-- assets/             #   .cbm, feature_columns.json, metadata, test_reference.csv
|   |-- src/inference.py    #   predict_log() e predict_cases()
|   +-- tests/              #   smoke test eseguibile
|
|-- risultati/              # Output completi del modello sul test set
|   |-- plots/              #   grafici per paese + scatter + residui + feature importance
|   |-- metrics/            #   metriche globali, per paese, per anno, feature importance
|   |-- predictions/        #   predizioni complete train e test (.csv)
|   |-- parameters/         #   parametri CatBoost, feature spec, metadata
|   +-- conclusioni.md      #   analisi e commento dei risultati
|
|-- genera_risultati.py     # Script per rigenerare tutti i risultati
|-- requirements.txt        # Dipendenze Python
+-- 2026_MED_Dengue.pdf     # Paper di riferimento
```

---

## Avvio rapido

### Smoke test del modello
```bash
python modello_utilizzato/tests/smoke_inference.py
```

### Rigenerare tutti i risultati
```bash
python genera_risultati.py
```

### Inferenza su nuovi dati
```python
import pandas as pd
from modello_utilizzato.src.inference import predict_log, predict_cases

df = pd.read_csv("DatasetFinale/test.csv")
log_preds  = predict_log(df)    # log_cases_per_100k
case_preds = predict_cases(df)  # casi assoluti (richiede colonna 'population')
```

### Installare le dipendenze
```bash
pip install -r requirements.txt
```

---

## Pipeline dati (sintesi)

```
DatiGeologici/     --+
DatiEpidemiologici/ -|  build_raw_dataset/  ->  dataset_raw.csv
DatiSocioEconomici/ -+

dataset_raw.csv  ->  build_panel_splits/ (01-07)  ->  train.csv / test.csv

train.csv  ->  CatBoost training  ->  catboost_dengue_2026.cbm
test.csv   ->  valutazione  ->  R^2 = 0.876 (log-space, 24 mesi, 11 paesi)
```

## Risultati principali

| Metrica   | Test 2022-2023 |
|-----------|---------------|
| R^2        | 0.876         |
| MAE       | 0.375 (log)   |
| RMSE      | 0.532 (log)   |
| sMAPE     | 29.9%         |

Migliori performer: Messico (R^2=0.891), Guatemala (R^2=0.885), Tailandia (R^2=0.871).  
Vedi `risultati/conclusioni.md` per l'analisi completa.

## Setup di valutazione

La valutazione simula uno scenario **rolling 1-step-ahead**: ad ogni mese *t* del test set, il modello dispone dei valori reali fino a *t*-1, inclusi i lag epidemiologici. Questo riflette un utilizzo operativo in cui i dati del mese precedente sono disponibili prima dell'emissione della previsione. Il target di *t* non è mai incluso tra le feature di input; l'assenza di leakage è verificata da `DatasetFinale/scripts/build_panel_splits/check_leak.py`.

---

## Dati climatici

I file NetCDF Copernicus (`DatiGeologici/`) pesano ~1.6 GB e sono conservati localmente. Per riprodurre la pipeline completa devono essere presenti in `DatiGeologici/` prima di eseguire `build_raw_dataset/merge_dati.py`.
