# 500 euro su Apple con le medie mobili: cinque anni di operazioni, commissioni e tasse

**Domanda:** la regola a medie mobili 50/200, applicata ad Apple con 500 euro, una commissione fissa di 1 euro a ordine e il 26% di imposta sulle plusvalenze, ha fatto guadagnare più del semplice buy & hold negli ultimi cinque anni? E se si fosse cominciato un altro giorno?

L'articolo completo, con risultati e grafici, è sul blog: [500 euro su Apple con le medie mobili: cinque anni di operazioni, commissioni e tasse](https://ticker-fight.blogspot.com/2026/10/500-euro-su-apple-con-le-medie-mobili.html).

## Cosa c'è in questa cartella

```
500-euro-su-apple-con-le-medie-mobili-cinque-anni-di-operazioni-commissioni-e-tasse/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica Apple e il cambio euro/dollaro da Yahoo Finance
    ├── 02_backtest_e_test.py  simulazione principale, controllo e finestre mobili
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              tutti i parametri e l'ipotesi, scritta prima dei risultati
    ├── simulazione.py         motore: segnale, ordini, commissioni, cambio, tassa e minusvalenze
    └── verifica_motore.py     19 controlli su dati inventati (conti a mano e formula indipendente)
```

## Come si rifà

```bash
cd articoli/500-euro-su-apple-con-le-medie-mobili-cinque-anni-di-operazioni-commissioni-e-tasse
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
