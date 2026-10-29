"""Passo 2 - Sell in May and go away: strategia novembre-aprile contro buy & hold, calendari alternativi e scimmie.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json         ogni numero dell'articolo, con descrizione e origine di calcolo
  stagioni.csv          per ogni indice e anno: rendimento di novembre-aprile, di maggio-ottobre e differenza
  calendari.csv         per ogni indice: risultato dei dodici calendari di sei mesi (quello di Halloween è "novembre")
  scimmie_finali.csv    valore finale netto di ogni scimmia, per indice
  curve.csv             valore giorno per giorno (una seduta su cinque) di strategia e buy & hold

Strategia: si compra alla chiusura dell'ultima seduta di ottobre e si vende alla chiusura dell'ultima seduta di aprile.
Il calendario è noto in anticipo: nessun look-ahead. Scimmia: stesso numero di ordini e stessa durata di ogni periodo
investito, ma ogni periodo è piazzato a caso dentro il suo anno. Tutto passa dallo stesso motore di simulazione
(commissioni, tassa e minusvalenze compresi).
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
NOMI_MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre",
             "ottobre", "novembre", "dicembre"]


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def slug(ticker: str) -> str:
    return ticker.replace("^", "").replace(".", "_").lower()


def stato_calendario(mese: np.ndarray, mesi) -> np.ndarray:
    """True nella seduta i se si resta investiti dopo la sua chiusura: la seduta successiva cade in uno dei mesi."""
    prossimo = np.r_[mese[1:], 0]
    return np.isin(prossimo, list(mesi))


def segnale(stato: np.ndarray) -> np.ndarray:
    """Il segnale della seduta j decide l'ordine della seduta j+1 (esecuzione alla chiusura): quindi segnale[j] = stato[j+1]."""
    return np.r_[stato[1:], False]


