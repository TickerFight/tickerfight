# 50 titoli dell'S&P 500, medie mobili contro buy & hold: la classifica

**Domanda:** su 50 titoli dell'S&P 500 scelti a sorte, la regola a medie mobili 50/200, con 500 euro per titolo, una commissione fissa di 1 euro a ordine e il 26% di imposta sulle plusvalenze, ha fatto guadagnare più del semplice buy & hold negli ultimi cinque anni? Il risultato è una classifica titolo per titolo.

L'articolo completo, con risultati e grafici, è sul blog: [50 titoli dell'S&P 500, medie mobili contro buy & hold: la classifica](https://ticker-fight.blogspot.com/2026/10/50-titoli-dells-500-medie-mobili-contro.html).

## Cosa c'è in questa cartella

```
50-titoli-dell-sp-500-medie-mobili-contro-buy-hold-la-classifica/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     sorteggia i 50 titoli, scarica prezzi e cambio euro/dollaro da Yahoo Finance
    ├── 02_backtest_e_test.py  simulazione su ogni titolo, classifica, portafoglio, controlli
    ├── 03_grafici.py          i tre grafici
    ├── config.py              parametri, regola di scelta dei titoli e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore: segnale, ordini, commissioni, cambio, tassa e minusvalenze
    └── verifica_motore.py     19 controlli su dati inventati (conti a mano e formula indipendente)
```

## Come si rifà

```bash
cd 50-titoli-dell-sp-500-medie-mobili-contro-buy-hold-la-classifica
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
