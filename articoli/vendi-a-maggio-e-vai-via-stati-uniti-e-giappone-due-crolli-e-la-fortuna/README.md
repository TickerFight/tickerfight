# «Vendi a maggio e vai via»: Stati Uniti e Giappone, due crolli e la fortuna

**Domanda:** tenere le azioni solo da novembre ad aprile batte il tenerle sempre, su quattro indici, e il risultato regge se si tolgono gli anni dei grandi crolli?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Dati:** S&P 500, Dow Jones, Nasdaq Composite e Nikkei 225.
- **Regola:** azioni da novembre ad aprile, liquidità da maggio a ottobre, confrontata con il buy & hold con costi e tasse.
- **Test:** bootstrap a blocchi della differenza di Sharpe, scimmie (stagioni a caso), stagioni escluse (1987 e 1998), quota di stagioni.

## Cosa c'è in questa cartella

```
vendi-a-maggio-e-vai-via-stati-uniti-e-giappone-due-crolli-e-la-fortuna/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica i dati da Yahoo Finance
    ├── 02_backtest_e_test.py  calcoli e test statistici
    ├── 03_grafici.py          i grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── simulazione.py
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/vendi-a-maggio-e-vai-via-stati-uniti-e-giappone-due-crolli-e-la-fortuna
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
