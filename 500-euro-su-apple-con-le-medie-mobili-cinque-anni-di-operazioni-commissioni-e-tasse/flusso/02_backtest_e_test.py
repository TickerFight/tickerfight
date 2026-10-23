"""Passo 2 - 500 euro su Apple con la regola 50/200: simulazione in euro e finestre mobili.

Legge SOLO i file in dati/ (scaricati dal passo 1) e produce in risultati/:
  metriche.json           ogni numero dell'articolo, con descrizione e origine di calcolo
  scenari.csv             valore finale e statistiche per ogni combinazione di esecuzione, costi e strategia
  operazioni_regola.csv   registro di tutte le operazioni della regola (esecuzione all'apertura, costi e tassa)
  operazioni_buy_hold.csv registro del buy & hold
  curve.csv               prezzo, medie, posizione e valore del portafoglio giorno per giorno
  finestre_mobili.csv     la stessa simulazione su finestre di cinque anni con partenza ogni mese

Regole del metodo:
  - l'ipotesi e i parametri sono scelti prima di guardare i risultati e dichiarati in config.py;
  - il segnale di fine seduta t decide l'ordine di t+1 (nessun look-ahead);
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
SCENARI = {"lordo": (0.0, 0.0), "comm": (config.COMMISSIONE, 0.0), "netto": (config.COMMISSIONE, config.ALIQUOTA)}
ETICHETTE = {"lordo": "senza costi né tasse", "comm": "con le commissioni", "netto": "con commissioni e tasse"}
NOME = {"mm": "regola 50/200", "bh": "buy & hold"}
SORGENTE = "02_backtest_e_test.py con simulazione.py"


def reg(chiave, valore, formato, descrizione, origine):
    """Registra un numero con la sua giustificazione (finisce nelle note dell'articolo)."""
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    titolo = s.carica_csv(config.FILE_DATI)
    cambio = s.carica_csv(config.FILE_CAMBIO)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    df = s.prepara(titolo, cambio, config.SMA_VELOCE, config.SMA_LENTA)
    # Il cambio di Yahoo parte dopo Apple (dicembre 2003): serve solo da quando partono le simulazioni.
    inizio_cambio = max(s.indice_data(df, config.INIZIO_FINESTRE), config.SMA_LENTA + 1) - 1
    if df["fx"].iloc[inizio_cambio:].isna().any():
        raise SystemExit("Cambio mancante in una seduta di Apple nel periodo delle simulazioni.")

    fine = df.index[-1]
    i0 = s.indice_data(df, fine - pd.DateOffset(years=config.ANNI_TEST))
    if i0 < config.SMA_LENTA + 1:
        raise SystemExit("Storia insufficiente per calcolare la media lenta prima dell'inizio del test.")
    n_test = len(df) - i0
    origine_dati = f"dati/ ({meta['fonte']}, {config.TICKER} e {config.TICKER_CAMBIO}, scaricati il {meta['scaricato_il_utc'][:10]})"

    # --- Simulazione principale e controllo ---------------------------------------------------------------
    R = {}
    for modo in (config.MODO_PRINCIPALE, config.MODO_CONTROLLO):
        for sc, (c, a) in SCENARI.items():
            for nome, strat in (("mm", True), ("bh", False)):
                R[(modo, sc, nome)] = s.simula(df, i0, config.CAPITALE, c, a, modo, strat)
    P = config.MODO_PRINCIPALE

    righe = []
    for (modo, sc, nome), r in R.items():
        righe.append({"esecuzione": modo, "costi": sc, "strategia": nome,
                      **{k: v for k, v in r.items() if k not in ("operazioni", "equity", "in_posizione")}})
    pd.DataFrame(righe).to_csv(config.RISULTATI / "scenari.csv", index=False, float_format="%.6f")
    pd.DataFrame(R[(P, "netto", "mm")]["operazioni"]).to_csv(
        config.RISULTATI / "operazioni_regola.csv", index=False, float_format="%.6f")
    pd.DataFrame(R[(P, "netto", "bh")]["operazioni"]).to_csv(
        config.RISULTATI / "operazioni_buy_hold.csv", index=False, float_format="%.6f")

    finestra = df.iloc[i0:]
    curve = pd.DataFrame({
        "data": finestra.index, "chiusura_usd": finestra["Close"].to_numpy(), "cambio": finestra["fx"].to_numpy(),
        "sma_veloce": finestra["sma_v"].to_numpy(), "sma_lenta": finestra["sma_l"].to_numpy(),
        "regola_in_posizione": R[(P, "netto", "mm")]["in_posizione"],
        "valore_regola_netto": R[(P, "netto", "mm")]["equity"], "valore_bh_netto": R[(P, "netto", "bh")]["equity"],
        "valore_regola_lordo": R[(P, "lordo", "mm")]["equity"], "valore_bh_lordo": R[(P, "lordo", "bh")]["equity"],
    })
    curve.to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.6f")

    # --- Numeri dell'articolo: parametri e dati -----------------------------------------------------------
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale in euro", "config.py, CAPITALE")
    reg("commissione", config.COMMISSIONE, "num2", "Commissione fissa per ogni ordine, in euro", "config.py, COMMISSIONE")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    reg("sma_veloce", config.SMA_VELOCE, "annonum", "Giorni della media veloce", "config.py, SMA_VELOCE")
    reg("sma_lenta", config.SMA_LENTA, "annonum", "Giorni della media lenta", "config.py, SMA_LENTA")
    reg("anni_test", config.ANNI_TEST, "annonum", "Anni del test", "config.py, ANNI_TEST")
    reg("data_inizio", str(finestra.index[0].date()), "data_lunga", "Prima seduta del test", origine_dati)
    reg("data_fine", str(fine.date()), "data_lunga", "Ultima seduta del test (ultimo dato scaricato)", origine_dati)
    reg("n_sedute", n_test, "int", "Sedute di borsa nel periodo del test", origine_dati)
    seg = df["segnale"].to_numpy()[i0 - 1:]     # dal segnale che decide il primo ordine fino all'ultimo giorno
    reg("n_incroci", int((seg[1:] != seg[:-1]).sum()), "int",
        "Incroci delle due medie nel periodo (cambi del segnale)", f"{SORGENTE}: cambi di valore del segnale")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("data_inizio_dati", meta["prima_data_titolo"], "data", "Prima seduta di Apple scaricata", "dati/metadati.json")
    reg("n_osservazioni_dati", meta["righe_titolo"], "int", "Sedute di Apple scaricate", "dati/metadati.json")
    reg("apertura_inizio_usd", float(finestra["Open"].iloc[0]), "num2", "Apertura di Apple alla prima seduta del test, in dollari", origine_dati)
    reg("chiusura_fine_usd", float(finestra["Close"].iloc[-1]), "num2", "Chiusura di Apple all'ultima seduta, in dollari", origine_dati)
    reg("var_apple_usd", float(finestra["Close"].iloc[-1] / finestra["Open"].iloc[0] - 1), "pct0",
        "Variazione del prezzo di Apple in dollari (dall'apertura iniziale alla chiusura finale)", origine_dati)
    reg("cambio_inizio", float(df["fx"].iloc[i0 - 1]), "num3", "Dollari per un euro all'inizio del test", origine_dati)
    reg("cambio_fine", float(df["fx"].iloc[-1]), "num3", "Dollari per un euro alla fine del test", origine_dati)
    reg("var_apple_eur", float((finestra["Close"].iloc[-1] / df["fx"].iloc[-1]) / (finestra["Open"].iloc[0] / df["fx"].iloc[i0 - 1]) - 1),
        "pct0", "Variazione del prezzo di Apple in euro, cambio incluso", origine_dati)

    # --- Numeri dell'articolo: risultati ------------------------------------------------------------------
    for sc in SCENARI:
        for nome in ("mm", "bh"):
            r = R[(P, sc, nome)]
            reg(f"finale_{nome}_{sc}", r["valore_finale_eur"], "num2",
                f"Valore finale in euro: {NOME[nome]}, {ETICHETTE[sc]} (si vende tutto alla fine)", f"{SORGENTE}, simula()")
    for nome in ("mm", "bh"):
        r = R[(P, "netto", nome)]
        reg(f"rend_{nome}_netto", r["rendimento_totale"], "pct0", f"Rendimento totale netto: {NOME[nome]}", f"{SORGENTE}, simula()")
        reg(f"cagr_{nome}_netto", r["cagr"], "pct1", f"Rendimento annuo composto netto: {NOME[nome]}", f"{SORGENTE}, simula()")
        reg(f"tasse_{nome}", r["tasse_eur"], "num2", f"Tasse pagate in euro: {NOME[nome]}", f"{SORGENTE}, simula()")
        reg(f"comm_{nome}", r["commissioni_eur"], "num2", f"Commissioni pagate in euro: {NOME[nome]}", f"{SORGENTE}, simula()")
        reg(f"maxdd_{nome}", -r["perdita_massima"], "pct0",
            f"Perdita massima dal picco, valore di mercato giornaliero: {NOME[nome]}", f"{SORGENTE}, simula(): minimo di valore/picco - 1")
    mm = R[(P, "netto", "mm")]
    reg("n_acquisti", mm["n_acquisti"], "int", "Acquisti della regola nel periodo", f"{SORGENTE}, simula()")
    reg("n_vendite_segnale", sum(1 for o in mm["operazioni"] if o["lato"] == "vendita" and o["motivo"] == "segnale"),
        "int", "Vendite della regola causate dal segnale (esclusa la vendita finale)", f"{SORGENTE}, simula()")
    reg("quota_investito", mm["quota_giorni_investito"], "pct0", "Quota di sedute con la regola investita", f"{SORGENTE}, simula()")
    diff = R[(P, "netto", "mm")]["valore_finale_eur"] - R[(P, "netto", "bh")]["valore_finale_eur"]
    reg("diff_netto", diff, "num2", "Differenza finale netta in euro, regola meno buy & hold (segno: + vantaggio della regola)",
        f"{SORGENTE}: finale_mm_netto - finale_bh_netto")
    reg("diff_netto_abs", abs(diff), "num2", "Valore assoluto della differenza finale netta in euro", f"{SORGENTE}: |finale_mm_netto - finale_bh_netto|")
    reg("diff_lordo_abs", abs(R[(P, "lordo", "mm")]["valore_finale_eur"] - R[(P, "lordo", "bh")]["valore_finale_eur"]),
        "num2", "Valore assoluto della differenza finale senza costi né tasse", f"{SORGENTE}")
    reg("costo_commissioni_mm", R[(P, "lordo", "mm")]["valore_finale_eur"] - R[(P, "comm", "mm")]["valore_finale_eur"],
        "num2", "Quanto tolgono le commissioni al risultato della regola, in euro", f"{SORGENTE}: finale_mm_lordo - finale_mm_comm")
    reg("costo_tasse_mm", R[(P, "comm", "mm")]["valore_finale_eur"] - R[(P, "netto", "mm")]["valore_finale_eur"],
        "num2", "Quanto toglie la tassa al risultato della regola, in euro", f"{SORGENTE}: finale_mm_comm - finale_mm_netto")
    reg("costo_tasse_bh", R[(P, "comm", "bh")]["valore_finale_eur"] - R[(P, "netto", "bh")]["valore_finale_eur"],
        "num2", "Quanto toglie la tassa al risultato del buy & hold, in euro", f"{SORGENTE}: finale_bh_comm - finale_bh_netto")
    reg("quota_tasse_mm", (R[(P, "comm", "mm")]["valore_finale_eur"] - R[(P, "netto", "mm")]["valore_finale_eur"])
        / (R[(P, "comm", "mm")]["valore_finale_eur"] - config.CAPITALE), "pct1",
        "Quota del guadagno (dopo le commissioni) che la tassa toglie al valore finale della regola",
        f"{SORGENTE}: (finale_mm_comm - finale_mm_netto) / (finale_mm_comm - capitale)")
    reg("quota_tasse_bh", (R[(P, "comm", "bh")]["valore_finale_eur"] - R[(P, "netto", "bh")]["valore_finale_eur"])
        / (R[(P, "comm", "bh")]["valore_finale_eur"] - config.CAPITALE), "pct1",
        "Quota del guadagno (dopo le commissioni) che la tassa toglie al valore finale del buy & hold",
        f"{SORGENTE}: (finale_bh_comm - finale_bh_netto) / (finale_bh_comm - capitale)")
    for nome in ("mm", "bh"):
        reg(f"finale_{nome}_chiusura", R[(config.MODO_CONTROLLO, "netto", nome)]["valore_finale_eur"], "num2",
            f"Controllo: valore finale netto con ordini alla chiusura, {NOME[nome]}", f"{SORGENTE}, simula(modo='chiusura')")

    # Un'operazione vera: il primo acquisto e la prima vendita della regola
    ops = mm["operazioni"]
    acq = next(o for o in ops if o["lato"] == "acquisto")
    ven = next(o for o in ops if o["lato"] == "vendita")
    o_src = "operazioni_regola.csv, prima coppia acquisto-vendita"
    reg("es_data_acq", acq["data"], "data_lunga", "Data del primo acquisto della regola", o_src)
    reg("es_prezzo_acq_usd", acq["prezzo_usd"], "num2", "Prezzo di apertura pagato, in dollari", o_src)
    reg("es_cambio_acq", acq["cambio"], "num3", "Cambio euro/dollaro usato nell'acquisto", o_src)
    reg("es_azioni", acq["azioni"], "num3", "Frazione di azione acquistata con 500 euro meno la commissione", o_src)
    reg("es_data_vend", ven["data"], "data_lunga", "Data della prima vendita", o_src)
    reg("es_prezzo_vend_usd", ven["prezzo_usd"], "num2", "Prezzo di vendita, in dollari", o_src)
    reg("es_incasso_netto", ven["incasso_netto_eur"], "num2", "Incasso in euro dopo la commissione", o_src)
    reg("es_plusvalenza", ven["plusvalenza_eur"], "num2", "Plusvalenza (o minusvalenza, se negativa) in euro", o_src)
    reg("es_tassa", ven["tassa_eur"], "num2", "Imposta pagata sulla prima vendita, in euro", o_src)
    reg("es_cambio_vend", ven["cambio"], "num3", "Cambio euro/dollaro usato nella prima vendita", o_src)
    reg("es_var_prezzo_usd", ven["prezzo_usd"] / acq["prezzo_usd"] - 1, "pct1",
        "Variazione del prezzo di Apple in dollari tra il primo acquisto e la prima vendita", o_src)
    reg("es_var_dollaro", acq["cambio"] / ven["cambio"] - 1, "pct1",
        "Variazione del valore del dollaro in euro tra il primo acquisto e la prima vendita (positiva: dollaro più forte)",
        o_src + ": cambio_acquisto / cambio_vendita - 1")

    # Operazioni raccontate nel testo: la coppia acquisto-vendita più breve e la vendita più costosa
    coppie = []
    for k, o in enumerate(ops):
        if o["lato"] == "acquisto":
            v = next((x for x in ops[k + 1:] if x["lato"] == "vendita"), None)
            if v is not None:
                coppie.append((o, v))
    breve = min((c for c in coppie if c[1]["motivo"] == "segnale"),
                key=lambda c: (pd.Timestamp(c[1]["data"]) - pd.Timestamp(c[0]["data"])).days)
    giorni_breve = (pd.Timestamp(breve[1]["data"]) - pd.Timestamp(breve[0]["data"])).days
    b_src = "operazioni_regola.csv, coppia acquisto-vendita più breve tra quelle chiuse da un segnale"
    reg("br_data_acq", breve[0]["data"], "data_lunga", "Data dell'acquisto della coppia più breve", b_src)
    reg("br_data_vend", breve[1]["data"], "data_lunga", "Data della vendita della coppia più breve", b_src)
    reg("br_giorni", giorni_breve, "int", "Giorni di calendario tra acquisto e vendita della coppia più breve", b_src)
    reg("br_perdita", -breve[1]["plusvalenza_eur"], "num2", "Perdita in euro della coppia più breve (commissioni incluse)", b_src)
    peggiore = min((o for o in ops if o["lato"] == "vendita" and o["motivo"] == "segnale"), key=lambda o: o["plusvalenza_eur"])
    k_p = ops.index(peggiore)
    p_src = "operazioni_regola.csv, vendita da segnale con la perdita maggiore"
    reg("pv_data", peggiore["data"], "data_lunga", "Data della vendita più costosa", p_src)
    reg("pv_prezzo_usd", peggiore["prezzo_usd"], "num2", "Prezzo di vendita della vendita più costosa, in dollari", p_src)
    reg("pv_perdita", -peggiore["plusvalenza_eur"], "num2", "Perdita in euro della vendita più costosa (commissioni incluse)", p_src)
    d_p = pd.Timestamp(peggiore["data"])
    pos_p = df.index.get_loc(d_p)
    reg("pv_rimbalzo", float(df["Close"].iloc[pos_p + 1] / df["Close"].iloc[pos_p] - 1), "pct1",
        "Variazione di Apple (chiusura su chiusura) nella seduta successiva alla vendita più costosa", origine_dati)
    riacq = next((x for x in ops[k_p + 1:] if x["lato"] == "acquisto"), None)
    if riacq is not None:
        reg("pv_data_riacq", riacq["data"], "data_lunga", "Data del riacquisto dopo la vendita più costosa", p_src)
        reg("pv_prezzo_riacq_usd", riacq["prezzo_usd"], "num2", "Prezzo di riacquisto, in dollari", p_src)
        reg("pv_salita", riacq["prezzo_usd"] / peggiore["prezzo_usd"] - 1, "pct0",
            "Di quanto era salito Apple (in dollari) tra la vendita più costosa e il riacquisto", p_src)

    # --- Finestre mobili: la data di partenza cambia il verdetto? -----------------------------------------
    primo_mese = pd.Series(np.arange(len(df)), index=df.index).groupby(df.index.to_period("M")).first()
    righe = []
    for pos in primo_mese.to_numpy():
        d0 = df.index[pos]
        if d0 < pd.Timestamp(config.INIZIO_FINESTRE) or pos < config.SMA_LENTA + 1:
            continue
        d1 = d0 + pd.DateOffset(years=config.ANNI_TEST)
        if d1 > df.index[-1]:
            break
        i1 = s.indice_data(df, d1)
        sub = df.iloc[:i1 + 1]
        a_ = s.simula(sub, pos, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, P, True)
        b_ = s.simula(sub, pos, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, P, False)
        righe.append({"data_inizio": d0, "data_fine": df.index[i1], "finale_regola": a_["valore_finale_eur"],
                      "finale_bh": b_["valore_finale_eur"], "differenza": a_["valore_finale_eur"] - b_["valore_finale_eur"],
                      "maxdd_regola": a_["perdita_massima"], "maxdd_bh": b_["perdita_massima"],
                      "tasse_regola": a_["tasse_eur"], "tasse_bh": b_["tasse_eur"]})
    fm = pd.DataFrame(righe)
    if fm.empty:
        raise SystemExit("Nessuna finestra mobile calcolata.")
    fm.to_csv(config.RISULTATI / "finestre_mobili.csv", index=False, float_format="%.6f")
    f_src = f"{SORGENTE}: finestre di {config.ANNI_TEST} anni, una partenza al mese dal {config.INIZIO_FINESTRE}, stessi costi e tasse"
    reg("fm_n", len(fm), "int", "Numero di finestre mobili", f_src)
    reg("fm_primo_inizio", str(fm["data_inizio"].iloc[0].date()), "data_lunga", "Prima data di partenza delle finestre", f_src)
    reg("fm_ultimo_inizio", str(fm["data_inizio"].iloc[-1].date()), "data_lunga", "Ultima data di partenza delle finestre", f_src)
    reg("fm_quota_vince", float((fm["differenza"] > 0).mean()), "pct0", "Quota di finestre in cui la regola chiude sopra il buy & hold (netto)", f_src)
    reg("fm_mediana_diff", float(fm["differenza"].median()), "num2", "Mediana della differenza finale netta in euro (regola meno buy & hold)", f_src)
    reg("fm_diff_min", float(fm["differenza"].min()), "num2", "Differenza finale netta peggiore per la regola, in euro", f_src)
    reg("fm_diff_max", float(fm["differenza"].max()), "num2", "Differenza finale netta migliore per la regola, in euro", f_src)
    reg("fm_quota_dd", float((fm["maxdd_regola"] > fm["maxdd_bh"]).mean()), "pct0",
        "Quota di finestre in cui la regola ha una perdita massima minore del buy & hold", f_src)
    reg("fm_mediana_dd_regola", float(-fm["maxdd_regola"].median()), "pct0", "Mediana della perdita massima della regola", f_src)
    reg("fm_mediana_dd_bh", float(-fm["maxdd_bh"].median()), "pct0", "Mediana della perdita massima del buy & hold", f_src)
    reg("fm_mediana_finale_regola", float(fm["finale_regola"].median()), "num2", "Mediana del valore finale netto della regola, in euro", f_src)
    reg("fm_mediana_finale_bh", float(fm["finale_bh"].median()), "num2", "Mediana del valore finale netto del buy & hold, in euro", f_src)

    payload = {
        "generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ambiente": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
        "dati": {"sha256_titolo": meta["sha256_titolo"], "sha256_cambio": meta["sha256_cambio"]},
        "valori": RIS,
    }
    (config.RISULTATI / "metriche.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri in risultati/metriche.json")
    print(f"Periodo {finestra.index[0].date()} -> {fine.date()}  ({n_test} sedute)")
    for sc in SCENARI:
        print(f"  {sc:7s} regola {R[(P, sc, 'mm')]['valore_finale_eur']:9.2f}   buy&hold {R[(P, sc, 'bh')]['valore_finale_eur']:9.2f}")
    print(f"  finestre mobili: {len(fm)}, la regola vince nel {(fm['differenza'] > 0).mean():.0%}")


if __name__ == "__main__":
    main()
