"""Passo 2 - Il settore migliore con il senno di poi: confronto con l'indice, il caso e la regola realizzabile.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json        ogni numero dell'articolo, con descrizione e origine di calcolo
  anni.csv             per anno: settore migliore, suo rendimento, rendimento di SPY, vincitore dell'anno prima e suo rendimento
  curve_capitale.csv   capitale (da 10.000) anno per anno: senno di poi, SPY, regola realizzabile, scimmia mediana, media dei settori
  scimmie.csv          rendimento annuo composto di ciascuna scimmia
  frequenze.csv        rotazione con senno di poi ogni anno, trimestre, mese: rendimento annuo e capitale finale
  settori.csv          per settore: rendimento annuo composto e numero di anni da migliore
Nessun look-ahead nella regola realizzabile: il settore del periodo t si sceglie solo con i rendimenti fino a t-1.
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
    META = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    rng = np.random.default_rng(config.SEME)
    tick = [t for t, _, _ in config.SETTORI]
    nomi = {t: n for t, n, _ in config.SETTORI}
    prezzi = pd.concat({t: pd.read_csv(config.file_dati(t), index_col=0, parse_dates=True)["Close"] for t in tick + [config.BENCHMARK[0]]}, axis=1)
    prezzi = prezzi.dropna()
    S = config.SOGLIE
    a1, a2 = config.ANNO_INIZIO, config.ANNO_FINE

    # ---------------- rotazione annuale ----------------
    ra = fx.rendimenti_periodo(prezzi, config.FREQUENZE["anno"], a1, a2)
    anni_lista = [int(x) for x in ra.index.year]
    R = ra[tick].values
    spy = ra[config.BENCHMARK[0]].values
    T = len(R)
    if T != a2 - a1 + 1:
        raise SystemExit(f"Anni completi attesi {a2 - a1 + 1}, trovati {T}")
    idx, best = fx.migliore_ex_post(R)
    cagr_best = fx.cagr(best, T)
    cagr_spy = fx.cagr(spy, T)
    eq = R.mean(axis=1)                      # media dei nove settori, ribilanciata ogni anno
    cagr_eq = fx.cagr(eq, T)
    cagr_set = {t: fx.cagr(R[:, i], T) for i, t in enumerate(tick)}
    miglior_set = max(cagr_set, key=cagr_set.get)

    reg("prima_anno", a1, "annonum", "Primo anno solare del confronto", "config.py, ANNO_INIZIO")
    reg("ultima_anno", a2, "annonum", "Ultimo anno solare del confronto", "config.py, ANNO_FINE")
    reg("n_anni", T, "int", "Anni solari completi del confronto", "dati/")
    reg("n_settori", len(tick), "int", "Settori (ETF SPDR) usati", "config.py, SETTORI")
    reg("data_scarico", META["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("capitale_iniziale", config.CAPITALE_INIZIALE, "int", "Capitale di partenza (dollari)", "config.py, CAPITALE_INIZIALE")
    reg("cagr_senno", cagr_best, "pct1", "Rendimento annuo composto scegliendo ogni anno il settore migliore con il senno di poi")
    reg("cagr_spy", cagr_spy, "pct1", "Rendimento annuo composto dell'S&P 500 (SPY, dividendi reinvestiti), buy & hold")
    reg("cagr_media_settori", cagr_eq, "pct1", "Rendimento annuo composto della media dei nove settori ribilanciata ogni anno")
    reg("miglior_settore_bh", nomi[miglior_set], "testo", "Settore col miglior rendimento annuo composto tenuto per tutto il periodo")
    reg("miglior_settore_bh_cagr", cagr_set[miglior_set], "pct1", "Rendimento annuo composto di quel settore buy & hold")
    reg("peggior_settore_bh", nomi[min(cagr_set, key=cagr_set.get)], "testo", "Settore col peggior rendimento annuo composto tenuto per tutto il periodo")
    reg("peggior_settore_bh_cagr", min(cagr_set.values()), "pct1", "Rendimento annuo composto di quel settore buy & hold")
    reg("vantaggio_senno_pp", (cagr_best - cagr_spy), "pp1", "Vantaggio annuo della scelta con il senno di poi sull'S&P 500 (punti percentuali)")
    reg("vantaggio_senno_su_best_pp", (cagr_best - cagr_set[miglior_set]), "pp1", "Vantaggio annuo del senno di poi sul miglior settore tenuto fermo (punti)")
    cap_senno = fx.curva_capitale(best, config.CAPITALE_INIZIALE)
    cap_spy = fx.curva_capitale(spy, config.CAPITALE_INIZIALE)
    reg("cap_senno", cap_senno[-1], "int", "Capitale finale (lordo) della scelta con il senno di poi, partendo dal capitale iniziale")
    reg("cap_spy", cap_spy[-1], "int", "Capitale finale (lordo) dell'S&P 500 (SPY), partendo dal capitale iniziale")
    reg("cap_rapporto", cap_senno[-1] / cap_spy[-1], "num1", "Rapporto tra capitale finale del senno di poi e quello dell'S&P 500")
    reg("best_mediano", float(np.median(best)), "pct0", "Rendimento mediano annuo del settore migliore")
    reg("best_min", float(best.min()), "pct0", "Rendimento del settore migliore nell'anno in cui è andato peggio")
    reg("best_min_anno", str(anni_lista[int(best.argmin())]), "testo", "Anno in cui il settore migliore è andato peggio", "anni.csv")
    reg("best_max", float(best.max()), "pct0", "Rendimento del settore migliore nell'anno in cui è andato meglio")
    reg("best_max_anno", str(anni_lista[int(best.argmax())]), "testo", "Anno del miglior rendimento del settore migliore", "anni.csv")
    reg("best_max_nome", nomi[tick[int(idx[best.argmax()])]], "testo", "Settore migliore nell'anno record", "anni.csv")
    reg("spy_mediano", float(np.median(spy)), "pct0", "Rendimento mediano annuo dell'S&P 500 (SPY)")
    perdite = [(anni_lista[t], nomi[tick[idx[t]]], best[t]) for t in range(T) if best[t] < 0]
    reg("n_anni_best_perde", len(perdite), "int", "Anni in cui anche il settore migliore ha chiuso in perdita", "anni.csv")
    reg("anni_best_perde", ", ".join(str(p[0]) for p in perdite) if perdite else "nessuno", "testo", "Quali anni", "anni.csv")
    n_dist = len(set(idx.tolist()))
    reg("n_settori_vincenti", n_dist, "int", "Settori diversi che sono stati i migliori almeno una volta", "anni.csv")
    conta = np.bincount(idx, minlength=len(tick))
    top = int(conta.argmax())
    reg("settore_piu_vincente", nomi[tick[top]], "testo", "Settore che è stato il migliore più volte", "anni.csv")
    reg("settore_piu_vincente_n", int(conta[top]), "int", "Quante volte", "anni.csv")
    reg("anni_spy_batte_senno", int((spy > best).sum()), "int", "Anni in cui l'S&P 500 ha battuto il settore migliore", "anni.csv")
    reg("anni_senno_batte_spy", int((best > spy).sum()), "int", "Anni in cui il settore migliore ha battuto l'S&P 500", "anni.csv")

    # ---------------- il caso: scimmie ----------------
    scim = fx.scimmie(R, config.N_SCIMMIE, T, rng)
    a = (1 - config.LIVELLO_CONFIDENZA) / 2
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie (scelta casuale del settore ogni anno)", "config.py, N_SCIMMIE")
    reg("scimmia_mediana", float(np.median(scim)), "pct1", "Rendimento annuo composto della scimmia mediana")
    reg("scimmia_lo", float(np.quantile(scim, a)), "pct1", "Estremo basso della fascia 95% delle scimmie")
    reg("scimmia_hi", float(np.quantile(scim, 1 - a)), "pct1", "Estremo alto della fascia 95% delle scimmie")
    reg("scimmie_battono_spy", float(np.mean(scim > cagr_spy)), "pct0", "Quota di scimmie che battono l'S&P 500")
    reg("scimmie_battono_media", float(np.mean(scim > cagr_eq)), "pct0", "Quota di scimmie che battono la media dei nove settori")
    reg("scimmia_migliore", float(scim.max()), "pct1", "Rendimento annuo della scimmia più fortunata")
    reg("scimmia_peggiore", float(scim.min()), "pct1", "Rendimento annuo della scimmia più sfortunata")
    p_senno = (1 + np.sum(scim >= cagr_best)) / (1 + config.N_SCIMMIE)
    reg("n_scimmie_eguagliano_senno", int((scim >= cagr_best).sum()), "int", "Scimmie che raggiungono il senno di poi")

    # ---------------- regola realizzabile: compra il vincitore dell'anno prima ----------------
    copia = fx.vincitore_precedente(R)
    Tc = len(copia)
    cagr_copia = fx.cagr(copia, Tc)
    scim_c = fx.scimmie(R[1:], config.N_SCIMMIE, Tc, rng)
    cagr_spy_c = fx.cagr(spy[1:], Tc)
    p_copia = (1 + np.sum(scim_c >= cagr_copia)) / (1 + config.N_SCIMMIE)
    h = fx.holm({"senno": p_senno, "copia": p_copia})
    reg("n_anni_copia", Tc, "int", "Anni della regola «compra il vincitore dell'anno prima» (il primo anno non ha un anno prima)")
    reg("cagr_copia", cagr_copia, "pct1", "Rendimento annuo composto della regola «compra il vincitore dell'anno prima»")
    reg("cagr_spy_copia", cagr_spy_c, "pct1", "Rendimento annuo composto dell'S&P 500 sugli stessi anni")
    reg("copia_vs_spy_pp", cagr_copia - cagr_spy_c, "pp1", "Vantaggio annuo (punti) della regola realizzabile sull'S&P 500, stessi anni")
    reg("copia_batte_scimmie", float(np.mean(scim_c < cagr_copia)), "pct0", "Quota di scimmie (stessi anni) battute dalla regola realizzabile")
    reg("copia_anni_vinti_spy", int((copia > spy[1:]).sum()), "int", "Anni in cui la regola realizzabile batte l'S&P 500")
    reg("p_senno_grezzo", p_senno, "pval", "p-value (non corretto): scimmie con rendimento pari o superiore al senno di poi")
    reg("p_copia_grezzo", p_copia, "pval", "p-value (non corretto): scimmie con rendimento pari o superiore alla regola realizzabile")
    reg("p_senno_holm", h["senno"], "pval", "p-value corretto per Holm, senno di poi")
    reg("p_copia_holm", h["copia"], "pval", "p-value corretto per Holm, regola realizzabile")
    reg("n_test_holm", 2, "int", "Test corretti con Holm (senno di poi e regola realizzabile contro le scimmie)")
    rango = fx.rango_vincitore_precedente(R)
    reg("rango_mediano", float(np.median(rango)), "num1", "Posizione mediana (1 = migliore, 9 = peggiore) nell'anno dopo del settore che ha vinto l'anno prima")
    reg("rango_medio", float(rango.mean()), "num1", "Posizione media nell'anno dopo del vincitore dell'anno prima (il caso darebbe 5,0)")
    reg("vince_ancora", int((rango == 1).sum()), "int", "Volte in cui il vincitore dell'anno prima vince anche l'anno dopo")
    reg("ultimo_ancora", int((rango == len(tick)).sum()), "int", "Volte in cui il vincitore dell'anno prima arriva ultimo l'anno dopo")
    reg("rango_atteso", (len(tick) + 1) / 2, "num1", "Posizione media attesa col solo caso: (nove settori + 1) / 2")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello della fascia delle scimmie", "config.py, LIVELLO_CONFIDENZA")
    reg("vince_ancora_atteso", Tc / len(tick), "num1", "Volte attese col solo caso (anni diviso nove settori)")

    # ---------------- frequenze: anno, trimestre, mese ----------------
    righe_f = []
    cap_per_freq = {}
    for nome_f, alias in config.FREQUENZE.items():
        rf = fx.rendimenti_periodo(prezzi, alias, a1, a2)
        Rf = rf[tick].values
        _, bf = fx.migliore_ex_post(Rf)
        cap = config.CAPITALE_INIZIALE * float(np.prod(1 + bf))
        cap_per_freq[nome_f] = cap
        righe_f.append({"frequenza": nome_f, "n_periodi": len(bf), "cagr": fx.cagr(bf, T), "capitale_finale": cap})
        reg(f"cap_{nome_f}", cap, "int", f"Capitale finale (lordo) scegliendo con il senno di poi il settore migliore ogni {nome_f}")
        reg(f"cagr_{nome_f}", fx.cagr(bf, T), "pct0", f"Rendimento annuo composto scegliendo con il senno di poi ogni {nome_f}")
        reg(f"n_periodi_{nome_f}", len(bf), "int", f"Numero di scelte fatte ({nome_f})")
        reg(f"best_medio_{nome_f}", float(bf.mean()), "pct1", f"Rendimento medio del settore migliore in un {nome_f}")
    reg("volte_mese_su_anno", cap_per_freq["mese"] / cap_per_freq["anno"], "int", "Capitale finale mensile diviso quello annuale (senno di poi)")
    reg("cifre_mese", float(np.log10(cap_per_freq["mese"])), "num1", "Logaritmo in base 10 del capitale finale mensile")

    # ---------------- netto di costi e tasse ----------------
    net_senno = fx.capitale_netto_rotazione(best, config.CAPITALE_INIZIALE, config.COSTO_ORDINE, config.TASSA)
    net_spy = fx.capitale_netto_buy_hold(spy, config.CAPITALE_INIZIALE, config.COSTO_ORDINE, config.TASSA)
    reg("costo_ordine", config.COSTO_ORDINE, "pct1", "Costo per ogni acquisto e ogni vendita", "config.py, COSTO_ORDINE")
    reg("tassa", config.TASSA, "pct0", "Tassa sulle plusvalenze", "config.py, TASSA")
    reg("net_senno", net_senno, "int", "Capitale finale netto (costi e tasse) della rotazione annuale con il senno di poi")
    reg("net_spy", net_spy, "int", "Capitale finale netto (costi e tasse) dell'S&P 500 buy & hold")
    reg("net_frazione", net_senno / cap_senno[-1], "pct0", "Quota del capitale lordo che resta dopo costi e tasse (senno di poi)")
    reg("net_frazione_spy", net_spy / cap_spy[-1], "pct0", "Quota del capitale lordo che resta dopo costi e tasse (S&P 500)")
    reg("net_cagr_senno", float((net_senno / config.CAPITALE_INIZIALE) ** (1 / T) - 1), "pct1", "Rendimento annuo composto netto della rotazione con senno di poi")
    reg("net_cagr_spy", float((net_spy / config.CAPITALE_INIZIALE) ** (1 / T) - 1), "pct1", "Rendimento annuo composto netto dell'S&P 500")

    # ---------------- soglie ----------------
    for k, f, d in (("ip1_pp", "int", "Soglia ipotesi 1: vantaggio annuo (punti) sull'S&P 500"),
                    ("ip2_quota", "pct0", "Soglia ipotesi 2: quota di scimmie che battono l'indice"),
                    ("ip3_pp", "int", "Soglia ipotesi 3: vantaggio massimo (punti) della regola realizzabile"),
                    ("ip3_perc", "pct0", "Soglia ipotesi 3: quota di scimmie battute"),
                    ("ip4_volte", "int", "Soglia ipotesi 4: multiplo del capitale finale mensile su quello annuale"),
                    ("ip5_frazione", "pct0", "Soglia ipotesi 5: frazione del capitale lordo che resta"),
                    ("ip7_lo", "int", "Soglia ipotesi 7: estremo basso della posizione mediana"),
                    ("ip7_hi", "int", "Soglia ipotesi 7: estremo alto della posizione mediana"),
                    ("alfa", "num2", "Soglia di significatività dopo Holm")):
        reg(f"s_{k}", S[k], f, d, "config.py, SOGLIE")

    # ---------------- tabelle ----------------
    anni_df = pd.DataFrame({"anno": anni_lista, "settore_migliore": [tick[i] for i in idx], "rendimento_migliore": best,
                            "rendimento_spy": spy, "media_settori": eq})
    vinc_prec = [""] + [tick[i] for i in idx[:-1]]
    anni_df["vincitore_anno_prima"] = vinc_prec
    anni_df["rendimento_vincitore_anno_prima"] = [np.nan] + list(copia)
    anni_df["rango_vincitore_anno_prima"] = [np.nan] + list(rango)
    anni_df.to_csv(config.RISULTATI / "anni.csv", index=False, float_format="%.5f")
    curve = pd.DataFrame({"anno": anni_lista, "senno_di_poi": cap_senno, "spy": cap_spy,
                          "media_settori": fx.curva_capitale(eq, config.CAPITALE_INIZIALE)})
    curve["regola_realizzabile"] = [np.nan] + list(fx.curva_capitale(copia, config.CAPITALE_INIZIALE))
    mediana_lr = np.median(np.log1p(R), axis=1)       # settore «mediano» di ogni anno, come riferimento del caso tipico
    curve["settore_mediano"] = fx.curva_capitale(np.expm1(mediana_lr), config.CAPITALE_INIZIALE)
    curve.to_csv(config.RISULTATI / "curve_capitale.csv", index=False, float_format="%.2f")
    pd.DataFrame({"cagr": scim}).to_csv(config.RISULTATI / "scimmie.csv", index=False, float_format="%.6f")
    pd.DataFrame({"cagr_copia_scimmie": scim_c}).to_csv(config.RISULTATI / "scimmie_stessi_anni_copia.csv", index=False, float_format="%.6f")
    pd.DataFrame(righe_f).to_csv(config.RISULTATI / "frequenze.csv", index=False, float_format="%.4f")
    pd.DataFrame([{"ticker": t, "nome": nomi[t], "cagr": cagr_set[t], "anni_migliore": int(conta[i])} for i, t in enumerate(tick)]).to_csv(
        config.RISULTATI / "settori.csv", index=False, float_format="%.5f")
    reg("cagr_bh_nomi", "; ".join(f"{nomi[t]} {cagr_set[t]*100:.1f}%".replace(".", ",") for t in tick), "testo", "Rendimento annuo composto di ciascun settore buy & hold", "settori.csv")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    (config.RISULTATI / "indici_usati.json").write_text(json.dumps({"settori": tick, "benchmark": config.BENCHMARK[0]}, indent=1), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
