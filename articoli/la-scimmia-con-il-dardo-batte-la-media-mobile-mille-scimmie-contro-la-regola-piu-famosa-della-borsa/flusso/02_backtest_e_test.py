"""Passo 2 - Media mobile contro scimmie.

Legge SOLO dati/*.csv e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine
  confronti.csv     per indice e lunghezza: regola, buy & hold, scimmie a blocchi e a moneta, percentili, p e p di Holm
  metà.csv          S&P 500, media principale, prima e dopo lo spartiacque
  distribuzioni.npz campioni delle scimmie (S&P 500, media principale) per i grafici
  indici_usati.json
"""
import json
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import funzioni as fx

RIS: dict = {}
SORG = "02_backtest_e_test.py con funzioni.py"


def reg(chiave, valore, formato, descrizione, origine=SORG):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def confronto(rend, pos, rng, costo):
    """Regola, buy & hold, scimmie a blocchi (con e senza costi) e a moneta (senza costi) su una serie."""
    T = len(rend)
    quota = float(pos.mean())
    val, lung = fx.blocchi(pos)
    n_op = int((np.diff(np.concatenate([[0], pos])) != 0).sum())
    out = {"T": T, "quota": quota, "n_operazioni": n_op}
    for nome, c in (("lordo", 0.0), ("netto", costo)):
        cg, sh, md = fx.metriche(rend, pos, c)
        out[f"regola_cagr_{nome}"], out[f"regola_sharpe_{nome}"], out[f"regola_mdd_{nome}"] = cg[0], sh[0], md[0]
    cg, sh, md = fx.metriche(rend, np.ones(T, dtype=np.int8), 0.0)
    out["bh_cagr"], out["bh_sharpe"], out["bh_mdd"] = cg[0], sh[0], md[0]
    camp = {k: [] for k in ("bl_cagr", "bl_sharpe", "bl_mdd", "bl_cagr_n", "bl_sharpe_n", "bl_mdd_n", "mo_cagr", "mo_sharpe", "mo_mdd")}
    chunk = 100
    for i in range(0, config.N_SCIMMIE, chunk):
        m = min(chunk, config.N_SCIMMIE - i)
        P = np.array([fx.scimmia_a_blocchi(val, lung, rng) for _ in range(m)])
        for suff, c in (("", 0.0), ("_n", costo)):
            a, b, d = fx.metriche(rend, P, c)
            camp["bl_cagr" + suff].append(a); camp["bl_sharpe" + suff].append(b); camp["bl_mdd" + suff].append(d)
        a, b, d = fx.metriche(rend, fx.scimmie_a_moneta(T, quota, m, rng), 0.0)
        camp["mo_cagr"].append(a); camp["mo_sharpe"].append(b); camp["mo_mdd"].append(d)
    camp = {k: np.concatenate(v) for k, v in camp.items()}
    for k, v in camp.items():
        out[k + "_media"] = float(v.mean()); out[k + "_p5"] = float(np.quantile(v, 0.05)); out[k + "_p95"] = float(np.quantile(v, 0.95))
    for met in ("cagr", "sharpe", "mdd"):
        for tipo in ("bl", "mo"):
            out[f"perc_{tipo}_{met}"], out[f"p_{tipo}_{met}"] = fx.percentile_e_p(out[f"regola_{met}_lordo"], camp[f"{tipo}_{met}"])
        out[f"perc_bln_{met}"], out[f"p_bln_{met}"] = fx.percentile_e_p(out[f"regola_{met}_netto"], camp[f"bl_{met}_n"])
    return out, camp


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(config.SEME)
    righe, usati, distr, meta_righe = [], [], {}, []
    maxn = max(config.LUNGHEZZE)
    for tk, nome, valuta in config.INDICI:
        df = pd.read_csv(config.file_dati(tk), parse_dates=["Date"], index_col="Date").sort_index()
        close = df["Close"].astype(float)
        if (close <= 0).any() or close.isna().any():
            raise SystemExit(f"{tk}: chiusure mancanti o non positive")
        rend_tot = close.pct_change().fillna(0.0).to_numpy()
        usati.append({"ticker": tk, "nome": nome, "slug": tk.replace("^", "").lower(), "prima": str(close.index[maxn].date()),
                      "ultima": str(close.index[-1].date()), "sedute": int(len(close) - maxn)})
        for n in config.LUNGHEZZE:
            pos = fx.posizione_sma(close, n)[maxn:]
            rend = rend_tot[maxn:]
            r, camp = confronto(rend, pos, rng, config.COSTO_CAMBIO)
            r.update({"ticker": tk, "indice": nome, "lunghezza": n})
            righe.append(r)
            if tk == config.INDICE_PRINCIPALE and n == config.LUNGHEZZA_PRINCIPALE:
                distr = {k: v.astype(np.float32) for k, v in camp.items()}
                # metà della storia
                data = close.index[maxn:]
                taglio = int(np.searchsorted(data, pd.Timestamp(config.DATA_SPARTIACQUE)))
                for lab, sl in (("prima", slice(0, taglio)), ("dopo", slice(taglio, None))):
                    rm, _ = confronto(rend[sl], pos[sl], rng, config.COSTO_CAMBIO)
                    rm.update({"meta": lab, "dal": str(data[sl][0].date()), "al": str(data[sl][-1].date())})
                    meta_righe.append(rm)
    R = pd.DataFrame(righe)
    for tipo in ("bl", "mo"):
        for met in ("cagr", "sharpe"):
            h = fx.holm({i: p for i, p in enumerate(R[f"p_{tipo}_{met}"])})
            R[f"holm_{tipo}_{met}"] = [h[i] for i in range(len(R))]
    R.to_csv(config.RISULTATI / "confronti.csv", index=False, float_format="%.6f")
    M = pd.DataFrame(meta_righe)
    M.to_csv(config.RISULTATI / "meta.csv", index=False, float_format="%.6f")
    np.savez_compressed(config.RISULTATI / "distribuzioni.npz", **distr)
    (config.RISULTATI / "indici_usati.json").write_text(json.dumps(usati, indent=1, ensure_ascii=False), encoding="utf-8")

    S, P = config.SOGLIE, config.LUNGHEZZA_PRINCIPALE
    sub = R[R.lunghezza == P].set_index("ticker")
    sp = R[(R.ticker == config.INDICE_PRINCIPALE)].set_index("lunghezza")
    s0 = sp.loc[P]
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie per ogni confronto", "config.py")
    reg("costo", config.COSTO_CAMBIO, "pct1", "Costo per ogni acquisto o vendita, quota del valore", "config.py")
    reg("lunghezza", P, "annonum", "Lunghezza (sedute) della media mobile principale", "config.py")
    reg("n_lunghezze", len(config.LUNGHEZZE), "annonum", "Lunghezze di media mobile provate", "config.py")
    reg("lung_min", min(config.LUNGHEZZE), "annonum", "Media più corta provata", "config.py")
    reg("lung_max", max(config.LUNGHEZZE), "annonum", "Media più lunga provata", "config.py")
    reg("n_confronti", len(R), "int", "Confronti regola contro scimmie (indici per lunghezze), corretti con Holm per ogni misura", "confronti.csv")
    reg("spartiacque", config.DATA_SPARTIACQUE, "data_lunga", "Data che divide in due la storia dell'S&P 500", "config.py")
    reg("data_inizio_sp", usati[0]["prima"], "data_lunga", "Primo giorno del confronto sull'S&P 500", "dati/")
    reg("data_ultima", usati[0]["ultima"], "data_lunga", "Ultima seduta dell'S&P 500", "dati/")
    reg("sedute_sp", usati[0]["sedute"], "int", "Sedute del confronto sull'S&P 500", "dati/")
    reg("soglia95", 0.95, "pct0", "Quota di scimmie da battere nelle ipotesi 3 e 4", "config.py")
    reg("soglia_ip3_alfa", S["ip3_alfa"], "num2", "Soglia di significatività", "config.py")
    reg("soglia_ip2_pp", S["ip2_pp"], "pp1", "Soglia di vantaggio sulla perdita massima", "config.py")
    reg("soglia_ip5", S["ip5_perc"], "pct0", "Percentile minimo dell'ipotesi 5", "config.py")
    reg("soglia_ip6_pp", S["ip6_pp"], "pp1", "Soglia di perdita da costi (ipotesi 6)", "config.py")
    reg("soglia_ip4_meta", S["ip4_meta"], "int", "Soglia del numero di combinazioni (ipotesi 4)", "config.py")

    # --- descrizione per indice (media principale) ------------------------------------------------------------
    for tk, r in sub.iterrows():
        s = tk.replace("^", "").lower()
        reg(f"{s}_quota", r["quota"], "pct0", f"Quota di sedute investite dalla media principale, {r['indice']}", "confronti.csv")
        reg(f"{s}_ops_anno", r["n_operazioni"] / (r["T"] / config.SEDUTE_ANNO), "num1", f"Operazioni (acquisti e vendite) per anno, {r['indice']}", "confronti.csv")
        reg(f"{s}_cagr", r["regola_cagr_lordo"], "pct1", f"Rendimento annuo della media principale senza costi, {r['indice']}", "confronti.csv")
        reg(f"{s}_cagr_bh", r["bh_cagr"], "pct1", f"Rendimento annuo del buy & hold, {r['indice']}", "confronti.csv")
        reg(f"{s}_mdd", r["regola_mdd_lordo"], "pct0", f"Perdita massima della media principale, {r['indice']}", "confronti.csv")
        reg(f"{s}_mdd_bh", r["bh_mdd"], "pct0", f"Perdita massima del buy & hold, {r['indice']}", "confronti.csv")
        reg(f"{s}_sharpe", r["regola_sharpe_lordo"], "num2", f"Sharpe della media principale, {r['indice']}", "confronti.csv")
        reg(f"{s}_sharpe_bh", r["bh_sharpe"], "num2", f"Sharpe del buy & hold, {r['indice']}", "confronti.csv")
        reg(f"{s}_sharpe_scimmie", r["bl_sharpe_media"], "num2", f"Sharpe medio delle scimmie a blocchi, {r['indice']}", "confronti.csv")
        reg(f"{s}_perc_sharpe", r["perc_bl_sharpe"], "pct0", f"Quota di scimmie a blocchi battute sullo Sharpe, {r['indice']}", "confronti.csv")
        reg(f"{s}_holm_sharpe", r["holm_bl_sharpe"], "pval", f"p corretto (Holm) sullo Sharpe contro le scimmie a blocchi, {r['indice']}", "confronti.csv")
        reg(f"{s}_cagr_scimmie", r["bl_cagr_media"], "pct1", f"Rendimento annuo medio delle scimmie a blocchi, {r['indice']}", "confronti.csv")
        reg(f"{s}_perc_cagr", r["perc_bl_cagr"], "pct0", f"Quota di scimmie a blocchi battute sul rendimento annuo, {r['indice']}", "confronti.csv")
        reg(f"{s}_holm_cagr", r["holm_bl_cagr"], "pval", f"p corretto (Holm) sul rendimento annuo contro le scimmie a blocchi, {r['indice']}", "confronti.csv")
        reg(f"{s}_perc_mdd", r["perc_bl_mdd"], "pct0", f"Quota di scimmie a blocchi con perdita massima più profonda della regola, {r['indice']}", "confronti.csv")
        reg(f"{s}_mdd_scimmie", r["bl_mdd_media"], "pct0", f"Perdita massima media delle scimmie a blocchi, {r['indice']}", "confronti.csv")
    # S&P 500: dettagli
    reg("sp_cagr_netto", s0["regola_cagr_netto"], "pct1", "Rendimento annuo della media principale con costi, S&P 500", "confronti.csv")
    reg("sp_costo_pp", s0["regola_cagr_lordo"] - s0["regola_cagr_netto"], "pp2", "Rendimento annuo perso per i costi, punti percentuali, S&P 500", "confronti.csv")
    reg("sp_perc_cagr_netto", s0["perc_bln_cagr"], "pct0", "Quota di scimmie a blocchi (con costi) battute sul rendimento annuo con costi, S&P 500", "confronti.csv")
    reg("sp_perc_sharpe_moneta", s0["perc_mo_sharpe"], "pct0", "Quota di scimmie a moneta battute sullo Sharpe, S&P 500", "confronti.csv")
    reg("sp_perc_cagr_moneta", s0["perc_mo_cagr"], "pct0", "Quota di scimmie a moneta battute sul rendimento annuo, S&P 500", "confronti.csv")
    reg("sp_cagr_moneta", s0["mo_cagr_media"], "pct1", "Rendimento annuo medio delle scimmie a moneta, S&P 500", "confronti.csv")
    reg("sp_sharpe_moneta", s0["mo_sharpe_media"], "num2", "Sharpe medio delle scimmie a moneta, S&P 500", "confronti.csv")
    reg("sp_cagr_scimmie_p5", s0["bl_cagr_p5"], "pct1", "5° percentile del rendimento annuo delle scimmie a blocchi, S&P 500", "confronti.csv")
    reg("sp_cagr_scimmie_p95", s0["bl_cagr_p95"], "pct1", "95° percentile del rendimento annuo delle scimmie a blocchi, S&P 500", "confronti.csv")
    reg("sp_sharpe_scimmie_p5", s0["bl_sharpe_p5"], "num2", "5° percentile dello Sharpe delle scimmie a blocchi, S&P 500", "confronti.csv")
    reg("sp_sharpe_scimmie_p95", s0["bl_sharpe_p95"], "num2", "95° percentile dello Sharpe delle scimmie a blocchi, S&P 500", "confronti.csv")
    reg("sp_ops", int(s0["n_operazioni"]), "int", "Operazioni totali della media principale, S&P 500", "confronti.csv")

    # --- verdetti ---------------------------------------------------------------------------------------------
    h1 = int((sub["regola_cagr_lordo"] < sub["bh_cagr"]).sum())
    reg("h1_n", h1, "annonum", "Indici in cui la media principale rende meno del buy & hold (ipotesi 1)", "confronti.csv")
    reg("h1_ok", int(h1 >= S["ip1_indici"]), "int", "1 se l'ipotesi 1 è confermata", "confronti.csv")
    vant = (sub["regola_mdd_lordo"] - sub["bh_mdd"])
    reg("h2_min_pp", float(vant.min()), "pp1", "Vantaggio minimo sulla perdita massima tra gli indici, punti percentuali", "confronti.csv")
    reg("h2_max_pp", float(vant.max()), "pp1", "Vantaggio massimo sulla perdita massima tra gli indici, punti percentuali", "confronti.csv")
    reg("h2_ok", int((vant >= S["ip2_pp"]).all()), "int", "1 se l'ipotesi 2 è confermata", "confronti.csv")
    h3 = int(((sub["holm_bl_sharpe"] < S["ip3_alfa"]) & (sub["perc_bl_sharpe"] >= 0.95)).sum())
    reg("h3_n", h3, "annonum", "Indici in cui lo Sharpe batte il 95% delle scimmie con Holm sotto 0,05 (ipotesi 3)", "confronti.csv")
    reg("h3_ok", int(h3 >= S["ip3_indici"]), "int", "1 se l'ipotesi 3 è confermata", "confronti.csv")
    h4 = int(((R["holm_bl_cagr"] < S["ip3_alfa"]) & (R["perc_bl_cagr"] >= 0.95)).sum())
    reg("h4_n", h4, "annonum", "Combinazioni in cui il rendimento annuo batte il 95% delle scimmie con Holm sotto 0,05 (ipotesi 4)", "confronti.csv")
    reg("h4_ok", int(h4 < S["ip4_meta"]), "int", "1 se l'ipotesi 4 è confermata", "confronti.csv")
    reg("h4_n_nominale", int(((R["p_bl_cagr"] < 0.05) & (R["perc_bl_cagr"] >= 0.95)).sum()), "annonum", "Combinazioni con p non corretto sotto 0,05 sul rendimento annuo", "confronti.csv")
    reg("h3_n_nominale20", int(((R["p_bl_sharpe"] < 0.05) & (R["perc_bl_sharpe"] >= 0.95)).sum()), "annonum", "Combinazioni (su 20) con p non corretto sotto 0,05 sullo Sharpe", "confronti.csv")
    reg("h3_n_holm20", int(((R["holm_bl_sharpe"] < 0.05) & (R["perc_bl_sharpe"] >= 0.95)).sum()), "annonum", "Combinazioni (su 20) con Holm sotto 0,05 sullo Sharpe", "confronti.csv")
    percs = sp["perc_bl_sharpe"]
    reg("h5_min", float(percs.min()), "pct0", "Quota minima di scimmie battute sullo Sharpe tra le 5 lunghezze, S&P 500", "confronti.csv")
    reg("h5_max", float(percs.max()), "pct0", "Quota massima di scimmie battute sullo Sharpe tra le 5 lunghezze, S&P 500", "confronti.csv")
    reg("h5_ok", int((percs >= S["ip5_perc"]).all()), "int", "1 se l'ipotesi 5 è confermata", "confronti.csv")
    reg("h6_ok", int(s0["regola_cagr_lordo"] - s0["regola_cagr_netto"] < S["ip6_pp"]), "int", "1 se l'ipotesi 6 è confermata", "confronti.csv")
    mp, md_ = M[M.meta == "prima"].iloc[0], M[M.meta == "dopo"].iloc[0]
    for lab, r in (("m1", mp), ("m2", md_)):
        reg(f"{lab}_dal", r["dal"], "data_lunga", "Inizio della metà", "meta.csv")
        reg(f"{lab}_al", r["al"], "data_lunga", "Fine della metà", "meta.csv")
        reg(f"{lab}_perc_sharpe", r["perc_bl_sharpe"], "pct0", "Quota di scimmie battute sullo Sharpe nella metà", "meta.csv")
        reg(f"{lab}_sharpe", r["regola_sharpe_lordo"], "num2", "Sharpe della regola nella metà", "meta.csv")
        reg(f"{lab}_sharpe_bh", r["bh_sharpe"], "num2", "Sharpe del buy & hold nella metà", "meta.csv")
        reg(f"{lab}_cagr", r["regola_cagr_lordo"], "pct1", "Rendimento annuo della regola nella metà", "meta.csv")
        reg(f"{lab}_cagr_bh", r["bh_cagr"], "pct1", "Rendimento annuo del buy & hold nella metà", "meta.csv")
        reg(f"{lab}_perc_cagr", r["perc_bl_cagr"], "pct0", "Quota di scimmie battute sul rendimento annuo nella metà", "meta.csv")
    reg("h7_ok", int(mp["perc_bl_sharpe"] >= S["ip7_perc"] and md_["perc_bl_sharpe"] >= S["ip7_perc"]), "int", "1 se l'ipotesi 7 è confermata", "meta.csv")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")
    print(R[["indice", "lunghezza", "regola_cagr_lordo", "bh_cagr", "perc_bl_cagr", "perc_bl_sharpe", "regola_mdd_lordo", "bh_mdd"]].round(3).to_string())


if __name__ == "__main__":
    main()
