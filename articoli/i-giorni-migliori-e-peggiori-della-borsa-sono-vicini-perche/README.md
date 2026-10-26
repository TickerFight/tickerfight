# I giorni migliori e peggiori della Borsa sono vicini: perché?

**Domanda:** i giorni di Borsa migliori e peggiori (l'1% più alto e l'1% più basso dei rendimenti giornalieri) cadono vicini nel tempo? Quanto più del caso? E la spiegazione sta nella volatilità di ieri?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Giorni estremi:** l'1% di sedute con il rendimento più alto e l'1% con il più basso, per ciascun indice.
- **Vicinanza:** distanza in sedute tra ogni giorno peggiore e il giorno migliore più vicino; quota di giorni peggiori con un migliore entro 10 sedute.
- **Il caso:** 2.000 storie per indice con gli stessi rendimenti giornalieri in ordine rimescolato. Otto test (4 indici per due versioni dei dati) corretti con Holm.
- **La volatilità:** quintili della volatilità di ieri (solo dati fino a ieri) e rendimenti divisi per la volatilità EWMA di ieri.
- **Il filtro:** fuori dal mercato quando la volatilità a 20 sedute supera l'80° percentile della propria storia fino a ieri; contro buy & hold e 1.000 scimmie con lo stesso numero di sedute in liquidità; con e senza costo di 0,1% per passaggio.
- **Indici:** di prezzo (niente dividendi), in valuta locale.

## Cosa c'è in questa cartella

```
i-giorni-migliori-e-peggiori-della-borsa-sono-vicini-perche/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica S&P 500, DAX, FTSE 100, Nikkei 225
    ├── 02_backtest_e_test.py  vicinanza, caso, volatilità, filtro
    ├── 03_grafici.py          i cinque grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            giorni estremi, distanze, volatilità di ieri, filtro, scimmie, Holm
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/i-giorni-migliori-e-peggiori-della-borsa-sono-vicini-perche
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
