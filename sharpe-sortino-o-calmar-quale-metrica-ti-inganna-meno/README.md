# Sharpe, Sortino o Calmar: quale metrica ti inganna meno?

**Domanda:** la stessa regola di investimento, misurata con tre metriche diverse, porta a conclusioni diverse? E quale delle tre metriche è la meno fragile?

L'articolo completo, con risultati e grafici, è sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Otto regole fisse, nessuna ottimizzata:** buy & hold; prezzo sopra la media a 50, 100, 200 giorni; incrocio 50/200; momentum a 12 mesi; investito solo a mercato calmo (volatilità a 20 giorni sotto il 20%); ritorno alla media nel trend (sotto la media a 5 giorni ma sopra quella a 200). Segnale ritardato di un giorno, costo 0,1% a ogni cambio, nessuna tassa, cassa a rendimento zero.
- **Metriche** sui rendimenti giornalieri netti: Sharpe (tasso senza rischio zero, 252 sedute), Sortino (obiettivo zero), Calmar (rendimento annuo composto diviso la perdita massima).
- **Prove:** classifiche sull'intero periodo; blocchi non sovrapposti di dieci anni (accordo tra le metriche e persistenza da un decennio al successivo); bootstrap a blocchi circolari di un mese (quanto resta la regola vincitrice); scimmie (regole casuali con lo stesso tempo investito e lo stesso numero di cambi del filtro a 200 giorni); buy & hold dimezzato come strumento di prova.
- **Sei ipotesi** scritte in `config.py` prima di guardare i dati.

## Cosa c'è in questa cartella

```
sharpe-sortino-o-calmar-quale-metrica-ti-inganna-meno/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica l'S&P 500 dal 1927
    ├── 02_backtest_e_test.py  classifiche, blocchi di dieci anni, bootstrap, scimmie
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              regole, parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            regole, metriche, correlazioni di rango, bootstrap, scimmie
    ├── motore_vettoriale.py   segnale, posizione con ritardo, valore (dall'articolo 4)
    └── verifica_motore.py     controlli su dati inventati (formule a mano, assenza di look-ahead)
```

## Come si rifà

```bash
cd sharpe-sortino-o-calmar-quale-metrica-ti-inganna-meno
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
