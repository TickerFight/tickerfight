# PAC mensile: conta il giorno del mese in cui compri?

**Domanda:** in un piano di accumulo con versamento mensile fisso, comprare il 3 o il 25 del mese cambia davvero il risultato, o la differenza è rumore?

L'articolo completo, con risultati e grafici, è sul blog: [PAC mensile: conta il giorno del mese in cui compri?](https://ticker-fight.blogspot.com/2026/10/pac-mensile-conta-il-giorno-del-mese-in.html).

## Il disegno

- **Piano:** ogni mese si versano 100 unità di valuta e si comprano quote frazionate dell'indice alla chiusura della prima seduta uguale o successiva al giorno scelto (da 1 a 28). Commissione di 2 per acquisto, tassa del 26% sulla plusvalenza alla vendita finale di tutto. Nessun look-ahead: il giorno è fissato in anticipo.
- **Indici:** S&P 500, DAX, CAC 40, Euro Stoxx 50, FTSE MIB, Nikkei 225, scelti prima di guardare i dati. Valuta locale, senza cambio.
- **Confronti:** il valore finale dei 28 giorni; mille serie con gli stessi rendimenti giornalieri messi in ordine casuale (stessa media e volatilità, nessun calendario); scimmie che scelgono un giorno a caso ogni mese.
- **Test:** scarto tra giorno migliore e peggiore contro le serie rimescolate con correzione di Holm sugli indici; trasferimento del giorno migliore agli altri indici; stabilità tra prima e seconda metà della storia.

## Cosa c'è in questa cartella

```
pac-mensile-conta-il-giorno-del-mese-in-cui-compri/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica sei indici azionari
    ├── 02_backtest_e_test.py  piano per ogni giorno 1-28, serie senza calendario, scimmie, test
    ├── 03_grafici.py          i tre grafici
    ├── config.py              indici, parametri e ipotesi, scritti prima dei risultati
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/pac-mensile-conta-il-giorno-del-mese-in-cui-compri
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
