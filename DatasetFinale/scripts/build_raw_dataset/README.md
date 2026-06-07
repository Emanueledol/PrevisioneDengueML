# build_raw_dataset -- Pipeline di raccolta e preparazione del dataset grezzo

Script che costruiscono `DatasetFinale/dataset_raw.csv` a partire dalle tre fonti
dati grezze. Non hanno un ordine rigido tra loro (raccolgono sorgenti indipendenti),
ma `merge_dati.py` va eseguito per ultimo perché unifica gli output degli altri.

---

## Sorgenti dati

| Cartella | Contenuto |
|----------|-----------|
| `DatiGeologici/` | File NetCDF Copernicus (variabili climatiche mensili: temperatura, precipitazioni, pressione, LAI) |
| `DatiEpidemiologici/` | File `.xlsx` per paese con i casi di dengue segnalati (fonte WHO/PAHO) |
| `DatiSocioEconomici/` | Indicatori socioeconomici World Bank (GDP, densità di popolazione, ecc.) |

---

## Script

### `carica_dati_socioeconomici.py`
Scarica via API World Bank (libreria `wbgapi`) gli indicatori socioeconomici per
i 12 paesi del campione (11 del modello + India come donatore per l'imputazione).

Indicatori scaricati:
- `Pop_Density`, `GDP_per_capita_PPP`, `GDP_nominal`, `Gross_capital_formation_pct`
- `Forest_area_pct`, `Rural_pop_pct`, `Urban_pop_pct`, `Safe_water_access_pct`

Output: `DatiSocioEconomici/dati_socio_economici_tesi.csv`.

> Richiede connessione internet. Per esecuzioni offline usare il CSV già presente.

### `media_regionale_socioeconomica.py`
Imputa i valori mancanti negli indicatori socioeconomici usando la **media regionale**
per cluster geografici definiti manualmente:
- *Sud America*: Argentina, Bolivia, Uruguay imputati con la media di Brasile, Paraguay, Perù
- *Sud-Est Asiatico*: Tailandia imputata con i dati India

Output: `DatiSocioEconomici/Dati_socioeconomici_media_regionale.csv`.

### `union_dati_epid.py`
Unisce tutti i file `.xlsx` presenti in `DatiEpidemiologici/` (uno per paese)
in un unico dataframe, aggiungendo una colonna `provenienza_file` per tracciare
la sorgente. Standardizza i nomi delle colonne tra i diversi formati WHO/PAHO.

Output: `DatiEpidemiologici/dataset_dengue_unito.xlsx`.

### `interpolazione_cases.py`
Riempie i valori mancanti nella colonna `cases` del dataset epidemiologico unito
usando **interpolazione lineare** per paese. Necessario perché alcuni paesi
(es. Argentina) hanno buchi mensili nella serie storica segnalata.

Input: `DatiEpidemiologici/dataset_dengue_unito.xlsx`  
Output: `DatiEpidemiologici/dataset_unito_fixed.xlsx`

### `merge_dati.py`
Script principale di fusione -- va eseguito dopo tutti gli altri. Legge i tre
file NetCDF Copernicus da `DatiGeologici/`, estrae le variabili climatiche per
ciascun paese tramite una mappa di coordinate regionali, e le unisce con i dati
epidemiologici (`dataset_unito_fixed.xlsx`) e socioeconomici
(`Dati_socioeconomici_media_regionale.csv`).

Variabili climatiche estratte:
- `t2m` -- temperatura a 2 metri (K)
- `tp` / `tp_mm` -- precipitazioni totali (m e mm)
- `sp` -- pressione superficiale (Pa)
- `lai_hv` / `lai_lv` -- indice di area fogliare (vegetazione alta e bassa)

Output: `DatasetFinale/dataset_raw.csv` -- il dataset grezzo unificato con tutte
le sorgenti allineate su base mensile e per paese (2014-2024).

---

## Ordine di esecuzione consigliato

```
1. carica_dati_socioeconomici.py   <- scarica da World Bank API
2. media_regionale_socioeconomica.py
3. union_dati_epid.py
4. interpolazione_cases.py
5. merge_dati.py                   <- produce dataset_raw.csv
```

---

## Output finale

`DatasetFinale/dataset_raw.csv` -- punto di partenza per
`build_panel_splits/01_build_clean_panel.py`.
