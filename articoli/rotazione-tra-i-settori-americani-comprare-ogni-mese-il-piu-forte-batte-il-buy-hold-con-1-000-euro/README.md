# Rotazione tra i settori americani: comprare ogni mese il più forte batte il buy & hold, con 1.000 euro?

**Domanda:** se ogni mese si compra il settore americano che ha reso di più negli ultimi mesi, con 1.000 € di capitale, commissioni per ordine e tassa del 26%, si batte il semplice buy & hold dell'S&P 500? Condizioni di chi parte con poco: commissione per ordine in tre scenari, tassa con minusvalenze riportate, azioni frazionate.

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Regola:** all'ultima seduta di ogni mese si calcola il rendimento di prezzo degli ultimi L giorni di borsa dei nove ETF settoriali SPDR e si scelgono i K migliori; l'ordine parte alla chiusura della prima seduta del mese dopo (nessun look-ahead). Si vendono i settori usciti dalla classifica e si comprano quelli entrati. Regola principale: L = 126 (circa sei mesi), K = 1.
- **Prove dichiarate in anticipo:** L in {63, 126, 252} e K in {1, 3}, cioè sei rotazioni, nessuna scelta a posteriori.
- **Strumenti:** XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY (dollari, convertiti in euro con il cambio del giorno); riferimenti: ETF sull'S&P 500 (SPY) tenuto e i nove settori tenuti in parti uguali.
- **Condizioni:** 1.000 €; commissione 0 €, 2 € a ordine e 0,1% dell'importo; tassa 26% con compensazione delle minusvalenze; dividendi e imposta di bollo non considerati.
- **Test:** scimmie (stessi giorni di ordine e stesso numero di ordini, settore scelto a caso; una coda) e bootstrap a blocchi della differenza di rendimento giornaliero tra rotazione e buy & hold, per le due rotazioni a sei mesi, con la correzione di Holm.

## Cosa c'è in questa cartella

```
rotazione-tra-i-settori-americani-comprare-ogni-mese-il-piu-forte-batte-il-buy-hold-con-1-000-euro/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica i nove ETF settoriali, l'ETF sull'S&P 500 e il cambio euro-dollaro
    ├── 02_backtest_e_test.py  buy & hold, nove settori tenuti, sei rotazioni, scimmie, bootstrap, correzione di Holm
    ├── 03_grafici.py          i cinque grafici
    ├── config.py              strumenti, parametri e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore in euro: ordini, commissioni, tassa, minusvalenze, rotazione, scimmie
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/rotazione-tra-i-settori-americani-comprare-ogni-mese-il-piu-forte-batte-il-buy-hold-con-1-000-euro
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
