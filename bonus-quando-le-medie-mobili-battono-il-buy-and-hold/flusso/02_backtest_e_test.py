"""Passo 2 - Quando la regola 50/200 batte il buy & hold? Caratteristiche dei titoli e test statistici.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json          ogni numero dell'articolo, con descrizione e origine di calcolo
  caratteristiche.csv    una riga per titolo: campione, caratteristiche prima del test, esito della regola
  correlazioni.csv       correlazioni di rango, intervalli di confidenza e p-value per campione e caratteristica
  terzili.csv            vittorie della regola nel terzo di titoli con l'indice più alto e nel terzo con l'indice più basso
  caso_studio.csv        giorno per giorno, il titolo del caso di studio (prezzo, medie, posizione, valori)

Regole del metodo:
  - ipotesi, caratteristiche e indice sono fissati in config.py prima di guardare come si legano al risultato;
  - le caratteristiche sono misurate sulle sedute PRIMA del primo ordine: nessuna informazione dal futuro;
  - sviluppo (titoli già visti) e validazione (titoli nuovi) sono tenuti separati;
  - il confronto è lo stesso degli articoli precedenti: 500 euro, 1 euro a ordine, 26% di tassa in euro;
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
SORGENTE = "02_backtest_e_test.py con simulazione.py"
CAMPIONI = {"sv": "sviluppo", "va": "validazione", "tot": "tutti i titoli"}
CAR = {"vol": "volatilità dell'anno precedente", "ret": "rendimento dei dodici mesi precedenti",
       "inc": "incroci tra le medie nei 200 giorni precedenti", "comp": "indice composito"}
DIREZIONE = {"vol": 1, "ret": -1, "inc": -1, "comp": 1}


def reg(chiave, valore, formato, descrizione, origine):
    """Registra un numero con la sua giustificazione (finisce nelle note dell'articolo)."""
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def rango_pct(x: pd.Series) -> pd.Series:
    """Rango percentuale (0-1) dentro il campione, con i pari merito alla media."""
    return (x.rank(method="average") - 0.5) / len(x)


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def test_correlazione(x: np.ndarray, y: np.ndarray, direzione: int, rng) -> tuple[float, float, float, float]:
    """Spearman, p-value di permutazione a una coda nella direzione dell'ipotesi, intervallo di confidenza bootstrap al 95%."""
    n = len(x)
    rho = spearman(x, y)
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    rxc = (rx - rx.mean()) / np.linalg.norm(rx - rx.mean())
    ryc = ry - ry.mean()
    idx = rng.random((config.N_PERMUTAZIONI, n)).argsort(axis=1)
    rho_perm = (ryc[idx] * rxc).sum(axis=1) / np.linalg.norm(ryc)
    p = (int((direzione * rho_perm >= direzione * rho).sum()) + 1) / (config.N_PERMUTAZIONI + 1)
    ib = rng.integers(0, n, (config.N_BOOTSTRAP, n))
    rb = pd.DataFrame(x[ib]).rank(axis=1).to_numpy()
    sb = pd.DataFrame(y[ib]).rank(axis=1).to_numpy()
    rb, sb = rb - rb.mean(axis=1, keepdims=True), sb - sb.mean(axis=1, keepdims=True)
    boot = (rb * sb).sum(axis=1) / np.sqrt((rb ** 2).sum(axis=1) * (sb ** 2).sum(axis=1))
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return rho, p, float(lo), float(hi)


def holm(p: dict) -> dict:
    ordine = sorted(p, key=p.get)
    m, corr, massimo = len(p), {}, 0.0
    for i, k in enumerate(ordine):
        massimo = max(massimo, min(1.0, (m - i) * p[k]))
        corr[k] = massimo
    return corr


def carica_titolo(percorso, cambio):
    df = s.prepara(s.carica_csv(percorso), cambio, config.SMA_VELOCE, config.SMA_LENTA)
    i0 = s.indice_data(df, df.index[-1] - pd.DateOffset(years=config.ANNI_TEST))
    return df, i0


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    comp = pd.read_csv(config.FILE_COMPOSIZIONE).set_index("ticker_yahoo")
    cambio = s.carica_csv(config.FILE_CAMBIO)
    rng = np.random.default_rng(config.SEME_STAT)

    gruppi = [("sv", config.DATI_SVIL, meta["titoli_sviluppo"]), ("va", config.DATI_VAL, meta["titoli_validazione"])]
    righe, esclusi, fine_set, inizio_set, caso = [], 0, set(), set(), None
    for camp, cartella, tickers in gruppi:
        for t in tickers:
            df, i0 = carica_titolo(cartella / f"{t}.csv", cambio)
            if i0 < config.SEDUTE_MINIME_PRIMA:
                if camp == "va":
                    raise SystemExit(f"{t}: storia troppo corta per misurare le caratteristiche.")
                esclusi += 1
                continue
            if df["fx"].iloc[i0 - 1:].isna().any():
                raise SystemExit(f"{t}: cambio mancante nel periodo del test.")
            fine_set.add(df.index[-1])
            inizio_set.add(df.index[i0])
            C = df["Close"].to_numpy()
            rend = np.diff(np.log(C[i0 - config.FINESTRA_VOLATILITA - 1:i0]))     # rendimenti fino alla seduta i0-1 compresa
            vol = float(rend.std(ddof=1) * np.sqrt(252))
            ret12 = float(C[i0 - 1] / C[i0 - 1 - config.FINESTRA_RENDIMENTO] - 1)
            seg = df["segnale"].to_numpy(bool)[i0 - 1 - config.FINESTRA_INCROCI:i0]
            inc = int((seg[1:] != seg[:-1]).sum())
            mm = s.simula(df, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, config.MODO_PRINCIPALE, True)
            bh = s.simula(df, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, config.MODO_PRINCIPALE, False)
            righe.append({
                "campione": camp, "ticker": t, "nome": comp.loc[t, "nome"], "settore": comp.loc[t, "settore"],
                "vol": vol, "ret": ret12, "inc": inc,
                "finale_mm_netto": mm["valore_finale_eur"], "finale_bh_netto": bh["valore_finale_eur"],
                "differenza": mm["valore_finale_eur"] - bh["valore_finale_eur"],
                "rend_bh_netto": bh["rendimento_totale"], "rend_mm_netto": mm["rendimento_totale"],
                "maxdd_mm": -mm["perdita_massima"], "maxdd_bh": -bh["perdita_massima"],
                "quota_investito": mm["quota_giorni_investito"], "n_ordini_mm": mm["n_acquisti"] + mm["n_vendite"],
            })
            if t == config.CASO_STUDIO:
                f = df.iloc[i0:]
                caso = pd.DataFrame({"data": f.index, "chiusura_usd": f["Close"].to_numpy(), "sma_veloce": f["sma_v"].to_numpy(),
                                     "sma_lenta": f["sma_l"].to_numpy(), "regola_in_posizione": mm["in_posizione"],
                                     "valore_regola_netto": mm["equity"], "valore_bh_netto": bh["equity"]})
    if max(fine_set) - min(fine_set) > pd.Timedelta(days=5) or max(inizio_set) - min(inizio_set) > pd.Timedelta(days=5):
        raise SystemExit("I titoli non coprono lo stesso periodo di test.")
    if caso is None:
        raise SystemExit("Titolo del caso di studio non trovato.")

    tab = pd.DataFrame(righe)
    tab["vince"] = tab["differenza"] > 0
    # indice composito: ranghi percentuali dentro ciascun campione, senza stime dai dati
    for camp in ("sv", "va", "tot"):
        m = tab["campione"].notna() if camp == "tot" else tab["campione"] == camp
        sub = tab[m]
        comp_idx = rango_pct(sub["vol"]) - rango_pct(sub["ret"]) - rango_pct(sub["inc"])
        tab.loc[m, f"comp_{camp}"] = comp_idx
    tab["comp"] = np.where(tab["campione"] == "sv", tab["comp_sv"], tab["comp_va"])
    tab.to_csv(config.RISULTATI / "caratteristiche.csv", index=False, float_format="%.6f")
    caso.to_csv(config.RISULTATI / "caso_studio.csv", index=False, float_format="%.6f")

    origine_dati = f"dati/ ({meta['fonte']}, scaricati il {meta['scaricato_il_utc'][:10]})"
    cs = "caratteristiche.csv"
    n_sv, n_va = int((tab.campione == "sv").sum()), int((tab.campione == "va").sum())

    # --- Parametri e campioni -----------------------------------------------------------------------------
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale per ogni titolo, in euro", "config.py, CAPITALE")
    reg("commissione", config.COMMISSIONE, "num2", "Commissione fissa per ogni ordine, in euro", "config.py, COMMISSIONE")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    reg("sma_veloce", config.SMA_VELOCE, "annonum", "Giorni della media veloce", "config.py, SMA_VELOCE")
    reg("sma_lenta", config.SMA_LENTA, "annonum", "Giorni della media lenta", "config.py, SMA_LENTA")
    reg("anni_test", config.ANNI_TEST, "annonum", "Anni del test", "config.py, ANNI_TEST")
    reg("seme", config.SEME, "annonum", "Seme del sorteggio dei titoli", "config.py, SEME")
    reg("finestra_vol", config.FINESTRA_VOLATILITA, "annonum", "Sedute usate per la volatilità", "config.py, FINESTRA_VOLATILITA")
    reg("finestra_inc", config.FINESTRA_INCROCI, "annonum", "Sedute usate per contare gli incroci", "config.py, FINESTRA_INCROCI")
    reg("n_permutazioni", config.N_PERMUTAZIONI, "int", "Permutazioni per i p-value", "config.py, N_PERMUTAZIONI")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap per gli intervalli di confidenza", "config.py, N_BOOTSTRAP")
    reg("livello_ic", 0.95, "pct0", "Livello degli intervalli di confidenza", "02_backtest_e_test.py, percentili 2,5 e 97,5 del bootstrap")
    for chiave, anno, rif in (("anno_brock", 1992, "Brock, Lakonishok e LeBaron, Journal of Finance"),
                              ("anno_mop", 2012, "Moskowitz, Ooi e Pedersen, Time Series Momentum"),
                              ("anno_han", 2013, "Han, Yang e Zhou, Journal of Financial and Quantitative Analysis"),
                              ("anno_zak", 2015, "Zakamulin, A Comprehensive Look at the Empirical Performance of Moving Average Trading Strategies")):
        reg(chiave, anno, "annonum", f"Anno di pubblicazione: {rif}", "bibliografia (vedi i link in fondo all'articolo)")
    reg("data_inizio", str(min(inizio_set).date()), "data_lunga", "Prima seduta del test", origine_dati)
    reg("data_fine", str(max(fine_set).date()), "data_lunga", "Ultima seduta del test", origine_dati)
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei titoli di validazione", "dati/metadati.json")
    reg("n_sv", n_sv, "int", "Titoli del campione di sviluppo usati nell'analisi", f"{cs}: campione = sv")
    reg("n_va", n_va, "int", "Titoli del campione di validazione", f"{cs}: campione = va")
    reg("n_tot", n_sv + n_va, "int", "Titoli in totale", f"{cs}")
    reg("n_esclusi_sv", esclusi, "int", "Titoli di sviluppo esclusi per storia troppo corta prima del test", "02: i0 < SEDUTE_MINIME_PRIMA")
    reg("n_val_provati", meta["titoli_validazione_provati"], "int", "Titoli provati per ottenere il campione di validazione", "dati/metadati.json")
    reg("n_val_scartati", meta["titoli_validazione_scartati"], "int", "Titoli scartati per dati assenti o storia troppo corta", "dati/metadati.json")

    for camp in ("sv", "va", "tot"):
        sub = tab if camp == "tot" else tab[tab.campione == camp]
        reg(f"n_vince_{camp}", int(sub["vince"].sum()), "int", f"Titoli su cui la regola batte il buy & hold, {CAMPIONI[camp]}", f"{cs}: differenza > 0")
        reg(f"quota_vince_{camp}", float(sub["vince"].mean()), "pct0", f"Quota di titoli su cui la regola batte il buy & hold, {CAMPIONI[camp]}", f"{cs}: differenza > 0")
        reg(f"mediana_diff_{camp}", float(sub["differenza"].median()), "num2", f"Differenza mediana in euro, regola meno buy & hold, {CAMPIONI[camp]}", f"{cs}: mediana di differenza")

    # --- Correlazioni -------------------------------------------------------------------------------------
    corr_righe, terz_righe = [], []
    for camp in ("sv", "va", "tot"):
        sub = tab if camp == "tot" else tab[tab.campione == camp]
        y = sub["differenza"].to_numpy()
        grezzi = {}
        for f in ("vol", "ret", "inc"):
            rho, p, lo, hi = test_correlazione(sub[f].to_numpy(), y, DIREZIONE[f], rng)
            grezzi[f] = (rho, p, lo, hi)
        pc = holm({f: v[1] for f, v in grezzi.items()})
        for f, (rho, p, lo, hi) in grezzi.items():
            reg(f"rho_{camp}_{f}", rho, "num2", f"Correlazione di rango tra {CAR[f]} e differenza regola meno buy & hold, {CAMPIONI[camp]}", f"{cs}: Spearman")
            reg(f"lo_{camp}_{f}", lo, "num2", f"Estremo inferiore dell'intervallo di confidenza al 95% della correlazione, {CAR[f]}, {CAMPIONI[camp]}", "bootstrap sui titoli")
            reg(f"hi_{camp}_{f}", hi, "num2", f"Estremo superiore dell'intervallo di confidenza al 95% della correlazione, {CAR[f]}, {CAMPIONI[camp]}", "bootstrap sui titoli")
            reg(f"p_{camp}_{f}", pc[f], "pval", f"p-value di permutazione a una coda, corretto con Holm sulle tre caratteristiche, {CAR[f]}, {CAMPIONI[camp]}", "permutazione + correzione di Holm")
            corr_righe.append({"campione": camp, "caratteristica": f, "n": len(sub), "rho": rho, "ic_inf": lo, "ic_sup": hi,
                               "p_una_coda": p, "p_holm": pc[f]})
        # indice composito
        xc = sub[f"comp_{camp}"].to_numpy()
        rho, p, lo, hi = test_correlazione(xc, y, 1, rng)
        reg(f"rho_{camp}_comp", rho, "num2", f"Correlazione di rango tra indice composito e differenza, {CAMPIONI[camp]}", f"{cs}: Spearman")
        reg(f"lo_{camp}_comp", lo, "num2", f"Estremo inferiore IC 95%, indice composito, {CAMPIONI[camp]}", "bootstrap sui titoli")
        reg(f"hi_{camp}_comp", hi, "num2", f"Estremo superiore IC 95%, indice composito, {CAMPIONI[camp]}", "bootstrap sui titoli")
        reg(f"p_{camp}_comp", p, "pval", f"p-value di permutazione a una coda, indice composito, {CAMPIONI[camp]}", "permutazione")
        corr_righe.append({"campione": camp, "caratteristica": "comp", "n": len(sub), "rho": rho, "ic_inf": lo, "ic_sup": hi,
                           "p_una_coda": p, "p_holm": p})

        # terzili dell'indice
        ordine = sub.assign(_c=xc).sort_values("_c", kind="stable")
        nt = len(sub) // 3
        basso, alto = ordine.iloc[:nt], ordine.iloc[-nt:]
        osservato = float(alto["vince"].mean() - basso["vince"].mean())
        v = sub["vince"].to_numpy(float)
        ordine_idx = np.argsort(xc, kind="stable")
        perm = rng.random((config.N_PERMUTAZIONI, len(sub))).argsort(axis=1)
        vp = v[ordine_idx][perm]
        stat = vp[:, -nt:].mean(axis=1) - vp[:, :nt].mean(axis=1)
        pt = (int((stat >= osservato).sum()) + 1) / (config.N_PERMUTAZIONI + 1)
        reg(f"terz_n_{camp}", nt, "int", f"Titoli in ciascun terzile estremo dell'indice, {CAMPIONI[camp]}", f"{cs}: un terzo di n")
        reg(f"terz_alto_{camp}", float(alto["vince"].mean()), "pct0", f"Quota di titoli su cui vince la regola nel terzo con l'indice più alto, {CAMPIONI[camp]}", f"{cs}")
        reg(f"terz_basso_{camp}", float(basso["vince"].mean()), "pct0", f"Quota di titoli su cui vince la regola nel terzo con l'indice più basso, {CAMPIONI[camp]}", f"{cs}")
        reg(f"terz_p_{camp}", pt, "pval", f"p-value di permutazione a una coda sulla differenza tra le due quote, {CAMPIONI[camp]}", "permutazione")
        reg(f"terz_med_alto_{camp}", float(alto["differenza"].median()), "num2", f"Differenza mediana in euro nel terzo con l'indice più alto, {CAMPIONI[camp]}", f"{cs}")
        reg(f"terz_med_basso_{camp}", float(basso["differenza"].median()), "num2", f"Differenza mediana in euro nel terzo con l'indice più basso, {CAMPIONI[camp]}", f"{cs}")
        terz_righe.append({"campione": camp, "gruppo": "indice alto", "n": nt, "quota_vince": float(alto["vince"].mean()),
                           "differenza_mediana": float(alto["differenza"].median())})
        terz_righe.append({"campione": camp, "gruppo": "indice basso", "n": nt, "quota_vince": float(basso["vince"].mean()),
                           "differenza_mediana": float(basso["differenza"].median())})
    # --- Lettura descrittiva dell'unica caratteristica con un segno chiaro: terzili del rendimento passato -------
    # Aggiunta DOPO aver visto le correlazioni: non è un test indipendente e qui non si calcolano p-value.
    tr_righe = []
    for camp in ("sv", "va", "tot"):
        sub = tab if camp == "tot" else tab[tab.campione == camp]
        o = sub.sort_values("ret", kind="stable")
        nt = len(sub) // 3
        gruppi_ret = {"basso": o.iloc[:nt], "medio": o.iloc[nt:len(o) - nt], "alto": o.iloc[-nt:]}
        reg(f"tr_n_{camp}", nt, "int", f"Titoli nel terzo con il rendimento passato più basso e in quello con il più alto, {CAMPIONI[camp]}", f"{cs}: un terzo di n")
        for g, d in gruppi_ret.items():
            reg(f"tr_{g}_{camp}", float(d["vince"].mean()), "pct0",
                f"Quota di titoli su cui vince la regola nel gruppo con rendimento passato {g}, {CAMPIONI[camp]}", f"{cs}: terzili di ret")
            tr_righe.append({"campione": camp, "gruppo": g, "n": len(d), "quota_vince": float(d["vince"].mean()),
                             "differenza_mediana": float(d["differenza"].median()), "rend_bh_mediano": float(d["rend_bh_netto"].median()),
                             "ret_mediano": float(d["ret"].median())})
        for g in ("basso", "alto"):
            reg(f"tr_med_{g}_{camp}", float(gruppi_ret[g]["differenza"].median()), "num2",
                f"Differenza mediana in euro nel gruppo con rendimento passato {g}, {CAMPIONI[camp]}", f"{cs}: terzili di ret")
        if camp == "tot":
            for g in ("basso", "alto"):
                reg(f"tr_rbh_{g}", float(gruppi_ret[g]["rend_bh_netto"].median()), "pct0",
                    f"Rendimento mediano del buy & hold nei cinque anni nel gruppo con rendimento passato {g}", f"{cs}: terzili di ret")
                reg(f"tr_ret_{g}", float(gruppi_ret[g]["ret"].median()), "pct0",
                    f"Rendimento passato mediano del gruppo {g}", f"{cs}: terzili di ret")
    pd.DataFrame(tr_righe).to_csv(config.RISULTATI / "terzili_rendimento.csv", index=False, float_format="%.6f")
    pd.DataFrame(corr_righe).to_csv(config.RISULTATI / "correlazioni.csv", index=False, float_format="%.6f")
    pd.DataFrame(terz_righe).to_csv(config.RISULTATI / "terzili.csv", index=False, float_format="%.6f")

    # --- Caratteristiche di chi vince e di chi perde (tutti i titoli) -----------------------------------------
    for f, nome, fmt in (("vol", "volatilità", "pct0"), ("ret", "rendimento dei dodici mesi precedenti", "pct0"), ("inc", "numero di incroci", "num1")):
        reg(f"med_{f}_vince", float(tab.loc[tab.vince, f].median()), fmt, f"Mediana di {nome} tra i titoli su cui vince la regola", f"{cs}: tutti i titoli")
        reg(f"med_{f}_perde", float(tab.loc[~tab.vince, f].median()), fmt, f"Mediana di {nome} tra i titoli su cui vince il buy & hold", f"{cs}: tutti i titoli")
        reg(f"rho_bh_{f}", spearman(tab[f].to_numpy(), tab["rend_bh_netto"].to_numpy()), "num2",
            f"Correlazione di rango tra {nome} e rendimento del buy & hold nei cinque anni (tutti i titoli)", f"{cs}: Spearman")
    reg("rho_diff_rend_bh", spearman(tab["rend_bh_netto"].to_numpy(), tab["differenza"].to_numpy()), "num2",
        "Correlazione di rango tra rendimento del buy & hold e differenza (tutti i titoli)", f"{cs}: Spearman")

    # --- Caso di studio -------------------------------------------------------------------------------------
    b = tab[tab.ticker == config.CASO_STUDIO].iloc[0]
    pr = lambda col: float(tab[col].rank(pct=True)[b.name])
    pr_comp = float(tab["comp_tot"].rank(pct=True)[b.name])
    src = f"{cs}, riga {config.CASO_STUDIO}"
    reg("bax_nome", b["nome"], "testo", "Nome del titolo del caso di studio", src)
    reg("bax_rend_bh", float(b["rend_bh_netto"]), "pct0", "Rendimento totale netto del buy & hold sul titolo", src)
    reg("bax_rend_mm", float(b["rend_mm_netto"]), "pct0", "Rendimento totale netto della regola sul titolo", src)
    reg("bax_finale_mm", float(b["finale_mm_netto"]), "num2", "Valore finale netto con la regola, in euro", src)
    reg("bax_finale_bh", float(b["finale_bh_netto"]), "num2", "Valore finale netto con il buy & hold, in euro", src)
    reg("bax_diff", float(b["differenza"]), "num2", "Differenza regola meno buy & hold, in euro", src)
    reg("bax_quota_investito", float(b["quota_investito"]), "pct0", "Quota di sedute con la regola investita", src)
    reg("bax_n_ordini", int(b["n_ordini_mm"]), "int", "Ordini della regola (acquisti e vendite, compresa la vendita finale)", src)
    reg("bax_maxdd_mm", float(b["maxdd_mm"]), "pct0", "Perdita massima dal picco con la regola", src)
    reg("bax_maxdd_bh", float(b["maxdd_bh"]), "pct0", "Perdita massima dal picco con il buy & hold", src)
    reg("bax_vol", float(b["vol"]), "pct0", "Volatilità annualizzata nell'anno precedente il test", src)
    reg("bax_vol_pct", pr("vol"), "pct0", "Posizione della volatilità nel campione complessivo (percentuale di titoli con volatilità minore o uguale)", f"{cs}: rango percentuale")
    reg("bax_ret", float(b["ret"]), "pct0", "Rendimento dei dodici mesi precedenti il test", src)
    reg("bax_ret_pct", pr("ret"), "pct0", "Posizione del rendimento passato nel campione complessivo (percentuale di titoli con rendimento minore o uguale)", f"{cs}: rango percentuale")
    reg("bax_inc", int(b["inc"]), "int", "Incroci tra le medie nei 200 giorni precedenti il test", src)
    reg("bax_inc_pct", pr("inc"), "pct0", "Posizione del numero di incroci nel campione complessivo (percentuale di titoli con meno incroci o pari)", f"{cs}: rango percentuale")
    reg("bax_comp_pct", pr_comp, "pct0", "Posizione dell'indice composito nel campione complessivo (percentuale di titoli con indice minore o uguale)", f"{cs}: rango percentuale")
    reg("bax_data_inizio", str(caso["data"].iloc[0].date()), "data_lunga", "Prima seduta del test sul titolo", "caso_studio.csv")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri in risultati/metriche.json")
    print(f"Titoli: sviluppo {n_sv}, validazione {n_va}, esclusi {esclusi}")
    for r in corr_righe:
        print(f"  {r['campione']:3s} {r['caratteristica']:5s} n={r['n']:3d} rho={r['rho']:+.2f} IC[{r['ic_inf']:+.2f},{r['ic_sup']:+.2f}] p={r['p_una_coda']:.4f} holm={r['p_holm']:.4f}")
    for r in terz_righe:
        print(f"  {r['campione']:3s} {r['gruppo']:13s} n={r['n']:3d} vince={r['quota_vince']:.0%} med={r['differenza_mediana']:+.1f}")


if __name__ == "__main__":
    main()
