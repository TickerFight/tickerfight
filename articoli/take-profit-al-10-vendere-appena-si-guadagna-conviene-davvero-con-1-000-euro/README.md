# Take profit al 10%: vendere appena si guadagna conviene davvero, con 1.000 euro?

**Domanda:** dopo un acquisto sul rimbalzo (chiusura almeno il 5% sotto il massimo delle ultime 20 chiusure), conviene vendere appena il prezzo sale del 10% (take profit) o semplicemente dopo 60 sedute? Condizioni di chi parte con 1.000 €: commissione per ordine in tre scenari, tassa del 26% con minusvalenze riportate, azioni frazionate.

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Ingresso (uguale per tutti):** si compra quando la chiusura sta almeno il 5% sotto il massimo delle ultime 20 chiusure; il segnale di fine seduta decide l'ordine della seduta dopo, eseguito alla chiusura (nessun look-ahead).
- **Take profit 10%:** si vende alla chiusura successiva a una chiusura che sta il 10% o più sopra il prezzo d'acquisto; se l'obiettivo non arriva si esce dopo 60 sedute.
- **Uscita a tempo 60 sedute (riferimento):** si vende alla chiusura successiva al sessantesimo giorno dall'acquisto. Dopo ogni uscita si rientra solo dopo che il segnale è tornato falso e poi vero.
- **Strumenti (scelti prima di guardare i dati):** un ETF azionario mondiale e un ETF sull'S&P 500 quotati a Milano in euro, più l'indice S&P 500 in dollari convertito in euro.
- **Condizioni:** 1.000 €; commissione 0 €, 2 € a ordine e 0,1% dell'importo; tassa 26% con compensazione delle minusvalenze; dividendi e imposta di bollo non considerati.
- **Confronti:** buy & hold; soglie di controllo del take profit (5% e 15%); scimmie con gli stessi periodi investiti e la stessa durata totale.
- **Test:** scimmie (una coda) e bootstrap a blocchi della differenza di rendimento giornaliero tra take profit e uscita a tempo, entrambi con la correzione di Holm sugli strumenti.

## Cosa c'è in questa cartella

```
take-profit-al-10-vendere-appena-si-guadagna-conviene-davvero-con-1-000-euro/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica due ETF, l'indice S&P 500 e il cambio euro-dollaro
    ├── 02_backtest_e_test.py  buy & hold, uscita a tempo, take profit, scimmie, bootstrap, correzione di Holm
    ├── 03_grafici.py          i grafici
    ├── config.py              strumenti, parametri e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore in euro: ordini, commissioni, tassa, minusvalenze, take profit, uscita a tempo, scimmie
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/take-profit-al-10-vendere-appena-si-guadagna-conviene-davvero-con-1-000-euro
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
