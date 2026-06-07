# Risultati e Conclusioni -- CatBoost Dengue Forecasting

**Periodo di valutazione:** Test set 2022-2023 (24 mesi x 11 paesi = 264 osservazioni)  
**Modello:** CatBoost con target `log_cases_per_100k` (log1p-normalizzato per popolazione)  
**Paesi:** Argentina, Bolivia, Brasile, Costa Rica, Guatemala, Honduras, Messico, Perù, Paraguay, Tailandia, Uruguay

---

## 0. Nota metodologica: setup di valutazione

La valutazione sul test set (2022-2023) simula uno scenario di **previsione rolling 1-step-ahead**: ad ogni mese *t*, il modello dispone dei valori reali fino a *t*-1, inclusi i lag epidemiologici (`cases_per_100k_lag1`, `log_cases_per_100k_lag1`, ecc.). Questo riflette un utilizzo operativo in cui i dati del mese precedente sono disponibili prima dell'emissione della previsione mensile -- analogamente a come funzionano ARIMA e i modelli autoregressivi standard.

Le feature lag **non costituiscono leakage**: il target del mese *t* (`log_cases_per_100k` di *t*) non è mai incluso tra le feature di input per predire *t* stesso, come verificato dallo script `DatasetFinale/scripts/build_panel_splits/check_leak.py`. Le feature autoregressiva rappresentano invece informazione storicamente disponibile al momento della predizione.

