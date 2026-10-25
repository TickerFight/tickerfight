# Chi ha più fortuna: chi compra una volta o chi compra ogni mese?

**Domanda:** chi investe tutto il budget il primo giorno (lump sum) finisce davanti a chi lo divide in dodici rate mensili (PAC) per quanti mesi di partenza? E quanto di quel risultato è solo il rialzo medio del mercato, cioè il caso?

L'articolo completo, con risultati e grafici, è sul blog: [Chi ha più fortuna: chi compra una volta o chi compra ogni mese?](https://ticker-fight.blogspot.com/2026/10/chi-ha-piu-fortuna-chi-compra-una-volta.html).

## Il disegno

- **Budget:** 1.200 euro. Lump sum: tutto al primo giorno di Borsa del mese di partenza. PAC: 100 euro al primo giorno di Borsa di ciascuno dei 12 mesi; la cassa non ancora investita non rende. Quote frazionate.
- **Valutazione:** al primo giorno di Borsa del mese 12 e del mese 24 dalla partenza, per ogni mese di partenza possibile (le partenze vicine si sovrappongono: gli intervalli di confidenza ricampionano gli anni; si guardano anche le partenze non sovrapposte, per mese di calendario).
- **Il caso:** (a) 1.000 storie per indice con gli stessi rendimenti mensili in ordine rimescolato; (b) 200 scimmie per partenza che piazzano le 12 rate in mesi a caso. Gli otto test del rimescolamento (4 indici per 2 orizzonti) sono corretti con Holm.
- **Costi:** scenario con 2 euro a ordine (12 ordini contro 1). Nessuna tassa: il confronto è lordo.
- **Indici:** di prezzo (niente dividendi), in valuta locale; il confronto è sempre dentro lo stesso indice.

## Cosa c'è in questa cartella

```
chi-ha-piu-fortuna-chi-compra-una-volta-o-chi-compra-ogni-mese/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica S&P 500, DAX, FTSE 100, Nikkei 225
    ├── 02_backtest_e_test.py  confronto su ogni mese di partenza, test contro il caso
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            prezzi mensili, valore di lump sum e PAC, scimmie, storie rimescolate, Holm
    └── verifica_motore.py     17 controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/chi-ha-piu-fortuna-chi-compra-una-volta-o-chi-compra-ogni-mese
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
