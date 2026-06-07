# Legenda e guida alla lettura dei grafici

Tutti i grafici sono stati generati da `genera_risultati.py` sul test set 2022-2023
(264 osservazioni: 24 mesi x 11 paesi). Il modello è un CatBoost che predice
`log_cases_per_100k` (log1p dei casi per 100.000 abitanti).

---

## Grafici per paese -- `{ISO3}_pred_vs_real.png` (11 file)

Un file per ciascun paese: ARG, BOL, BRA, CRI, GTM, HND, MEX, PER, PRY, THA, URY.
Ogni figura è divisa in **due pannelli**:

### Pannello superiore -- Casi assoluti (2014-2023)

Mostra l'intera serie storica dei casi di dengue segnalati nel paese.

| Elemento | Significato |
|----------|-------------|
| Linea blu chiara (2014-2021) | Casi reali nel periodo di training -- dati su cui il modello è stato addestrato |
| Linea blu piena (2022-2023) | Casi reali nel periodo di test -- mai visti durante il training |
| Linea rossa tratteggiata (2022-2023) | Casi **predetti** dal modello sul test set |
| Linea grigia verticale tratteggiata | Separazione tra train e test (1 gennaio 2022) |

L'asse Y è in **casi assoluti** (non normalizzati), quindi paesi grandi come Brasile
e Messico avranno valori molto più alti rispetto a Uruguay o Costa Rica.

### Pannello inferiore -- Log(casi/100k) sul test (2022-2023)

Mostra il confronto reali vs predetti nel solo periodo di test, nella scala usata
dal modello come target (`log_cases_per_100k = log1p(casi / popolazione x 100.000)`).

| Elemento | Significato |
|----------|-------------|
| Linea blu piena | Valori reali di `log_cases_per_100k` |
| Linea rossa tratteggiata | Valori predetti dal modello |
| R^2 nel titolo | Coefficiente di determinazione sul test (quanto la predizione spiega la varianza reale) |
| MAE nel titolo | Errore assoluto medio in scala logaritmica |

La scala logaritmica elimina l'effetto della dimensione del paese e rende
le performance comparabili tra nazioni con popolazioni molto diverse.

---

## `totale_mensile_aggregato.png`

Aggrega i casi di tutti e 11 i paesi mese per mese sul test set 2022-2023.

| Elemento | Significato |
|----------|-------------|
| Linea blu | Totale casi reali (somma degli 11 paesi) |
| Linea rossa tratteggiata | Totale casi predetti (somma delle predizioni per paese) |

Permette di valutare il **comportamento globale** del modello: se sovra- o
sottostima sistematicamente, se cattura la stagionalità aggregata e i picchi
(es. grande outbreak Sud America inizio 2023).

---

## `scatter_all_countries.png`

Scatter plot di tutti i 264 punti del test set: asse X = valori reali di
`log_cases_per_100k`, asse Y = valori predetti. Ogni paese ha un colore diverso.

| Elemento | Significato |
|----------|-------------|
| Ogni punto | Una singola coppia (mese, paese) del test |
| Colore | Paese (legenda in figura) |
| Linea nera tratteggiata (`y = x`) | Predizione perfetta: i punti sopra la diagonale sono sovrastimati, quelli sotto sottostimati |
| R^2 nel titolo | R^2 globale calcolato su tutti i 264 punti |

Permette di identificare **cluster di errore** (es. punti di un paese sistematicamente
distanti dalla diagonale) e outlier (picchi epidemici difficili da prevedere).

---

## `residuals_per_country.png`

Boxplot dei residui per ciascun paese: `residuo = predetto - reale` in scala `log_cases_per_100k`.

| Elemento | Significato |
|----------|-------------|
| Scatola (box) | Intervallo interquartile (IQR) dei residui -- il 50% centrale delle predizioni |
| Linea centrale nella box | Mediana dei residui |
| Baffi (whiskers) | Estensione fino a 1.5x IQR |
| Punti fuori dai baffi | Outlier (mesi con errore eccezionale) |
| Linea rossa tratteggiata (`y = 0`) | Residuo zero = predizione perfetta |

Un paese con la mediana **sopra lo zero** tende a essere sistematicamente sovrastimato;
sotto lo zero, sottostimato. Un IQR ampio indica alta variabilità dell'errore.

---

## `feature_importance.png`

Grafico a barre orizzontali delle top-20 feature per importanza CatBoost (score: gain).

| Elemento | Significato |
|----------|-------------|
| Barre | Importanza percentuale di ciascuna feature rispetto al totale |
| Ordine | Dalla più alla meno importante (in alto la più rilevante) |

Le due feature dominanti (`cases_per_100k_lag1` e `log_cases_per_100k_lag1`,
circa 38% combinato) mostrano la **natura autoregressiva** del segnale: il mese
precedente è il predittore più informativo. Il lag-12 cattura la **stagionalità
annuale**. `Pop_Density` è la prima feature strutturale (non temporale).

> **Nota sul setup di valutazione:** i lag usano i valori reali del mese precedente
> (rolling 1-step-ahead), non le predizioni propagate. Vedere `risultati/conclusioni.md`
> 0 per la discussione metodologica completa.