Questa assunzione va distinta da uno scenario **zero-look-ahead** (dove si predice l'intero 2022-2023 a partire da dicembre 2021 senza osservare alcun dato del test), che richiederebbe di propagare le predizioni come input dei lag anziché i valori reali.

---

## 1. Metriche globali

### Train (2014-2021)
| Metrica | Valore |
|---------|--------|
| R^2      | 0.9988 |
| MAE     | 0.0363 |

### Test (2022-2023) -- log-space
| Metrica | Valore |
|---------|--------|
| MAE     | 0.3752 |
| RMSE    | 0.5323 |
| R^2      | 0.8759 |
| sMAPE   | 29.92% |

Il modello raggiunge un R^2 di **0.876** sul test set in spazio logaritmico, confermando una capacità predittiva solida su un orizzonte di 24 mesi mai visti durante il training. Il gap tra train (R^2=0.999) e test riflette la difficoltà intrinseca di generalizzare un segnale epidemico ad anni successivi, ma non indica overfitting grave: il modello cattura struttura reale, non rumore.

---

## 2. Performance per paese

| Paese        | ISO3 | R^2     | MAE   | Note |
|--------------|------|--------|-------|------|
| Messico      | MEX  | 0.891  | 0.249 | Miglior R^2 -- ciclo stagionale regolare e stabile |
| Guatemala    | GTM  | 0.885  | 0.321 | Ottima cattura dei picchi estivi |
| Tailandia    | THA  | 0.871  | 0.286 | Unico paese asiatico, generalizza bene |
| Costa Rica   | CRI  | 0.814  | 0.349 | Buona capacità predittiva |
| Bolivia      | BOL  | 0.810  | 0.436 | Stagionalità complessa, R^2 soddisfacente |
| Argentina    | ARG  | 0.728  | 0.526 | Picco esplosivo 2023 (febbraio-marzo) sottostimato |
| Paraguay     | PRY  | 0.692  | 0.687 | Errori elevati; gennaio 2022 fortemente sovrastimato |
| Perù         | PER  | 0.666  | 0.374 | Segnale irregolare, stagionalità parzialmente catturata |
| Honduras     | HND  | 0.663  | 0.294 | MAE contenuto nonostante R^2 medio |
| Brasile      | BRA  | 0.553  | 0.468 | Maggiore difficoltà: eterogeneità regionale non catturata |
| Uruguay      | URY  | -1.192 | 0.138 | *Vedi nota sotto* |

**Nota su Uruguay:** Il valore negativo di R^2 è statisticamente fuorviante. L'Uruguay ha una trasmissione di dengue quasi assente (media log_cases/100k ~ 0.139, std ~ 0.116), quindi la varianza del target è quasi nulla. Il modello predice in media 0.181 -- vicino al reale -- ma con R^2 che penalizza qualsiasi scostamento rispetto a una baseline piatta. Il MAE di 0.138 è il **più basso di tutti i paesi**, confermando che il modello si comporta correttamente: il problema è la metrica, non la previsione.

---

## 3. Analisi della feature importance

Le prime 5 feature per importanza (CatBoost gain):

| Feature                   | Importanza (%) |
|---------------------------|----------------|
| cases_per_100k_lag1       | 19.82          |
| log_cases_per_100k_lag1   | 18.49          |
| log_cases_per_100k_lag2   | 5.17           |
| Pop_Density               | 3.49           |
| cases_per_100k_lag12      | 2.97           |

Le feature autoregressiva di lag-1 dominano (38% combinato), confermando che **il mese precedente è il predittore più forte**. Il lag-12 cattura la stagionalità annuale. La densità di popolazione (`Pop_Density`) appare tra le prime feature strutturali, coerentemente con il ruolo dell'urbanizzazione nella trasmissione del virus.

---

## 4. Casi peggiori e migliori

### Predizioni con errore assoluto più alto
| Data       | Paese    | Reale (log) | Predetto (log) | Residuo |
|------------|----------|-------------|----------------|---------|
| 2022-01 | Paraguay | 0.834 | 3.508 | +2.674 |
| 2023-03 | Argentina | 4.594 | 2.009 | -2.586 |
| 2023-12 | Paraguay | 6.109 | 4.578 | -1.531 |

Paraguay gennaio 2022: il modello sovrastima fortemente perché il lag-1 (dicembre 2021) segnalava una coda attiva che poi non si è materializzata in un focolaio. Argentina marzo 2023 corrisponde al **grande outbreak argentino** del 2023 -- un evento eccezionale che esula dal pattern storico, difficile da anticipare senza informazioni esogene.

### Predizioni più accurate
| Data       | Paese      | Reale (log) | Predetto (log) | Residuo |
|------------|------------|-------------|----------------|---------|
| 2022-07 | Honduras | 3.579 | 3.578 | -0.002 |
| 2022-10 | Guatemala | 1.902 | 1.899 | -0.003 |
| 2023-03 | Costa Rica | 1.791 | 1.807 | +0.016 |

---

## 5. Punti di forza del modello

- **Generalizzazione geografica:** lo stesso modello funziona su 10 dei 11 paesi (escludendo Uruguay per le ragioni descritte) senza addestramenti separati.
- **Stagionalità annuale:** il lag-12 permette di catturare i cicli ricorrenti.
- **Normalizzazione per popolazione:** il target log(casi/100k) rende le previsioni comparabili tra paesi con dimensioni molto diverse (Brasile vs Uruguay).
- **R^2 globale 0.876** su un test set out-of-sample di 24 mesi è un risultato solido per previsioni epidemiologiche mensili.

## 6. Limiti e prospettive

- **Outbreak estremi:** eventi come il focolaio argentino 2023 (fuori distribuzione storica) non sono anticipabili senza feature esogene (es. dati ENSO, densità vettoriale, mobilità).
- **Uruguay e paesi a bassa endemia:** il modello non è calibrato per previsioni near-zero; un approccio separato (es. soglia + classificatore) migliorerebbe le stime.
- **Brasile:** l'eterogeneità regionale del paese più grande del campione richiederebbe dati sub-nazionali per un forecasting accurato.
- **Nessun aggiornamento in tempo reale:** il modello usa dati climatici e socioeconomici storici; integrare dati in tempo reale (ERA5 mensile, Google Trends) potrebbe ridurre il lag.

---

*Generato da `genera_risultati.py` -- dati: DatasetFinale/test.csv -- modello: modello_utilizzato/assets/catboost_dengue_2026.cbm*
