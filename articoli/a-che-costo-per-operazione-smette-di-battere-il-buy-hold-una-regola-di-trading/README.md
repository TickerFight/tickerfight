# A che costo per operazione smette di battere il buy & hold una regola di trading?

**Domanda:** per ogni regola di investimento, a quale costo per cambio di posizione smette di battere il buy & hold? L'articolo 101 ha fatto crescere il costo e guardato la perdita; qui si cerca direttamente il costo di pareggio, una volta sul rendimento annuo e una volta sullo Sharpe.

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Dieci regole fisse, nessuna ottimizzata:** prezzo sopra la media a 10, 20, 50, 100, 200 giorni; incroci 10/50 e 50/200; momentum a 3 e 12 mesi; ritorno alla media nel trend. Il segnale della chiusura di ieri decide la posizione di oggi. Riferimento: buy & hold.
- **Costo di pareggio:** il costo per cambio (commissione, spread e slippage insieme, nessuna tassa) a cui la regola ha lo stesso rendimento annuo, o lo stesso Sharpe, del buy & hold. Si trova per bisezione tra 0 e 5%; se la regola è già sotto a costo zero vale 0, se è sopra anche al 5% è «oltre il 5%».
- **Due metà del periodo** per vedere se il pareggio è stabile; **500 scimmie** con la stessa frequenza di cambi del prezzo sopra la media a 50 giorni per il confronto con il caso.
- **Cinque ipotesi** scritte in `config.py` prima di guardare i dati.

## Cosa c'è in questa cartella

```
a-che-costo-per-operazione-smette-di-battere-il-buy-hold-una-regola-di-trading/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica l'S&P 500 dal 1927
    ├── 02_backtest_e_test.py  costo di pareggio, due metà del periodo, scimmie, verdetti
    ├── 03_grafici.py          i cinque grafici
    ├── config.py              regole, parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            regole, rendimenti netti dei costi, costo di pareggio, Spearman, scimmie
    ├── motore_vettoriale.py   segnale, posizione con ritardo, valore
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/a-che-costo-per-operazione-smette-di-battere-il-buy-hold-una-regola-di-trading
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
