# DatasetFinale/scripts/

Pipeline completa che costruisce il dataset finale a partire dalle sorgenti grezze.
Organizzata in due fasi sequenziali:

```
build_raw_dataset/    ->    build_panel_splits/
(fonti grezze ->            (dataset_raw.csv ->
 dataset_raw.csv)           train.csv / test.csv)
```

## Fase 1 -- `build_raw_dataset/`

Raccoglie e fonde le tre sorgenti dati indipendenti:
- Dati climatici Copernicus (NetCDF)
- Dati epidemiologici WHO/PAHO (xlsx per paese)
- Indicatori socioeconomici World Bank (CSV)

Output: `DatasetFinale/dataset_raw.csv`

## Fase 2 -- `build_panel_splits/`

Costruisce il panel in formato modello-ready:
aggiunge target, lag, rolling mean e stagionalità, poi divide in train/test.

Output: `DatasetFinale/train.csv` e `DatasetFinale/test.csv`

Vedere i README nelle sottocartelle per i dettagli di ogni script.
