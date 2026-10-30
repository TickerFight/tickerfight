# Anatomia di un drawdown: quanto scende l'S&P 500, quanto dura e quanto ci mette a risalire?

**Domanda:** quanto scende l'S&P 500 dai suoi massimi, quanto dura la discesa e quanto ci vuole per tornare al massimo? E i crolli veri sono più gravi di quelli che produrrebbe il solo caso?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Drawdown:** chiusura divisa per il massimo storico precedente, meno uno. Un episodio va dal massimo fino al giorno in cui la chiusura torna almeno a quel massimo; si contano gli episodi di almeno il 5%.
- **Tre durate:** discesa (massimo → minimo), recupero (minimo → nuovo massimo), totale.
- **Il caso:** 500 serie ottenute rimescolando a sorte i rendimenti giornalieri reali (stessa distribuzione, ordine casuale), con seme fisso.
- **Dati:** indice di prezzo, senza dividendi; nessuna strategia, nessun costo.

## Cosa c'è in questa cartella

```
anatomia-di-un-drawdown-quanto-scende-l-sp-500-quanto-dura-e-quanto-ci-mette-a-risalire/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica l'S&P 500 dal 1927
    ├── 02_backtest_e_test.py  episodi, durate, confronto con serie rimescolate
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              parametri, definizioni e ipotesi, scritti prima dei risultati
    ├── motore_drawdown.py     serie dei drawdown ed episodi (massimo, minimo, recupero)
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/anatomia-di-un-drawdown-quanto-scende-l-sp-500-quanto-dura-e-quanto-ci-mette-a-risalire
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
