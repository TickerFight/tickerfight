# Il VIX come segnale: cosa dice davvero dei mesi che verranno?

**Domanda:** che cosa dice il VIX dei rendimenti e della volatilità del mese successivo, e una regola semplice basata sul VIX batte il buy & hold sull'S&P 500 e la fortuna?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Segnale:** a fine mese, percentile del VIX rispetto a tutta la sua storia fino a quel giorno (finestra crescente, minimo 504 giorni di storia).
- **Niente look-ahead:** il segnale della chiusura t si scambia alla chiusura t+1 e lavora dal rendimento della seduta t+2.
- **Studio:** quintili del percentile contro rendimento e volatilità del mese successivo; correlazione di rango con test di permutazione; differenza tra quinto e primo quintile con bootstrap.
- **Regole:** A (in azioni solo se il percentile è sotto l'80%) e B (in azioni solo se è almeno al 50%), contro buy & hold e contro 5.000 scimmie (stessa quota di mesi in azioni, mesi a caso). Sei varianti di soglia, tutte riportate.
- **Costi:** 5 punti base su ogni scambio. Le tasse non sono modellate.

## Cosa c'è in questa cartella

```
il-vix-come-segnale-cosa-dice-davvero-dei-mesi-che-verranno/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica S&P 500 e VIX
    ├── 02_backtest_e_test.py  studio per quintili, regole A e B, scimmie, bootstrap, varianti
    ├── 03_grafici.py          i cinque grafici
    ├── config.py              dati, parametri, varianti e ipotesi, scritti prima dei risultati
    ├── motore.py              percentile del VIX, segnale ritardato, regole, costi, metriche, test
    └── verifica_motore.py     controlli su dati inventati (conti a mano, assenza di look-ahead)
```

## Come si rifà

```bash
cd articoli/il-vix-come-segnale-cosa-dice-davvero-dei-mesi-che-verranno
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
