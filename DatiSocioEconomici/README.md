# DatiSocioEconomici/

Indicatori socioeconomici annuali scaricati dalla **World Bank Open Data API**
per i paesi del campione. Periodo: 2014-2023.

## File

| File | Contenuto |
|------|-----------|
| `dati_socio_economici_tesi.csv` | Dati grezzi scaricati via API -- valori mancanti presenti |
| `Dati_socioeconomici_media_regionale.csv` | Dati dopo imputazione regionale -- file usato nella pipeline |

## Indicatori inclusi

| Codice World Bank | Colonna nel dataset | Descrizione |
|-------------------|---------------------|-------------|
| `EN.POP.DNST` | `Pop_Density` | Densità di popolazione (ab/km^2) |
| `NY.GDP.PCAP.PP.CD` | `GDP_per_capita_PPP` | PIL pro capite a parità di potere d'acquisto (USD) |
| `NY.GDP.MKTP.CD` | `GDP_nominal` | PIL nominale (USD correnti) |
| `NE.GDI.FTOT.ZS` | `Gross_capital_formation_pct` | Formazione lorda di capitale (% PIL) |
| `AG.LND.FRST.ZS` | `Forest_area_pct` | Superficie forestale (% territorio) |
| `SP.RUR.TOTL.ZS` | `Rural_pop_pct` | Popolazione rurale (% totale) |
| `SP.URB.TOTL.IN.ZS` | `Urban_pop_pct` | Popolazione urbana (% totale) |
| `SH.H2O.SMDW.ZS` | `Safe_water_access_pct` | Accesso ad acqua potabile sicura (% popolazione) |

## Script

### `DatiSocioEconomici.py`
Scarica i dati grezzi via `wbgapi` per i 12 paesi (ARG, BOL, BRA, CRI, GTM, HND, MEX,
PRY, PER, URY, THA, IND) e li salva in `dati_socio_economici_tesi.csv`.
Richiede connessione internet; per esecuzioni offline usare il CSV già presente.

### `MediaRegionaleDatiSocioEconomici.py`
Imputa i valori mancanti con **media regionale per cluster geografico**:
- *Sud America*: Argentina, Bolivia, Uruguay <- media di Brasile, Paraguay, Perù
- *Sud-Est Asiatico*: Tailandia <- dati India

Output: `Dati_socioeconomici_media_regionale.csv`, usato da `merge_dati.py`.

## Ordine di esecuzione

```
1. DatiSocioEconomici.py              -> dati_socio_economici_tesi.csv
2. MediaRegionaleDatiSocioEconomici.py -> Dati_socioeconomici_media_regionale.csv
```
