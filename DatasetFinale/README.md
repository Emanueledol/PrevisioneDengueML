# DatasetFinale/

Contiene il dataset effettivamente usato per addestrare e valutare il modello finale,
più la pipeline di script che lo ha prodotto.

## File dataset

| File | Righe | Descrizione |
|------|-------|-------------|
| `dataset_raw.csv` | ~1320 | Dataset grezzo unificato (climatico + epidemiologico + socioeconomico), 2014-2024, 11 paesi |
| `train.csv` | 924 | Split di training 2014-2021 con tutte le 39 feature ingegnerizzate |
| `test.csv` | 264 | Split di test 2022-2023 (24 mesi x 11 paesi) |
| `feature_columns.json` | -- | Specifica delle 39 feature, target e colonne categoriali per CatBoost e MLP |

### Struttura delle colonne in train.csv / test.csv

- **Identificatori:** `year`, `month`, `economy` (ISO3), `date`, `cases_raw`, `population`
- **Feature climatiche:** `t2m`, `tp`, `sp`, `lai_hv`, `lai_lv`, `tp_mm`
- **Feature socioeconomiche:** `Forest_area_pct`, `GDP_nominal`, `GDP_per_capita_PPP`, `Gross_capital_formation_pct`, `Pop_Density`, `Rural_pop_pct`, `Safe_water_access_pct`, `Urban_pop_pct`
- **Lag climatici:** `t2m_lag1/2/3`, `tp_mm_lag1/2/3`
- **Stagionalità:** `sin_month`, `cos_month`
- **Lag epidemiologici:** `cases_lag1/2/3/12`, `cases_per_100k_lag1/2/3/12`, `log_cases_per_100k_lag1/2/3/12`
- **Rolling mean:** `cases_per_100k_roll3/6/12_mean`, `log_cases_per_100k_roll3/6/12_mean`
- **Target:** `log_cases_per_100k`

## Cartella scripts/

Contiene la pipeline completa che trasforma i dati grezzi nel dataset finale.

```
scripts/
|-- build_raw_dataset/   # Da DatiGeologici/ + DatiEpidemiologici/ + DatiSocioEconomici/ -> dataset_raw.csv
+-- build_panel_splits/  # Da dataset_raw.csv -> train.csv / test.csv
```

Vedere i README nelle rispettive sottocartelle per i dettagli di ciascuno script.
