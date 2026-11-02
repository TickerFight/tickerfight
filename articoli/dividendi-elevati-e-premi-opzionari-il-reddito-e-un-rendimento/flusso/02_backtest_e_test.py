"""Passo 2 - Dividendi elevati e premi opzionari: reddito contro rendimento.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json   ogni numero dell'articolo, con descrizione e origine
  curve.csv       valore di 1 dollaro (distribuzioni reinvestite) negli otto ETF (una seduta su cinque)
  tabella.csv     una riga per ETF: rendimento totale, del solo prezzo, reddito, volatilità, Sharpe, capitale finale con prelievo
"""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import funzioni as f
import motore as m

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con motore.py e funzioni.py"
GA = config.GIORNI_ANNO


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def carica(ticker: str) -> pd.DataFrame:
    df = pd.read_csv(config.file_dati(ticker), parse_dates=["Date"], index_col="Date").sort_index()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep="last")]
    if df[["Close", "Adj Close"]].isna().any().any() or (df[["Close", "Adj Close"]] <= 0).any().any():
        raise SystemExit(f"{ticker}: dati mancanti o non positivi.")
    return df[["Close", "Adj Close"]].astype(float)


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    sigle = [s for _, _, s in config.ETF]
    dati = {s: carica(t) for t, _, s in config.ETF}
    close = pd.concat({s: d["Close"] for s, d in dati.items()}, axis=1).dropna()
    adj = pd.concat({s: d["Adj Close"] for s, d in dati.items()}, axis=1).dropna()
    anni = (adj.index[-1] - adj.index[0]).days / 365.25
    if anni < config.ANNI_MINIMI:
        raise SystemExit(f"Storia comune di {anni:.1f} anni: troppo corta.")
    R = adj.pct_change().dropna()
    # serie di fine mese (ultima seduta di ogni mese), per prezzo e per prezzo con distribuzioni
    fm = close.groupby([close.index.year, close.index.month]).tail(1)
    fm_idx = fm.index
    close_m, adj_m = close.loc[fm_idx], adj.loc[fm_idx]
    n_mesi = len(fm_idx) - 1
    rng = np.random.default_rng(config.SEME)
    a = (1 - config.LIVELLO_CONFIDENZA) / 2
    rata = config.CAPITALE * config.PRELIEVO_ANNUO / config.MESI_ANNO

    reg("data_inizio", str(adj.index[0].date()), "data_lunga", "Prima seduta in comune degli otto ETF", "dati/")
    reg("data_ultima", str(adj.index[-1].date()), "data_lunga", "Ultima seduta nei dati", "dati/")
    reg("anni", anni, "num1", "Anni di storia comune", "dati/")
    reg("n_sedute", len(R), "int", "Rendimenti giornalieri in comune", "dati/")
    reg("n_mesi", n_mesi, "int", "Mesi usati nella simulazione del prelievo", "dati/")
    reg("n_etf", len(sigle), "int", "ETF nell'analisi", "config.py")
    reg("n_reddito", len(config.REDDITO), "int", "ETF da reddito", "config.py")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale della simulazione del prelievo", "config.py")
    reg("prelievo_annuo", config.PRELIEVO_ANNUO, "pct0", "Prelievo annuo fisso, in quota del capitale iniziale", "config.py")
    reg("rata", rata, "num2", "Rata mensile prelevata", "config.py")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sul reddito e sulle plusvalenze", "config.py")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti del bootstrap", "config.py")
    reg("blocco", config.BLOCCO_BOOTSTRAP, "int", "Giorni per blocco del bootstrap", "config.py")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py")

    stat, righe = {}, []
    for s in sigle:
        k = s.lower()
        r = R[s].to_numpy()
        p, i = f.componenti_mensili(close_m[s].to_numpy(), adj_m[s].to_numpy())
        cagr_tot = m.cagr(r, GA)
        cagr_prezzo = float(np.prod(1 + p) ** (config.MESI_ANNO / len(p)) - 1)
        reddito = float(np.prod(1 + i) ** (config.MESI_ANNO / len(i)) - 1)
        senza, con = f.prelievo(p, i, config.CAPITALE, rata, 0.0), f.prelievo(p, i, config.CAPITALE, rata, config.ALIQUOTA)
        stat[s] = dict(cagr=cagr_tot, prezzo=cagr_prezzo, reddito=reddito, vol=m.vol(r, GA), sharpe=m.sharpe(r, GA),
                       dd=-m.max_dd(r), f0=senza["finale"], f1=con["finale"])
        reg(f"{k}_cagr", cagr_tot, "pct1", f"Rendimento annuo composto di {s} con le distribuzioni reinvestite", "motore.cagr")
        reg(f"{k}_prezzo", cagr_prezzo, "pct1", f"Rendimento annuo composto del solo prezzo di {s} (senza distribuzioni)", "funzioni.componenti_mensili")
        reg(f"{k}_reddito", reddito, "pct1", f"Quota media annua di {s} distribuita come reddito (composta sui mesi)", "funzioni.componenti_mensili")
        reg(f"{k}_vol", stat[s]["vol"], "pct1", f"Volatilità annua di {s}", "motore.vol")
        reg(f"{k}_sharpe", stat[s]["sharpe"], "num2", f"Rapporto di Sharpe di {s} (tasso privo di rischio zero)", "motore.sharpe")
        reg(f"{k}_dd", stat[s]["dd"], "pct0", f"Perdita massima dal picco di {s}", "motore.max_dd")
        reg(f"{k}_f0", senza["finale"], "int", f"Capitale finale con prelievo fisso, senza tasse, in {s}", "funzioni.prelievo")
        reg(f"{k}_f1", con["finale"], "int", f"Capitale netto finale con prelievo fisso e tasse, in {s}", "funzioni.prelievo")
        reg(f"{k}_esaurito", int(con["esaurito"]), "int", f"Mese di esaurimento del capitale con tasse in {s} (0 se non si esaurisce)", "funzioni.prelievo")
        righe.append(dict(etf=s, cagr=cagr_tot, prezzo=cagr_prezzo, reddito=reddito, vol=stat[s]["vol"], sharpe=stat[s]["sharpe"],
                          dd=stat[s]["dd"], finale_senza_tasse=senza["finale"], finale_con_tasse=con["finale"]))
    reg("prelevato", f.prelievo(*f.componenti_mensili(close_m["SPY"].to_numpy(), adj_m["SPY"].to_numpy()), config.CAPITALE, rata, 0.0)["prelevato"],
        "int", "Totale prelevato nel periodo (uguale per tutti se il capitale non si esaurisce)", "funzioni.prelievo")

    ix = config.INDICE
    esiti = {i: [] for i in range(1, 7)}
    boots = {}
    for s in config.REDDITO:
        k = s.lower()
        reg(f"{k}_diff_cagr", stat[s]["cagr"] - stat[ix]["cagr"], "pp1", f"Rendimento annuo di {s} meno quello di {ix}, in punti percentuali", "motore.cagr")
        reg(f"{k}_diff_reddito", stat[s]["reddito"] - stat[ix]["reddito"], "pp1", f"Reddito annuo di {s} meno quello di {ix}, in punti percentuali", "funzioni.componenti_mensili")
        reg(f"{k}_diff_f1", stat[s]["f1"] - stat[ix]["f1"], "int", f"Capitale netto finale di {s} meno quello di {ix}", "funzioni.prelievo")
        esiti[1].append(stat[s]["reddito"] > stat[ix]["reddito"])
        esiti[2].append(stat[s]["cagr"] <= stat[ix]["cagr"])
        if s in config.PREMIO:
            esiti[3].append(stat[s]["prezzo"] <= config.H3_PREZZO_MAX)
        esiti[4].append(stat[s]["f0"] <= stat[ix]["f0"])
        esiti[5].append(stat[s]["f1"] <= stat[ix]["f1"])
        if s in config.DIVIDENDO:
            boot = m.bootstrap_diff_sharpe(R[s].to_numpy(), R[ix].to_numpy(), config.N_BOOTSTRAP, config.BLOCCO_BOOTSTRAP, GA, rng)
            lo, hi = [float(x) for x in np.quantile(boot, [a, 1 - a])]
            boots[s] = boot
            reg(f"{k}_sh_diff", stat[s]["sharpe"] - stat[ix]["sharpe"], "num2", f"Sharpe di {s} meno Sharpe di {ix}", "motore.sharpe")
            reg(f"{k}_sh_lo", lo, "num2", f"Estremo inferiore dell'intervallo bootstrap della differenza di Sharpe ({s} meno {ix})", "motore.bootstrap_diff_sharpe")
            reg(f"{k}_sh_hi", hi, "num2", f"Estremo superiore dell'intervallo bootstrap della differenza di Sharpe ({s} meno {ix})", "motore.bootstrap_diff_sharpe")
            esiti[6].append(lo <= 0 <= hi)
    n_att = {1: len(config.REDDITO), 2: len(config.REDDITO), 3: len(config.PREMIO), 4: len(config.REDDITO), 5: len(config.REDDITO), 6: len(config.DIVIDENDO)}
    for i in range(1, 7):
        reg(f"h{i}_esito", int(all(esiti[i])), "int", f"Ipotesi {i}: 1 se confermata per tutti gli ETF interessati, 0 se smentita", "confronto con config.py")
        reg(f"h{i}_n", int(sum(esiti[i])), "int", f"ETF in cui l'ipotesi {i} è confermata", "confronto con config.py")
        reg(f"h{i}_tot", n_att[i], "int", f"ETF a cui si applica l'ipotesi {i}", "config.py")
    reg("n_conf", int(sum(all(esiti[i]) for i in range(1, 7))), "int", "Ipotesi confermate (su sei)", "confronto con config.py")
    n_meglio = int(sum(stat[s]["f1"] > stat[ix]["f1"] for s in config.REDDITO))
    reg("n_meglio_f1", n_meglio, "int", "ETF da reddito con capitale netto finale più alto di SPY", "funzioni.prelievo")
    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi")
    json.dump({"valori": RIS}, open(config.RISULTATI / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    cum = np.cumprod(1.0 + R.to_numpy(), axis=0)
    camp = np.arange(0, len(R), 5)
    pd.DataFrame({"data": R.index[camp].strftime("%Y-%m-%d"), **{s.lower(): cum[camp, j] for j, s in enumerate(sigle)}}).to_csv(
        config.RISULTATI / "curve.csv", index=False, float_format="%.5f")
    pd.DataFrame(righe).to_csv(config.RISULTATI / "tabella.csv", index=False, float_format="%.5f")
    print(f"Scritti {len(RIS)} numeri in metriche.json")
    for i in range(1, 7):
        print(f"H{i}: {esiti[i]}")


if __name__ == "__main__":
    main()
