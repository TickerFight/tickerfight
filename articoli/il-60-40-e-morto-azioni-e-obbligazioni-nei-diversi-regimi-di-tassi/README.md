# Il 60/40 è morto? Azioni e obbligazioni nei diversi regimi di tassi

**Domanda:** il portafoglio classico 60% azioni / 40% obbligazioni funziona ancora, o dipende dal regime di tassi in cui lo si usa? Qui il 60/40 viene seguito dal 1981 a oggi, diviso in tre regimi di tassi (bassi, medi, alti), con un controllo sul caso (portafogli a peso azionario casuale) e sull'incertezza (bootstrap).

L'articolo completo, con risultati e grafici, è sul blog: [Il 60/40 è morto? Azioni e obbligazioni nei diversi regimi di tassi](https://ticker-fight.blogspot.com/2026/10/il-6040-e-morto-azioni-e-obbligazioni.html).

## Il disegno

- **Dati (Yahoo Finance):** fondo Vanguard 500 Index `VFINX` (azioni USA, dividendi reinvestiti), rendimento del Treasury a 10 anni `^TNX`, Bot a 13 settimane `^IRX` (liquidità), fondo Vanguard Total Bond Market `VBMFX` (solo controllo).
- **Obbligazioni:** serie sintetica di un Treasury a 10 anni a cedola pari, ricostruita ogni mese dal rendimento a 10 anni con il prezzo esatto di un'obbligazione a cedole semestrali (cedola = rendimento del mese precedente, scadenza residua 10 anni meno un mese, più un mese di cedola).
- **Portafoglio:** 60/40, ribilanciato ogni gennaio, da gennaio 1981 all'ultimo mese completo. Rendimenti nominali in dollari, lordi di costi e tasse.
- **Regimi:** rendimento a 10 anni di fine mese precedente: bassi sotto il 3%, alti dal 6% in su, medi in mezzo.
- **Finestre a 10 anni:** rendimento annuo del 60/40 nei 120 mesi successivi a ogni mese, con il regime di partenza noto alla partenza.
- **Incertezza e caso:** bootstrap a blocchi circolari di 12 mesi sulla differenza di Sharpe; 2000 portafogli con peso azionario casuale ripescato ogni gennaio.
- **Controllo del metodo:** correlazione tra la serie sintetica e `VBMFX` dal 1987.

## Cosa c'è in questa cartella

```
il-60-40-e-morto-azioni-e-obbligazioni-nei-diversi-regimi-di-tassi/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica fondo azionario, fondo obbligazionario, tassi a 10 anni e a 13 settimane
    ├── 02_backtest_e_test.py  serie mensili, regimi, finestre a 10 anni, bootstrap, scimmie
    ├── 03_grafici.py          i tre grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            obbligazione sintetica, portafoglio ribilanciato, statistiche, bootstrap
    └── verifica_motore.py     19 controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/il-60-40-e-morto-azioni-e-obbligazioni-nei-diversi-regimi-di-tassi
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
