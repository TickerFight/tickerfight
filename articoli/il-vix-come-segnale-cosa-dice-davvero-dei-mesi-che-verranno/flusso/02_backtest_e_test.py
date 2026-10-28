"""Passo 2 - Il VIX come segnale: studio mese per mese e due regole contro buy & hold e scimmie.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine
  quintili.csv      per quintile del percentile del VIX: mesi, rendimento medio, quota positiva, volatilità, peggiore
  mesi.csv          un record per mese (percentile, rendimento, volatilità del mese dopo)
  varianti.csv      le sei varianti di robustezza, tutte
  scimmie_sharpe.csv, bootstrap.csv     Sharpe delle scimmie e differenze di Sharpe ricampionate (regole A e B)
  curve.csv         curve delle due regole e del buy & hold (una seduta su cinque)
Scimmia: stessa quota di mesi in azioni della regola, ma mesi scelti a caso (confronto lordo di costi).
"""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import motore as m

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con motore.py"
GA = config.GIORNI_ANNO


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def carica(ticker):
    df = pd.read_csv(config.file_dati(ticker), parse_dates=["Date"], index_col="Date").sort_index()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep="last")]
    c = df["Close"].astype(float)
    if (c <= 0).any() or c.isna().any():
        raise SystemExit(f"{ticker}: chiusure mancanti o non positive.")
    return c


def esegui_regola(d, tipo, soglia, rng):
    s = m.serie_regola(d, tipo, soglia, config.COSTO_BP)
    anni = (d.index[-1] - d.index[0]).days / 365.25
    rs, rb = s["strategia"], s["buyhold"]
    out = dict(s=s, anni=anni, cagr_s=m.cagr(rs, anni), cagr_b=m.cagr(rb, anni), vol_s=m.vol_annua(rs, GA), vol_b=m.vol_annua(rb, GA),
               dd_s=m.perdita_massima(rs), dd_b=m.perdita_massima(rb), sh_s=m.sharpe(rs, GA), sh_b=m.sharpe(rb, GA),
               quota=float(s["peso"].mean()), scambi=float(s["scambio"].sum() / anni))
    if rng is not None:
        boot = m.bootstrap_dsharpe(rs.to_numpy(), rb.to_numpy(), config.N_BOOTSTRAP, config.BLOCCO_BOOTSTRAP, GA, rng)
        a = (1 - config.LIVELLO_CONFIDENZA) / 2
        out["boot"] = boot
        out["lo"], out["hi"] = [float(x) for x in np.quantile(boot, [a, 1 - a])]
        g = s.groupby("periodo")
        w = g["peso"].first().to_numpy()
        s1 = g["r"].sum().to_numpy()
        s2 = g["r"].apply(lambda x: (x ** 2).sum()).to_numpy()
        n = len(s)
        out["sh_lordo"] = float(m.sharpe_da_somme(w, s1, s2, n, GA))
        perm = rng.permuted(np.tile(w, (config.N_SCIMMIE, 1)), axis=1)
        out["sh_sc"] = m.sharpe_da_somme(perm, s1, s2, n, GA)
        out["p_sc"] = (int((out["sh_sc"] >= out["sh_lordo"]).sum()) + 1) / (config.N_SCIMMIE + 1)
        crisi = {}
        for k, (et, ini, fin) in enumerate(config.CRISI):
            sel = (s.index >= pd.Timestamp(ini)) & (s.index <= pd.Timestamp(fin))
            crisi[k] = dict(s=float(np.prod(1 + rs.to_numpy()[sel]) - 1), b=float(np.prod(1 + rb.to_numpy()[sel]) - 1),
                            peso=float(s["peso"].to_numpy()[sel].mean())) if (s.index[0] <= pd.Timestamp(ini) and sel.sum() > 5) else None
        out["crisi"] = crisi
    return out


