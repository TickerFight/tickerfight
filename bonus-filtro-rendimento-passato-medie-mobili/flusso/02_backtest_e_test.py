"""Passo 2 - Il filtro sul rendimento passato, provato fuori campione.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json              ogni numero dell'articolo, con descrizione e origine di calcolo
  titoli.csv                 una riga per titolo: rendimento passato, gruppo, risultati di regola, buy & hold e filtro
  curva_portafoglio.csv      valore giorno per giorno dei portafogli: buy & hold, regola, filtro, filtro sulla metà
  simulazioni_casuali.csv    valore finale del portafoglio quando la regola è assegnata a caso a un terzo dei titoli

Regole del metodo:
  - ipotesi, strategia e parametri sono fissati in config.py prima di guardare i risultati;
  - il rendimento passato è misurato sui dodici mesi PRIMA del primo ordine e l'ordinamento dei titoli si fa
    il primo giorno: nessuna informazione dal futuro;
  - ogni titolo parte con 500 euro, 1 euro a ordine e 26% di tassa in euro: gli stessi conti degli articoli precedenti;
  - ogni numero dell'articolo passa da reg(): niente cifre scritte a mano nel testo.
"""
import json
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import simulazione as s

RIS: dict = {}


def reg(chiave, valore, formato, descrizione, origine):
    """Registra un numero con la sua giustificazione (finisce nelle note dell'articolo)."""
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def spearman(x, y) -> float:
    return float(np.corrcoef(pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy())[0, 1])


def test_correlazione(x, y, rng):
    """Spearman, p-value di permutazione a una coda (ipotesi: correlazione negativa), IC bootstrap al 95%."""
    n = len(x)
    rho = spearman(x, y)
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    rxc = (rx - rx.mean()) / np.linalg.norm(rx - rx.mean())
    ryc = ry - ry.mean()
    idx = rng.random((config.N_PERMUTAZIONI, n)).argsort(axis=1)
    rho_perm = (ryc[idx] * rxc).sum(axis=1) / np.linalg.norm(ryc)
    p = (int((rho_perm <= rho).sum()) + 1) / (config.N_PERMUTAZIONI + 1)
    ib = rng.integers(0, n, (config.N_BOOTSTRAP, n))
    a = pd.DataFrame(np.asarray(x)[ib]).rank(axis=1).to_numpy()
    b = pd.DataFrame(np.asarray(y)[ib]).rank(axis=1).to_numpy()
    a, b = a - a.mean(axis=1, keepdims=True), b - b.mean(axis=1, keepdims=True)
    boot = (a * b).sum(axis=1) / np.sqrt((a ** 2).sum(axis=1) * (b ** 2).sum(axis=1))
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return rho, p, float(lo), float(hi)


