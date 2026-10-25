# Volatility targeting: ridurre le azioni quando il mercato trema migliora il portafoglio?

**Domanda:** ridurre l'esposizione quando la volatilità sale rende un portafoglio azionario migliore, o solo più tranquillo?

L'articolo completo, con risultati e grafici, è sul blog: [Volatility targeting: ridurre le azioni quando il mercato trema migliora il portafoglio?](https://ticker-fight.blogspot.com/2026/10/volatility-targeting-ridurre-le-azioni.html).

## Il disegno

- **Strategia:** a fine mese si misura la volatilità degli ultimi 21 giorni di borsa; il peso in azioni del mese successivo è obiettivo (10% annuo) diviso volatilità, con tetto a 1 (nessuna leva); il resto è in cassa, che non rende.
- **Niente look-ahead:** il peso calcolato alla chiusura dell'ultima seduta del mese si scambia alla chiusura della seduta seguente e lavora dal rendimento della seduta ancora dopo.
- **Indici:** S&P 500, Nasdaq Composite, DAX, FTSE 100, CAC 40, Nikkei 225, scelti prima di guardare i dati. Indici di prezzo, valuta locale.
- **Confronti:** buy & hold; buy & hold con la stessa volatilità della strategia (peso fisso); scimmie con gli stessi pesi in mesi casuali.
- **Test:** differenza di Sharpe con bootstrap a blocchi (21 giorni), p-value delle scimmie con correzione di Holm, cinque varianti di robustezza riportate tutte, due finestre di crisi fissate in anticipo.
- **Costi:** 5 punti base su ogni scambio. Le tasse non sono modellate (dichiarato nei limiti).

## Cosa c'è in questa cartella

```
volatility-targeting-ridurre-le-azioni-quando-il-mercato-trema-migliora-il-portafoglio/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica sei indici azionari
    ├── 02_backtest_e_test.py  strategia, buy & hold, stessa volatilità, scimmie, bootstrap, varianti
    ├── 03_grafici.py          i cinque grafici
    ├── config.py              indici, parametri, varianti e ipotesi, scritti prima dei risultati
    ├── motore.py              volatilità, pesi mensili, posizione ritardata, costi, metriche, bootstrap
    └── verifica_motore.py     controlli su dati inventati (conti a mano, assenza di look-ahead)
```

## Come si rifà

```bash
cd articoli/volatility-targeting-ridurre-le-azioni-quando-il-mercato-trema-migliora-il-portafoglio
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
