# PAC dal 2000: il decennio perso

**Domanda:** un piano di accumulo mensile partito nel 2000 sull'S&P 500 ha davvero battuto il versamento unico, e quanto dipende dalla data di partenza?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Dati:** S&P 500 (indice di prezzo) mensile.
- **Confronto:** PAC con commissioni e tasse contro versamento unico dello stesso capitale, su tutte le date di partenza.
- **Test:** rango della partenza 2000 tra tutte le partenze, serie rimescolate (scimmie), confronto con la partenza 1929.

## Cosa c'è in questa cartella

```
pac-dal-2000-il-decennio-perso/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica i dati da Yahoo Finance
    ├── 02_backtest_e_test.py  calcoli e test statistici
    ├── 03_grafici.py          i grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/pac-dal-2000-il-decennio-perso
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
