"""Passo 2 - Overfitting in pratica: ottimizzare su dieci anni, provare sui cinque successivi.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json              ogni numero dell'articolo, con descrizione e origine di calcolo
  finestre.csv               per ogni finestra: periodi, coppia scelta, rendimento in ottimizzazione e in prova, confronti
  esperimento_griglia.csv    per ogni dimensione di griglia: rendimento in ottimizzazione e in prova del migliore, e distanza
  rendimenti_griglia.csv     rendimento annuo in ottimizzazione e in prova di ogni coppia della griglia principale, per finestra

Tutto passa da funzioni.py (segnale ritardato di un giorno, costo a ogni cambio di posizione).
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


def bootstrap_ic(x: np.ndarray, rng) -> tuple[float, float]:
    b = rng.choice(x, size=(config.N_BOOTSTRAP, len(x)), replace=True).mean(axis=1)
    a = (1 - config.LIVELLO_CONFIDENZA) / 2
    lo, hi = np.quantile(b, [a, 1 - a])
    return float(lo), float(hi)


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    date = close.index
    n = len(close)
    pool = fx.coppie(config.POOL_VELOCE, config.POOL_LENTA)
    griglia = fx.coppie(config.GRIGLIA_VELOCE, config.GRIGLIA_LENTA)
    indice = {c: k for k, c in enumerate(pool)}
    if config.COPPIA_FISSA not in indice or any(c not in indice for c in griglia):
        raise SystemExit("La griglia principale e la coppia fissa devono stare nel pool.")
    g_idx = np.array([indice[c] for c in griglia])
    logr = fx.log_rendimenti(close, pool, config.COSTO_CAMBIO)
    rend_bh = np.log1p(m_rend(close))
    fin = fx.finestre(n, config.INIZIO_TEST_SEDUTE, config.SEDUTE_OTTIMIZZAZIONE, config.SEDUTE_PROVA, config.PASSO)
    if len(fin) < 8:
        raise SystemExit("Troppo poche finestre.")
    rng = np.random.default_rng(config.SEME)

    righe, righe_g = [], []
    perm_cache = []
    exp_is = {d: [] for d in config.DIMENSIONI}
    exp_oos = {d: [] for d in config.DIMENSIONI}
    for w, (a, b, c) in enumerate(fin):
        tr, te = fx.cagr_finestra(logr, date, a, b), fx.cagr_finestra(logr, date, b, c)
        j = int(tr[g_idx].argmax())
        f_scelta, l_scelta = griglia[j]
        k_sc = g_idx[j]
        bh_te = float(np.exp(rend_bh[b:c].sum() / ((date[c - 1] - date[b - 1]).days / 365.25)) - 1)
        bh_tr = float(np.exp(rend_bh[a:b].sum() / ((date[b - 1] - date[a - 1]).days / 365.25)) - 1)
        kf = indice[config.COPPIA_FISSA]
        casuale_te = float(te[g_idx].mean())
        rango = float((te[g_idx] <= te[k_sc]).mean())
        righe.append({"finestra": w + 1, "inizio_ott": date[a].date(), "fine_ott": date[b - 1].date(), "inizio_prova": date[b].date(),
                      "fine_prova": date[c - 1].date(), "veloce": f_scelta, "lenta": l_scelta, "cagr_ott": tr[k_sc], "cagr_prova": te[k_sc],
                      "cagr_prova_griglia_media": casuale_te, "rango_prova": rango, "cagr_prova_fissa": te[kf],
                      "cagr_ott_fissa": tr[kf], "cagr_ott_bh": bh_tr, "cagr_prova_bh": bh_te})
        for q, k in enumerate(g_idx):
            righe_g.append({"finestra": w + 1, "veloce": griglia[q][0], "lenta": griglia[q][1], "cagr_ott": tr[k], "cagr_prova": te[k]})
        perm = np.argsort(rng.random((config.N_ESTRAZIONI, len(pool))), axis=1)
        r = fx.migliore_nei_sottoinsiemi(tr, te, perm, config.DIMENSIONI)
        for d in config.DIMENSIONI:
            exp_is[d].append(r[d][0])
            exp_oos[d].append(r[d][1])
    W = pd.DataFrame(righe)
    nf = len(W)

    reg("n_finestre", nf, "int", "Finestre (ottimizzazione e prova) dentro la storia", "finestre.csv")
    reg("anni_ott", config.SEDUTE_OTTIMIZZAZIONE / 252, "annonum", "Anni del periodo di ottimizzazione", "config.py, SEDUTE_OTTIMIZZAZIONE")
    reg("anni_prova", config.SEDUTE_PROVA / 252, "annonum", "Anni del periodo di prova", "config.py, SEDUTE_PROVA")
    reg("n_coppie_griglia", len(griglia), "int", "Coppie di medie nella griglia principale", "config.py")
    reg("n_coppie_pool", len(pool), "int", "Coppie di medie nel pool dell'esperimento sulla dimensione della griglia", "config.py")
    reg("costo", config.COSTO_CAMBIO, "pct1", "Costo per ogni cambio di posizione, quota del valore", "config.py, COSTO_CAMBIO")
    reg("prima_data", str(date[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_inizio", str(date[config.INIZIO_TEST_SEDUTE].date()), "data_lunga", "Inizio della prima finestra di ottimizzazione", "dati/ e config.py")
    reg("data_fine", str(date[fin[-1][2] - 1].date()), "data_lunga", "Fine dell'ultimo periodo di prova", "finestre.csv")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("n_estrazioni", config.N_ESTRAZIONI, "int", "Sottoinsiemi casuali per finestra e dimensione", "config.py")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py")
    reg("coppia_fissa_veloce", config.COPPIA_FISSA[0], "annonum", "Media veloce della coppia scelta a priori", "config.py")
    reg("coppia_fissa_lenta", config.COPPIA_FISSA[1], "annonum", "Media lenta della coppia scelta a priori", "config.py")

    # --- Ipotesi 1: il crollo ---------------------------------------------------------------------------------
    degrado = (W["cagr_ott"] - W["cagr_prova"]).to_numpy()
    lo, hi = bootstrap_ic(degrado, rng)
    reg("media_ott", float(W["cagr_ott"].mean()), "pct1", "Rendimento annuo medio della coppia ottimizzata nel periodo di ottimizzazione", "finestre.csv")
    reg("media_prova", float(W["cagr_prova"].mean()), "pct1", "Rendimento annuo medio della stessa coppia nel periodo di prova", "finestre.csv")
    reg("degrado_medio", float(degrado.mean()), "pp1", "Distanza media tra rendimento in ottimizzazione e in prova, punti percentuali", "finestre.csv")
    reg("degrado_lo", lo, "pp1", "Estremo inferiore dell'intervallo bootstrap della distanza", "bootstrap sulle finestre")
    reg("degrado_hi", hi, "pp1", "Estremo superiore dell'intervallo bootstrap della distanza", "bootstrap sulle finestre")
    reg("n_prova_sotto_ott", int((W["cagr_prova"] < W["cagr_ott"]).sum()), "int", "Finestre in cui il rendimento in prova è più basso di quello in ottimizzazione", "finestre.csv")
    reg("peggio_degrado", float(degrado.max()), "pp1", "La distanza più grande tra le finestre, punti percentuali", "finestre.csv")
    reg("n_prova_negativa", int((W["cagr_prova"] < 0).sum()), "int", "Finestre in cui la coppia ottimizzata ha un rendimento annuo negativo in prova", "finestre.csv")

    # --- Ipotesi 2: contro una coppia a caso ---------------------------------------------------------------------
    dif = (W["cagr_prova"] - W["cagr_prova_griglia_media"]).to_numpy()
    lo, hi = bootstrap_ic(dif, rng)
    reg("media_prova_casuale", float(W["cagr_prova_griglia_media"].mean()), "pct1", "Rendimento annuo medio in prova della coppia media della griglia (una coppia a caso)", "finestre.csv")
    reg("dif_casuale_media", float(dif.mean()), "pp1", "Rendimento in prova della coppia ottimizzata meno quello della coppia a caso, punti percentuali", "finestre.csv")
    reg("dif_casuale_lo", lo, "pp1", "Estremo inferiore dell'intervallo bootstrap", "bootstrap sulle finestre")
    reg("dif_casuale_hi", hi, "pp1", "Estremo superiore dell'intervallo bootstrap", "bootstrap sulle finestre")
    reg("n_batte_casuale", int((dif > 0).sum()), "int", "Finestre in cui la coppia ottimizzata batte la coppia a caso in prova", "finestre.csv")
    reg("rango_mediano", float(W["rango_prova"].median()), "pct0", "Posto mediano della coppia ottimizzata in prova: quota di coppie della griglia che fa meno o uguale", "finestre.csv")
    reg("n_rango_primo_quarto", int((W["rango_prova"] >= 0.75).sum()), "int", "Finestre in cui la coppia ottimizzata sta nel quarto migliore della griglia in prova", "finestre.csv")
    reg("n_rango_ultimo_quarto", int((W["rango_prova"] <= 0.25).sum()), "int", "Finestre in cui la coppia ottimizzata sta nel quarto peggiore della griglia in prova", "finestre.csv")
    dfix = (W["cagr_prova"] - W["cagr_prova_fissa"]).to_numpy()
    reg("media_prova_fissa", float(W["cagr_prova_fissa"].mean()), "pct1", "Rendimento annuo medio in prova della coppia scelta a priori", "finestre.csv")
    reg("dif_fissa_media", float(dfix.mean()), "pp1", "Rendimento in prova della coppia ottimizzata meno quello della coppia scelta a priori, punti percentuali", "finestre.csv")
    reg("n_batte_fissa", int((dfix > 0).sum()), "int", "Finestre in cui la coppia ottimizzata batte la coppia scelta a priori in prova", "finestre.csv")

    # --- Ipotesi 4: contro il buy & hold ----------------------------------------------------------------------------
    reg("media_prova_bh", float(W["cagr_prova_bh"].mean()), "pct1", "Rendimento annuo medio del buy & hold nei periodi di prova", "finestre.csv")
    reg("media_ott_bh", float(W["cagr_ott_bh"].mean()), "pct1", "Rendimento annuo medio del buy & hold nei periodi di ottimizzazione", "finestre.csv")
    reg("n_batte_bh", int((W["cagr_prova"] > W["cagr_prova_bh"]).sum()), "int", "Finestre in cui la coppia ottimizzata batte il buy & hold in prova", "finestre.csv")
    reg("n_batte_bh_ott", int((W["cagr_ott"] > W["cagr_ott_bh"]).sum()), "int", "Finestre in cui la coppia ottimizzata batte il buy & hold in ottimizzazione", "finestre.csv")

    # --- Stabilità delle scelte -----------------------------------------------------------------------------------
    reg("n_coppie_distinte", int(len(set(zip(W["veloce"], W["lenta"])))), "int", "Coppie diverse scelte nelle finestre", "finestre.csv")
    reg("salto_lenta_mediano", float(np.median(np.abs(np.diff(W["lenta"])))), "int", "Variazione mediana, tra finestre consecutive, della media lenta scelta (giorni)", "finestre.csv")
    reg("salto_veloce_mediano", float(np.median(np.abs(np.diff(W["veloce"])))), "int", "Variazione mediana, tra finestre consecutive, della media veloce scelta (giorni)", "finestre.csv")
    ripetute = sum(1 for k in range(1, nf) if (W["veloce"].iloc[k], W["lenta"].iloc[k]) == (W["veloce"].iloc[k - 1], W["lenta"].iloc[k - 1]))
    reg("n_scelte_ripetute", ripetute, "int", "Volte in cui la finestra successiva sceglie la stessa coppia della precedente", "finestre.csv")

    # --- Ipotesi 3: la dimensione della griglia ---------------------------------------------------------------------
    esp = pd.DataFrame({"dimensione": list(config.DIMENSIONI),
                        "cagr_ott": [float(np.mean(exp_is[d])) for d in config.DIMENSIONI],
                        "cagr_prova": [float(np.mean(exp_oos[d])) for d in config.DIMENSIONI]})
    esp["distanza"] = esp["cagr_ott"] - esp["cagr_prova"]
    gp = {int(r.dimensione): r for r in esp.itertuples()}
    for d in (1, 16, 256, max(config.DIMENSIONI)):
        reg(f"esp_ott_{d}", float(gp[d].cagr_ott), "pct1", f"Rendimento annuo medio in ottimizzazione del migliore tra {d} coppie estratte a caso", "esperimento_griglia.csv")
        reg(f"esp_prova_{d}", float(gp[d].cagr_prova), "pct1", f"Rendimento annuo medio in prova del migliore tra {d} coppie estratte a caso", "esperimento_griglia.csv")
        reg(f"esp_dist_{d}", float(gp[d].distanza), "pp1", f"Distanza tra rendimento in ottimizzazione e in prova con {d} coppie, punti percentuali", "esperimento_griglia.csv")
    reg("h3_ok", int(gp[256].distanza > gp[16].distanza > gp[1].distanza), "int", "1 se la distanza cresce da 1 a 16 a 256 coppie", "esperimento_griglia.csv")
    reg("esp_crescita_prova", float(gp[max(config.DIMENSIONI)].cagr_prova - gp[1].cagr_prova), "pp1", "Guadagno medio in prova passando da una coppia al massimo della dimensione, punti percentuali", "esperimento_griglia.csv")
    reg("esp_crescita_ott", float(gp[max(config.DIMENSIONI)].cagr_ott - gp[1].cagr_ott), "pp1", "Guadagno medio in ottimizzazione passando da una coppia al massimo della dimensione, punti percentuali", "esperimento_griglia.csv")
    reg("dim_256", 256, "int", "Dimensione di griglia usata come confronto intermedio nell'esperimento", "config.py, DIMENSIONI")
    reg("gv_min", min(config.GRIGLIA_VELOCE), "annonum", "Media veloce più corta della griglia principale (giorni)", "config.py")
    reg("gv_max", max(config.GRIGLIA_VELOCE), "annonum", "Media veloce più lunga della griglia principale (giorni)", "config.py")
    reg("gl_min", min(config.GRIGLIA_LENTA), "annonum", "Media lenta più corta della griglia principale (giorni)", "config.py")
    reg("gl_max", max(config.GRIGLIA_LENTA), "annonum", "Media lenta più lunga della griglia principale (giorni)", "config.py")
    reg("dim_max", max(config.DIMENSIONI), "int", "Dimensione massima della griglia nell'esperimento", "config.py, DIMENSIONI")

    # --- Due finestre da raccontare ----------------------------------------------------------------------------------
    for nome, r in (("ult", W.iloc[-1]), ("pegg", W.iloc[int(np.argmax(degrado))])):
        reg(f"{nome}_inizio_ott", str(r["inizio_ott"]), "data_lunga", "Inizio del periodo di ottimizzazione della finestra", "finestre.csv")
        reg(f"{nome}_inizio_prova", str(r["inizio_prova"]), "data_lunga", "Inizio del periodo di prova della finestra", "finestre.csv")
        reg(f"{nome}_fine_prova", str(r["fine_prova"]), "data_lunga", "Fine del periodo di prova della finestra", "finestre.csv")
        reg(f"{nome}_veloce", int(r["veloce"]), "annonum", "Media veloce scelta nella finestra", "finestre.csv")
        reg(f"{nome}_lenta", int(r["lenta"]), "annonum", "Media lenta scelta nella finestra", "finestre.csv")
        reg(f"{nome}_ott", float(r["cagr_ott"]), "pct1", "Rendimento annuo in ottimizzazione della coppia scelta", "finestre.csv")
        reg(f"{nome}_prova", float(r["cagr_prova"]), "pct1", "Rendimento annuo in prova della coppia scelta", "finestre.csv")
        reg(f"{nome}_bh", float(r["cagr_prova_bh"]), "pct1", "Rendimento annuo in prova del buy & hold", "finestre.csv")

    W.to_csv(config.RISULTATI / "finestre.csv", index=False, float_format="%.6f")
    esp.to_csv(config.RISULTATI / "esperimento_griglia.csv", index=False, float_format="%.6f")
    pd.DataFrame(righe_g).to_csv(config.RISULTATI / "rendimenti_griglia.csv", index=False, float_format="%.6f")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri; {nf} finestre")
    print(f"in ottimizzazione {W['cagr_ott'].mean():.1%}, in prova {W['cagr_prova'].mean():.1%}, griglia a caso {W['cagr_prova_griglia_media'].mean():.1%}, buy & hold {W['cagr_prova_bh'].mean():.1%}")


def m_rend(close: pd.Series) -> np.ndarray:
    return close.pct_change().fillna(0.0).to_numpy()


if __name__ == "__main__":
    main()