def periodi(stato: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = np.r_[False, stato, False].astype(int)
    d = np.diff(x)
    return np.flatnonzero(d == 1), np.flatnonzero(d == -1)       # inizio e fine (esclusa) di ogni periodo


def holm(p: dict) -> dict:
    ordine = sorted(p, key=p.get)
    m = len(ordine)
    out, massimo = {}, 0.0
    for k, nome in enumerate(ordine):
        massimo = max(massimo, min(1.0, (m - k) * p[nome]))
        out[nome] = massimo
    return out


def scimmia(inizi: np.ndarray, durate: np.ndarray, n: int, rng) -> np.ndarray:
    """Ogni periodo investito è piazzato a caso dentro il suo anno (blocco tra un inizio e il successivo), con almeno
    una seduta in cassa prima del blocco seguente: il numero di ordini e la durata di ogni periodo restano quelli reali."""
    stato = np.zeros(n, dtype=bool)
    fini_blocco = np.r_[inizi[1:], n]
    for ini, fine, d in zip(inizi, fini_blocco, durate):
        massimo = int(fine - d - 1)
        if massimo < ini:                       # periodo che riempie il blocco (ultimo, troncato): nessuna libertà
            massimo = ini
        a = int(rng.integers(ini, massimo + 1))
        stato[a:a + d] = True
    return stato


def analizza(tk: str, nome: str, valuta: str, indice_rng: int) -> dict | None:
    sl = slug(tk)
    meta = [r for r in META["indici"] if r["ticker"] == tk][0]
    if meta["stato"] != "ok":
        return None
    t = s.carica_csv(config.file_dati(tk))
    df = pd.DataFrame({"Open": t["Close"], "Close": t["Close"], "fx": 1.0}).astype(float)
    n = len(df)
    mese = df.index.month.to_numpy()
    stato = stato_calendario(mese, config.MESI_INVESTITI)
    inizi, fini = periodi(stato)
    inizi_ok = inizi[inizi >= 1]
    if len(inizi_ok) == 0:
        return None
    i0 = int(inizi_ok[0])
    df["segnale"] = segnale(stato)
    h = s.simula(df, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, config.MODO, True)
    bh = s.simula(df, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, config.MODO, False)

    # --- Rendimenti dei due semestri, anno per anno (da chiusura a chiusura) -------------------------------------
    C = df["Close"].to_numpy()
    righe = []
    ini_p = [a for a in inizi if a >= i0]
    fini_p = [b for a, b in zip(inizi, fini) if a >= i0]
    for k in range(len(ini_p) - 1):
        if fini_p[k] >= n or ini_p[k + 1] >= n:
            break
        inv = C[fini_p[k]] / C[ini_p[k]] - 1
        est = C[ini_p[k + 1]] / C[fini_p[k]] - 1
        righe.append({"indice": tk, "anno_inizio": int(df.index[ini_p[k]].year), "inverno": inv, "estate": est, "diff": inv - est})
    st = pd.DataFrame(righe)
    if len(st) < config.STAGIONI_MINIME:
        print(f"{tk}: scartato, solo {len(st)} stagioni complete")
        return None
    d = st["diff"].to_numpy()
    rng = np.random.default_rng([config.SEME, indice_rng])
    boot = rng.choice(d, size=(config.N_BOOTSTRAP, len(d)), replace=True).mean(axis=1)
    alfa = (1 - config.LIVELLO_CONFIDENZA) / 2
    lo, hi = np.quantile(boot, [alfa, 1 - alfa])
    p_diff = (int((boot <= 0).sum()) + 1) / (config.N_BOOTSTRAP + 1)
    # Maberly e Pierce: senza le due stagioni con il crollo del 1987 e la crisi di LTCM del 1998
    escl = st[st["anno_inizio"].isin(config.STAGIONI_ESCLUSE)]
    senza = st[~st["anno_inizio"].isin(config.STAGIONI_ESCLUSE)]["diff"].to_numpy()
    rng2 = np.random.default_rng([config.SEME + 1, indice_rng])
    if len(escl) == len(config.STAGIONI_ESCLUSE) and len(senza) >= config.STAGIONI_MINIME:
        boot2 = rng2.choice(senza, size=(config.N_BOOTSTRAP, len(senza)), replace=True).mean(axis=1)
        p_senza = (int((boot2 <= 0).sum()) + 1) / (config.N_BOOTSTRAP + 1)
        senza_info = dict(media=float(senza.mean()), p=p_senza, n=len(senza), diff_escl=[float(x) for x in escl["diff"]])
    else:
        senza_info = None
    prima = st[st["anno_inizio"] <= config.DATA_PUBBLICAZIONE]["diff"]
    dopo = st[st["anno_inizio"] > config.DATA_PUBBLICAZIONE]["diff"]

    # --- I dodici calendari --------------------------------------------------------------------------------------
    cal = []
    for k in range(12):
        mesi = [((10 + k + j) % 12) + 1 for j in range(6)]        # k=0: novembre-aprile; k=1: dicembre-maggio ...
        sg = segnale(stato_calendario(mese, mesi))
        d2 = df.copy()
        d2["segnale"] = sg
        r = s.simula(d2, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, config.MODO, True)
        cal.append({"indice": tk, "k": k, "primo_mese": NOMI_MESI[mesi[0] - 1], "mese_n": mesi[0],
                    "finale": r["valore_finale_eur"], "cagr": r["cagr"]})
    cal = pd.DataFrame(cal)
    rango = int((cal["finale"] > cal.loc[0, "finale"]).sum() + 1)

    # --- Le scimmie ---------------------------------------------------------------------------------------------
    ini_i = np.array(ini_p, dtype=int)
    dur = np.array([b - a for a, b in zip(ini_p, fini_p)], dtype=int)
    dur = np.minimum(dur, n - ini_i)
    finali = np.empty(config.N_SCIMMIE)
    d3 = df.copy()
    for j in range(config.N_SCIMMIE):
        st_m = scimmia(ini_i, dur, n, rng)
        d3["segnale"] = segnale(st_m)
        r = s.simula(d3, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, config.MODO, True)
        if (r["n_acquisti"] != h["n_acquisti"] or r["n_vendite"] != h["n_vendite"]
                or abs(r["quota_giorni_investito"] - h["quota_giorni_investito"]) > 1e-9):
            raise SystemExit(f"{tk}: la scimmia {j} non ha la stessa dieta della strategia")
        finali[j] = r["valore_finale_eur"]
    p_sc = (int((finali >= h["valore_finale_eur"]).sum()) + 1) / (config.N_SCIMMIE + 1)

    camp = np.arange(0, n - i0, 5)
    curva = pd.DataFrame({"indice": tk, "data": df.index[i0:][camp], "valore_h": h["equity"][camp], "valore_bh": bh["equity"][camp]})
    return dict(tk=tk, sl=sl, nome=nome, valuta=valuta, df=df, i0=i0, h=h, bh=bh, st=st, lo=lo, hi=hi, p_diff=p_diff,
                prima=prima, dopo=dopo, senza=senza_info, cal=cal, rango=rango, finali=finali, p_sc=p_sc, curva=curva)


def main() -> None:
    global META
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    META = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    res = []
    for k, (tk, nome, valuta) in enumerate(config.INDICI):
        r = analizza(tk, nome, valuta, k)
        if r:
            res.append(r)
            print(f"{tk}: {len(r['st'])} stagioni, Halloween {r['h']['valore_finale_eur']:.0f} contro buy & hold {r['bh']['valore_finale_eur']:.0f}, "
                  f"rango {r['rango']}/12, p scimmie {r['p_sc']:.3f}")
    if len(res) < 3:
        raise SystemExit("Troppi pochi indici utilizzabili.")

    ph = holm({r["tk"]: r["p_sc"] for r in res})
    for r in res:
        sl, h, bh, st = r["sl"], r["h"], r["bh"], r["st"]
        reg(f"{sl}_nome", r["nome"], "testo", "Nome dell'indice", "config.py, INDICI")
        reg(f"{sl}_valuta", r["valuta"], "testo", "Valuta dell'indice", "config.py, INDICI")
        reg(f"{sl}_data_inizio", str(r["df"].index[r["i0"]].date()), "data_lunga", f"Prima operazione del test su {r['nome']} (ultima seduta di ottobre dopo l'inizio dei dati)", "dati/")
        reg(f"{sl}_anni", h["anni"], "num1", f"Anni del test su {r['nome']}")
        reg(f"{sl}_n_stagioni", len(st), "int", f"Anni completi con novembre-aprile e il maggio-ottobre seguente per {r['nome']}", "stagioni.csv")
        reg(f"{sl}_media_inv", float(st["inverno"].mean()), "pct1", f"Rendimento medio di novembre-aprile, {r['nome']}", "stagioni.csv")
        reg(f"{sl}_media_est", float(st["estate"].mean()), "pct1", f"Rendimento medio di maggio-ottobre, {r['nome']}", "stagioni.csv")
        reg(f"{sl}_diff", float(st["diff"].mean()), "pp1", f"Differenza media tra novembre-aprile e maggio-ottobre, in punti percentuali, {r['nome']}", "stagioni.csv")
        reg(f"{sl}_diff_lo", float(r["lo"]), "pp1", f"Estremo inferiore dell'intervallo bootstrap della differenza, {r['nome']}", "bootstrap sugli anni")
        reg(f"{sl}_diff_hi", float(r["hi"]), "pp1", f"Estremo superiore dell'intervallo bootstrap della differenza, {r['nome']}", "bootstrap sugli anni")
        reg(f"{sl}_p_diff", float(r["p_diff"]), "pval", f"p-value a una coda: quota di ricampionamenti con differenza media non positiva, {r['nome']}", "bootstrap sugli anni")
        reg(f"{sl}_quota_anni", float((st["diff"] > 0).mean()), "pct0", f"Quota di anni in cui novembre-aprile ha reso più del maggio-ottobre seguente, {r['nome']}", "stagioni.csv")
        reg(f"{sl}_finale_h", h["valore_finale_eur"], "int", f"Valore finale netto della strategia novembre-aprile, {r['nome']} (capitale iniziale e valore nella valuta dell'indice)")
        reg(f"{sl}_finale_bh", bh["valore_finale_eur"], "int", f"Valore finale netto del buy & hold, {r['nome']}")
        reg(f"{sl}_cagr_h", h["cagr"], "pct1", f"Rendimento annuo composto netto della strategia novembre-aprile, {r['nome']}")
        reg(f"{sl}_cagr_bh", bh["cagr"], "pct1", f"Rendimento annuo composto netto del buy & hold, {r['nome']}")
        reg(f"{sl}_dd_h", -h["perdita_massima"], "pct0", f"Perdita massima dal picco della strategia novembre-aprile, {r['nome']}")
        reg(f"{sl}_dd_bh", -bh["perdita_massima"], "pct0", f"Perdita massima dal picco del buy & hold, {r['nome']}")
        reg(f"{sl}_quota_dentro", h["quota_giorni_investito"], "pct0", f"Quota di sedute con la strategia investita, {r['nome']}")
        reg(f"{sl}_n_ordini", h["n_acquisti"] + h["n_vendite"], "int", f"Ordini della strategia novembre-aprile (acquisti e vendite), {r['nome']}")
        reg(f"{sl}_tasse_h", h["tasse_eur"], "int", f"Tasse pagate dalla strategia novembre-aprile, {r['nome']}")
        reg(f"{sl}_tasse_bh", bh["tasse_eur"], "int", f"Tasse pagate dal buy & hold (a fine periodo), {r['nome']}")
        reg(f"{sl}_rango", r["rango"], "int", f"Posto di novembre-aprile tra i dodici calendari di sei mesi (uno è il migliore), {r['nome']}", "calendari.csv")
        reg(f"{sl}_sc_mediana", float(np.median(r["finali"])), "int", f"Valore finale mediano delle scimmie, {r['nome']}", "scimmie_finali.csv")
        reg(f"{sl}_sc_sotto", float((r["finali"] < h["valore_finale_eur"]).mean()), "pct0", f"Quota di scimmie che chiudono sotto la strategia, {r['nome']}", "scimmie_finali.csv")
        reg(f"{sl}_p_sc", r["p_sc"], "pval", f"p-value a una coda: quota di scimmie che fanno almeno quanto la strategia, {r['nome']}", "scimmie_finali.csv")
        reg(f"{sl}_p_holm", ph[r["tk"]], "pval", f"p-value delle scimmie corretto con il metodo di Holm sugli indici, {r['nome']}", "scimmie_finali.csv")
        reg(f"{sl}_sc_sopra_bh", float((r["finali"] >= bh["valore_finale_eur"]).mean()), "pct1", f"Quota di scimmie che fanno almeno quanto il buy & hold, {r['nome']}", "scimmie_finali.csv")
        reg(f"{sl}_n_prima", len(r["prima"]), "int", f"Anni fino al {config.DATA_PUBBLICAZIONE} nel test, {r['nome']}", "stagioni.csv")
        reg(f"{sl}_n_dopo", len(r["dopo"]), "int", f"Anni dopo il {config.DATA_PUBBLICAZIONE} nel test, {r['nome']}", "stagioni.csv")
        if len(r["prima"]) >= 5:
            reg(f"{sl}_diff_prima", float(r["prima"].mean()), "pp1", f"Differenza media fino al {config.DATA_PUBBLICAZIONE}, {r['nome']}", "stagioni.csv")
        reg(f"{sl}_diff_dopo", float(r["dopo"].mean()) if len(r["dopo"]) else 0.0, "pp1", f"Differenza media dopo il {config.DATA_PUBBLICAZIONE}, {r['nome']}", "stagioni.csv")

    # --- Senza le due stagioni di Maberly e Pierce ---------------------------------------------------------------------
    con_senza = [r for r in res if r["senza"] is not None]
    for r in con_senza:
        sl = r["sl"]
        reg(f"{sl}_senza_diff", r["senza"]["media"], "pp1", f"Differenza media tra novembre-aprile e maggio-ottobre senza le due stagioni del 1987 e del 1998, in punti percentuali, {r['nome']}", "stagioni.csv")
        reg(f"{sl}_senza_p", r["senza"]["p"], "pval", f"p-value bootstrap della differenza media senza le due stagioni (analisi non prevista tra le ipotesi), {r['nome']}", "bootstrap sugli anni")
        reg(f"{sl}_senza_n", r["senza"]["n"], "int", f"Stagioni rimaste dopo aver tolto le due, {r['nome']}", "stagioni.csv")
        reg(f"{sl}_senza_rapporto", r["senza"]["media"] / float(r["st"]["diff"].mean()), "pct0", f"Differenza senza le due stagioni in rapporto a quella con tutte le stagioni, {r['nome']}", "stagioni.csv")
        reg(f"{sl}_escl_1987", r["senza"]["diff_escl"][0], "pp1", f"Differenza tra novembre-aprile e maggio-ottobre nella stagione del crollo di ottobre 1987, in punti percentuali, {r['nome']}", "stagioni.csv")
        reg(f"{sl}_escl_1998", r["senza"]["diff_escl"][1], "pp1", f"Differenza tra novembre-aprile e maggio-ottobre nella stagione della crisi LTCM del 1998, in punti percentuali, {r['nome']}", "stagioni.csv")
    reg("n_senza_valutabili", len(con_senza), "int", "Indici che contengono le due stagioni escluse", "stagioni.csv")
    reg("n_h4_ok", sum(r["senza"]["media"] <= config.H4_FRAZIONE * float(r["st"]["diff"].mean()) for r in con_senza), "int", "Indici in cui la differenza senza le due stagioni è al massimo la frazione dichiarata di quella con tutte", "stagioni.csv")
    reg("n_senza_positiva", sum(r["senza"]["media"] > 0 for r in con_senza), "int", "Indici in cui la differenza resta positiva senza le due stagioni", "stagioni.csv")
    reg("n_senza_signif", sum(r["senza"]["p"] < 0.05 for r in con_senza), "int", "Indici in cui la differenza senza le due stagioni ha p-value bootstrap sotto il cinque per cento (senza correzione)", "bootstrap sugli anni")
    reg("h4_frazione", config.H4_FRAZIONE, "pct0", "Ipotesi 4: frazione massima della differenza che deve restare senza le due stagioni", "config.py, H4_FRAZIONE")
    reg("anno_crollo", 1987, "annonum", "Anno del crollo di ottobre", "Maberly e Pierce (2004)")
    reg("anno_ltcm", 1998, "annonum", "Anno della crisi LTCM", "Maberly e Pierce (2004)")

    # --- Numeri complessivi, per le quattro ipotesi ----------------------------------------------------------------
    n_ind = len(res)
    reg("n_indici", n_ind, "int", "Indici utilizzabili nel test", "config.py, INDICI e dati/")
    reg("n_scartati", len(config.INDICI) - n_ind, "int", "Indici scartati (nessun dato o storia troppo corta)", "metadati.json")
    reg("n_totale", len(config.INDICI), "int", "Indici scelti in partenza", "config.py, INDICI")
    reg("n_diff_positiva", sum(float(r["st"]["diff"].mean()) > 0 for r in res), "int", "Indici in cui novembre-aprile rende in media più di maggio-ottobre", "stagioni.csv")
    reg("n_diff_signif", sum(r["p_diff"] < 0.05 for r in res), "int", "Indici in cui la differenza media ha p-value bootstrap sotto il cinque per cento (senza correzione)", "bootstrap sugli anni")
    reg("n_batte_bh", sum(r["h"]["valore_finale_eur"] > r["bh"]["valore_finale_eur"] for r in res), "int", "Indici in cui la strategia novembre-aprile chiude sopra il buy & hold, al netto di costi e tasse")
    reg("n_dd_minore", sum(r["h"]["perdita_massima"] > r["bh"]["perdita_massima"] for r in res), "int", "Indici in cui la strategia ha una perdita massima più piccola del buy & hold")
    reg("n_holm_signif", sum(ph[r["tk"]] < 0.05 for r in res), "int", "Indici in cui la strategia batte le scimmie con p-value corretto sotto il cinque per cento", "scimmie_finali.csv")
    reg("n_sc_sopra_mediana", sum(r["h"]["valore_finale_eur"] > np.median(r["finali"]) for r in res), "int", "Indici in cui la strategia chiude sopra la mediana delle scimmie", "scimmie_finali.csv")
    eval4 = [r for r in res if len(r["prima"]) >= 5 and len(r["dopo"]) >= 5]
    reg("n_h4_valutabili", len(eval4), "int", f"Indici con almeno cinque anni prima e cinque dopo il {config.DATA_PUBBLICAZIONE}", "stagioni.csv")
    reg("n_h4_minore", sum(float(r["dopo"].mean()) < float(r["prima"].mean()) for r in eval4), "int", "Indici in cui la differenza media dopo è più piccola di quella prima", "stagioni.csv")
    reg("n_primi_tre", sum(r["rango"] <= 3 for r in res), "int", "Indici in cui novembre-aprile è tra i tre migliori calendari su dodici", "calendari.csv")
    reg("n_primo_posto", sum(r["rango"] == 1 for r in res), "int", "Indici in cui novembre-aprile è il migliore dei dodici calendari", "calendari.csv")
    reg("diff_media_tutti", float(np.mean([r["st"]["diff"].mean() for r in res])), "pp1", "Media, sugli indici, della differenza media tra novembre-aprile e maggio-ottobre, in punti percentuali", "stagioni.csv")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie simulate per ogni indice", "config.py, N_SCIMMIE")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py, N_BOOTSTRAP")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py, SEME")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale, nella valuta di ciascun indice", "config.py, CAPITALE")
    reg("commissione", config.COMMISSIONE, "num2", "Commissione fissa per ordine, nella valuta dell'indice", "config.py, COMMISSIONE")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    reg("anno_pubblicazione", config.DATA_PUBBLICAZIONE, "annonum", "Anno dell'articolo di Bouman e Jacobsen", "config.py, DATA_PUBBLICAZIONE")
    reg("lit_bj_mercati", 36, "int", "Mercati con l'effetto Halloween su 37 nel campione di Bouman e Jacobsen, secondo l'abstract", "Bouman e Jacobsen (2002), abstract")
    reg("lit_bj_campione", 37, "int", "Mercati del campione di Bouman e Jacobsen", "Bouman e Jacobsen (2002), abstract")
    reg("lit_mp_anno", 2004, "annonum", "Anno dell'articolo di Maberly e Pierce", "Maberly e Pierce, Econ Journal Watch 1(1)")
    reg("lit_crollo_anno", 1987, "annonum", "Anno del crollo di ottobre indicato da Maberly e Pierce", "Maberly e Pierce (2004), abstract")
    reg("lit_lcm_anno", 1998, "annonum", "Anno del fallimento di Long-Term Capital Management indicato da Maberly e Pierce", "Maberly e Pierce (2004), abstract")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py, LIVELLO_CONFIDENZA")
    reg("data_scarico", meta_data(), "data", "Data del download dei dati", "dati/metadati.json")
    reg("data_ultima", max(str(r["df"].index[-1].date()) for r in res), "data_lunga", "Ultima seduta presente nei dati", "dati/")

    # --- File di supporto ---------------------------------------------------------------------------------------
    pd.concat([r["st"] for r in res]).to_csv(config.RISULTATI / "stagioni.csv", index=False, float_format="%.6f")
    pd.concat([r["cal"] for r in res]).to_csv(config.RISULTATI / "calendari.csv", index=False, float_format="%.4f")
    pd.concat([r["curva"] for r in res]).to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.4f")
    pd.DataFrame({r["tk"]: r["finali"] for r in res}).to_csv(config.RISULTATI / "scimmie_finali.csv", index=False, float_format="%.4f")
    (config.RISULTATI / "indici_usati.json").write_text(json.dumps([{"ticker": r["tk"], "slug": r["sl"], "nome": r["nome"]} for r in res], ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


def meta_data() -> str:
    return META["scaricato_il_utc"][:10]


if __name__ == "__main__":
    main()
