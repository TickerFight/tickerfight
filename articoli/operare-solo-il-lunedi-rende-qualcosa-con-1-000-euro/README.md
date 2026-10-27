# Operare solo il lunedì: rende qualcosa con 1.000 euro?

**Domanda:** stare investiti solo nella seduta del lunedì (o di un altro giorno fisso della settimana) rende qualcosa, con le condizioni di chi parte con 1.000 €? Commissione per ordine in tre scenari, tassa del 26% con minusvalenze riportate, azioni frazionate.

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Regola:** investiti solo nella seduta di un giorno fisso: acquisto alla chiusura della seduta precedente, vendita alla chiusura del giorno scelto. Se il giorno è festivo, quella settimana non si opera. Si provano tutti e cinque i giorni.
- **Strumenti:** ETF azionario mondiale e ETF sull'S&P 500 (euro, Milano), indice S&P 500 in dollari convertito in euro.
- **Condizioni:** 1.000 €; commissione 0 €, 2 € a ordine e 0,1%; tassa 26% con compensazione delle minusvalenze; dividendi, bollo e spread non considerati.
- **Test:** scimmie (stesso numero di sedute investite, scelte a caso, valutate al lordo), 15 test con la correzione di Holm.

## Cosa c'è in questa cartella

```
operare-solo-il-lunedi-rende-qualcosa-con-1-000-euro/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica due ETF, l'indice S&P 500 e il cambio euro-dollaro
    ├── 02_backtest_e_test.py  buy & hold, cinque giorni della settimana, scimmie, correzione di Holm
    ├── 03_grafici.py          i grafici
    ├── config.py              strumenti, parametri e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore in euro: ordini, commissioni, tassa, minusvalenze, scimmie
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/operare-solo-il-lunedi-rende-qualcosa-con-1-000-euro
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
