# Portafogli di titoli casuali contro l'indice: quanto conta scegliere i titoli?

**Domanda:** mille portafogli estratti a caso dall'S&P 100 battono l'indice? Quanto conta, da sola, la scelta dei titoli?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Universo:** i componenti dell'S&P 100 di oggi (lista fissata a priori, una classe azionaria per società); restano i titoli con prezzi dal primo giorno del periodo (2006).
- **Portafogli:** 1.000 per ciascuna dimensione (5, 10, 20, 30 titoli), estratti a caso, pesi uguali, ribilanciati ogni primo giorno di Borsa dell'anno; nessun costo né tassa.
- **Confronti:** SPY (rendimento totale) e universo a pesi uguali (stesso difetto di campione).
- **Controlli:** altri quattro semi, due metà del periodo (persistenza), singoli titoli.
- **Nessun look-ahead:** i titoli sono estratti prima di guardare i rendimenti.

## Cosa c'è in questa cartella

```
portafogli-di-titoli-casuali-contro-l-indice-quanto-conta-scegliere-i-titoli/
├── requirements.txt   librerie Python (versioni fissate)
└── flusso/
    ├── 01_scarica_dati.py     scarica i prezzi corretti dell'universo e dello SPY
    ├── 02_backtest_e_test.py  estrae i portafogli, li confronta con SPY e universo, controllo con altri semi
    ├── 03_grafici.py          crea i quattro grafici
    ├── config.py              parametri, universo e ipotesi (scritte prima dei risultati)
    ├── funzioni.py            curve dei portafogli a pesi uguali con ribilanciamento annuale, CAGR, Sharpe, drawdown
    └── verifica_motore.py     controlli delle funzioni su dati inventati
```

## Come si rifà

```bash
cd articoli/portafogli-di-titoli-casuali-contro-l-indice-quanto-conta-scegliere-i-titoli
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
