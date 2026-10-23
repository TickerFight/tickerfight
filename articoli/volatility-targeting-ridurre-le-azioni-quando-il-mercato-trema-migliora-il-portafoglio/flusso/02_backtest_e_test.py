"""Passo 2 - Volatility targeting: strategia contro buy & hold, contro il buy & hold con la stessa volatilità e contro le scimmie.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json       ogni numero dell'articolo, con descrizione e origine di calcolo
  indici_usati.json   indici effettivamente usati
  varianti.csv        le varianti di robustezza, tutte, indice per indice
  scimmie_sharpe.csv  Sharpe lordo di ogni scimmia, per indice
  bootstrap.csv       differenze di Sharpe ricampionate (strategia - buy & hold), per indice
  curve_<ticker>.csv  curve, pesi e volatilità mobile dell'indice principale (una seduta su cinque)
Scimmia: stessi pesi mensili della strategia, ma assegnati ai mesi in ordine casuale (confronto lordo di costi).
"""
import json
import math
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


def slug(ticker: str) -> str:
    return ticker.replace("^", "").replace(".", "_").lower()


def holm(p: dict) -> dict:
    ordine = sorted(p, key=p.get)
    mm = len(ordine)
    out, massimo = {}, 0.0
    for k, nome in enumerate(ordine):
        massimo = max(massimo, min(1.0, (mm - k) * p[nome]))
        out[nome] = massimo
    return out


def carica(ticker: str) -> pd.Series:
    df = pd.read_csv(config.file_dati(ticker), parse_dates=["Date"], index_col="Date").sort_index()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep="last")]
    c = df["Close"].astype(float)
    if (c <= 0).any() or c.isna().any():
        raise SystemExit(f"{ticker}: chiusure mancanti o non positive.")
    return c


def metriche_base(d: pd.DataFrame, anni: float) -> dict:
    rs, rb = d["strategia"], d["buyhold"]
    vs, vb = m.vol_annua(rs, GA), m.vol_annua(rb, GA)
    k = vs / vb                                   # buy & hold con la stessa volatilità: peso fisso k, ribilanciato ogni giorno
    req = k * d["r"]
    req.iloc[0] -= config.COSTO_BP / 1e4 * k      # paga l'acquisto iniziale
    return dict(rs=rs, rb=rb, req=req, k=k, vs=vs, vb=vb, veq=m.vol_annua(req, GA),
                cagr_s=m.cagr(rs, anni), cagr_b=m.cagr(rb, anni), cagr_eq=m.cagr(req, anni),
                dd_s=m.perdita_massima(rs), dd_b=m.perdita_massima(rb), dd_eq=m.perdita_massima(req),
                sh_s=m.sharpe(rs, GA), sh_b=m.sharpe(rb, GA),
                vv_s=m.volvol(rs, GA), vv_b=m.volvol(rb, GA))


