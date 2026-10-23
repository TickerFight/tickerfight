# Quando le medie mobili battono il buy & hold? Tre indizi dalla letteratura messi alla prova

**Domanda:** nell'articolo sui 50 titoli la regola 50/200 ha battuto il buy & hold solo in 11 casi su 50. Si può prevedere quali? Tre caratteristiche del titolo, misurate prima del primo ordine e scelte dalla letteratura, vengono messe alla prova su 50 titoli già visti (sviluppo) e su 150 titoli nuovi (validazione).

L'articolo completo, con risultati e grafici, è sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Sviluppo.** I 50 titoli dell'articolo precedente: già visti, servono a esplorare.
- **Validazione.** 150 titoli nuovi, presi con lo stesso sorteggio (stesso elenco, stesso seme) dopo quelli già usati. Servono a confermare.
- **Caratteristiche** (misurate sulle sedute prima del primo ordine): volatilità dell'anno precedente, rendimento dei dodici mesi precedenti, incroci tra le medie nei 200 giorni precedenti. Il segno atteso di ciascuna è in `config.py` con il riferimento scientifico.
- **Indice composito:** somma dei ranghi percentuali, senza stime dai dati.
- **Statistica:** correlazione di rango, p-value di permutazione a una coda nella direzione dell'ipotesi con correzione di Holm, intervalli di confidenza bootstrap.

## Cosa c'è in questa cartella

```
bonus-quando-le-medie-mobili-battono-il-buy-and-hold/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica i 150 titoli di validazione da Yahoo Finance
    ├── 02_backtest_e_test.py  caratteristiche, simulazione, correlazioni, permutazioni, bootstrap
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              parametri, ipotesi e indice, scritti prima dei risultati
    ├── simulazione.py         motore: segnale, ordini, commissioni, cambio, tassa e minusvalenze
    └── verifica_motore.py     19 controlli su dati inventati
```

## Come si rifà

```bash
cd bonus-quando-le-medie-mobili-battono-il-buy-and-hold
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
