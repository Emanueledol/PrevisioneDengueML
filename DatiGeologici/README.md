# DatiGeologici/

Dati climatici mensili scaricati da **Copernicus ERA5** (European Centre for Medium-Range Weather Forecasts).
Formato NetCDF (`.nc`), griglia spaziale ritagliata sulle aree geografiche dei paesi del campione.

## File

| File | Area geografica | Paesi inclusi |
|------|----------------|---------------|
| `Copernicus_SudAmerica_Messico.nc` | Sud America + Messico | ARG, BOL, BRA, CRI, GTM, HND, MEX, PER, PRY, URY |
| `Copernicus_India.nc` | Subcontinente indiano | IND (usato come donatore per imputazione THA) |
| `Copernicus_Thai.nc` | Sud-Est Asiatico | THA |
| `DatiGeologici.rar` | -- | Archivio di backup dei tre file .nc |

## Variabili contenute

| Variabile | Descrizione | Unità |
|-----------|-------------|-------|
| `t2m` | Temperatura dell'aria a 2 metri | K (Kelvin) |
| `tp` | Precipitazioni totali | m (metri) |
| `sp` | Pressione superficiale | Pa (Pascal) |
| `lai_hv` | Leaf Area Index -- vegetazione alta | m^2/m^2 |
| `lai_lv` | Leaf Area Index -- vegetazione bassa | m^2/m^2 |

Le variabili sono aggregate su base **mensile** per paese tramite media spaziale
delle celle di griglia che ricadono nel territorio nazionale.
L'estrazione e l'aggregazione sono eseguite da `DatasetFinale/scripts/build_raw_dataset/merge_dati.py`.

## Note

- I file `.nc` **non sono inclusi nel repository** perché superano il limite di 100 MB per file imposto da GitHub (`Copernicus_SudAmerica_Messico.nc` = 625 MB, `Copernicus_India.nc` = 173 MB). Solo `Copernicus_Thai.nc` (56 MB) sarebbe sotto soglia, ma è escluso per coerenza.
- Per riprodurre la pipeline, scaricare i file ERA5 dal portale Copernicus Climate Data Store: [cds.climate.copernicus.eu](https://cds.climate.copernicus.eu). Il dataset di riferimento è **ERA5 monthly averaged data on single levels** (variabili: 2m temperature, total precipitation, surface pressure, LAI high/low vegetation), ritagliato sulle bounding box dei paesi del campione, periodo 2014-2024.
- Periodo temporale: 2014-2024.
- La conversione `tp` da metri a millimetri (`tp_mm = tp x 1000`) è applicata in `merge_dati.py`.
