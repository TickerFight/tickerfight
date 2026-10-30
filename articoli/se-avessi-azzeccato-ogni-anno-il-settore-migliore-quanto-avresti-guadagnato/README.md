# Se avessi azzeccato ogni anno il settore migliore, quanto avresti guadagnato?

**Domanda:** se all'inizio di ogni anno avessi saputo quale dei nove settori azionari americani sarebbe stato il migliore, quanto avresti guadagnato rispetto all'S&P 500? E quanto di quel vantaggio sopravvive quando non si può sapere in anticipo?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Dati:** XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY (i nove settori SPDR originali, nati a dicembre 1998) e SPY come S&P 500; prezzi corretti per i dividendi, anni solari completi dal 1999 al 2025.
- **Senno di poi:** ogni anno si tiene il settore col rendimento più alto di quell'anno (scelto a fine anno, quindi impossibile in pratica). Lo stesso a trimestri e a mesi.
- **Il caso:** 10.000 scimmie che scelgono un settore a caso ogni anno.
- **La regola realizzabile:** comprare il settore che ha vinto l'anno prima (solo dati passati).
- **Costi e tasse:** 0,1% per ordine, 26% sulle plusvalenze con minusvalenze riportate; si vende e si ricompra tutto ogni anno (stima prudente: se il settore si ripete, in pratica non si venderebbe).
- **Test multipli:** due test contro le scimmie, corretti con Holm.

## Cosa c'è in questa cartella

```
se-avessi-azzeccato-ogni-anno-il-settore-migliore-quanto-avresti-guadagnato/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica i nove ETF settoriali SPDR e SPY
    ├── 02_backtest_e_test.py  senno di poi, caso, regola realizzabile, frequenze, costi e tasse
    ├── 03_grafici.py          i cinque grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            rendimenti per periodo, scelta ex post, scimmie, regola realizzabile, tasse, Holm
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/se-avessi-azzeccato-ogni-anno-il-settore-migliore-quanto-avresti-guadagnato
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
