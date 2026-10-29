"""Passo 2 - ETF covered call: XYLD contro SPY e QYLD contro QQQ.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine
  curve.csv         valore di 1 dollaro nei quattro ETF (una seduta su cinque)
  mensili.csv       rendimenti mensili dei quattro ETF
  bootstrap.csv     differenze di Sharpe ricampionate (covered call meno indice) per le due coppie
  miste.csv         valore di 1 dollaro del portafoglio con la stessa volatilità, per le due coppie (una seduta su cinque)
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


def carica(ticker: str, colonna: str) -> pd.Series:
    df = pd.read_csv(config.file_dati(ticker), parse_dates=["Date"], index_col="Date").sort_index()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep="last")]
    c = df[colonna].astype(float)
    if c.isna().any() or (c < 0).any():
        raise SystemExit(f"{ticker}: dati mancanti o negativi.")
    return c


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    sigle = [s for _, _, s in config.ETF]
    prezzi = pd.concat({s: carica(t, config.COLONNA_PREZZO) for t, _, s in config.ETF}, axis=1).dropna()
    anni = (prezzi.index[-1] - prezzi.index[0]).days / 365.25
    if anni < config.ANNI_MINIMI:
        raise SystemExit(f"Storia comune di {anni:.1f} anni: troppo corta.")
    tasso = carica(config.TICKER_LIQUIDITA, "Close").reindex(prezzi.index, method="ffill").bfill() / 100.0
    R = prezzi.pct_change().dropna()
    liq = (tasso.reindex(R.index) / GA).to_numpy()          # rendimento giornaliero della liquidità
    fini = m.fine_mese(R.index)
    mensili = m.rendimenti_mensili(R.to_numpy(), fini)
    ci = {s: i for i, s in enumerate(sigle)}
    rng = np.random.default_rng(config.SEME)
    a = (1 - config.LIVELLO_CONFIDENZA) / 2

    reg("data_inizio", str(prezzi.index[0].date()), "data_lunga", "Prima seduta in comune dei quattro ETF", "dati/")
    reg("data_ultima", str(prezzi.index[-1].date()), "data_lunga", "Ultima seduta nei dati", "dati/")
    reg("anni", anni, "num1", "Anni di storia comune", "dati/")
    reg("n_sedute", len(R), "int", "Rendimenti giornalieri in comune", "dati/")
    reg("n_mesi", len(mensili), "int", "Mesi usati per la cattura", "dati/")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale per tradurre i rendimenti in dollari", "config.py")
    reg("tasso_medio", float(tasso.mean()), "pct1", "Tasso a tre mesi medio nel periodo", "dati/IRX.csv")
    reg("h2_riduzione", config.H2_VOL_RIDUZIONE, "pct0", "Ipotesi 2: riduzione relativa minima della volatilità", "config.py")
    reg("h3_dd", config.H3_DD_MIN, "pct0", "Ipotesi 3: perdita massima minima del covered call", "config.py")
    reg("h4_up", config.H4_UP_MAX, "pct0", "Ipotesi 4: cattura massima dei mesi di rialzo", "config.py")
    reg("h4_down", config.H4_DOWN_MIN, "pct0", "Ipotesi 4: cattura minima dei mesi di ribasso", "config.py")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti del bootstrap", "config.py")
    reg("blocco", config.BLOCCO_BOOTSTRAP, "int", "Giorni per blocco del bootstrap", "config.py")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py")

    stat = {}
    for s in sigle:
        r = R[s].to_numpy()
        e = m.equity(r)
        stat[s] = dict(cagr=m.cagr(r, GA), vol=m.vol(r, GA), sharpe=m.sharpe(r, GA), dd=-m.max_dd(r), finale=config.CAPITALE * float(e[-1]))
        k = s.lower()
        reg(f"{k}_cagr", stat[s]["cagr"], "pct1", f"Rendimento annuo composto di {s} (distribuzioni reinvestite)", "motore.cagr")
        reg(f"{k}_vol", stat[s]["vol"], "pct1", f"Volatilità annua di {s}", "motore.vol")
        reg(f"{k}_sharpe", stat[s]["sharpe"], "num2", f"Rapporto di Sharpe di {s} (tasso privo di rischio zero)", "motore.sharpe")
        reg(f"{k}_dd", stat[s]["dd"], "pct0", f"Perdita massima dal picco di {s}", "motore.max_dd")
        reg(f"{k}_finale", stat[s]["finale"], "int", f"Valore finale del capitale iniziale in {s}", "motore.equity")

    esiti = {i: [] for i in range(1, 8)}
    boots = {}
    miste = {}
    for cc, ix in config.COPPIE:
        k, kx = cc.lower(), ix.lower()
        rc, rx = R[cc].to_numpy(), R[ix].to_numpy()
        reg(f"{k}_diff_cagr", stat[cc]["cagr"] - stat[ix]["cagr"], "pp1", f"Rendimento annuo di {cc} meno quello di {ix}, in punti percentuali", "motore.cagr")
        rel = stat[cc]["vol"] / stat[ix]["vol"] - 1.0
        reg(f"{k}_vol_rel", -rel, "pct0", f"Riduzione relativa della volatilità di {cc} rispetto a {ix}", "motore.vol")
        reg(f"{k}_diff_dd", stat[ix]["dd"] - stat[cc]["dd"], "pp1", f"Perdita massima di {ix} meno quella di {cc}, in punti percentuali", "motore.max_dd")
        reg(f"{k}_rapporto_finale", stat[cc]["finale"] / stat[ix]["finale"], "num2", f"Valore finale di {cc} diviso quello di {ix}", "motore.equity")
        reg(f"{k}_corr", float(np.corrcoef(rc, rx)[0, 1]), "num2", f"Correlazione dei rendimenti giornalieri tra {cc} e {ix}", "dati/")
        su, giu = f.cattura(mensili[:, ci[cc]], mensili[:, ci[ix]])
        reg(f"{k}_cat_su", su, "pct0", f"Cattura dei mesi di rialzo di {ix} da parte di {cc}", "funzioni.cattura")
        reg(f"{k}_cat_giu", giu, "pct0", f"Cattura dei mesi di ribasso di {ix} da parte di {cc}", "funzioni.cattura")
        boot = m.bootstrap_diff_sharpe(rc, rx, config.N_BOOTSTRAP, config.BLOCCO_BOOTSTRAP, GA, rng)
        lo, hi = [float(x) for x in np.quantile(boot, [a, 1 - a])]
        boots[cc] = boot
        reg(f"{k}_sh_diff", stat[cc]["sharpe"] - stat[ix]["sharpe"], "num2", f"Sharpe di {cc} meno Sharpe di {ix}", "motore.sharpe")
        reg(f"{k}_sh_lo", lo, "num2", f"Estremo inferiore dell'intervallo bootstrap a blocchi della differenza di Sharpe ({cc} meno {ix})", "motore.bootstrap_diff_sharpe")
        reg(f"{k}_sh_hi", hi, "num2", f"Estremo superiore dell'intervallo bootstrap a blocchi della differenza di Sharpe ({cc} meno {ix})", "motore.bootstrap_diff_sharpe")
        w = f.peso_stessa_volatilita(rx, liq, stat[cc]["vol"], GA)
        rm = f.miscela(rx, liq, w)
        mix_cagr, mix_sh, mix_dd = m.cagr(rm, GA), m.sharpe(rm, GA), -m.max_dd(rm)
        miste[cc] = m.equity(rm)
        reg(f"{k}_w", w, "pct0", f"Peso di {ix} nel portafoglio con la stessa volatilità di {cc} (il resto in liquidità)", "funzioni.peso_stessa_volatilita")
        reg(f"{k}_mix_cagr", mix_cagr, "pct1", f"Rendimento annuo composto del portafoglio {ix} e liquidità con la volatilità di {cc}", "motore.cagr")
        reg(f"{k}_mix_dd", mix_dd, "pct0", f"Perdita massima del portafoglio {ix} e liquidità con la volatilità di {cc}", "motore.max_dd")
        reg(f"{k}_mix_diff", mix_cagr - stat[cc]["cagr"], "pp1", f"Rendimento annuo del portafoglio con la stessa volatilità meno quello di {cc}, in punti percentuali", "motore.cagr")
        n_crisi_meglio = 0
        crisi = []
        for j, (nome, ini, fin) in enumerate(config.CRISI):
            sel = (R.index >= pd.Timestamp(ini)) & (R.index <= pd.Timestamp(fin))
            if sel.sum() < 5:
                raise SystemExit(f"Fase «{nome}» fuori dai dati.")
            rcc, rix = float(np.prod(1 + rc[sel]) - 1), float(np.prod(1 + rx[sel]) - 1)
            crisi.append((rcc, rix))
            reg(f"{k}_crisi{j}_cc", rcc, "pct0", f"Rendimento di {cc} nella fase «{nome}»", "dati/")
            reg(f"{k}_crisi{j}_ix", rix, "pct0", f"Rendimento di {ix} nella fase «{nome}»", "dati/")
            reg(f"{k}_crisi{j}_meglio", int(rcc > rix), "int", f"1 se {cc} perde meno di {ix} nella fase «{nome}»", "dati/")
            n_crisi_meglio += int(rcc > rix)
        reg(f"{k}_n_crisi_meglio", n_crisi_meglio, "int", f"Fasi di crisi in cui {cc} perde meno di {ix}", "dati/")
        esiti[1].append(stat[cc]["cagr"] < stat[ix]["cagr"])
        esiti[2].append(rel <= -config.H2_VOL_RIDUZIONE)
        esiti[3].append(stat[cc]["dd"] > config.H3_DD_MIN)
        esiti[4].append(su < config.H4_UP_MAX and giu > config.H4_DOWN_MIN)
        esiti[5].append(lo <= 0 <= hi)
        esiti[6].append(mix_cagr > stat[cc]["cagr"])
        esiti[7].append(n_crisi_meglio == len(config.CRISI))
    for i in range(1, 8):
        reg(f"h{i}_esito", int(all(esiti[i])), "int", f"Ipotesi {i}: 1 se confermata in entrambe le coppie, 0 se smentita", "confronto con config.py")
        reg(f"h{i}_n_coppie", int(sum(esiti[i])), "int", f"Coppie su due in cui l'ipotesi {i} è confermata", "confronto con config.py")
    reg("n_conf", int(sum(all(esiti[i]) for i in range(1, 8))), "int", "Ipotesi confermate (su sette)", "confronto con config.py")
    reg("n_coppie", len(config.COPPIE), "int", "Coppie covered call e indice", "config.py")
    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi")
    json.dump({"valori": RIS}, open(config.RISULTATI / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    cum = np.cumprod(1.0 + R.to_numpy(), axis=0)
    camp = np.arange(0, len(R), 5)
    pd.DataFrame({"data": R.index[camp].strftime("%Y-%m-%d"), **{s.lower(): cum[camp, ci[s]] for s in sigle}}).to_csv(
        config.RISULTATI / "curve.csv", index=False, float_format="%.5f")
    pd.DataFrame({"data": R.index[camp].strftime("%Y-%m-%d"), **{f"mix_{cc.lower()}": miste[cc][camp] for cc, _ in config.COPPIE}}).to_csv(
        config.RISULTATI / "miste.csv", index=False, float_format="%.5f")
    pd.DataFrame(mensili, columns=sigle).to_csv(config.RISULTATI / "mensili.csv", index=False, float_format="%.6f")
    pd.DataFrame({cc.lower(): boots[cc] for cc, _ in config.COPPIE}).to_csv(config.RISULTATI / "bootstrap.csv", index=False, float_format="%.5f")
    print(f"Scritti {len(RIS)} numeri in metriche.json")
    for i in range(1, 8):
        print(f"H{i}: {esiti[i]}")


if __name__ == "__main__":
    main()
