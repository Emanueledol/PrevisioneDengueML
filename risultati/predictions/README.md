# risultati/predictions/

Predizioni complete del modello affiancate ai valori reali.

## File

### `test_predictions.csv`
Test set 2022-2023 (264 righe: 24 mesi x 11 paesi) con colonne aggiuntive:

| Colonna | Contenuto |
|---------|-----------|
| `log_pred` | Predizione del modello in log-space (`log_cases_per_100k`) |
| `cases_pred` | Casi assoluti stimati (inversa della normalizzazione) |
| `cases_per_100k_pred` | Casi per 100.000 abitanti stimati |
| `cases_real` | Casi reali (`cases_raw`) |
| `log_real` | Valore reale del target (`log_cases_per_100k`) |

### `train_predictions.csv`
Training set 2014-2021 con le stesse colonne aggiuntive. Utile per diagnosticare
l'adattamento del modello al periodo di training e confrontare il gap train/test.

## Residui

Il residuo per ogni osservazione è calcolabile come `log_pred - log_real`.
Un residuo positivo indica sovrastima, negativo sottostima.
