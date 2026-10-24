# Stop loss al 5%: protegge o taglia i guadagni?

**Domanda:** su una regola di trend (chiusura sopra la media a 200 sedute) uno stop loss fisso al 5% protegge dalle perdite grosse o taglia i guadagni? Condizioni di chi parte con 1.000 €: commissione per ordine in tre scenari, tassa del 26% con minusvalenze riportate, azioni frazionate.

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Regola di trend:** investito se la chiusura sta sopra la media mobile semplice a 200 sedute; il segnale di fine seduta decide l'ordine della seduta dopo, eseguito alla chiusura (nessun look-ahead).
- **Stop loss:** se la chiusura scende del 5% o più sotto il prezzo di acquisto, si vende alla chiusura della seduta successiva; si rientra solo dopo che il segnale è tornato falso e poi vero.
- **Strumenti (scelti prima di guardare i dati):** un ETF azionario mondiale e un ETF sull'S&P 500 quotati a Milano in euro, più l'indice S&P 500 in dollari convertito in euro.
- **Condizioni:** 1.000 €; commissione 0 €, 2 € a ordine e 0,1% dell'importo; tassa 26% con compensazione delle minusvalenze; dividendi e imposta di bollo non considerati.
- **Confronti:** buy & hold; la stessa regola senza stop; tre soglie di controllo (3%, 8%, 10%); scimmie con lo stesso numero di periodi investiti e la stessa durata totale.
- **Test:** scimmie (una coda) e bootstrap a blocchi della differenza di rendimento giornaliero tra regola con stop e senza, entrambi con la correzione di Holm sugli strumenti.

## Cosa c'è in questa cartella

```
stop-loss-al-5-protegge-o-taglia-i-guadagni/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica due ETF, l'indice S&P 500 e il cambio euro-dollaro
    ├── 02_backtest_e_test.py  buy & hold, trend, trend con stop, scimmie, bootstrap, correzione di Holm
    ├── 03_grafici.py          i cinque grafici
    ├── config.py              strumenti, parametri e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore in euro: ordini, commissioni, tassa, minusvalenze, stop loss, scimmie
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/stop-loss-al-5-protegge-o-taglia-i-guadagni
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
