# USA, Europa o mercati emergenti: chi ha vinto davvero negli ultimi vent'anni, e il primato è stabile?

**Domanda:** negli ultimi vent'anni gli Stati Uniti hanno battuto Europa e mercati emergenti, e quanto è stabile quel primato su finestre mobili?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Aree e strumenti:** Stati Uniti (SPY), Europa sviluppata (VGK), mercati emergenti (EEM), ETF quotati in dollari con dividendi reinvestiti (prezzo aggiustato di Yahoo Finance). Controllo con VTI, VGK, VWO. Scelti prima di guardare i dati.
- **Periodo:** da quando esistono tutti e tre gli ETF.
- **Confronti:** rendimento annuo, volatilità, perdita massima e Sharpe su tutto il periodo; finestre mobili di 3, 5 e 10 anni (a fine mese); volatilità e correlazione a un anno mobile; due crisi fissate in anticipo; persistenza del vincitore dei cinque anni precedenti con test di permutazione; scimmie che scelgono l'area a caso ogni mese.
- **Test:** bootstrap a blocchi (21 giorni) per la differenza di Sharpe, permutazioni, scimmie. Nessuna strategia ottimizzata, niente costi né tasse (sono buy & hold).
- **Niente look-ahead:** nel test di persistenza il vincitore "previsto" usa solo i cinque anni che finiscono nel mese di partenza.

## Cosa c'è in questa cartella

```
usa-europa-o-mercati-emergenti-chi-ha-vinto-davvero-negli-ultimi-vent-anni-e-il-primato-e-stabile/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica cinque ETF
    ├── 02_backtest_e_test.py  rendimento, rischio, finestre, correlazioni, persistenza, scimmie
    ├── 03_grafici.py          i cinque grafici
    ├── config.py              ETF, parametri, crisi e ipotesi, scritti prima dei risultati
    ├── motore.py              metriche, finestre mobili, persistenza, bootstrap, scimmie
    └── verifica_motore.py     controlli su dati inventati (conti a mano)
```

## Come si rifà

```bash
cd articoli/usa-europa-o-mercati-emergenti-chi-ha-vinto-davvero-negli-ultimi-vent-anni-e-il-primato-e-stabile
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
