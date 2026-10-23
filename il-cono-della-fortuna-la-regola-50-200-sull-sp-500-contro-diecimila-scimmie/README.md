# Il cono della fortuna: la regola 50/200 sull'S&P 500 contro diecimila scimmie

**Domanda:** in dieci anni di S&P 500, il risultato della regola 50/200 è distinguibile da quello di una «scimmia» che compra e vende a caso, ma con la stessa dieta della regola (stessi giorni investiti, stesso numero di ordini, stesse durate di permanenza)? Il confronto è con 10.000 scimmie e si vede in un grafico a cono, anche in 3D.

L'articolo completo, con risultati e grafici, è sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Scimmia:** ha lo stesso numero di ordini della regola, le stesse durate di ciascun periodo investito e lo stesso totale di giorni investiti; cambia solo il momento in cui entra, perché le pause tra un periodo e l'altro sono distribuite a caso. Il programma controlla che ogni scimmia abbia la stessa dieta della regola.
- **Costi:** 1 € a ordine, tassa 26% con compensazione delle minusvalenze, cambio dell'ultima chiusura, come negli altri articoli.
- **Ipotesi scritte prima dei risultati:** vedi `flusso/config.py`.

## Cosa c'è in questa cartella

```
il-cono-della-fortuna-la-regola-50-200-sull-sp-500-contro-diecimila-scimmie/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica S&P 500 e cambio euro-dollaro
    ├── 02_backtest_e_test.py  regola, 10.000 scimmie, cono, percentili, perdita massima
    ├── 03_grafici.py          cono 2D, cono 3D (immagine e GIF che ruota), percentile nel tempo, istogrammi
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore: segnale, ordini, commissioni, cambio, tassa e minusvalenze
    └── verifica_motore.py     19 controlli su dati inventati
```

## Come si rifà

```bash
cd il-cono-della-fortuna-la-regola-50-200-sull-sp-500-contro-diecimila-scimmie
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
