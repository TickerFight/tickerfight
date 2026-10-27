# Large cap contro small cap: il premio di dimensione esiste, decennio per decennio?

**Domanda:** il premio di dimensione, cioè il vantaggio storico delle aziende piccole su quelle grandi, c'è davvero, decennio per decennio?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Sfidanti:** S&P 500 (grandi) contro S&P MidCap 400, Russell 2000 e S&P SmallCap 600, scelti prima di guardare i dati. Indici di prezzo in dollari (nessun dividendo), sempre confrontati a coppie sulla storia in comune.
- **Confronti:** rendimento annuo composto; differenza media mensile con bootstrap per anni; quota di mesi vinti; decenni; finestre mobili di cinque e dieci anni; scimmie che ogni mese scelgono a caso tra grandi e piccole.

## Cosa c'è in questa cartella

```
large-cap-contro-small-cap-il-premio-di-dimensione-esiste-decennio-per-decennio/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica i quattro indici
    ├── 02_backtest_e_test.py  coppie, decenni, finestre mobili, bootstrap, scimmie
    ├── 03_grafici.py          i tre grafici
    ├── config.py              indici, parametri e ipotesi, scritti prima dei risultati
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/large-cap-contro-small-cap-il-premio-di-dimensione-esiste-decennio-per-decennio
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
