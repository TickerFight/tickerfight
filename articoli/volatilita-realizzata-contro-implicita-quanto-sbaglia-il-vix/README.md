# Volatilità realizzata contro implicita: quanto sbaglia il VIX?

L'articolo completo, con risultati e grafici, è sul blog: [Volatilità realizzata contro implicita: quanto sbaglia il VIX?](https://ticker-fight.blogspot.com/2026/11/volatilita-realizzata-contro-implicita.html).

## Cosa c'è in questa cartella

```
volatilita-realizzata-contro-implicita-quanto-sbaglia-il-vix/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py
    ├── 02_backtest_e_test.py
    ├── 03_grafici.py
    ├── config.py
    ├── funzioni.py
    └── verifica_motore.py
```

## Come si rifà

```bash
cd articoli/volatilita-realizzata-contro-implicita-quanto-sbaglia-il-vix
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
