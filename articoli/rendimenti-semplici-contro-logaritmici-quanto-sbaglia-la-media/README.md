# Rendimenti semplici contro logaritmici: quanto sbaglia la media?

**Domanda:** quando la differenza tra rendimento semplice e logaritmico conta, e quanto si sbaglia a usare la media dei rendimenti semplici come se fosse il rendimento che un investitore ha davvero ottenuto?

L'articolo completo, con risultati e grafici, è sul blog: [Rendimenti semplici contro logaritmici: quanto sbaglia la media?](https://ticker-fight.blogspot.com/2026/10/rendimenti-semplici-contro-logaritmici.html).

## Il disegno

- **Finestra:** dall'ultima chiusura del primo anno solare all'ultima chiusura dell'ultimo anno solare completo, così rendimenti giornalieri, mensili e annuali coprono lo stesso periodo.
- **Media semplice contro rendimento composto:** media dei rendimenti semplici giornalieri per le sedute in un anno, contro il rendimento annuo composto del buy & hold.
- **Mezza varianza:** il divario tra media semplice e media logaritmica dovrebbe essere circa la varianza annua divisa per due.
- **Decenni, frequenze, giorno per giorno:** il divario per decennio (segue la volatilità?), calcolato con dati giornalieri, mensili e annuali, e la differenza tra i due rendimenti seduta per seduta.
- **Nessuna strategia:** il confronto è con il buy & hold, cioè con ciò che l'investitore ha davvero ottenuto.

## Cosa c'è in questa cartella

```
rendimenti-semplici-contro-logaritmici-quanto-sbaglia-la-media/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica l'S&P 500 dal 1927
    ├── 02_backtest_e_test.py  divario su tutto il periodo, per decennio, per frequenza e giorno per giorno
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── motore_vettoriale.py   rendimenti semplici e logaritmici, media e varianza annua, rendimento composto
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/rendimenti-semplici-contro-logaritmici-quanto-sbaglia-la-media
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
