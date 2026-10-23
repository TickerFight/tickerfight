"""Passo 2 - Mille portafogli casuali di k titoli contro lo SPY e contro l'universo a pesi uguali.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json          ogni numero dell'articolo, con descrizione e origine di calcolo
  portafogli_k<k>.csv    per ogni portafoglio: rendimento annuo composto, Sharpe, drawdown massimo, CAGR nelle due metà
  riassunto_k.csv        per ogni k: mediana, percentili, quote di vittorie, Sharpe e drawdown mediani
  curve.csv              SPY, universo a pesi uguali e fascia (5°, 50°, 95° percentile) dei portafogli da K_PRINCIPALE titoli
  universo_usato.json    titoli tenuti e scartati

Nessun look-ahead: i titoli di ogni portafoglio sono estratti prima di guardare i rendimenti; i pesi sono 1/k all'inizio di
ogni anno solare. Nessun costo, nessuna tassa.
"""
import json
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import funzioni as fx

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con funzioni.py"


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    df = pd.read_csv(config.FILE_PREZZI, index_col="Date", parse_dates=True).sort_index()
    df = df[df.index >= pd.Timestamp(config.INIZIO)]
    spy = df[config.INDICE].dropna()
    giorni = spy.index                       # calendario di riferimento: i giorni di Borsa dello SPY
    df = df.reindex(giorni)

    # --- Universo: solo i titoli con prezzo dal primo giorno e quasi senza buchi ------------------------------------
    candidati = [t for t in config.UNIVERSO if t in df.columns]
    mancanti_download = [t for t in config.UNIVERSO if t not in df.columns]
    tenuti, scartati = [], {t: "assente da Yahoo Finance" for t in mancanti_download}
    for t in candidati:
        s = df[t]
        if pd.isna(s.iloc[0]):
            scartati[t] = "non quotato dal primo giorno"
        elif s.isna().mean() > config.SOGLIA_BUCHI:
            scartati[t] = "troppi giorni senza prezzo"
        else:
            tenuti.append(t)
    P_df = df[tenuti].ffill()
    P_df[config.INDICE] = df[config.INDICE]
    if P_df.isna().any().any():
        raise SystemExit("Prezzi mancanti dopo il riempimento: controllare i dati.")
    n = len(tenuti)
    if n < max(config.K_TITOLI) + 5:
        raise SystemExit(f"Universo troppo piccolo: {n} titoli.")
    (config.RISULTATI / "universo_usato.json").write_text(
        json.dumps({"tenuti": tenuti, "scartati": scartati}, ensure_ascii=False, indent=1), encoding="utf-8")

    P = P_df[tenuti].to_numpy(float)
    P_spy = P_df[[config.INDICE]].to_numpy(float)
    anni = giorni.year.to_numpy()
    T = len(giorni)
    giorni_cal = (giorni[-1] - giorni[0]).days
    i_meta = int(giorni.searchsorted(pd.Timestamp(config.META_DATA)))
    giorni_h1 = (giorni[i_meta] - giorni[0]).days
    giorni_h2 = (giorni[-1] - giorni[i_meta]).days

    # --- Confronti: SPY e universo a pesi uguali ---------------------------------------------------------------------
    V_spy = (P_spy / P_spy[0])[:, 0]
    V_ew = fx.curve_portafogli(P, anni, np.full((n, 1), 1.0 / n))[:, 0]

    def met(V):
        v = V.reshape(-1, 1)
        return {"cagr": float(fx.cagr(v, giorni_cal)[0]), "sharpe": float(fx.sharpe(v, config.GIORNI_ANNO_BORSA, config.TASSO_SENZA_RISCHIO)[0]),
                "mdd": float(fx.max_drawdown(v)[0]),
                "cagr_h1": float(fx.cagr(v[: i_meta + 1], giorni_h1)[0]),
                "cagr_h2": float(fx.cagr(v[i_meta:], giorni_h2)[0])}
    m_spy, m_ew = met(V_spy), met(V_ew)

    reg("data_prima", str(giorni[0].date()), "data_lunga", "Primo giorno di Borsa del periodo", "dati/prezzi.csv")
    reg("data_ultima", str(giorni[-1].date()), "data_lunga", "Ultimo giorno di Borsa del periodo", "dati/prezzi.csv")
    reg("anno_prima", str(giorni[0].date()), "anno", "Anno del primo giorno", "dati/prezzi.csv")
    reg("anno_ultima", str(giorni[-1].date()), "anno", "Anno dell'ultimo giorno", "dati/prezzi.csv")
    reg("anni_periodo", giorni_cal / config.GIORNI_ANNO_CALENDARIO, "num1", "Anni coperti dal periodo", "giorni di calendario / 365,25")
    reg("data_meta", str(giorni[i_meta].date()), "data_lunga", "Primo giorno di Borsa della seconda metà", "config.py, META_DATA")
    reg("anno_meta", str(giorni[i_meta].date()), "anno", "Anno in cui comincia la seconda metà", "config.py, META_DATA")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("n_universo_lista", len(config.UNIVERSO), "int", "Titoli nella lista di partenza (S&P 100 di oggi, una classe per società)", "config.py, UNIVERSO")
    reg("n_universo", n, "int", "Titoli tenuti nell'universo (prezzi dal primo giorno)", "02_backtest_e_test.py, filtro sui dati")
    reg("n_scartati", len(scartati), "int", "Titoli della lista scartati (non quotati dal primo giorno o assenti)", "02_backtest_e_test.py, filtro sui dati")
    reg("n_portafogli", config.N_PORTAFOGLI, "int", "Portafogli estratti per ogni dimensione", "config.py, N_PORTAFOGLI")
    reg("k_principale", config.K_PRINCIPALE, "int", "Dimensione di riferimento dei portafogli", "config.py, K_PRINCIPALE")
    for i, k in enumerate(config.K_TITOLI, 1):
        reg(f"k{i}", k, "int", f"Dimensione {i} dei portafogli (titoli)", "config.py, K_TITOLI")
    reg("livello_basso", config.LIVELLO_BASSO, "pct0", "Percentile basso della fascia", "config.py, LIVELLO_BASSO")
    reg("livello_alto", config.LIVELLO_ALTO, "pct0", "Percentile alto della fascia", "config.py, LIVELLO_ALTO")
    reg("s_ip1_quota", config.SOGLIE["ip1_quota"], "pct0", "Soglia della prima ipotesi: quota di portafogli che batte lo SPY", "config.py, SOGLIE")
    reg("s_ip2_lo", config.SOGLIE["ip2_lo"], "pct0", "Estremo inferiore della seconda ipotesi", "config.py, SOGLIE")
    reg("s_ip2_hi", config.SOGLIE["ip2_hi"], "pct0", "Estremo superiore della seconda ipotesi", "config.py, SOGLIE")
    reg("s_ip4_quota", config.SOGLIE["ip4_quota"], "pct0", "Soglia della quarta ipotesi: quota di portafogli da 5 titoli che perde contro lo SPY", "config.py, SOGLIE")
    reg("s_ip5_pp", config.SOGLIE["ip5_pp"], "num1", "Soglia della quinta ipotesi: punti percentuali di distanza tra drawdown", "config.py, SOGLIE")
    reg("s_ip6_corr", config.SOGLIE["ip6_corr"], "num2", "Soglia della sesta ipotesi: valore assoluto della correlazione", "config.py, SOGLIE")

    reg("spy_cagr", m_spy["cagr"], "pct1", "Rendimento annuo composto dello SPY (dividendi reinvestiti)", "SPY buy & hold, funzioni.cagr")
    reg("spy_sharpe", m_spy["sharpe"], "num2", "Sharpe annualizzato dello SPY (tasso senza rischio zero)", "funzioni.sharpe")
    reg("spy_mdd", -m_spy["mdd"], "pct1", "Perdita massima dal picco dello SPY (valore assoluto)", "funzioni.max_drawdown")
    reg("spy_cagr_h1", m_spy["cagr_h1"], "pct1", "Rendimento annuo composto dello SPY nella prima metà", "funzioni.cagr")
    reg("spy_cagr_h2", m_spy["cagr_h2"], "pct1", "Rendimento annuo composto dello SPY nella seconda metà", "funzioni.cagr")
    reg("ew_cagr", m_ew["cagr"], "pct1", "Rendimento annuo composto dell'universo a pesi uguali, ribilanciato ogni anno", "funzioni.curve_portafogli, funzioni.cagr")
    reg("ew_sharpe", m_ew["sharpe"], "num2", "Sharpe annualizzato dell'universo a pesi uguali", "funzioni.sharpe")
    reg("ew_mdd", -m_ew["mdd"], "pct1", "Perdita massima dal picco dell'universo a pesi uguali (valore assoluto)", "funzioni.max_drawdown")
    reg("ew_meno_spy", m_ew["cagr"] - m_spy["cagr"], "pp1", "Rendimento annuo dell'universo a pesi uguali meno quello dello SPY, in punti percentuali", "ew_cagr - spy_cagr")
    reg("ew_cagr_h1", m_ew["cagr_h1"], "pct1", "Rendimento annuo composto dell'universo a pesi uguali nella prima metà", "funzioni.cagr")
    reg("ew_cagr_h2", m_ew["cagr_h2"], "pct1", "Rendimento annuo composto dell'universo a pesi uguali nella seconda metà", "funzioni.cagr")

    # --- Portafogli casuali -----------------------------------------------------------------------------------------
    rng = np.random.default_rng(config.SEED)
    righe_k = []
    fascia = None
    q_lo, q_hi = config.LIVELLO_BASSO, config.LIVELLO_ALTO
    for i, k in enumerate(config.K_TITOLI, 1):
        W = fx.estrai_pesi(n, k, config.N_PORTAFOGLI, rng)
        V = fx.curve_portafogli(P, anni, W)
        c = fx.cagr(V, giorni_cal)
        sh = fx.sharpe(V, config.GIORNI_ANNO_BORSA, config.TASSO_SENZA_RISCHIO)
        md = fx.max_drawdown(V)
        c1 = fx.cagr(V[: i_meta + 1], giorni_h1)
        c2 = fx.cagr(V[i_meta:], giorni_h2)
        pd.DataFrame({"cagr": c, "sharpe": sh, "mdd": md, "cagr_h1": c1, "cagr_h2": c2}).to_csv(
            config.RISULTATI / f"portafogli_k{k}.csv", index=False, float_format="%.6f")
        p_lo, p_med, p_hi = np.quantile(c, [q_lo, 0.5, q_hi])
        quota_spy = float((c > m_spy["cagr"]).mean())
        quota_ew = float((c > m_ew["cagr"]).mean())
        righe_k.append({"k": k, "cagr_p5": p_lo, "cagr_med": p_med, "cagr_p95": p_hi, "quota_spy": quota_spy, "quota_ew": quota_ew,
                        "sharpe_med": float(np.median(sh)), "mdd_med": float(np.median(md)), "mdd_p5": float(np.quantile(md, q_lo)),
                        "cagr_min": float(c.min()), "cagr_max": float(c.max())})
        reg(f"k{k}_p5", p_lo, "pct1", f"Rendimento annuo composto al 5° percentile dei portafogli da {k} titoli", "np.quantile sui portafogli")
        reg(f"k{k}_med", p_med, "pct1", f"Rendimento annuo composto mediano dei portafogli da {k} titoli", "np.quantile sui portafogli")
        reg(f"k{k}_p95", p_hi, "pct1", f"Rendimento annuo composto al 95° percentile dei portafogli da {k} titoli", "np.quantile sui portafogli")
        reg(f"k{k}_larghezza", p_hi - p_lo, "pp1", f"Larghezza della fascia 5°-95° percentile del rendimento annuo dei portafogli da {k} titoli, in punti percentuali", "p95 - p5")
        reg(f"k{k}_min", c.min(), "pct1", f"Rendimento annuo composto del peggior portafoglio da {k} titoli", "min sui portafogli")
        reg(f"k{k}_max", c.max(), "pct1", f"Rendimento annuo composto del miglior portafoglio da {k} titoli", "max sui portafogli")
        reg(f"k{k}_quota_spy", quota_spy, "pct1", f"Quota di portafogli da {k} titoli con rendimento annuo composto superiore a quello dello SPY", "media del confronto sui portafogli")
        reg(f"k{k}_quota_perde", 1 - quota_spy, "pct1", f"Quota di portafogli da {k} titoli con rendimento annuo composto inferiore a quello dello SPY", "1 - quota di vittorie")
        reg(f"k{k}_quota_ew", quota_ew, "pct1", f"Quota di portafogli da {k} titoli con rendimento annuo composto superiore a quello dell'universo a pesi uguali", "media del confronto sui portafogli")
        reg(f"k{k}_sharpe_med", float(np.median(sh)), "num2", f"Sharpe mediano dei portafogli da {k} titoli", "mediana sui portafogli")
        reg(f"k{k}_mdd_med", -float(np.median(md)), "pct1", f"Perdita massima dal picco mediana dei portafogli da {k} titoli (valore assoluto)", "mediana sui portafogli")
        reg(f"k{k}_mdd_distanza", (-float(np.median(md))) - (-m_spy["mdd"]), "pp1", f"Perdita massima mediana dei portafogli da {k} titoli meno quella dello SPY, in punti percentuali", "mdd_med - spy_mdd")
        reg(f"k{k}_meglio_spy_sharpe", float((sh > m_spy["sharpe"]).mean()), "pct0", f"Quota di portafogli da {k} titoli con Sharpe superiore a quello dello SPY", "media del confronto sui portafogli")
        # metà del periodo
        reg(f"k{k}_quota_spy_h1", float((c1 > m_spy["cagr_h1"]).mean()), "pct0", f"Quota di portafogli da {k} titoli che batte lo SPY nella prima metà", "confronto sulla prima metà")
        reg(f"k{k}_quota_spy_h2", float((c2 > m_spy["cagr_h2"]).mean()), "pct0", f"Quota di portafogli da {k} titoli che batte lo SPY nella seconda metà", "confronto sulla seconda metà")
        reg(f"k{k}_quota_spy_entrambe", float(((c1 > m_spy["cagr_h1"]) & (c2 > m_spy["cagr_h2"])).mean()), "pct0",
            f"Quota di portafogli da {k} titoli che batte lo SPY in entrambe le metà", "confronto sulle due metà")
        reg(f"k{k}_quota_peggio_entrambe", float(((c1 < m_spy["cagr_h1"]) & (c2 < m_spy["cagr_h2"])).mean()), "pct0",
            f"Quota di portafogli da {k} titoli che perde contro lo SPY in entrambe le metà", "confronto sulle due metà")
        if k == config.K_PRINCIPALE:
            e1, e2 = c1 - m_spy["cagr_h1"], c2 - m_spy["cagr_h2"]
            corr = float(np.corrcoef(e1, e2)[0, 1])
            reg("corr_meta", corr, "num2", "Correlazione tra i portafogli dell'eccesso di rendimento annuo sullo SPY nella prima e nella seconda metà (k di riferimento)", "np.corrcoef")
            reg("corr_meta_abs", abs(corr), "num2", "Valore assoluto di corr_meta", "abs(corr_meta)")
            pd.DataFrame({"eccesso_h1": e1, "eccesso_h2": e2}).to_csv(config.RISULTATI / "persistenza.csv", index=False, float_format="%.6f")
            fascia = np.quantile(V, [q_lo, 0.5, q_hi], axis=1)
            # sovrapposizione media tra due portafogli qualsiasi: quanti titoli in comune (attesa k*k/n)
            reg("sovrapposizione_attesa", k * k / n, "num1", "Titoli in comune attesi tra due portafogli casuali di k titoli (k·k/n)", "k_principale^2 / n_universo")
            # rendimento medio di un singolo titolo, per mostrare la dispersione tra titoli
            ct = fx.cagr(P / P[0], giorni_cal)
            reg("titolo_peggiore", ct.min(), "pct1", "Rendimento annuo composto del peggior titolo dell'universo", "funzioni.cagr sui singoli titoli")
            reg("titolo_migliore", ct.max(), "pct1", "Rendimento annuo composto del miglior titolo dell'universo", "funzioni.cagr sui singoli titoli")
            reg("titolo_mediano", float(np.median(ct)), "pct1", "Rendimento annuo composto mediano dei singoli titoli", "funzioni.cagr sui singoli titoli")
            reg("quota_titoli_sopra_spy", float((ct > m_spy["cagr"]).mean()), "pct0", "Quota di titoli dell'universo che batte lo SPY (un titolo solo)", "confronto dei singoli titoli con lo SPY")
    pd.DataFrame(righe_k).to_csv(config.RISULTATI / "riassunto_k.csv", index=False, float_format="%.6f")
    pd.DataFrame({"Date": giorni, "spy": V_spy, "universo_pesi_uguali": V_ew,
                  "fascia_bassa": fascia[0], "fascia_mediana": fascia[1], "fascia_alta": fascia[2]}).to_csv(
        config.RISULTATI / "curve.csv", index=False, float_format="%.6f")

    # --- Verdetti delle ipotesi (numeri chiave) -----------------------------------------------------------------------
    kp = config.K_PRINCIPALE
    larg = [RIS[f"k{k}_larghezza"]["valore"] for k in config.K_TITOLI]
    reg("ip3_si_restringe", int(all(a > b for a, b in zip(larg, larg[1:]))), "int", "1 se la fascia 5°-95° si restringe a ogni passo di k, 0 altrimenti", "confronto tra k consecutivi")

    # --- Controllo con altri semi: la quota di vittorie dipende dall'estrazione? ---------------------------------------------
    quote_spy, quote_ew = [RIS[f"k{kp}_quota_spy"]["valore"]], [RIS[f"k{kp}_quota_ew"]["valore"]]
    for sd in config.SEED_CONTROLLO:
        W = fx.estrai_pesi(n, kp, config.N_PORTAFOGLI, np.random.default_rng(sd))
        c = fx.cagr(fx.curve_portafogli(P, anni, W), giorni_cal)
        quote_spy.append(float((c > m_spy["cagr"]).mean()))
        quote_ew.append(float((c > m_ew["cagr"]).mean()))
    reg("seed_n", 1 + len(config.SEED_CONTROLLO), "int", "Estrazioni indipendenti (semi diversi) del controllo", "config.py, SEED e SEED_CONTROLLO")
    reg("seed_spy_min", min(quote_spy), "pct1", "Quota minima di portafogli (k di riferimento) che batte lo SPY, tra i semi", "min sui semi")
    reg("seed_spy_max", max(quote_spy), "pct1", "Quota massima di portafogli (k di riferimento) che batte lo SPY, tra i semi", "max sui semi")
    reg("seed_ew_min", min(quote_ew), "pct1", "Quota minima di portafogli (k di riferimento) che batte l'universo a pesi uguali, tra i semi", "min sui semi")
    reg("seed_ew_max", max(quote_ew), "pct1", "Quota massima di portafogli (k di riferimento) che batte l'universo a pesi uguali, tra i semi", "max sui semi")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri; universo di {n} titoli, {len(scartati)} scartati")


if __name__ == "__main__":
    main()
