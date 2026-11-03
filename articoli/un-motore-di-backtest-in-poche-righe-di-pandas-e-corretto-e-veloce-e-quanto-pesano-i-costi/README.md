# Un motore di backtest in poche righe di pandas: è corretto, è veloce, e quanto pesano i costi?

**Domanda:** un motore di backtest scritto in poche righe di pandas è corretto, e quanto è più veloce di un ciclo giorno per giorno? E quanto pesano i costi di transazione su tre regole semplici del S&P 500?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Convenzioni:** il segnale della chiusura di ieri decide la posizione di oggi (`shift(1)`); a ogni cambio di posizione si paga un costo in percentuale del capitale.
- **Tre regole, non ottimizzate:** chiusura sopra quella di ieri; chiusura sopra la media a 20 giorni; media a 50 giorni sopra quella a 200.
- **Prova del nove:** lo stesso calcolo con un ciclo seduta per seduta; le due curve devono coincidere.
- **Tempi:** il più veloce di sette esecuzioni, per ciascun motore.

## Cosa c'è in questa cartella

```
un-motore-di-backtest-in-poche-righe-di-pandas-e-corretto-e-veloce-e-quanto-pesano-i-costi/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica l'S&P 500 dal 1927
    ├── 02_backtest_e_test.py  righe, differenza tra i motori, tempi, costi
    ├── 03_grafici.py          i tre grafici
    ├── config.py              parametri, soglie e ipotesi, scritti prima dei risultati
    ├── motore_50_righe.py     il motore vettoriale: segnali, shift di un giorno, costi, valore, CAGR, perdita massima
    ├── motore_ciclo.py        lo stesso motore con un ciclo, per la prova del nove e i tempi
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/un-motore-di-backtest-in-poche-righe-di-pandas-e-corretto-e-veloce-e-quanto-pesano-i-costi
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
