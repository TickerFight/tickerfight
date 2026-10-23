# Il filtro sul rendimento passato funziona davvero? Prova fuori campione su 150 titoli

**Domanda:** il filtro trovato (regola 50/200 solo sui titoli con rendimento passato basso, buy & hold sugli altri) funziona anche fuori campione, cioè in un periodo precedente e su titoli mai usati prima?

L'articolo completo, con risultati e grafici, è sul blog: [Il filtro sul rendimento passato funziona davvero? Prova fuori campione su 150 titoli](https://ticker-fight.blogspot.com/2026/10/il-filtro-sul-rendimento-passato.html).

## Il disegno

- **Fuori campione due volte:** periodo diverso (i cinque anni fino al 20 ottobre 2021, mentre il filtro è stato trovato sul 2021-2026) e titoli diversi (150 mai usati negli articoli precedenti).
- **Strategia:** il primo giorno si ordinano i titoli per rendimento dei dodici mesi precedenti. Sul terzo più basso si applica la regola 50/200, sugli altri si compra e si tiene. Controllo: la metà più bassa.
- **Confronti:** buy & hold su tutti, regola su tutti, e una scelta casuale dello stesso numero di titoli su cui applicare la regola (10.000 sorteggi).
- **Riferimento:** lo stesso filtro sul periodo 2021-2026, dove però è stato trovato: serve solo come confronto, non come prova.

## Cosa c'è in questa cartella

```
il-filtro-sul-rendimento-passato-funziona-davvero-prova-fuori-campione-su-150-titoli/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica cambio e 150 titoli mai usati, fino a ottobre 2021
    ├── 02_backtest_e_test.py  simulazione dei portafogli, test, scelta casuale, confronto con il 2021-2026
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              parametri, strategia e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore: segnale, ordini, commissioni, cambio, tassa e minusvalenze
    └── verifica_motore.py     19 controlli su dati inventati
```

## Come si rifà

```bash
cd il-filtro-sul-rendimento-passato-funziona-davvero-prova-fuori-campione-su-150-titoli
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
