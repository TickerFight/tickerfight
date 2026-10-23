"""Passo 2 - Santa Claus rally: la finestra di sette sedute contro buy & hold, finestre generiche e scimmie.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json       ogni numero dell'articolo, con descrizione e origine di calcolo
  finestre.csv        per ogni indice e anno: date di entrata e uscita e rendimento della finestra
  griglia.csv         per ogni indice: rendimento medio delle varianti della finestra (sedute di dicembre x sedute di gennaio)
  scimmie_medie.csv   rendimento medio delle finestre piazzate a caso, per ogni scimmia e indice
  scimmie_finali.csv  valore finale netto di ogni scimmia, per indice
  indici_usati.json   indici utilizzabili

Strategia: si compra alla chiusura della sesta-ultima seduta di dicembre e si vende alla chiusura della seconda seduta di
gennaio; il resto dell'anno si sta in cassa. Il calendario è noto in anticipo: nessun look-ahead. Scimmia: una finestra
della stessa durata per anno, piazzata a caso dentro il suo anno. Strategia e buy & hold passano dal motore di
simulazione (commissioni, tassa e minusvalenze); per le scimmie si usa la versione veloce, controllata contro il motore.
"""
import json
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import finestre as f
import simulazione as s

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con simulazione.py"


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
    m = len(ordine)
    out, massimo = {}, 0.0
    for k, nome in enumerate(ordine):
        massimo = max(massimo, min(1.0, (m - k) * p[nome]))
        out[nome] = massimo
    return out