def analizza(tk, nome, valuta, k_rng):
    meta = [r for r in META["indici"] if r["ticker"] == tk][0]
    if meta["stato"] != "ok":
        return None
    c = carica(tk)
    d = m.serie_strategia(c, config.OBIETTIVO_VOL, config.FINESTRA, config.TETTO_PESO, GA, config.COSTO_BP)
    anni = (d.index[-1] - d.index[0]).days / 365.25
    if anni < config.ANNI_MINIMI:
        print(f"{tk}: scartato, solo {anni:.1f} anni")
        return None
    b = metriche_base(d, anni)
    rs, rb = b["rs"].to_numpy(), b["rb"].to_numpy()
    rng = np.random.default_rng([config.SEME, k_rng])

    # --- bootstrap a blocchi sulla differenza di Sharpe --------------------------------------------------
    boot = m.bootstrap_dsharpe(rs, rb, config.N_BOOTSTRAP, config.BLOCCO_BOOTSTRAP, GA, rng)
    alfa = (1 - config.LIVELLO_CONFIDENZA) / 2
    lo, hi = np.quantile(boot, [alfa, 1 - alfa])

    # --- scimmie: stessi pesi, mesi a caso (lordo di costi) --------------------------------------------
    g = d.groupby("periodo")
    w = g["peso"].first().to_numpy()
    s1 = g["r"].sum().to_numpy()
    s2 = g["r"].apply(lambda x: (x ** 2).sum()).to_numpy()
    n = len(d)
    sh_lordo = float(m.sharpe_da_somme(w, s1, s2, n, GA))
    perm = rng.permuted(np.tile(w, (config.N_SCIMMIE, 1)), axis=1)
    sh_sc = m.sharpe_da_somme(perm, s1, s2, n, GA)
    p_sc = (int((sh_sc >= sh_lordo).sum()) + 1) / (config.N_SCIMMIE + 1)

    # --- finestre di crisi --------------------------------------------------------------------------------
    crisi = {}
    for k, (etichetta, ini, fin) in enumerate(config.CRISI):
        sel = (d.index >= pd.Timestamp(ini)) & (d.index <= pd.Timestamp(fin))
        if d.index[0] <= pd.Timestamp(ini) and sel.sum() > 5:
            crisi[k] = dict(s=float(np.prod(1 + rs[sel]) - 1), b=float(np.prod(1 + rb[sel]) - 1),
                            eq=float(np.prod(1 + b["req"].to_numpy()[sel]) - 1),
                            peso_medio=float(d["peso"].to_numpy()[sel].mean()))
        else:
            crisi[k] = None

    # --- varianti di robustezza (tutte riportate) ------------------------------------------------------------
    var = []
    for et, obiettivo, finestra, tetto in config.VARIANTI:
        dv = m.serie_strategia(c, obiettivo, finestra, tetto, GA, config.COSTO_BP)
        av = (dv.index[-1] - dv.index[0]).days / 365.25
        bv = metriche_base(dv, av)
        var.append(dict(indice=tk, variante=et, obiettivo=obiettivo, finestra=finestra, tetto=tetto,
                        sharpe_s=bv["sh_s"], sharpe_b=bv["sh_b"], cagr_s=bv["cagr_s"], cagr_b=bv["cagr_b"],
                        dd_s=bv["dd_s"], dd_b=bv["dd_b"], vol_s=bv["vs"], vol_b=bv["vb"],
                        peso_medio=float(dv["peso"].mean())))

    # --- curve dell'indice principale ------------------------------------------------------------------------
    curva = None
    if tk == config.INDICE_PRINCIPALE:
        es, eb, eq = m.equity(rs), m.equity(rb), m.equity(b["req"])
        vol_s = pd.Series(rs, index=d.index).rolling(GA).std(ddof=0) * np.sqrt(GA)
        vol_b = pd.Series(rb, index=d.index).rolling(GA).std(ddof=0) * np.sqrt(GA)
        e1 = np.r_[1.0, es]
        e2 = np.r_[1.0, eb]
        dd_s = (es / np.maximum.accumulate(np.r_[1.0, es])[1:] - 1)
        dd_b = (eb / np.maximum.accumulate(np.r_[1.0, eb])[1:] - 1)
        camp = np.arange(0, n, 5)
        curva = pd.DataFrame({"data": d.index[camp], "strategia": es[camp], "buyhold": eb[camp], "stessa_vol": eq[camp],
                              "dd_strategia": dd_s[camp], "dd_buyhold": dd_b[camp], "peso": d["peso"].to_numpy()[camp],
                              "vol_strategia": vol_s.to_numpy()[camp], "vol_buyhold": vol_b.to_numpy()[camp]})

    return dict(tk=tk, sl=slug(tk), nome=nome, d=d, anni=anni, b=b, lo=lo, hi=hi, boot=boot, sh_lordo=sh_lordo, sh_sc=sh_sc,
                p_sc=p_sc, crisi=crisi, var=var, curva=curva, w=w)


