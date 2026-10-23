# Quanto è fortunata la tua strategia? Il Golden Cross alla prova del caso

**Domanda:** la regola della media mobile 50/200 sull'S&P 500 batte il caso, oppure il suo risultato è compatibile con la fortuna?

L'articolo completo, con risultati e grafici, è sul blog: [Quanto è fortunata la tua strategia? Il Golden Cross alla prova del caso](https://ticker-fight.blogspot.com/2026/10/quanto-e-fortunata-la-tua-strategia-il.html).

## Cosa c'è in questa cartella

```
quanto-e-fortunata-la-tua-strategia-il-golden-cross-alla-prova-del-caso/
├── requirements.txt   librerie Python necessarie
└── flusso/
    ├── 01_scarica_dati.py     scarica ^GSPC da Yahoo Finance e salva i metadati
    ├── 02_backtest_e_test.py  backtest 50/200, test a timing casuale, bootstrap, sotto-periodi
    ├── 03_grafici.py          crea i cinque grafici
    └── config.py              tutti i parametri dell'analisi, in un solo posto
```

## Come si rifà

```bash
cd articoli/quanto-e-fortunata-la-tua-strategia-il-golden-cross-alla-prova-del-caso
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
