# Rotazione settoriale mensile: venti regole, quante reggono dopo costi e tasse?

**Domanda:** una rotazione mensile tra i nove ETF settoriali americani batte il buy & hold e i nove settori tenuti in parti uguali? E, tra venti regole dichiarate in anticipo, quante reggono ai costi, ai test multipli e al passare del tempo?

L'articolo completo, con risultati e grafici, è sul blog: [Rotazione settoriale mensile: venti regole, quante reggono dopo costi e tasse?](https://ticker-fight.blogspot.com/2026/10/rotazione-settoriale-mensile-venti.html).

## Il disegno

- **Regole:** a fine mese si scelgono i K settori con il rendimento più alto delle ultime L sedute (L = 21, 63, 126, 189, 252; K = 1, 2, 3, 4): venti regole, tutte dichiarate prima. Ordine alla chiusura della prima seduta del mese dopo.
- **Condizioni:** 10.000 euro, commissione dello 0,1% dell'importo di ogni ordine, tassa del 26% con minusvalenze riportate, azioni frazionate, dollaro convertito in euro.
- **Riferimenti:** buy & hold dell'ETF sull'S&P 500; i nove settori tenuti in parti uguali.
- **Test:** quante regole battono i riferimenti, al lordo e al netto; classifica delle regole nelle due metà del periodo; bootstrap a blocchi della differenza giornaliera netta rispetto ai nove settori, con correzione di Holm sulle venti regole.

## Cosa c'è in questa cartella

```
rotazione-settoriale-mensile-venti-regole-quante-reggono-dopo-costi-e-tasse/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica i nove ETF, l'ETF sull'S&P 500 e il cambio
    ├── 02_backtest_e_test.py  venti regole, riferimenti, metà periodo, bootstrap con correzione di Holm
    ├── 03_grafici.py          i tre grafici
    ├── config.py              strumenti, griglia delle regole e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore in euro: ordini, commissioni, tassa 26% con minusvalenze
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/rotazione-settoriale-mensile-venti-regole-quante-reggono-dopo-costi-e-tasse
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
