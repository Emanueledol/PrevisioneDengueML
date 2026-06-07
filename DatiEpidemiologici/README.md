# DatiEpidemiologici/

Dati grezzi sui casi di dengue segnalati per paese, scaricati da **WHO PAHO**
(Pan American Health Organization) e WHO Global Health Observatory.
Periodo: 2014-2024 (copertura variabile per paese).

## File dati grezzi -- uno per paese

| File | Paese | ISO3 |
|------|-------|------|
| `dengue-global-data-argentina-2026-05-03 (1).xlsx` | Argentina | ARG |
| `dengue-global-data-bolivia-2026-05-03 (1).xlsx` | Bolivia | BOL |
| `dengue-global-data-brazil-2026-05-03.xlsx` | Brasile | BRA |
| `dengue-global-data-costarica-2026-05-03.xlsx` | Costa Rica | CRI |
| `dengue-global-data-guatemala-2026-05-03.xlsx` | Guatemala | GTM |
| `dengue-global-data-honduras-2026-05-03.xlsx` | Honduras | HND |
| `dengue-global-data-messico-2026-05-03.xlsx` | Messico | MEX |
| `dengue-global-data-paraguay-2026-05-03.xlsx` | Paraguay | PRY |
| `dengue-global-data-peru-2026-05-03.xlsx` | Perù | PER |
| `dengue-global-data-thailandia-2026-05-03.xlsx` | Tailandia | THA |
| `dengue-global-data-uruguay-2026-05-03.xlsx` | Uruguay | URY |

> L'India non è inclusa nel modello finale ma è presente in `DatiGeologici/` come
> donatore climatico per l'imputazione di Tailandia.

## File intermedi prodotti dagli script

| File | Prodotto da | Contenuto |
|------|-------------|-----------|
| `dataset_dengue_unito.xlsx` | `UnioneDatiEpid.py` | Tutti i paesi uniti in un unico dataframe |
| `dataset_unito_fixed.xlsx` | `Interpolazione_cases.py` | Come sopra, con buchi mensili interpolati |

## Script

### `UnioneDatiEpid.py`
Legge tutti i file `.xlsx` della cartella e li concatena in `dataset_dengue_unito.xlsx`.
Aggiunge la colonna `provenienza_file` per tracciare la sorgente di ciascuna riga.

### `Interpolazione_cases.py`
Applica interpolazione lineare per paese sulla colonna `cases` di `dataset_dengue_unito.xlsx`,
riempiendo i mesi mancanti nella serie storica. Salva il risultato in `dataset_unito_fixed.xlsx`,
che è il file usato da `merge_dati.py` come input epidemiologico.

## Ordine di esecuzione

```
1. UnioneDatiEpid.py         -> dataset_dengue_unito.xlsx
2. Interpolazione_cases.py   -> dataset_unito_fixed.xlsx
```
