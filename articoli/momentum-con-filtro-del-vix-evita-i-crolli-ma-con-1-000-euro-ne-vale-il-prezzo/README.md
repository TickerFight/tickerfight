# Momentum con filtro del VIX: evita i crolli, ma con 1.000 euro ne vale il prezzo?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Regola di base:** all'ultima seduta di ogni mese si calcola il rendimento di prezzo delle ultime L sedute dei nove ETF settoriali SPDR e si comprano in parti uguali i tre migliori; l'ordine parte alla chiusura della prima seduta del mese dopo (nessun look-ahead). L in {126, 252}.
- **Filtro:** se il VIX alla chiusura di fine mese supera la soglia (20, 25 o 30), il giorno dopo si vende tutto e si resta in liquidità fino a un fine mese con il VIX sotto la soglia.
- **Regole:** 2 senza filtro + 6 con filtro, più il buy & hold dell'ETF sull'S&P 500. Regola principale: 126 sedute, soglia 25.
- **Condizioni:** 1.000 €; commissione 0 €, 2 € a ordine e 0,1% dell'importo; tassa 26% con compensazione delle minusvalenze; dividendi e imposta di bollo non considerati.
- **Test:** scimmie (stessa regola di base, stesso numero di mesi in liquidità ma scelti a caso) e bootstrap a blocchi della differenza tra regola filtrata e non filtrata, con la correzione di Holm.

## Cosa c'è in questa cartella

```
momentum-con-filtro-del-vix-evita-i-crolli-ma-con-1-000-euro-ne-vale-il-prezzo/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py
    ├── 02_backtest_e_test.py
    ├── 03_grafici.py
    ├── config.py
    ├── simulazione.py
    └── verifica_motore.py
```

## Come si rifà

```bash
cd articoli/momentum-con-filtro-del-vix-evita-i-crolli-ma-con-1-000-euro-ne-vale-il-prezzo
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
