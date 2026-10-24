# Overfitting in pratica: ottimizzare su dieci anni, provare sui cinque dopo

**Domanda:** se scelgo la migliore coppia di medie mobili su dieci anni e la uso nei cinque successivi, quanto crolla il rendimento? E cosa succede quando provo più coppie?

L'articolo completo, con risultati e grafici, è sul blog: [Overfitting in pratica: ottimizzare su dieci anni, provare sui cinque dopo](https://ticker-fight.blogspot.com/2026/10/overfitting-in-pratica-ottimizzare-su.html).

## Il disegno

- **Regola:** media mobile veloce sopra la lenta, segnale ritardato di un giorno (nessun look-ahead), costo di 0,1% a ogni cambio di posizione, nessuna tassa, cassa a rendimento zero.
- **Finestre:** si ottimizza su dieci anni, si prova sui cinque successivi, si avanza di cinque anni: i periodi di prova non si sovrappongono.
- **Griglia principale:** 8 medie veloci per 6 medie lente, 44 coppie con veloce < lenta. **Pool (684 coppie):** tutte le coppie con veloce da 5 a 100 e lenta da 50 a 400 per l'esperimento sulla dimensione della griglia.
- **Confronti in prova:** coppia ottimizzata contro la media della griglia (una coppia a caso), contro la coppia 50/200 scelta a priori e contro il buy & hold.
- **Esperimento:** per ogni finestra si estraggono sottoinsiemi casuali del pool di 1, 2, 4 ... 512 coppie, si sceglie la migliore in ottimizzazione e si guarda cosa fa in prova.

## Cosa c'è in questa cartella

```
overfitting-in-pratica-ottimizzare-su-dieci-anni-provare-sui-cinque-dopo/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica l'S&P 500 dal 1927
    ├── 02_backtest_e_test.py  ottimizzazione e prova, confronti, esperimento sulla dimensione della griglia
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              parametri, griglie e ipotesi, scritti prima dei risultati
    ├── funzioni.py            rendimenti di tutte le coppie, finestre, migliore di un sottoinsieme
    ├── motore_vettoriale.py   segnale, posizione con ritardo, valore (dall'articolo 4)
    └── verifica_motore.py     16 controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/overfitting-in-pratica-ottimizzare-su-dieci-anni-provare-sui-cinque-dopo
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
