# ETF covered call: rendita o rinuncia?

**Domanda:** gli ETF che vendono ogni mese opzioni call sull'indice e distribuiscono il premio (XYLD sull'S&P 500, QYLD sul Nasdaq-100) rendono di più, di meno o con meno rischio dell'indice? E uno stesso rischio si può ottenere più semplicemente con indice e liquidità?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Dati:** chiusure aggiustate (distribuzioni reinvestite) di XYLD, QYLD, SPY e QQQ dal giorno in cui esistono tutti e quattro.
- **Coppie:** XYLD contro SPY, QYLD contro QQQ.
- **Misure:** rendimento annuo composto, volatilità, Sharpe, perdita massima, cattura mensile dei rialzi e dei ribassi.
- **Test:** bootstrap a blocchi della differenza di Sharpe; portafoglio di indice e liquidità con la stessa volatilità del covered call; crollo del 2020 e rialzo dei tassi del 2022.

## Cosa c'è in questa cartella

```
etf-covered-call-rendita-o-rinuncia/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica SPY, QQQ, XYLD, QYLD e il tasso a tre mesi (^IRX) da Yahoo Finance
    ├── 02_backtest_e_test.py  metriche, cattura, bootstrap, portafoglio con la stessa volatilità, due fasi di crisi
    ├── 03_grafici.py          i grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            cattura dei mesi di rialzo e ribasso, portafoglio con la stessa volatilità
    ├── motore.py              rendimento, volatilità, Sharpe, perdita massima, bootstrap a blocchi
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/etf-covered-call-rendita-o-rinuncia
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