def uguali(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def analizza(tk: str, nome: str, valuta: str, indice_rng: int) -> dict | None:
    meta = [r for r in META["indici"] if r["ticker"] == tk][0]
    if meta["stato"] != "ok":
        return None
    t = s.carica_csv(config.file_dati(tk))
    C = t["Close"].to_numpy(float)
    n = len(C)
    date = t.index
    K_D, K_G = config.SEDUTE_DICEMBRE, config.SEDUTE_GENNAIO
    d = K_D + K_G
    ent, usc, anni = f.trova_finestre(date, K_D, K_G)
    if len(ent) < config.ANNI_MINIMI:
        print(f"{tk}: scartato, solo {len(ent)} finestre complete")
        return None
    i0 = int(ent[0])
    rend = C[usc] / C[ent] - 1
    ok_dur = bool(np.all(usc - ent == d))
    if not ok_dur:
        raise SystemExit(f"{tk}: durata delle finestre incoerente")

    # --- Motore: strategia e buy & hold -----------------------------------------------------------------------------
    stato = np.zeros(n, dtype=bool)
    for e, x in zip(ent, usc):
        stato[e:x] = True
    df = pd.DataFrame({"Open": C, "Close": C, "fx": 1.0}, index=date)
    df["segnale"] = np.r_[stato[1:], False]
    h = s.simula(df, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, config.MODO, True)
    bh = s.simula(df, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, config.MODO, False)
    anno_usc = date.year.to_numpy()[usc]
    fv, tv = f.finale_veloce(C, anno_usc, ent, usc, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA)
    if not (uguali(fv, h["valore_finale_eur"]) and uguali(tv, h["tasse_eur"])):
        raise SystemExit(f"{tk}: motore veloce e motore completo non coincidono ({fv} contro {h['valore_finale_eur']})")
    if h["n_acquisti"] != len(ent):
        raise SystemExit(f"{tk}: numero di acquisti inatteso")

    # --- Finestre reali e finestre generiche -----------------------------------------------------------------------
    rng = np.random.default_rng([config.SEME, indice_rng])
    boot = rng.choice(rend, size=(config.N_BOOTSTRAP, len(rend)), replace=True).mean(axis=1)
    alfa = (1 - config.LIVELLO_CONFIDENZA) / 2
    lo, hi = np.quantile(boot, [alfa, 1 - alfa])
    gen = C[i0 + d:] / C[i0:n - d] - 1
    media, media_gen = float(rend.mean()), float(gen.mean())

    # --- Le scimmie ------------------------------------------------------------------------------------------------
    lunghezza = int(np.median(np.diff(ent))) if len(ent) > 1 else 252
    fine_ultimo = min(n, int(ent[-1]) + lunghezza)
    pos = f.scimmie(C, ent, d, fine_ultimo, config.N_SCIMMIE, rng)
    ret_sc = C[pos + d] / C[pos] - 1
    medie_sc = ret_sc.mean(axis=1)
    quota_sc = float((ret_sc > 0).mean())
    p_media = (int((medie_sc >= media).sum()) + 1) / (config.N_SCIMMIE + 1)
    anno_calend = date.year.to_numpy()
    finali = np.empty(config.N_SCIMMIE)
    for j in range(config.N_SCIMMIE):
        finali[j], _ = f.finale_veloce(C, anno_calend[pos[j] + d], pos[j], pos[j] + d, config.CAPITALE,
                                       config.COMMISSIONE, config.ALIQUOTA)
    p_valore = (int((finali >= h["valore_finale_eur"]).sum()) + 1) / (config.N_SCIMMIE + 1)

    # --- Prima e dopo ---------------------------------------------------------------------------------------------
    prima = rend[anni < config.ANNO_DIVISIONE]
    dopo = rend[anni >= config.ANNO_DIVISIONE]
    # Test AGGIUNTO dopo aver visto i risultati principali (non è tra le ipotesi): le scimmie sulle sole finestre del periodo «dopo»
    p_dopo = None
    if len(dopo) >= 5:
        sc_dopo = ret_sc[:, anni >= config.ANNO_DIVISIONE].mean(axis=1)
        p_dopo = (int((sc_dopo >= dopo.mean()).sum()) + 1) / (config.N_SCIMMIE + 1)

    # --- Griglia di varianti --------------------------------------------------------------------------------------
    griglia = []
    for kk in config.GRIGLIA_DICEMBRE:
        for mm in config.GRIGLIA_GENNAIO:
            e2, x2, a2 = f.trova_finestre(date, kk, mm)
            sel = (a2 >= anni[0]) & (a2 <= anni[-1])
            r2 = C[x2[sel]] / C[e2[sel]] - 1
            L = kk + mm
            g2 = float((C[i0 + L:] / C[i0:n - L] - 1).mean())
            griglia.append({"indice": tk, "k": kk, "m": mm, "n": int(sel.sum()), "media": float(r2.mean()),
                            "generica": g2, "eccesso": float(r2.mean()) - g2})
    griglia = pd.DataFrame(griglia)
    standard = griglia[(griglia["k"] == K_D) & (griglia["m"] == K_G)].iloc[0]
    rango_griglia = int((griglia["eccesso"] > standard["eccesso"]).sum() + 1)

    tab = pd.DataFrame({"indice": tk, "anno": anni, "entrata": date[ent].strftime("%Y-%m-%d"),
                        "uscita": date[usc].strftime("%Y-%m-%d"), "rendimento": rend})
    return dict(tk=tk, sl=slug(tk), nome=nome, valuta=valuta, date=date, i0=i0, ent=ent, usc=usc, anni=anni, rend=rend,
                lo=lo, hi=hi, media=media, media_gen=media_gen, gen=gen, h=h, bh=bh, medie_sc=medie_sc, quota_sc=quota_sc,
                p_media=p_media, finali=finali, p_valore=p_valore, prima=prima, dopo=dopo, p_dopo=p_dopo, griglia=griglia,
                rango_griglia=rango_griglia, tab=tab)


def main() -> None:
    global META
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    META = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    res = []
    for k, (tk, nome, valuta) in enumerate(config.INDICI):
        r = analizza(tk, nome, valuta, k)
        if r:
            res.append(r)
            print(f"{tk}: {len(r['rend'])} finestre, media {r['media']:.4%} contro generica {r['media_gen']:.4%}, "
                  f"p scimmie {r['p_media']:.4f}, strategia {r['h']['valore_finale_eur']:.0f} contro buy & hold {r['bh']['valore_finale_eur']:.0f}")
    if len(res) < 4:
        raise SystemExit("Troppi pochi indici utilizzabili.")

    ph = holm({r["tk"]: r["p_media"] for r in res})
    ph_dopo = holm({r["tk"]: r["p_dopo"] for r in res if r["p_dopo"] is not None})
    for r in res:
        sl, h, bh, rend = r["sl"], r["h"], r["bh"], r["rend"]
        reg(f"{sl}_nome", r["nome"], "testo", "Nome dell'indice", "config.py, INDICI")
        reg(f"{sl}_data_inizio", str(r["date"][r["i0"]].date()), "data_lunga", f"Prima operazione del test su {r['nome']} (sesta-ultima seduta del primo dicembre utile)", "dati/")
        reg(f"{sl}_anni", h["anni"], "num1", f"Anni del test su {r['nome']}")
        reg(f"{sl}_n_finestre", len(rend), "int", f"Finestre complete (dicembre e gennaio seguente) per {r['nome']}", "finestre.csv")
        reg(f"{sl}_media", r["media"], "pct2", f"Rendimento medio della finestra di sette sedute, {r['nome']}", "finestre.csv")
        reg(f"{sl}_mediana", float(np.median(rend)), "pct2", f"Rendimento mediano della finestra, {r['nome']}", "finestre.csv")
        reg(f"{sl}_media_gen", r["media_gen"], "pct2", f"Rendimento medio di una finestra di sette sedute qualunque, {r['nome']}", "tutte le finestre di sette sedute, dalla prima entrata")
        reg(f"{sl}_eccesso", r["media"] - r["media_gen"], "pp2", f"Rendimento medio della finestra meno quello medio di una finestra qualunque, in punti percentuali, {r['nome']}", "finestre.csv")
        reg(f"{sl}_lo", r["lo"], "pct2", f"Estremo inferiore dell'intervallo bootstrap del rendimento medio della finestra, {r['nome']}", "bootstrap sugli anni")
        reg(f"{sl}_hi", r["hi"], "pct2", f"Estremo superiore dell'intervallo bootstrap del rendimento medio della finestra, {r['nome']}", "bootstrap sugli anni")
        reg(f"{sl}_quota_pos", float((rend > 0).mean()), "pct0", f"Quota di anni in cui la finestra ha chiuso in positivo, {r['nome']}", "finestre.csv")
        reg(f"{sl}_quota_pos_gen", float((r["gen"] > 0).mean()), "pct0", f"Quota di finestre di sette sedute qualunque chiuse in positivo, {r['nome']}", "tutte le finestre di sette sedute")
        reg(f"{sl}_n_pos", int((rend > 0).sum()), "int", f"Anni con la finestra in positivo, {r['nome']}", "finestre.csv")
        reg(f"{sl}_n_neg", int((rend <= 0).sum()), "int", f"Anni con la finestra in perdita o a zero, {r['nome']}", "finestre.csv")
        reg(f"{sl}_peggiore", float(rend.min()), "pct1", f"Peggiore rendimento della finestra in un anno, {r['nome']}", "finestre.csv")
        reg(f"{sl}_anno_peggiore", int(r["anni"][rend.argmin()]) + 1, "annonum", f"Anno (gennaio) della peggiore finestra, {r['nome']}", "finestre.csv")
        reg(f"{sl}_migliore", float(rend.max()), "pct1", f"Miglior rendimento della finestra in un anno, {r['nome']}", "finestre.csv")
        reg(f"{sl}_sc_media", float(np.mean(r["medie_sc"])), "pct2", f"Rendimento medio delle scimmie (finestre della stessa durata piazzate a caso), {r['nome']}", "scimmie_medie.csv")
        reg(f"{sl}_p_media", r["p_media"], "pval", f"p-value a una coda: quota di scimmie con rendimento medio almeno pari a quello della finestra, {r['nome']}", "scimmie_medie.csv")
        reg(f"{sl}_p_holm", ph[r["tk"]], "pval", f"p-value delle scimmie corretto con il metodo di Holm sugli indici, {r['nome']}", "scimmie_medie.csv")
        reg(f"{sl}_finale_h", h["valore_finale_eur"], "int", f"Valore finale netto della strategia (capitale iniziale e valore nella valuta dell'indice), {r['nome']}")
        reg(f"{sl}_finale_bh", bh["valore_finale_eur"], "int", f"Valore finale netto del buy & hold, {r['nome']}")
        reg(f"{sl}_cagr_h", h["cagr"], "pct2", f"Rendimento annuo composto netto della strategia, {r['nome']}")
        reg(f"{sl}_cagr_bh", bh["cagr"], "pct1", f"Rendimento annuo composto netto del buy & hold, {r['nome']}")
        reg(f"{sl}_quota_dentro", h["quota_giorni_investito"], "pct1", f"Quota di sedute con la strategia investita, {r['nome']}")
        reg(f"{sl}_n_ordini", h["n_acquisti"] + h["n_vendite"], "int", f"Ordini della strategia (acquisti e vendite), {r['nome']}")
        reg(f"{sl}_comm", h["commissioni_eur"], "int", f"Commissioni pagate dalla strategia, {r['nome']}")
        reg(f"{sl}_tasse_h", h["tasse_eur"], "int", f"Tasse pagate dalla strategia, {r['nome']}")
        reg(f"{sl}_tasse_bh", bh["tasse_eur"], "int", f"Tasse pagate dal buy & hold (a fine periodo), {r['nome']}")
        reg(f"{sl}_sc_sotto", float((r["finali"] < h["valore_finale_eur"]).mean()), "pct0", f"Quota di scimmie che chiudono sotto la strategia (valore finale), {r['nome']}", "scimmie_finali.csv")
        reg(f"{sl}_n_prima", len(r["prima"]), "int", f"Finestre iniziate a dicembre fino al {config.ANNO_DIVISIONE - 1}, {r['nome']}", "finestre.csv")
        reg(f"{sl}_n_dopo", len(r["dopo"]), "int", f"Finestre iniziate a dicembre dal {config.ANNO_DIVISIONE}, {r['nome']}", "finestre.csv")
        if len(r["prima"]):
            reg(f"{sl}_media_prima", float(r["prima"].mean()), "pct2", f"Rendimento medio della finestra fino al {config.ANNO_DIVISIONE - 1}, {r['nome']}", "finestre.csv")
        if len(r["dopo"]):
            reg(f"{sl}_media_dopo", float(r["dopo"].mean()), "pct2", f"Rendimento medio della finestra dal {config.ANNO_DIVISIONE}, {r['nome']}", "finestre.csv")
        if r["p_dopo"] is not None:
            reg(f"{sl}_p_dopo", r["p_dopo"], "pval", f"p-value a una coda delle scimmie sulle sole finestre dal {config.ANNO_DIVISIONE} (test aggiunto dopo i risultati principali), {r['nome']}", "scimmie")
            reg(f"{sl}_p_dopo_holm", ph_dopo[r["tk"]], "pval", f"p-value del test sul periodo «dopo» corretto con Holm, {r['nome']}", "scimmie")
        reg(f"{sl}_rango_griglia", r["rango_griglia"], "int", f"Posto della finestra standard tra le varianti della griglia, per eccesso sul caso (uno è la migliore), {r['nome']}", "griglia.csv")
        reg(f"{sl}_griglia_pos", int((r["griglia"]["eccesso"] > 0).sum()), "int", f"Varianti della griglia con rendimento medio sopra quello di una finestra qualunque della stessa durata, {r['nome']}", "griglia.csv")

    # --- Numeri complessivi -----------------------------------------------------------------------------------------
    n_ind = len(res)
    ecc = [r["media"] - r["media_gen"] for r in res]
    reg("n_indici", n_ind, "int", "Indici utilizzabili nel test", "config.py, INDICI e dati/")
    reg("n_scartati", len(config.INDICI) - n_ind, "int", "Indici scartati (nessun dato o storia troppo corta)", "metadati.json")
    reg("n_totale", len(config.INDICI), "int", "Indici scelti in partenza", "config.py, INDICI")
    reg("n_media_pos", sum(r["media"] > 0 for r in res), "int", "Indici in cui il rendimento medio della finestra è positivo", "finestre.csv")
    reg("n_sopra_gen", sum(r["media"] > r["media_gen"] for r in res), "int", "Indici in cui il rendimento medio della finestra supera quello di una finestra qualunque", "finestre.csv")
    reg("n_h1", sum(r["media"] > 0 and r["media"] > r["media_gen"] for r in res), "int", "Indici con rendimento medio della finestra positivo e sopra quello di una finestra qualunque", "finestre.csv")
    reg("n_quota_sopra", sum(float((r["rend"] > 0).mean()) > float((r["gen"] > 0).mean()) for r in res), "int", "Indici in cui la quota di anni positivi della finestra supera quella delle finestre qualunque", "finestre.csv")
    reg("eccesso_medio", float(np.mean(ecc)), "pp2", "Media, sugli indici, dell'eccesso del rendimento della finestra sul caso, in punti percentuali", "finestre.csv")
    reg("n_signif_nocorr", sum(r["p_media"] < 0.05 for r in res), "int", "Indici con p-value delle scimmie sotto il cinque per cento (senza correzione)", "scimmie_medie.csv")
    reg("n_holm_signif", sum(ph[r["tk"]] < 0.05 for r in res), "int", "Indici con p-value corretto con Holm sotto il cinque per cento", "scimmie_medie.csv")
    reg("n_sotto_bh", sum(r["h"]["valore_finale_eur"] < r["bh"]["valore_finale_eur"] for r in res), "int", "Indici in cui la strategia chiude sotto il buy & hold, al netto di costi e tasse")
    reg("n_batte_bh", sum(r["h"]["valore_finale_eur"] > r["bh"]["valore_finale_eur"] for r in res), "int", "Indici in cui la strategia chiude sopra il buy & hold, al netto di costi e tasse")
    eval4 = [r for r in res if len(r["prima"]) >= 5 and len(r["dopo"]) >= 5]
    reg("n_h4_valutabili", len(eval4), "int", f"Indici con almeno cinque finestre prima e cinque dopo il {config.ANNO_DIVISIONE}", "finestre.csv")
    reg("n_h4_minore", sum(float(r["dopo"].mean()) < float(r["prima"].mean()) for r in eval4), "int", "Indici in cui il rendimento medio dopo è più basso di quello prima", "finestre.csv")
    reg("n_ic_positivo", sum(r["lo"] > 0 for r in res), "int", "Indici in cui l'intervallo bootstrap del rendimento medio della finestra sta sopra zero", "bootstrap sugli anni")
    reg("n_dopo_valutabili", len(ph_dopo), "int", f"Indici con almeno cinque finestre dal {config.ANNO_DIVISIONE} (test sul periodo «dopo»)", "finestre.csv")
    reg("n_dopo_signif", sum(r["p_dopo"] is not None and r["p_dopo"] < 0.05 for r in res), "int", "Indici con p-value sul periodo «dopo» sotto il cinque per cento (senza correzione; test aggiunto dopo i risultati principali)", "scimmie")
    reg("n_dopo_holm", sum(v < 0.05 for v in ph_dopo.values()), "int", "Indici con p-value sul periodo «dopo» corretto con Holm sotto il cinque per cento (test aggiunto dopo i risultati principali)", "scimmie")
    reg("n_griglia_primo", sum(r["rango_griglia"] == 1 for r in res), "int", "Indici in cui la finestra standard è la migliore tra le varianti della griglia", "griglia.csv")
    reg("n_griglia_prima_meta", sum(r["rango_griglia"] <= 13 for r in res), "int", "Indici in cui la finestra standard è nella metà migliore (prime tredici) delle varianti della griglia", "griglia.csv")
    reg("griglia_dic_min", min(config.GRIGLIA_DICEMBRE), "int", "Minimo di sedute di dicembre nella griglia", "config.py")
    reg("griglia_dic_max", max(config.GRIGLIA_DICEMBRE), "int", "Massimo di sedute di dicembre nella griglia", "config.py")
    reg("griglia_gen_min", min(config.GRIGLIA_GENNAIO), "int", "Minimo di sedute di gennaio nella griglia", "config.py")
    reg("griglia_gen_max", max(config.GRIGLIA_GENNAIO), "int", "Massimo di sedute di gennaio nella griglia", "config.py")
    reg("n_griglia_celle", len(config.GRIGLIA_DICEMBRE) * len(config.GRIGLIA_GENNAIO), "int", "Varianti della griglia (sedute di dicembre per sedute di gennaio)", "config.py")
    reg("sedute_dic", config.SEDUTE_DICEMBRE, "int", "Sedute di dicembre della finestra", "config.py, SEDUTE_DICEMBRE")
    reg("sedute_gen", config.SEDUTE_GENNAIO, "int", "Sedute di gennaio della finestra", "config.py, SEDUTE_GENNAIO")
    reg("sedute_tot", config.SEDUTE_DICEMBRE + config.SEDUTE_GENNAIO, "int", "Sedute totali della finestra", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie simulate per ogni indice", "config.py, N_SCIMMIE")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py, N_BOOTSTRAP")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py, SEME")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale, nella valuta di ciascun indice", "config.py, CAPITALE")
    reg("commissione", config.COMMISSIONE, "num2", "Commissione fissa per ordine, nella valuta dell'indice", "config.py, COMMISSIONE")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    reg("anno_divisione", config.ANNO_DIVISIONE, "annonum", "Primo anno del periodo «dopo»", "config.py, ANNO_DIVISIONE")
    reg("anno_prima", config.ANNO_DIVISIONE - 1, "annonum", "Ultimo anno del periodo «prima»", "config.py, ANNO_DIVISIONE")
    reg("lit_patel_anno", 2023, "annonum", "Anno dell'articolo di Patel sul Journal of Accounting and Finance", "Patel (2023), pagina della rivista")
    reg("lit_patel_da", 2000, "annonum", "Primo anno dei dati di Patel", "Patel (2023), abstract")
    reg("lit_patel_a", 2021, "annonum", "Ultimo anno dei dati di Patel", "Patel (2023), abstract")
    reg("lit_nippani_anno", 2015, "annonum", "Anno dell'articolo di Nippani, Washer e Johnson", "Nippani, Washer, Johnson (2015), Journal of Financial Planning")
    reg("lit_nippani_pct", 0.01, "pct0", "Extra rendimento circa stimato da Nippani, Washer e Johnson per un periodo di sette giorni", "Nippani, Washer, Johnson (2015), sintesi dell'articolo")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py, LIVELLO_CONFIDENZA")
    reg("data_scarico", META["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("data_ultima", max(str(r["date"][-1].date()) for r in res), "data_lunga", "Ultima seduta presente nei dati", "dati/")

    # --- File di supporto ---------------------------------------------------------------------------------------
    pd.concat([r["tab"] for r in res]).to_csv(config.RISULTATI / "finestre.csv", index=False, float_format="%.6f")
    pd.concat([r["griglia"] for r in res]).to_csv(config.RISULTATI / "griglia.csv", index=False, float_format="%.6f")
    pd.DataFrame({r["tk"]: r["medie_sc"] for r in res}).to_csv(config.RISULTATI / "scimmie_medie.csv", index=False, float_format="%.8f")
    pd.DataFrame({r["tk"]: r["finali"] for r in res}).to_csv(config.RISULTATI / "scimmie_finali.csv", index=False, float_format="%.4f")
    (config.RISULTATI / "indici_usati.json").write_text(json.dumps([{"ticker": r["tk"], "slug": r["sl"], "nome": r["nome"]} for r in res], ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
