# Stazionarietà e test ADF: i prezzi dell'S&P 500 sono stazionari? E i rendimenti?

**Domanda:** i prezzi e i rendimenti dell'S&P 500 sono stazionari? Che cosa dice il test di Dickey-Fuller aumentato (ADF) e quanto ci si può fidare?

L'articolo completo, con risultati e grafici, è sul blog: [Stazionarietà e test ADF: i prezzi dell'S&P 500 sono stazionari? E i rendimenti?](https://ticker-fight.blogspot.com/2026/10/stazionarieta-e-test-adf-i-prezzi-dells.html).

## Il disegno

- **Serie:** logaritmo della chiusura giornaliera e rendimenti logaritmici giornalieri dell'S&P 500 (indice di prezzo, senza dividendi).
- **Test:** ADF con ritardi scelti con il criterio AIC (massimo 20). Sul log-prezzo con costante e trend, sui rendimenti con la sola costante. Ipotesi nulla: radice unitaria.
- **Finestre:** decenni di 2.520 sedute non sovrapposti.
- **Simulazioni:** 1.000 random walk e 1.000 serie stazionarie lente (mezza vita di cinque anni), con la stessa volatilità dei dati reali, lunghe come una finestra: servono a misurare dimensione e potenza del test.

## Cosa c'è in questa cartella

```
stazionarieta-e-test-adf-i-prezzi-dell-sp-500-sono-stazionari-e-i-rendimenti/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica l'S&P 500 dal 1927
    ├── 02_backtest_e_test.py  ADF su intero periodo e finestre di dieci anni, simulazioni di dimensione e potenza
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            ADF, finestre, random walk e serie stazionarie simulate
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/stazionarieta-e-test-adf-i-prezzi-dell-sp-500-sono-stazionari-e-i-rendimenti
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
