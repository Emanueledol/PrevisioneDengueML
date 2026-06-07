# modello_utilizzato/tests/

Test di verifica del modello in produzione.

## `smoke_inference.py`

Smoke test eseguibile senza configurazione manuale. Verifica tre cose:

1. **Caricamento** -- il file `.cbm` esiste ed è leggibile da CatBoost
2. **Range predizioni** -- i valori `log_cases_per_100k` sono in `[-1.0, 10.0]`
   e i casi assoluti sono non negativi e sotto una soglia massima ragionevole
3. **Copertura paesi** -- nessuno degli 11 paesi produce `NaN`

Esce con successo se tutti i controlli passano; lancia un `AssertionError` con
messaggio esplicativo al primo fallimento.

```bash
python modello_utilizzato/tests/smoke_inference.py
```

Usa `assets/test_reference.csv` come input (una copia del test set 2022-2023),
quindi non dipende da `DatasetFinale/` ed è eseguibile in isolamento.
