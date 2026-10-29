# Quanti anni di dati servono per fidarsi?

**Domanda:** quanto è stabile il rapporto di Sharpe misurato su pochi anni di dati? Quanti anni servono perché un backtest dica qualcosa di affidabile?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Dati veri:** Sharpe dell'S&P 500 (indice di prezzo, tasso zero) su tutte le finestre di 1, 2, 3, 5, 10, 20 e 30 anni, una per mese di partenza.
- **Simulazione:** una strategia con Sharpe vero 0,5 e rendimenti normali indipendenti; per ogni durata si estraggono media e varianza campionarie dalle loro distribuzioni esatte.
- **Misure:** quota di Sharpe negativi, ampiezza tra 5° e 95° percentile, probabilità di Sharpe negativo e potenza del test al 95%.

## Cosa c'è in questa cartella

```
quanti-anni-di-dati-servono-per-fidarsi/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica l'S&P 500 dal 1927 (i dati sono quelli già usati negli articoli 301, 426 e 13)
    ├── 02_backtest_e_test.py  Sharpe su tutte le finestre di 1–30 anni e simulazione con Sharpe vero noto
    ├── 03_grafici.py          i grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            Sharpe su finestre mobili, simulazione esatta dello Sharpe campionario
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/quanti-anni-di-dati-servono-per-fidarsi
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
