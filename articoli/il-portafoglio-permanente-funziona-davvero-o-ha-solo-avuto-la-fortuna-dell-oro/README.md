# Il Portafoglio Permanente funziona davvero, o ha solo avuto la fortuna dell'oro?

**Domanda:** il Portafoglio Permanente di Harry Browne (un quarto azioni, un quarto obbligazioni di Stato lunghe, un quarto oro, un quarto liquidità) funziona davvero, o ha solo avuto la fortuna del rialzo dell'oro? Lo seguiamo da settembre 2000 all'ultimo mese completo e lo confrontiamo con le sole azioni, con il 60/40, con due versioni amputate (senza oro, senza liquidità) e con 2000 portafogli a pesi casuali.

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Dati (Yahoo Finance):** `VFINX` (azioni), `VUSTX` (Treasury lunghi), `GC=F` (oro, future continuo), `GLD` (controllo dell'oro), `VBMFX` (obbligazioni aggregate, per il 60/40), `^IRX` (Bot a 13 settimane, liquidità).
- **Portafogli:** pesi fissi, ribilanciati ogni gennaio, da settembre 2000 all'ultimo mese completo. Rendimenti nominali, in dollari, lordi di costi e tasse.
- **Incertezza e caso:** bootstrap a blocchi di 12 mesi sulla differenza di Sharpe; 2000 portafogli con pesi casuali ripescati ogni gennaio.
- **Sotto-periodi:** fino a dicembre 2011 e da gennaio 2012 (scelti a priori).

## Cosa c'è in questa cartella

```
il-portafoglio-permanente-funziona-davvero-o-ha-solo-avuto-la-fortuna-dell-oro/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica fondi, oro e Bot da Yahoo Finance
    ├── 02_backtest_e_test.py  serie mensili, anni solari, sotto-periodi, bootstrap, scimmie
    ├── 03_grafici.py          i tre grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            portafoglio ribilanciato, statistiche, bootstrap
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/il-portafoglio-permanente-funziona-davvero-o-ha-solo-avuto-la-fortuna-dell-oro
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
