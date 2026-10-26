# I buffer ETF limitano davvero le perdite? Cosa si protegge e cosa si cede in 12 mesi

**Domanda:** i buffer ETF (serie Innovator U.S. Equity Buffer) riducono davvero le perdite dell'S&P 500 su 12 mesi? Quanto rendimento cedono nei rialzi? E un portafoglio 80% azioni e 20% liquidità farebbe lo stesso?

L'articolo completo, con risultati e grafici, è sul blog: [I buffer ETF limitano davvero le perdite? Cosa si protegge e cosa si cede in 12 mesi](https://ticker-fight.blogspot.com/2026/10/i-buffer-etf-limitano-davvero-le.html).

## Il disegno

- **Dati:** prezzi giornalieri aggiustati da Yahoo Finance di PJAN, PFEB, …, PDEC (un fondo per mese di partenza), di SPY (S&P 500 total return) e `^IRX` (tasso a 3 mesi).
- **Periodo:** dal primo giorno di borsa del mese di partenza del fondo al primo giorno di borsa dello stesso mese dell'anno dopo; solo periodi completi. Il confronto vale per chi compra al primo giorno e tiene fino alla fine.
- **Confronti:** S&P 500 total return nelle stesse date; portafoglio 80% SPY e 20% liquidità, ribilanciato all'inizio.
- **Limiti noti:** pochi anni indipendenti (i fondi di mesi diversi si sovrappongono), nessuna tassa, un giorno di scarto possibile sul punto di partenza.

## Cosa c'è in questa cartella

```
i-buffer-etf-limitano-davvero-le-perdite-cosa-si-protegge-e-cosa-si-cede-in-12-mesi/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica i dodici fondi, SPY e il tasso a 3 mesi
    ├── 02_backtest_e_test.py  i test delle cinque ipotesi e il registro dei numeri
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            finestre di 12 mesi per fondo e portafoglio di confronto
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/i-buffer-etf-limitano-davvero-le-perdite-cosa-si-protegge-e-cosa-si-cede-in-12-mesi
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
