"""Passo 2 - Rotazione mensile tra nove ETF settoriali: venti regole dichiarate in anticipo.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine di calcolo
  prove.csv         per regola e scenario: valore finale, rendimento annuo, ordini, costi, tasse, perdita massima
  meta_periodo.csv  rendimento annuo netto di ogni regola nella prima e nella seconda metà del periodo
  curve.csv         valore (una seduta su cinque) di buy & hold, nove settori e regola centrale

Regole: "bh" = buy & hold dell'ETF sull'S&P 500; "eq" = i nove settori comprati in parti uguali e tenuti;
"r<L>_<K>" = rotazione mensile verso i K settori con il rendimento più alto delle ultime L sedute.
Scenari: "lordo" (nessun costo, nessuna tassa) e "c0" (commissione proporzionale e tassa del 26%).
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
SCEN = [("lordo", 0.0, 0.0, 0.0)] + [(f"c{k}", f, p, config.ALIQUOTA) for k, (_, f, p) in enumerate(config.SCENARI_COSTO)]
M = f"c{config.SCENARIO_PRINCIPALE}"


def rid_rot(L: int, k: int) -> str:
    return f"r{L}_{k}"


GRIGLIA = [(L, k) for k in config.N_SETTORI for L in config.LOOKBACKS]
VARIANTI = [rid_rot(L, k) for L, k in GRIGLIA]
R_CENTRALE = rid_rot(*config.CENTRALE)
NOME_REGOLA = {"bh": "buy & hold dell'S&P 500", "eq": "nove settori tenuti"}
for L, k in GRIGLIA:
    NOME_REGOLA[rid_rot(L, k)] = f"rotazione, {L} sedute, {k} {'settore' if k == 1 else 'settori'}"


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def holm(p: dict) -> dict:
    ordine = sorted(p, key=p.get)
    m = len(ordine)
    out, massimo = {}, 0.0
    for k, nome in enumerate(ordine):
        massimo = max(massimo, min(1.0, (m - k) * p[nome]))
        out[nome] = massimo
    return out


def bootstrap_blocchi(d: np.ndarray, rng) -> np.ndarray:
    N, L = len(d), config.LUNGHEZZA_BLOCCO
    nb = int(np.ceil(N / L))
    medie = np.empty(config.N_BOOTSTRAP)
    passo = 250
    for a in range(0, config.N_BOOTSTRAP, passo):
        m = min(passo, config.N_BOOTSTRAP - a)
        inizi = rng.integers(0, N, size=(m, nb))
        idx = (inizi[:, :, None] + np.arange(L)[None, None, :]) % N
        medie[a:a + m] = d[idx.reshape(m, -1)[:, :N]].mean(axis=1)
    return medie


def ranghi(x: np.ndarray) -> np.ndarray:
    return np.argsort(np.argsort(-x)) + 1          # 1 = valore più alto


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    stato = {r["ticker"]: r["stato"] for r in meta["strumenti"]}
    tickers = [t for t, _ in config.SETTORI] + [config.BENCHMARK[0]]
    for t in tickers + [config.TICKER_CAMBIO]:
        if stato.get(t) != "ok":
            raise SystemExit(f"Dati mancanti per {t}: {stato.get(t)}")
    chiusure = {t: s.carica_csv(config.file_dati(t)) for t in tickers}
    cambio = s.carica_csv(config.file_dati(config.TICKER_CAMBIO))
    date, nomi, C, FX = s.prepara(chiusure, cambio)
    n = len(date)
    anni_idx = date.year.to_numpy()
    col_sett = list(range(len(config.SETTORI)))
    col_spy = nomi.index(config.BENCHMARK[0])
    t_min = max(config.LOOKBACKS)

    piani = {rid_rot(L, k): s.piano_rotazione(C, date, L, k, t_min, col_sett) for L, k in GRIGLIA}
    i0 = min(min(p) for p in piani.values())
    if any(min(p) != i0 for p in piani.values()):
        raise SystemExit("Le regole non partono tutte nella stessa seduta.")
    piani["bh"] = {i0: (col_spy,)}
    piani["eq"] = {i0: tuple(col_sett)}
    anni_test = (date[-1] - date[i0]).days / 365.25
    if anni_test < config.STORIA_MINIMA_ANNI:
        raise SystemExit(f"Solo {anni_test:.1f} anni di test: troppo pochi.")
    REGOLE = ["bh", "eq"] + VARIANTI
    print(f"{n} sedute dal {date[0].date()} al {date[-1].date()}; test dal {date[i0].date()} ({anni_test:.1f} anni)")

    sim = {}
    for rid in REGOLE:
        for sid, f, p, al in SCEN:
            sim[(rid, sid)] = s.simula(C, FX, anni_idx, piani[rid], i0, config.CAPITALE, f, p, al, serie=True)
    cg = {k: s.cagr(v["valore_finale_eur"], config.CAPITALE, date, i0) for k, v in sim.items()}
    prove = [{"regola": rid, "scenario": sid, "finale": r["valore_finale_eur"], "cagr": cg[(rid, sid)],
              "ordini": r["n_acquisti"] + r["n_vendite"], "commissioni": r["commissioni_eur"], "tasse": r["tasse_eur"],
              "perdita_massima": r["perdita_massima"]} for (rid, sid), r in sim.items()]

    # prima e seconda metà (equity netta)
    mezzo_rend = {}
    for rid in REGOLE:
        e = sim[(rid, M)]["equity"]
        m = len(e) // 2
        a1, a2 = m / 252.0, (len(e) - m) / 252.0
        mezzo_rend[rid] = ((e[m - 1] / e[0]) ** (1 / a1) - 1, (e[-1] / e[m - 1]) ** (1 / a2) - 1)
    # bootstrap a blocchi: ogni regola contro i nove settori tenuti, netto
    e_eq = sim[("eq", M)]["equity"]
    pv, boot = {}, {}
    for q, rid in enumerate(VARIANTI):
        e = sim[(rid, M)]["equity"]
        d = (e[1:] / e[:-1] - 1) - (e_eq[1:] / e_eq[:-1] - 1)
        medie = bootstrap_blocchi(d - d.mean(), np.random.default_rng([config.SEME, 2, q]))
        osserv = float(d.mean())
        pv[rid] = (int((np.abs(medie) >= abs(osserv)).sum()) + 1) / (config.N_BOOTSTRAP + 1)
        boot[rid] = osserv * 252
    ph = holm(pv)

    # --- Numeri ------------------------------------------------------------------------------------------------------------
    reg("n_sedute", n, "int", "Sedute comuni a tutti gli strumenti e al cambio", "dati/")
    reg("data_inizio", str(date[i0].date()), "data_lunga", "Prima seduta del test (primo ordine di tutte le regole)", "dati/")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta presente nei dati", "dati/")
    reg("anni", anni_test, "num1", "Anni del test")
    reg("n_regole", len(VARIANTI), "int", "Regole di rotazione della griglia", "config.py, LOOKBACKS e N_SETTORI")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale in euro", "config.py, CAPITALE")
    reg("commissione_perc", config.SCENARI_COSTO[config.SCENARIO_PRINCIPALE][2], "pct1", "Commissione proporzionale all'importo di ogni ordine", "config.py, SCENARI_COSTO")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap a blocchi", "config.py")
    reg("blocco", config.LUNGHEZZA_BLOCCO, "int", "Sedute per blocco nel bootstrap", "config.py")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello di significatività complementare", "config.py")
    for rid in REGOLE:
        for sid, *_ in SCEN:
            x = sim[(rid, sid)]
            reg(f"{rid}_{sid}_finale", x["valore_finale_eur"], "int", f"Valore finale di {config.CAPITALE:.0f} euro ({NOME_REGOLA[rid]}, scenario {sid})")
            reg(f"{rid}_{sid}_cagr", cg[(rid, sid)], "pct1", f"Rendimento annuo composto ({NOME_REGOLA[rid]}, scenario {sid})")
        x = sim[(rid, M)]
        reg(f"{rid}_dd", -x["perdita_massima"], "pct0", f"Perdita massima dal picco ({NOME_REGOLA[rid]}, netto)")
        reg(f"{rid}_ordini_anno", (x["n_acquisti"] + x["n_vendite"]) / anni_test, "num1", f"Ordini all'anno ({NOME_REGOLA[rid]})")
        reg(f"{rid}_tasse", x["tasse_eur"], "int", f"Tasse pagate in tutto ({NOME_REGOLA[rid]})")
        reg(f"{rid}_costo", x["commissioni_eur"], "int", f"Commissioni pagate in tutto ({NOME_REGOLA[rid]})")
        reg(f"{rid}_meta1", mezzo_rend[rid][0], "pct1", f"Rendimento annuo netto nella prima metà del periodo ({NOME_REGOLA[rid]})", "meta_periodo.csv")
        reg(f"{rid}_meta2", mezzo_rend[rid][1], "pct1", f"Rendimento annuo netto nella seconda metà del periodo ({NOME_REGOLA[rid]})", "meta_periodo.csv")
    for rid in VARIANTI:
        reg(f"{rid}_diff_eq", boot[rid], "pp1", f"Differenza annua netta rispetto ai nove settori tenuti, punti percentuali ({NOME_REGOLA[rid]})", "bootstrap a blocchi")
        reg(f"{rid}_p", pv[rid], "pval", f"p-value (bootstrap a blocchi) della differenza netta contro i nove settori tenuti ({NOME_REGOLA[rid]})", "bootstrap a blocchi")
        reg(f"{rid}_p_holm", ph[rid], "pval", f"p-value corretto con il metodo di Holm sulle venti regole ({NOME_REGOLA[rid]})", "bootstrap a blocchi")
    sv = sorted(VARIANTI)
    c_lordo = np.array([cg[(r, "lordo")] for r in VARIANTI])
    c_netto = np.array([cg[(r, M)] for r in VARIANTI])
    reg("n_ip1", int((c_lordo > cg[("bh", "lordo")]).sum()), "int", "Regole con rendimento annuo lordo sopra il buy & hold dell'S&P 500", "prove.csv")
    reg("n_lordo_sopra_eq", int((c_lordo > cg[("eq", "lordo")]).sum()), "int", "Regole con rendimento annuo lordo sopra i nove settori tenuti", "prove.csv")
    reg("n_netto_sopra_bh", int((c_netto > cg[("bh", M)]).sum()), "int", "Regole con rendimento annuo netto sopra il buy & hold dell'S&P 500", "prove.csv")
    reg("n_ip2", int((c_netto > cg[("eq", M)]).sum()), "int", "Regole con rendimento annuo netto sopra i nove settori tenuti", "prove.csv")
    reg("n_holm_signif", int(sum(ph[r] < 0.05 for r in VARIANTI)), "int", "Regole con p-value corretto con Holm sotto il cinque per cento", "bootstrap a blocchi")
    reg("n_p_signif", int(sum(pv[r] < 0.05 for r in VARIANTI)), "int", "Regole con p-value non corretto sotto il cinque per cento", "bootstrap a blocchi")
    m1 = np.array([mezzo_rend[r][0] for r in VARIANTI])
    m2 = np.array([mezzo_rend[r][1] for r in VARIANTI])
    r1, r2 = ranghi(m1), ranghi(m2)
    ib = int(np.argmin(r1))
    reg("migliore1_nome", NOME_REGOLA[VARIANTI[ib]], "testo", "Regola con il rendimento netto più alto nella prima metà del periodo", "meta_periodo.csv")
    reg("migliore1_cagr1", m1[ib], "pct1", "Rendimento annuo netto della migliore della prima metà, nella prima metà", "meta_periodo.csv")
    reg("migliore1_cagr2", m2[ib], "pct1", "Rendimento annuo netto della migliore della prima metà, nella seconda metà", "meta_periodo.csv")
    reg("migliore1_rango2", int(r2[ib]), "int", "Posto (1 = migliore) che la migliore della prima metà ha nella seconda metà, tra le venti regole", "meta_periodo.csv")
    ib2 = int(np.argmin(r2))
    reg("migliore2_nome", NOME_REGOLA[VARIANTI[ib2]], "testo", "Regola con il rendimento netto più alto nella seconda metà del periodo", "meta_periodo.csv")
    reg("migliore2_rango1", int(r1[ib2]), "int", "Posto che la migliore della seconda metà aveva nella prima metà", "meta_periodo.csv")
    sp = float(np.corrcoef(r1, r2)[0, 1])
    reg("spearman_meta", sp, "num2", "Correlazione tra le classifiche delle venti regole nelle due metà (Spearman)", "meta_periodo.csv")
    ig = int(np.argmax(c_netto))
    reg("migliore_nome", NOME_REGOLA[VARIANTI[ig]], "testo", "Regola con il rendimento annuo netto più alto su tutto il periodo", "prove.csv")
    reg("migliore_cagr", c_netto[ig], "pct1", "Rendimento annuo netto della migliore su tutto il periodo", "prove.csv")
    reg("migliore_p_holm", ph[VARIANTI[ig]], "pval", "p-value corretto della migliore su tutto il periodo", "bootstrap a blocchi")
    iw = int(np.argmin(c_netto))
    reg("peggiore_nome", NOME_REGOLA[VARIANTI[iw]], "testo", "Regola con il rendimento annuo netto più basso", "prove.csv")
    reg("peggiore_cagr", c_netto[iw], "pct1", "Rendimento annuo netto della peggiore su tutto il periodo", "prove.csv")
    reg("cagr_mediana_regole", float(np.median(c_netto)), "pct1", "Mediana dei rendimenti annui netti delle venti regole", "prove.csv")
    reg("attrito_medio", float(np.mean(c_lordo - c_netto)), "pp1", "Punti di rendimento annuo persi in media dal lordo al netto, sulle venti regole", "prove.csv")
    reg("ordini_anno_min", float(min(RIS[f"{r}_ordini_anno"]["valore"] for r in VARIANTI)), "num1", "Ordini all'anno della regola che ne fa meno", "prove.csv")
    reg("ordini_anno_max", float(max(RIS[f"{r}_ordini_anno"]["valore"] for r in VARIANTI)), "num1", "Ordini all'anno della regola che ne fa di più", "prove.csv")
    # per lookback: la regola migliore con k=1 e con k=4
    reg("n_lookback_breve_sopra", int(sum(cg[(rid_rot(21, k), M)] > cg[("eq", M)] for k in config.N_SETTORI)), "int", "Regole con osservazione di un mese sopra i nove settori tenuti, netto", "prove.csv")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    for nome, v in config.SOGLIE.items():
        reg(f"soglia_{nome}", v, "int", f"Soglia dell'ipotesi ({nome})", "config.py, SOGLIE")
    reg("anno_mg", 1999, "annonum", "Anno dell'articolo di Moskowitz e Grinblatt", "Moskowitz e Grinblatt, Journal of Finance")

    pd.DataFrame(prove).to_csv(config.RISULTATI / "prove.csv", index=False, float_format="%.6f")
    pd.DataFrame({"regola": VARIANTI + ["bh", "eq"], "meta1": [mezzo_rend[r][0] for r in VARIANTI + ["bh", "eq"]],
                  "meta2": [mezzo_rend[r][1] for r in VARIANTI + ["bh", "eq"]]}).to_csv(config.RISULTATI / "meta_periodo.csv", index=False, float_format="%.6f")
    cur = pd.DataFrame({"data": date[i0:].astype(str), **{rid: sim[(rid, M)]["equity"] for rid in ("bh", "eq", R_CENTRALE)}}).iloc[::5]
    cur.to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.2f")
    (config.RISULTATI / "regole.json").write_text(json.dumps([{"id": rid_rot(L, k), "L": L, "k": k} for L, k in GRIGLIA]), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
