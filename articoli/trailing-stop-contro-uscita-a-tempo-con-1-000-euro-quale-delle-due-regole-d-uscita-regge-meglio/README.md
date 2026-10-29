# Trailing stop contro uscita a tempo: con 1.000 euro, quale delle due regole d'uscita regge meglio?

**Domanda:** dopo un ingresso sul trend (chiusura sopra la media a 200 sedute), conviene uscire con un trailing stop del 10% (si vende quando il prezzo scende del 10% dal massimo raggiunto dopo l'acquisto) o semplicemente dopo 60 sedute? Condizioni di chi parte con 1.000 €: commissione per ordine in tre scenari, tassa del 26% con minusvalenze riportate, azioni frazionate.

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Ingresso (uguale per tutti):** si compra quando la chiusura sta sopra la media mobile semplice a 200 sedute; il segnale di fine seduta decide l'ordine della seduta dopo, eseguito alla chiusura (nessun look-ahead).
- **Trailing stop 10%:** si vende alla chiusura successiva a una chiusura che sta il 10% o più sotto il massimo delle chiusure dall'acquisto.
- **Uscita a tempo 60 sedute:** si vende alla chiusura successiva al sessantesimo giorno dall'acquisto. Dopo l'uscita si rientra solo dopo che il segnale è tornato falso e poi vero.
- **Strumenti (scelti prima di guardare i dati):** un ETF azionario mondiale e un ETF sull'S&P 500 quotati a Milano in euro, più l'indice S&P 500 in dollari convertito in euro.
- **Condizioni:** 1.000 €; commissione 0 €, 2 € a ordine e 0,1% dell'importo; tassa 26% con compensazione delle minusvalenze; dividendi e imposta di bollo non considerati.
- **Confronti:** buy & hold; l'uscita di trend (vendere sotto la media); soglie di controllo (5% e 15%; 20 e 120 sedute); scimmie con lo stesso numero di periodi investiti e la stessa durata totale.
- **Test:** scimmie (una coda) e bootstrap a blocchi della differenza di rendimento giornaliero tra trailing stop e uscita a tempo, entrambi con la correzione di Holm sugli strumenti.

## Cosa c'è in questa cartella

```
trailing-stop-contro-uscita-a-tempo-con-1-000-euro-quale-delle-due-regole-d-uscita-regge-meglio/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica due ETF, l'indice S&P 500 e il cambio euro-dollaro
    ├── 02_backtest_e_test.py  buy & hold, uscita di trend, trailing stop, uscita a tempo, scimmie, bootstrap, correzione di Holm
    ├── 03_grafici.py          i cinque grafici
    ├── config.py              strumenti, parametri e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore in euro: ordini, commissioni, tassa, minusvalenze, trailing stop, uscita a tempo, scimmie
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/trailing-stop-contro-uscita-a-tempo-con-1-000-euro-quale-delle-due-regole-d-uscita-regge-meglio
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
