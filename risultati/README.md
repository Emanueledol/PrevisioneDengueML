# risultati/

Output completi del modello CatBoost sul test set 2022-2023.
Generati da `genera_risultati.py` nella root del progetto.

## Contenuto

| Cartella / File | Contenuto |
|-----------------|-----------|
| `plots/` | Grafici PNG (11 per paese + 4 aggregati) + PDF con tutti i plot in sequenza |
| `metrics/` | Metriche di performance (globali, per paese, per anno, feature importance) |
| `predictions/` | Predizioni complete su train e test con valori reali affiancati |
| `parameters/` | Parametri del modello e specifica delle feature |
| `conclusioni.md` | Analisi e commento dei risultati, nota metodologica sul setup di valutazione |

## Risultati principali (test 2022-2023, log-space)

| Metrica | Valore |
|---------|--------|
| R^2      | 0.876  |
| MAE     | 0.375  |
| RMSE    | 0.532  |
| sMAPE   | 29.9%  |

## Rigenerare i risultati

```bash
python genera_risultati.py
```

Sovrascrive tutti i file in questa cartella (plots, metrics, predictions, parameters).
`conclusioni.md` non viene rigenerata automaticamente -- aggiornarla manualmente
se i risultati cambiano.
