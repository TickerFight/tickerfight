# ACF e PACF dei rendimenti: l'S&P 500 ha memoria?

**Domanda:** i rendimenti giornalieri dell'S&P 500 hanno memoria? Che cosa dicono l'autocorrelazione (ACF) e l'autocorrelazione parziale (PACF), e dove sta davvero la memoria: nel segno o nella grandezza dei movimenti?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Serie:** rendimenti logaritmici giornalieri dell'S&P 500 (indice di prezzo, senza dividendi), il loro valore assoluto e il loro quadrato.
- **Misure:** ACF e PACF ai ritardi 1–20 (fino a 100 per i movimenti); banda al 99% di una serie senza memoria; Ljung-Box su 20 ritardi; correzione di Holm sui 20 test.
- **Caso:** 1.000 rimescolamenti dei rendimenti su tutta la storia (stessa distribuzione, nessuna memoria).
- **Finestre:** decenni di 2.520 sedute non sovrapposti; quota di varianza spiegata da un AR(1) (ACF1 al quadrato).

## Cosa c'è in questa cartella

```
acf-e-pacf-dei-rendimenti-l-sp-500-ha-memoria/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica l'S&P 500 dal 1927 (i dati sono quelli già usati nell'articolo 301)
    ├── 02_backtest_e_test.py  ACF/PACF su intero periodo e finestre di dieci anni, Ljung-Box, rimescolamenti
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            ACF, PACF (Durbin-Levinson), Ljung-Box, Holm, finestre
    └── verifica_motore.py     controlli su dati inventati (rumore bianco, AR(1), AR(2), grappoli di volatilità)
```

## Come si rifà

```bash
cd articoli/acf-e-pacf-dei-rendimenti-l-sp-500-ha-memoria
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
