# Prezzi adjusted e non adjusted: l'errore gonfia o sgonfia i risultati?

**Domanda:** quanto sbaglia chi valuta un backtest sulla colonna «Close» di Yahoo Finance invece che su «Adj Close», e che cosa succede se si usano prezzi non corretti per gli split?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Close contro Adj Close:** in Yahoo Finance `Close` è già corretta per gli split ma non per i dividendi; `Adj Close` è corretta anche per i dividendi (rendimento totale).
- **Sei strumenti scelti a priori:** SPY, QQQ, XLU, VNQ, Coca-Cola, Apple.
- **Regola 50/200 in quattro versioni:** segnale su Adj Close (corretta), segnale su Close, valutazione sui soli prezzi, segnale sul prezzo grezzo ricostruito (Close per il prodotto degli split successivi).
- **Niente commissioni né tasse:** l'obiettivo è isolare l'effetto dei dati.

## Cosa c'è in questa cartella

```
prezzi-adjusted-e-non-adjusted-l-errore-gonfia-o-sgonfia-i-risultati/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica sei strumenti con dividendi e split
    ├── 02_backtest_e_test.py  buy & hold sui soli prezzi e a rendimento totale, regola 50/200 in quattro versioni
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              strumenti, regole e ipotesi, scritti prima dei risultati
    ├── motore_vettoriale.py   segnale, posizione con ritardo, valore, rendimento annuo, ricostruzione del prezzo grezzo
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/prezzi-adjusted-e-non-adjusted-l-errore-gonfia-o-sgonfia-i-risultati
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