def main():
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    if any(r["stato"] != "ok" for r in meta["indici"]):
        raise SystemExit("Mancano i dati di S&P 500 o VIX.")
    close, vix = carica(config.TICKER_INDICE), carica(config.TICKER_VIX)
    d = m.tabella_base(close, vix, config.STORIA_MINIMA)
    anni = (d.index[-1] - d.index[0]).days / 365.25
    rng = np.random.default_rng(config.SEME)
    R = config.RISULTATI

    # --- studio mese per mese -----------------------------------------------------------------------
    ms = m.mesi(d, GA)
    ms.to_csv(R / "mesi.csv", float_format="%.6f")
    pct, rend, vol = ms["pct"].to_numpy(), ms["rend"].to_numpy(), ms["vol"].to_numpy()
    rho_v, p_v = m.spearman_permutazione(pct, vol, config.N_PERMUTAZIONI, rng)
    rho_r, p_r = m.spearman_permutazione(pct, rend, config.N_PERMUTAZIONI, rng)
    q = m.quintili(pct, config.N_QUINTILI)
    righe = []
    for k in range(config.N_QUINTILI):
        sel = q == k
        righe.append(dict(quintile=k + 1, mesi=int(sel.sum()), rend_medio=float(rend[sel].mean()), quota_positivi=float((rend[sel] > 0).mean()),
                          vol_media=float(vol[sel].mean()), peggiore=float(rend[sel].min()), migliore=float(rend[sel].max())))
    Q = pd.DataFrame(righe)
    Q.to_csv(R / "quintili.csv", index=False, float_format="%.6f")
    bd = m.bootstrap_diff_medie(rend[q == config.N_QUINTILI - 1], rend[q == 0], config.N_BOOTSTRAP, rng)
    a = (1 - config.LIVELLO_CONFIDENZA) / 2
    lo_q, hi_q = [float(x) for x in np.quantile(bd, [a, 1 - a])]
    diff_q = float(rend[q == config.N_QUINTILI - 1].mean() - rend[q == 0].mean())

    reg("sp_prima_data", str(d.index[0].date()), "data", "Prima seduta con un segnale in vigore")
    reg("sp_ultima_data", str(d.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/*.csv")
    reg("sp_anni", anni, "num1", "Anni di storia usati")
    reg("n_mesi", len(ms), "int", "Mesi (periodi tra due segnali) usati nello studio")
    reg("rho_vol", rho_v, "num2", "Correlazione di rango tra percentile del VIX e volatilità realizzata del mese successivo")
    reg("p_vol", p_v, "pval", "p-value (permutazione, due code) della correlazione con la volatilità del mese successivo")
    reg("rho_rend", rho_r, "num2", "Correlazione di rango tra percentile del VIX e rendimento del mese successivo")
    reg("p_rend", p_r, "pval", "p-value (permutazione, due code) della correlazione con il rendimento del mese successivo")
    for _, r in Q.iterrows():
        k = int(r["quintile"])
        reg(f"q{k}_mesi", int(r["mesi"]), "int", f"Mesi nel quintile {k} del percentile del VIX")
        reg(f"q{k}_rend", r["rend_medio"], "pct2", f"Rendimento medio del mese successivo, quintile {k}")
        reg(f"q{k}_pos", r["quota_positivi"], "pct0", f"Quota di mesi positivi nel mese successivo, quintile {k}")
        reg(f"q{k}_vol", r["vol_media"], "pct1", f"Volatilità annualizzata media del mese successivo, quintile {k}")
        reg(f"q{k}_peggio", r["peggiore"], "pct1", f"Peggior mese successivo, quintile {k}")
        reg(f"q{k}_meglio", r["migliore"], "pct1", f"Miglior mese successivo, quintile {k}")
    reg("diff_q", diff_q, "pct2", "Rendimento medio mensile del quinto quintile meno quello del primo")
    reg("diff_q_lo", lo_q, "pct2", "Estremo inferiore dell'intervallo al 95% della differenza tra quinto e primo quintile", "bootstrap dei mesi dei due gruppi")
    reg("diff_q_hi", hi_q, "pct2", "Estremo superiore dell'intervallo al 95% della differenza tra quinto e primo quintile", "bootstrap dei mesi dei due gruppi")
    reg("rend_medio_tutti", float(rend.mean()), "pct2", "Rendimento medio mensile di tutti i mesi")
    reg("vol_media_tutti", float(vol.mean()), "pct1", "Volatilità annualizzata media del mese successivo, tutti i mesi")

    # --- le due regole -----------------------------------------------------------------------------
    cur = {}
    for nome, tipo, soglia in [("a", "A", config.SOGLIA_A), ("b", "B", config.SOGLIA_B)]:
        r = esegui_regola(d, tipo, soglia, rng)
        cur[nome] = r
        s = r["s"]
        reg(f"{nome}_soglia", soglia, "pct0", f"Soglia del percentile del VIX, regola {tipo}", "config.py")
        reg(f"{nome}_cagr_s", r["cagr_s"], "pct1", f"Rendimento annuo composto netto, regola {tipo}")
        reg(f"{nome}_cagr_b", r["cagr_b"], "pct1", "Rendimento annuo composto del buy & hold sullo stesso periodo")
        reg(f"{nome}_vol_s", r["vol_s"], "pct1", f"Volatilità annua realizzata, regola {tipo}")
        reg(f"{nome}_vol_b", r["vol_b"], "pct1", "Volatilità annua realizzata del buy & hold")
        reg(f"{nome}_dd_s", r["dd_s"], "pct1", f"Perdita massima, regola {tipo}")
        reg(f"{nome}_dd_b", r["dd_b"], "pct1", "Perdita massima del buy & hold")
        reg(f"{nome}_sh_s", r["sh_s"], "num2", f"Indice di Sharpe, regola {tipo} (cassa a rendimento zero)")
        reg(f"{nome}_sh_b", r["sh_b"], "num2", "Indice di Sharpe del buy & hold (cassa a rendimento zero)")
        reg(f"{nome}_dsh", r["sh_s"] - r["sh_b"], "num2", f"Differenza di Sharpe, regola {tipo} meno buy & hold")
        reg(f"{nome}_dsh_lo", r["lo"], "num2", f"Estremo inferiore dell'intervallo al 95% della differenza di Sharpe, regola {tipo}", "bootstrap a blocchi circolari di 21 giorni")
        reg(f"{nome}_dsh_hi", r["hi"], "num2", f"Estremo superiore dell'intervallo al 95% della differenza di Sharpe, regola {tipo}", "bootstrap a blocchi circolari di 21 giorni")
        reg(f"{nome}_quota", r["quota"], "pct0", f"Quota di sedute in azioni, regola {tipo}")
        reg(f"{nome}_scambi", r["scambi"], "num1", f"Scambio annuo in multipli del capitale, regola {tipo}")
        reg(f"{nome}_finale_s", config.CAPITALE * m.equity(s["strategia"])[-1], "int", f"Valore finale di {config.CAPITALE:.0f} euro con la regola {tipo}, prima delle tasse")
        reg(f"{nome}_finale_b", config.CAPITALE * m.equity(s["buyhold"])[-1], "int", f"Valore finale di {config.CAPITALE:.0f} euro con il buy & hold, prima delle tasse")
        reg(f"{nome}_sh_lordo", r["sh_lordo"], "num2", f"Sharpe lordo di costi, regola {tipo}, base del confronto con le scimmie")
        reg(f"{nome}_sh_sc_med", float(np.mean(r["sh_sc"])), "num2", f"Sharpe lordo medio delle scimmie, regola {tipo}")
        reg(f"{nome}_p_sc", r["p_sc"], "pval", f"Quota di scimmie con Sharpe uguale o maggiore, regola {tipo} (p-value)")
        reg(f"{nome}_ic_zero", int(r["lo"] <= 0 <= r["hi"]), "int", f"1 se l'intervallo della differenza di Sharpe contiene lo zero, regola {tipo}")
        for k, (et, _, _) in enumerate(config.CRISI):
            cr = r["crisi"][k]
            if cr:
                reg(f"{nome}_crisi{k}_s", cr["s"], "pct1", f"Rendimento della regola {tipo} nella finestra «{et}»")
                reg(f"{nome}_crisi{k}_b", cr["b"], "pct1", f"Rendimento del buy & hold nella finestra «{et}»")
                reg(f"{nome}_crisi{k}_peso", cr["peso"], "pct0", f"Quota di sedute in azioni della regola {tipo} nella finestra «{et}»")
    for k, (et, ini, fin) in enumerate(config.CRISI):
        reg(f"crisi{k}_nome", et, "testo", "Nome della finestra di crisi", "config.py, CRISI")
        reg(f"crisi{k}_ini", ini, "data", f"Inizio della finestra «{et}»", "config.py, CRISI")
        reg(f"crisi{k}_fin", fin, "data", f"Fine della finestra «{et}»", "config.py, CRISI")

    # --- varianti -------------------------------------------------------------------------------------
    var = []
    for k, (et, tipo, soglia) in enumerate(config.VARIANTI):
        v = esegui_regola(d, tipo, soglia, None)
        var.append(dict(variante=et, regola=tipo, soglia=soglia, sharpe_s=v["sh_s"], sharpe_b=v["sh_b"], cagr_s=v["cagr_s"], cagr_b=v["cagr_b"],
                        dd_s=v["dd_s"], dd_b=v["dd_b"], quota=v["quota"]))
        reg(f"var{k}_nome", et, "testo", "Nome della variante", "config.py, VARIANTI")
        reg(f"var{k}_sh", v["sh_s"], "num2", f"Sharpe, variante «{et}»")
        reg(f"var{k}_cagr", v["cagr_s"], "pct1", f"Rendimento annuo, variante «{et}»")
        reg(f"var{k}_dd", v["dd_s"], "pct1", f"Perdita massima, variante «{et}»")
        reg(f"var{k}_quota", v["quota"], "pct0", f"Quota di sedute in azioni, variante «{et}»")
    pd.DataFrame(var).to_csv(R / "varianti.csv", index=False, float_format="%.6f")

    # --- parametri e fonti --------------------------------------------------------------------------
    reg("storia_minima", config.STORIA_MINIMA, "int", "Giorni di storia del VIX richiesti prima del primo percentile", "config.py")
    reg("costo_bp", config.COSTO_BP, "int", "Costo di ogni scambio in punti base", "config.py")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale di riferimento in euro", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Numero di scimmie", "config.py")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti del bootstrap", "config.py")
    reg("n_permutazioni", config.N_PERMUTAZIONI, "int", "Permutazioni del test di correlazione", "config.py")
    reg("blocco", config.BLOCCO_BOOTSTRAP, "int", "Giorni per blocco del bootstrap", "config.py")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello di confidenza", "config.py")
    reg("giorni_anno", GA, "int", "Giorni di borsa in un anno per annualizzare", "config.py")
    reg("lit_btz_anno", 2009, "annonum", "Anno di Bollerslev, Tauchen e Zhou, Review of Financial Studies (volume 22)", "riferimento bibliografico")
    reg("lit_bh_anno", 2014, "annonum", "Anno di Bekaert e Hoerova, ECB Working Paper n. 1675", "riferimento bibliografico")
    reg("lit_btz_dal", 1990, "annonum", "Anno da cui parte il campione di Bollerslev e coautori (post-1990), secondo l'abstract", "abstract dell'articolo")
    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi")

    json.dump({"valori": RIS}, open(R / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    pd.DataFrame({"a": cur["a"]["sh_sc"], "b": cur["b"]["sh_sc"]}).to_csv(R / "scimmie_sharpe.csv", index=False, float_format="%.5f")
    pd.DataFrame({"a": cur["a"]["boot"], "b": cur["b"]["boot"]}).to_csv(R / "bootstrap.csv", index=False, float_format="%.5f")
    n = len(d)
    camp = np.arange(0, n, 5)
    sa, sb = cur["a"]["s"], cur["b"]["s"]
    ea, eb, ebh = m.equity(sa["strategia"]), m.equity(sb["strategia"]), m.equity(sa["buyhold"])
    dd = lambda e: e / np.maximum.accumulate(np.r_[1.0, e])[1:] - 1
    pd.DataFrame({"data": d.index[camp], "regola_a": ea[camp], "regola_b": eb[camp], "buyhold": ebh[camp],
                  "dd_a": dd(ea)[camp], "dd_b": dd(eb)[camp], "dd_buyhold": dd(ebh)[camp],
                  "pct": d["pct"].to_numpy()[camp]}).to_csv(R / "curve.csv", index=False, float_format="%.6f")
    print(Q.to_string())
    print(f"rho vol {rho_v:.2f} (p {p_v:.4f}); rho rend {rho_r:.2f} (p {p_r:.4f}); diff Q5-Q1 {diff_q:.4f} [{lo_q:.4f}, {hi_q:.4f}]")
    for nome in "ab":
        r = cur[nome]
        print(f"{nome}: Sharpe {r['sh_s']:.2f} vs {r['sh_b']:.2f} IC [{r['lo']:.2f},{r['hi']:.2f}] dd {r['dd_s']:.2f} vs {r['dd_b']:.2f} p scimmie {r['p_sc']:.3f}")
    print(f"Scritti {len(RIS)} numeri in metriche.json")


if __name__ == "__main__":
    main()
