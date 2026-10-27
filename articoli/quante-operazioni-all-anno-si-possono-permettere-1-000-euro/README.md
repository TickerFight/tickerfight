# Quante operazioni all'anno si possono permettere 1.000 euro?

**Domanda:** con 1.000 € di capitale, 2 € a ordine (o 0,1%) e la tassa del 26%, quanti ordini all'anno si possono fare prima che i costi si mangino il rendimento? Per misurare solo il peso della frequenza si usa una «regola a cicli» senza alcun segnale di mercato: si è investiti tutte le sedute tranne una ogni L; la si prova a sei frequenze e la si confronta con il buy & hold e con le scimmie.

L'articolo completo, con risultati e grafici, è sul blog: [Quante operazioni all'anno si possono permettere 1.000 euro?](https://ticker-fight.blogspot.com/2026/10/quante-operazioni-allanno-si-possono.html).

## Il disegno

- **Regola a cicli:** ciclo di L sedute (252, 126, 63, 21, 10, 5): L−1 sedute investite e una fuori; vendita e riacquisto alla chiusura. Nessun segnale di mercato, nessun look-ahead.
- **Strumenti:** un ETF azionario mondiale e un ETF sull'S&P 500 (euro, Milano), più l'indice S&P 500 in dollari convertito in euro.
- **Condizioni:** 1.000 €; commissione 0 €, 2 € a ordine e 0,1%; tassa 26% con minusvalenze riportate; dividendi, bollo e spread non considerati.
- **Soglia di sostenibilità (scritta prima):** perdita di rendimento annuo netto, rispetto al buy & hold, non sopra 0,5 punti con 2 € a ordine.
- **Test:** scimmie (stesso numero di periodi e stessa durata totale), 18 test con la correzione di Holm.

## Cosa c'è in questa cartella

```
quante-operazioni-all-anno-si-possono-permettere-1-000-euro/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica due ETF, l'indice S&P 500 e il cambio euro-dollaro
    ├── 02_backtest_e_test.py  buy & hold, sei frequenze, scimmie, correzione di Holm
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              strumenti, parametri e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore in euro: ordini, commissioni, tassa, minusvalenze, scimmie
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/quante-operazioni-all-anno-si-possono-permettere-1-000-euro
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