def main() -> None:
    global META
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    META = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    res = []
    for k, (tk, nome, valuta) in enumerate(config.INDICI):
        r = analizza(tk, nome, valuta, k)
        if r:
            res.append(r)
            b = r["b"]
            print(f"{tk}: {r['anni']:.1f} anni, Sharpe {b['sh_s']:.2f} contro {b['sh_b']:.2f}, volatilità {b['vs']:.3f} contro {b['vb']:.3f}, "
                  f"perdita massima {b['dd_s']:.2f} contro {b['dd_b']:.2f}, p scimmie {r['p_sc']:.3f}")
    if len(res) < 4:
        raise SystemExit("Troppi pochi indici utilizzabili.")

    ph = holm({r["tk"]: r["p_sc"] for r in res})
    n_ind = len(res)
    for r in res:
        sl, b, d = r["sl"], r["b"], r["d"]
        pesi = d["peso"]
        reg(f"{sl}_nome", r["nome"], "testo", "Nome dell'indice", "config.py, INDICI")
        reg(f"{sl}_prima_data", str(d.index[0].date()), "data", f"Prima seduta in cui la strategia ha una posizione ({r['nome']})")
        reg(f"{sl}_anni", r["anni"], "num1", f"Anni di storia usati ({r['nome']})")
        reg(f"{sl}_cagr_s", b["cagr_s"], "pct1", f"Rendimento annuo composto netto del volatility targeting ({r['nome']})")
        reg(f"{sl}_cagr_b", b["cagr_b"], "pct1", f"Rendimento annuo composto del buy & hold ({r['nome']})")
        reg(f"{sl}_cagr_eq", b["cagr_eq"], "pct1", f"Rendimento annuo composto del buy & hold con la stessa volatilità della strategia ({r['nome']})")
        reg(f"{sl}_vol_s", b["vs"], "pct1", f"Volatilità annua realizzata della strategia ({r['nome']})")
        reg(f"{sl}_vol_b", b["vb"], "pct1", f"Volatilità annua realizzata del buy & hold ({r['nome']})")
        reg(f"{sl}_vv_s", b["vv_s"], "pct1", f"Deviazione standard della volatilità a un anno mobile, strategia ({r['nome']})")
        reg(f"{sl}_vv_b", b["vv_b"], "pct1", f"Deviazione standard della volatilità a un anno mobile, buy & hold ({r['nome']})")
        reg(f"{sl}_dd_s", b["dd_s"], "pct1", f"Perdita massima della strategia ({r['nome']})")
        reg(f"{sl}_dd_b", b["dd_b"], "pct1", f"Perdita massima del buy & hold ({r['nome']})")
        reg(f"{sl}_dd_eq", b["dd_eq"], "pct1", f"Perdita massima del buy & hold con la stessa volatilità ({r['nome']})")
        reg(f"{sl}_sh_s", b["sh_s"], "num2", f"Indice di Sharpe della strategia, cassa a rendimento zero ({r['nome']})")
        reg(f"{sl}_sh_b", b["sh_b"], "num2", f"Indice di Sharpe del buy & hold, cassa a rendimento zero ({r['nome']})")
        reg(f"{sl}_dsh", b["sh_s"] - b["sh_b"], "num2", f"Differenza di Sharpe strategia meno buy & hold ({r['nome']})")
        reg(f"{sl}_dsh_lo", r["lo"], "num2", f"Estremo inferiore dell'intervallo al 95% della differenza di Sharpe ({r['nome']})",
            "bootstrap a blocchi circolari di 21 giorni su coppie di giorni")
        reg(f"{sl}_dsh_hi", r["hi"], "num2", f"Estremo superiore dell'intervallo al 95% della differenza di Sharpe ({r['nome']})",
            "bootstrap a blocchi circolari di 21 giorni su coppie di giorni")
        reg(f"{sl}_finale_s", config.CAPITALE * m.equity(b["rs"])[-1], "int", f"Valore finale di {config.CAPITALE:.0f} euro con la strategia, al lordo delle tasse ({r['nome']})")
        reg(f"{sl}_finale_b", config.CAPITALE * m.equity(b["rb"])[-1], "int", f"Valore finale di {config.CAPITALE:.0f} euro con il buy & hold, al lordo delle tasse ({r['nome']})")
        reg(f"{sl}_peso_medio", float(pesi.mean()), "pct0", f"Peso medio in azioni della strategia ({r['nome']})")
        reg(f"{sl}_quota_tetto", float((pesi >= config.TETTO_PESO - 1e-12).mean()), "pct0", f"Quota di sedute con peso pieno (tetto) ({r['nome']})")
        reg(f"{sl}_peso_min", float(pesi.min()), "pct0", f"Peso minimo raggiunto dalla strategia ({r['nome']})")
        reg(f"{sl}_scambi_anno", float(d["scambio"].sum() / r["anni"]), "num1",
            f"Scambio annuo, in multipli del capitale (somma delle variazioni di peso per anno) ({r['nome']})")
        reg(f"{sl}_sh_lordo", r["sh_lordo"], "num2", f"Sharpe lordo di costi della strategia, base del confronto con le scimmie ({r['nome']})")
        reg(f"{sl}_sh_sc_med", float(np.mean(r["sh_sc"])), "num2", f"Sharpe lordo medio delle scimmie ({r['nome']})")
        reg(f"{sl}_p_sc", r["p_sc"], "pval", f"Quota di scimmie con Sharpe uguale o maggiore della strategia (p-value) ({r['nome']})")
        reg(f"{sl}_p_sc_holm", ph[r["tk"]], "pval", f"p-value delle scimmie dopo la correzione di Holm ({r['nome']})")
        for kk, (et, _, _) in enumerate(config.CRISI):
            cr = r["crisi"][kk]
            if cr:
                reg(f"{sl}_crisi{kk}_s", cr["s"], "pct1", f"Rendimento della strategia nella finestra «{et}» ({r['nome']})")
                reg(f"{sl}_crisi{kk}_b", cr["b"], "pct1", f"Rendimento del buy & hold nella finestra «{et}» ({r['nome']})")
                reg(f"{sl}_crisi{kk}_peso", cr["peso_medio"], "pct0", f"Peso medio della strategia nella finestra «{et}» ({r['nome']})")

    # --- aggregati -----------------------------------------------------------------------------------------
    B = [r["b"] for r in res]
    reg("n_indici", n_ind, "int", "Numero di indici utilizzabili", "02_backtest_e_test.py")
    reg("n_scartati", len(config.INDICI) - n_ind, "int", "Indici scartati per dati assenti o storia troppo corta", "02_backtest_e_test.py")
    reg("n_vol_minore", sum(b["vs"] < b["vb"] for b in B), "int", "Indici in cui la volatilità della strategia è più bassa di quella del buy & hold")
    reg("n_vv_minore", sum(b["vv_s"] < b["vv_b"] for b in B), "int", "Indici in cui la volatilità a un anno varia meno nella strategia")
    reg("n_dd_minore", sum(b["dd_s"] > b["dd_b"] for b in B), "int", "Indici in cui la perdita massima della strategia è più piccola")
    reg("n_cagr_minore", sum(b["cagr_s"] < b["cagr_b"] for b in B), "int", "Indici in cui il rendimento annuo della strategia è più basso del buy & hold")
    reg("n_sh_sopra", sum(b["sh_s"] > b["sh_b"] for b in B), "int", "Indici in cui lo Sharpe della strategia è più alto di quello del buy & hold")
    reg("n_ic_zero", sum(r["lo"] <= 0 <= r["hi"] for r in res), "int", "Indici in cui l'intervallo di confidenza della differenza di Sharpe contiene lo zero")
    reg("n_ic_sopra", sum(r["lo"] > 0 for r in res), "int", "Indici in cui l'intervallo della differenza di Sharpe sta tutto sopra lo zero")
    reg("n_ic_sotto", sum(r["hi"] < 0 for r in res), "int", "Indici in cui l'intervallo della differenza di Sharpe sta tutto sotto lo zero")
    reg("n_scimmie_sign", sum(r["p_sc"] < 0.05 for r in res), "int", "Indici in cui meno del 5% delle scimmie ha uno Sharpe uguale o maggiore (senza correzione)")
    reg("n_scimmie_holm", sum(ph[r["tk"]] < 0.05 for r in res), "int", "Indici in cui il p-value delle scimmie resta sotto il 5% dopo la correzione di Holm")
    reg("n_eq_cagr_sopra", sum(b["cagr_s"] > b["cagr_eq"] for b in B), "int", "Indici in cui la strategia batte in rendimento annuo il buy & hold con la stessa volatilità")
    reg("n_eq_dd_meglio", sum(b["dd_s"] > b["dd_eq"] for b in B), "int", "Indici in cui la strategia ha una perdita massima più piccola del buy & hold con la stessa volatilità")
    reg("sh_diff_media", float(np.mean([b["sh_s"] - b["sh_b"] for b in B])), "num2", "Differenza media di Sharpe (strategia meno buy & hold) sugli indici")
    reg("peso_medio_tutti", float(np.mean([r["d"]["peso"].mean() for r in res])), "pct0", "Peso medio in azioni, media sugli indici")

    # --- parametri e fonti (giustificano le cifre del testo) ----------------------------------------------
    reg("obiettivo", config.OBIETTIVO_VOL, "pct0", "Volatilità annua obiettivo", "config.py, OBIETTIVO_VOL")
    reg("finestra", config.FINESTRA, "int", "Giorni di borsa per misurare la volatilità", "config.py, FINESTRA")
    reg("tetto", config.TETTO_PESO, "pct0", "Peso massimo in azioni", "config.py, TETTO_PESO")
    reg("costo_bp", config.COSTO_BP, "int", "Costo di ogni scambio in punti base", "config.py, COSTO_BP")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale di riferimento in euro", "config.py, CAPITALE")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Numero di scimmie", "config.py, N_SCIMMIE")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti del bootstrap", "config.py, N_BOOTSTRAP")
    reg("blocco", config.BLOCCO_BOOTSTRAP, "int", "Giorni per blocco del bootstrap", "config.py, BLOCCO_BOOTSTRAP")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello di confidenza", "config.py, LIVELLO_CONFIDENZA")
    reg("giorni_anno", GA, "int", "Giorni di borsa in un anno per annualizzare", "config.py, GIORNI_ANNO")
    reg("tetto_alto", config.VARIANTI[4][3], "num1", "Tetto della variante con leva", "config.py, VARIANTI")
    for kk, (et, ini, fin) in enumerate(config.CRISI):
        reg(f"crisi{kk}_nome", et, "testo", "Nome della finestra di crisi", "config.py, CRISI")
        reg(f"crisi{kk}_ini", ini, "data", f"Inizio della finestra «{et}» (fissata prima dei risultati)", "config.py, CRISI")
        reg(f"crisi{kk}_fin", fin, "data", f"Fine della finestra «{et}» (fissata prima dei risultati)", "config.py, CRISI")
    for kk, (et, ob, fi, te) in enumerate(config.VARIANTI):
        reg(f"var{kk}_nome", et, "testo", "Nome della variante di robustezza", "config.py, VARIANTI")
        vr = [v for r in res for v in r["var"] if v["variante"] == et]
        reg(f"var{kk}_n_sh", sum(v["sharpe_s"] > v["sharpe_b"] for v in vr), "int", f"Indici con Sharpe più alto del buy & hold, variante «{et}»")
        reg(f"var{kk}_n_dd", sum(v["dd_s"] > v["dd_b"] for v in vr), "int", f"Indici con perdita massima più piccola del buy & hold, variante «{et}»")
        reg(f"var{kk}_n_cagr", sum(v["cagr_s"] > v["cagr_b"] for v in vr), "int", f"Indici con rendimento annuo più alto del buy & hold, variante «{et}»")
        reg(f"var{kk}_dsh", float(np.mean([v["sharpe_s"] - v["sharpe_b"] for v in vr])), "num2", f"Differenza media di Sharpe sugli indici, variante «{et}»")
        reg(f"var{kk}_peso", float(np.mean([v["peso_medio"] for v in vr])), "pct0", f"Peso medio sugli indici, variante «{et}»")
    reg("lit_mm_anno", 2017, "annonum", "Anno di Moreira e Muir, Journal of Finance (volume 72)", "riferimento bibliografico")
    reg("lit_cowy_anno", 2020, "annonum", "Anno di Cederburg, O'Doherty, Wang e Yan, Journal of Financial Economics (volume 138)", "riferimento bibliografico")
    reg("lit_cowy_n", 103, "int", "Strategie azionarie studiate da Cederburg e coautori, secondo l'abstract", "abstract dell'articolo")
    reg("lit_hh_anno", 2018, "annonum", "Anno di Harvey e coautori, Journal of Portfolio Management", "riferimento bibliografico")
    reg("data_ultima", max(str(r["d"].index[-1].date()) for r in res), "data_lunga", "Ultima seduta dei dati", "dati/*.csv")

    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi", "02_backtest_e_test.py")

    # --- file ---------------------------------------------------------------------------------------------
    R = config.RISULTATI
    json.dump({"valori": RIS}, open(R / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump([{"ticker": r["tk"], "slug": r["sl"], "nome": r["nome"]} for r in res], open(R / "indici_usati.json", "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    pd.DataFrame([v for r in res for v in r["var"]]).to_csv(R / "varianti.csv", index=False, float_format="%.6f")
    pd.DataFrame({r["sl"]: r["sh_sc"] for r in res}).to_csv(R / "scimmie_sharpe.csv", index=False, float_format="%.5f")
    pd.DataFrame({r["sl"]: r["boot"] for r in res}).to_csv(R / "bootstrap.csv", index=False, float_format="%.5f")
    for r in res:
        if r["curva"] is not None:
            r["curva"].to_csv(R / "curva_principale.csv", index=False, float_format="%.6f")
    print(f"Scritti {len(RIS)} numeri in metriche.json")


if __name__ == "__main__":
    main()
