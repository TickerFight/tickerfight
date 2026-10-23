# Quanto costa davvero ogni operazione? Da 0 a 0,5% su quasi un secolo di S&P 500

**Domanda:** quanto pesano davvero i costi per operazione, facendoli variare da 0 a 0,5% del valore scambiato? Pesano in proporzione ai cambi di posizione? Cambiano la classifica delle regole? Quanto costa ribilanciare un portafoglio? E che cosa succede a chi cambia posizione a caso e spesso?

L'articolo completo, con risultati e grafici, è sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Otto regole fisse (le stesse dell'articolo 61), nessuna ottimizzata:** buy & hold; prezzo sopra la media a 50, 100, 200 giorni; incrocio 50/200; momentum a 12 mesi; investito solo a mercato calmo; ritorno alla media nel trend. Il segnale della chiusura di ieri decide la posizione di oggi. Un cambio è un acquisto o una vendita dell'intera posizione; l'ingresso iniziale dalla cassa si paga.
- **Sei livelli di costo:** 0, 0,05, 0,10, 0,20, 0,30, 0,50% del valore scambiato (commissione, spread e slippage insieme). Nessuna tassa, cassa a rendimento zero.
- **Ribilanciamento:** portafoglio 50% S&P 500 e 50% cassa, riportato al 50/50 ogni seduta, ogni 21 sedute, ogni 252 sedute.
- **Scimmie:** 300 posizioni casuali per ognuna di cinque probabilità giornaliere di cambiare stato (1, 5, 10, 20, 50%).
- **Sei ipotesi** scritte in `config.py` prima di guardare i dati.

## Cosa c'è in questa cartella

```
101-il-costo-nascosto/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica l'S&P 500 dal 1927
    ├── 02_backtest_e_test.py  costi, ribilanciamento, scimmie, verdetti
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              regole, parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            regole, rendimenti netti dei costi, ribilanciamento, scimmie
    ├── motore_vettoriale.py   segnale, posizione con ritardo, valore (dall'articolo 4)
    └── verifica_motore.py     controlli su dati inventati (formule a mano, assenza di look-ahead)
```

## Come si rifà

```bash
cd 101-il-costo-nascosto
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
