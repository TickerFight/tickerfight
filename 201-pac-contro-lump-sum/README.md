# PAC contro lump sum: conta più la lunghezza delle rate o il decennio di partenza?

**Domanda:** investire tutto subito (lump sum, cioè buy & hold dal primo giorno) o a rate (PAC)? Qui il PAC viene provato con cinque lunghezze (3, 6, 12, 24, 36 rate), con valutazione a 60 mesi dalla partenza, su ogni mese di partenza della storia di quattro indici; poi si guarda decennio per decennio, le partenze vicino ai massimi, gli esiti peggiori e il confronto con il caso (scimmie).

L'articolo completo, con risultati e grafici, è sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Budget:** 12.000 euro. Lump sum: tutto al primo giorno di Borsa del mese di partenza. PAC a N rate: un N-esimo del budget al primo giorno di Borsa di ciascuno degli N mesi; la cassa non ancora investita non rende. Quote frazionate, nessun costo, nessuna tassa.
- **Valutazione:** al primo giorno di Borsa del mese 60 dalla partenza, per ogni mese di partenza possibile (le partenze vicine si sovrappongono: gli intervalli di confidenza ricampionano gli anni).
- **Lunghezze del PAC:** 3, 6, 12, 24, 36 rate; il PAC di riferimento è quello a 12 rate.
- **Decenni:** dal 1930 al 2010, fissati a priori, sull'S&P 500.
- **Ai massimi:** partenze con prezzo entro il 3% dal massimo dei prezzi fino a quel mese (nessun look-ahead).
- **Il caso:** 200 scimmie per partenza che piazzano le 12 rate in mesi a caso nei primi 12 mesi.
- **Indici:** di prezzo (niente dividendi), in valuta locale; il confronto è sempre dentro lo stesso indice.

## Cosa c'è in questa cartella

```
201-pac-contro-lump-sum/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica S&P 500, DAX, FTSE 100, Nikkei 225
    ├── 02_backtest_e_test.py  confronto su ogni mese di partenza e tutte le metriche
    ├── 03_grafici.py          i tre grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            prezzi mensili, valore di lump sum e PAC, scimmie, massimi, decenni
    └── verifica_motore.py     18 controlli su dati inventati
```

## Come si rifà

```bash
cd 201-pac-contro-lump-sum
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