def maxdd(v) -> float:
    v = np.asarray(v)
    return float(-(v / np.maximum.accumulate(v) - 1).min())


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    comp = pd.read_csv(config.FILE_COMPOSIZIONE).set_index("ticker_yahoo")
    cambio = s.carica_csv(config.FILE_CAMBIO)
    rng = np.random.default_rng(config.SEME_STAT)

    righe, eq_mm, eq_bh, fine_set, inizio_set = [], {}, {}, set(), set()
    for t in meta["titoli"]:
        df = s.prepara(s.carica_csv(config.DATI_TITOLI / f"{t}.csv"), cambio, config.SMA_VELOCE, config.SMA_LENTA)
        df = df[df.index <= pd.Timestamp(config.FINE_TEST)]
        i0 = s.indice_data(df, df.index[-1] - pd.DateOffset(years=config.ANNI_TEST))
        if i0 < config.SEDUTE_MINIME_PRIMA:
            raise SystemExit(f"{t}: storia troppo corta.")
        if df["fx"].iloc[i0 - 1:].isna().any():
            raise SystemExit(f"{t}: cambio mancante nel periodo del test.")
        fine_set.add(df.index[-1])
        inizio_set.add(df.index[i0])
        C = df["Close"].to_numpy()
        ret = float(C[i0 - 1] / C[i0 - 1 - config.FINESTRA_RENDIMENTO] - 1)
        mm = s.simula(df, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, config.MODO_PRINCIPALE, True)
        bh = s.simula(df, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, config.MODO_PRINCIPALE, False)
        righe.append({"ticker": t, "nome": comp.loc[t, "nome"], "settore": comp.loc[t, "settore"], "ret": ret,
                      "finale_mm": mm["valore_finale_eur"], "finale_bh": bh["valore_finale_eur"],
                      "differenza": mm["valore_finale_eur"] - bh["valore_finale_eur"],
                      "rend_bh": bh["rendimento_totale"], "rend_mm": mm["rendimento_totale"]})
        d = df.index[i0:]
        eq_mm[t] = pd.Series(mm["equity"], index=d)
        eq_bh[t] = pd.Series(bh["equity"], index=d)
    if max(fine_set) - min(fine_set) > pd.Timedelta(days=5) or max(inizio_set) - min(inizio_set) > pd.Timedelta(days=5):
        raise SystemExit("I titoli non coprono lo stesso periodo di test.")

    tab = pd.DataFrame(righe)
    n = len(tab)
    ordine = tab["ret"].rank(method="first").astype(int)       # 1 = rendimento passato più basso
    nt, nm = int(n * config.QUOTA_FILTRO), int(n * config.QUOTA_CONTROLLO)
    tab["gruppo"] = np.where(ordine <= nt, "basso", np.where(ordine > n - nt, "alto", "medio"))
    tab["filtro"] = ordine <= nt
    tab["filtro_meta"] = ordine <= nm
    tab["finale_filtro"] = np.where(tab["filtro"], tab["finale_mm"], tab["finale_bh"])
    tab["finale_filtro_meta"] = np.where(tab["filtro_meta"], tab["finale_mm"], tab["finale_bh"])
    tab["vince"] = tab["differenza"] > 0
    tab.to_csv(config.RISULTATI / "titoli.csv", index=False, float_format="%.6f")

    ok = pd.DataFrame(eq_mm).notna().all(axis=1) & pd.DataFrame(eq_bh).notna().all(axis=1)
    EM, EB = pd.DataFrame(eq_mm)[ok], pd.DataFrame(eq_bh)[ok]
    f_set = list(tab.loc[tab["filtro"], "ticker"])
    m_set = list(tab.loc[tab["filtro_meta"], "ticker"])
    curva = pd.DataFrame({
        "data": EM.index,
        "valore_bh": EB.sum(axis=1).to_numpy(), "valore_regola": EM.sum(axis=1).to_numpy(),
        "valore_filtro": (EM[f_set].sum(axis=1) + EB.drop(columns=f_set).sum(axis=1)).to_numpy(),
        "valore_filtro_meta": (EM[m_set].sum(axis=1) + EB.drop(columns=m_set).sum(axis=1)).to_numpy(),
    })
    curva.to_csv(config.RISULTATI / "curva_portafoglio.csv", index=False, float_format="%.6f")

    cap = config.CAPITALE * n
    F = {"bh": tab["finale_bh"].sum(), "mm": tab["finale_mm"].sum(), "fl": tab["finale_filtro"].sum(),
         "fm": tab["finale_filtro_meta"].sum()}
    tl = "titoli.csv"
    origine_dati = f"dati/ ({meta['fonte']}, scaricati il {meta['scaricato_il_utc'][:10]})"

    # --- Parametri e campione -------------------------------------------------------------------------------
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale per ogni titolo, in euro", "config.py, CAPITALE")
    reg("capitale_totale", cap, "int", "Capitale iniziale complessivo, in euro", "config.py: CAPITALE per numero di titoli")
    reg("commissione", config.COMMISSIONE, "num2", "Commissione fissa per ogni ordine, in euro", "config.py, COMMISSIONE")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    reg("sma_veloce", config.SMA_VELOCE, "annonum", "Giorni della media veloce", "config.py, SMA_VELOCE")
    reg("sma_lenta", config.SMA_LENTA, "annonum", "Giorni della media lenta", "config.py, SMA_LENTA")
    reg("n_permutazioni", config.N_PERMUTAZIONI, "int", "Permutazioni per i p-value", "config.py, N_PERMUTAZIONI")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py, N_BOOTSTRAP")
    reg("livello_ic", 0.95, "pct0", "Livello degli intervalli di confidenza e percentile alto usato per la distribuzione casuale", "02_backtest_e_test.py, percentili 2,5 e 97,5 del bootstrap; 95° percentile")
    reg("seme", config.SEME, "annonum", "Seme del sorteggio dei titoli", "config.py, SEME")
    reg("data_inizio", str(min(inizio_set).date()), "data_lunga", "Prima seduta del test", origine_dati)
    reg("data_fine", str(max(fine_set).date()), "data_lunga", "Ultima seduta del test", origine_dati)
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("n_titoli", n, "int", "Titoli del campione fuori campione", f"{tl}")
    reg("n_gia_usati", meta["titoli_gia_usati"], "int", "Titoli già usati negli articoli precedenti, esclusi dal sorteggio", "dati/metadati.json")
    reg("n_provati", meta["titoli_provati"], "int", "Titoli provati per ottenerne il numero richiesto", "dati/metadati.json")
    reg("n_scartati", meta["titoli_scartati"], "int", "Titoli scartati per dati assenti o storia troppo corta", "dati/metadati.json")
    reg("n_filtro", nt, "int", "Titoli nel gruppo con il rendimento passato più basso (a cui si applica la regola)", f"{tl}: un terzo di n")
    reg("n_filtro_meta", nm, "int", "Titoli nel gruppo di controllo (metà più bassa)", f"{tl}: metà di n")
    reg("soglia_ret", float(tab.loc[tab["filtro"], "ret"].max()), "pct0",
        "Rendimento passato più alto tra i titoli del terzo più basso (soglia del filtro)", f"{tl}")

    # --- 1) La relazione si ripete? ---------------------------------------------------------------------------
    rho, p, lo, hi = test_correlazione(tab["ret"].to_numpy(), tab["differenza"].to_numpy(), rng)
    reg("rho", rho, "num2", "Correlazione di rango tra rendimento passato e differenza regola meno buy & hold, fuori campione", f"{tl}: Spearman")
    reg("rho_lo", lo, "num2", "Estremo inferiore dell'intervallo di confidenza al 95%", "bootstrap sui titoli")
    reg("rho_hi", hi, "num2", "Estremo superiore dell'intervallo di confidenza al 95%", "bootstrap sui titoli")
    reg("rho_p", p, "pval", "p-value di permutazione a una coda (ipotesi: correlazione negativa)", "permutazione")
    reg("quota_vince", float(tab["vince"].mean()), "pct0", "Quota di titoli su cui la regola batte il buy & hold, fuori campione", f"{tl}: differenza > 0")
    reg("n_vince", int(tab["vince"].sum()), "int", "Titoli su cui la regola batte il buy & hold", f"{tl}: differenza > 0")
    reg("mediana_diff", float(tab["differenza"].median()), "num2", "Differenza mediana in euro, regola meno buy & hold", f"{tl}")
    for g in ("basso", "medio", "alto"):
        d = tab[tab["gruppo"] == g]
        reg(f"g_{g}_vince", float(d["vince"].mean()), "pct0", f"Quota di titoli su cui vince la regola nel gruppo con rendimento passato {g}", f"{tl}")
        reg(f"g_{g}_ret", float(d["ret"].median()), "pct0", f"Rendimento passato mediano del gruppo {g}", f"{tl}")
        reg(f"g_{g}_rbh", float(d["rend_bh"].median()), "pct0", f"Rendimento mediano del buy & hold nei cinque anni, gruppo {g}", f"{tl}")
        reg(f"g_{g}_diff", float(d["differenza"].median()), "num2", f"Differenza mediana in euro, gruppo {g}", f"{tl}")
    reg("rho_diff_rbh", spearman(tab["rend_bh"].to_numpy(), tab["differenza"].to_numpy()), "num2",
        "Correlazione di rango tra rendimento del buy & hold e differenza", f"{tl}: Spearman")
    reg("rho_ret_rbh", spearman(tab["ret"].to_numpy(), tab["rend_bh"].to_numpy()), "num2",
        "Correlazione di rango tra rendimento passato e rendimento del buy & hold nei cinque anni", f"{tl}: Spearman")

    # --- 2) e 3) Portafogli ------------------------------------------------------------------------------------
    nomi = {"bh": "buy & hold su tutti i titoli", "mm": "regola su tutti i titoli",
            "fl": "regola sul terzo con rendimento passato più basso, buy & hold sugli altri",
            "fm": "regola sulla metà con rendimento passato più basso, buy & hold sugli altri"}
    for k, v in F.items():
        reg(f"finale_{k}", float(v), "num2", f"Valore finale netto in euro del portafoglio: {nomi[k]}", f"{tl}: somma dei valori finali")
        reg(f"rend_{k}", float(v / cap - 1), "pct0", f"Rendimento totale netto del portafoglio: {nomi[k]}", "finale / capitale_totale - 1")
    for k, col in (("bh", "valore_bh"), ("mm", "valore_regola"), ("fl", "valore_filtro"), ("fm", "valore_filtro_meta")):
        reg(f"maxdd_{k}", maxdd(curva[col]), "pct0", f"Perdita massima dal picco del portafoglio: {nomi[k]}", "curva_portafoglio.csv")
    reg("diff_fl_bh", float(F["fl"] - F["bh"]), "num2", "Filtro meno buy & hold, in euro (segno: + vantaggio del filtro)", "finale_fl - finale_bh")
    reg("diff_fl_bh_abs", float(abs(F["fl"] - F["bh"])), "num2", "Distanza in euro tra filtro e buy & hold", "|finale_fl - finale_bh|")
    reg("diff_fl_bh_pct_abs", float(abs(F["fl"] / F["bh"] - 1)), "pct1", "Distanza tra filtro e buy & hold in percentuale del valore finale del buy & hold", "|finale_fl / finale_bh - 1|")
    reg("diff_fl_mm", float(F["fl"] - F["mm"]), "num2", "Filtro meno regola su tutti i titoli, in euro", "finale_fl - finale_mm")
    reg("diff_mm_bh_abs", float(abs(F["mm"] - F["bh"])), "num2", "Distanza in euro tra regola su tutti i titoli e buy & hold", "|finale_mm - finale_bh|")
    reg("diff_fm_bh", float(F["fm"] - F["bh"]), "num2", "Controllo: filtro sulla metà meno buy & hold, in euro", "finale_fm - finale_bh")
    d_stock = (tab["finale_filtro"] - tab["finale_bh"]).to_numpy()
    ib = rng.integers(0, n, (config.N_BOOTSTRAP, n))
    medie = d_stock[ib].mean(axis=1)
    lo_b, hi_b = np.percentile(medie, [2.5, 97.5])
    reg("fl_bh_medio", float(d_stock.mean()), "num2", "Differenza media per titolo, filtro meno buy & hold, in euro", f"{tl}")
    reg("fl_bh_lo", float(lo_b), "num2", "Estremo inferiore IC 95% della differenza media per titolo", "bootstrap sui titoli")
    reg("fl_bh_hi", float(hi_b), "num2", "Estremo superiore IC 95% della differenza media per titolo", "bootstrap sui titoli")

    # --- Scelta casuale dello stesso numero di titoli -------------------------------------------------------------
    mm_v, bh_v = tab["finale_mm"].to_numpy(), tab["finale_bh"].to_numpy()
    idx = rng.random((config.N_PERMUTAZIONI, n)).argsort(axis=1)[:, :nt]
    scelta = np.zeros((config.N_PERMUTAZIONI, n), dtype=bool)
    np.put_along_axis(scelta, idx, True, axis=1)
    casuali = np.where(scelta, mm_v, bh_v).sum(axis=1)
    pd.DataFrame({"finale_portafoglio": casuali}).to_csv(config.RISULTATI / "simulazioni_casuali.csv", index=False, float_format="%.4f")
    reg("cas_mediana", float(np.median(casuali)), "num2", "Valore finale mediano quando la regola è assegnata a caso a un terzo dei titoli, in euro", "simulazioni_casuali.csv")
    reg("cas_p95", float(np.percentile(casuali, 95)), "num2", "95° percentile del valore finale con assegnazione casuale, in euro", "simulazioni_casuali.csv")
    reg("cas_quota", (int((casuali >= F["fl"]).sum()) + 1) / (config.N_PERMUTAZIONI + 1), "pct0",
        "Stessa quota, in percentuale", "simulazioni_casuali.csv")
    reg("cas_p", (int((casuali >= F["fl"]).sum()) + 1) / (config.N_PERMUTAZIONI + 1), "pval",
        "Quota di assegnazioni casuali che fanno almeno quanto il filtro (p-value a una coda)", "simulazioni_casuali.csv")

    # --- Riferimento: lo stesso filtro sul periodo 2021-2026 (dentro il campione: serve solo come confronto) ---------
    rif = pd.read_csv(config.FILE_RIFERIMENTO)
    nr = len(rif)
    ntr = int(nr * config.QUOTA_FILTRO)
    basso = rif["ret"].rank(method="first") <= ntr
    fr_mm, fr_bh = float(rif["finale_mm_netto"].sum()), float(rif["finale_bh_netto"].sum())
    fr_fl = float(np.where(basso, rif["finale_mm_netto"], rif["finale_bh_netto"]).sum())
    src_r = "riferimento_2021_2026.csv (articolo precedente)"
    reg("rif_n", nr, "int", "Titoli del periodo di riferimento 2021-2026", src_r)
    reg("rif_finale_bh", fr_bh, "num2", "Riferimento: valore finale netto del buy & hold su tutti i titoli, in euro", src_r)
    reg("rif_finale_mm", fr_mm, "num2", "Riferimento: valore finale netto della regola su tutti i titoli, in euro", src_r)
    reg("rif_finale_fl", fr_fl, "num2", "Riferimento: valore finale netto con il filtro, in euro", src_r)
    reg("rif_diff_fl_bh_abs", abs(fr_fl - fr_bh), "num2", "Riferimento: distanza in euro tra filtro e buy & hold", src_r)
    reg("rif_diff_fl_bh_pct_abs", abs(fr_fl / fr_bh - 1), "pct1", "Riferimento: distanza tra filtro e buy & hold in percentuale del valore finale del buy & hold", src_r)
    reg("rif_diff_fl_mm", fr_fl - fr_mm, "num2", "Riferimento: filtro meno regola su tutti i titoli, in euro", src_r)
    reg("rif_rho", spearman(rif["ret"].to_numpy(), rif["differenza"].to_numpy()), "num2", "Riferimento: correlazione di rango tra rendimento passato e differenza", src_r)

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri in risultati/metriche.json")
    print(f"Periodo {min(inizio_set).date()} -> {max(fine_set).date()}, {n} titoli")
    print(f"rho={rho:+.2f} IC[{lo:+.2f},{hi:+.2f}] p={p:.4f}; la regola vince su {int(tab['vince'].sum())}/{n}")
    for g in ("basso", "medio", "alto"):
        d = tab[tab['gruppo'] == g]
        print(f"  gruppo {g:6s} n={len(d)} vince={d['vince'].mean():.0%} diff mediana={d['differenza'].median():+.1f}")
    print(f"portafogli: bh {F['bh']:.0f}  regola {F['mm']:.0f}  filtro {F['fl']:.0f}  filtro meta {F['fm']:.0f}")
    print(f"casuale: mediana {np.median(casuali):.0f}  p95 {np.percentile(casuali, 95):.0f}  filtro {F['fl']:.0f}")
    print(f"riferimento 2021-26: bh {fr_bh:.0f}  regola {fr_mm:.0f}  filtro {fr_fl:.0f}")


if __name__ == "__main__":
    main()
