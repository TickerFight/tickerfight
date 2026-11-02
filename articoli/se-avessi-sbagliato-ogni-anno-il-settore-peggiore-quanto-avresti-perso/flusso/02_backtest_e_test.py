"""Passo 2 - Il settore peggiore con il senno di poi: confronto con l'indice, il caso e la regola realizzabile.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json        ogni numero dell'articolo, con descrizione e origine di calcolo
  anni.csv             per anno: settore peggiore, suo rendimento, rendimento di SPY, perdente dell'anno prima e suo rendimento
  curve_capitale.csv   capitale (da 10.000) anno per anno: peggiore con senno di poi, SPY, regola realizzabile, media dei settori
  scimmie.csv          rendimento annuo composto di ciascuna scimmia
  frequenze.csv        scelta del peggiore con senno di poi ogni anno, trimestre, mese
  settori.csv          per settore: rendimento annuo composto e numero di anni da peggiore
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
    idx, pegg = fx.peggiore_ex_post(R)
    cagr_pegg = fx.cagr(pegg, T)
    cagr_spy = fx.cagr(spy, T)
    eq = R.mean(axis=1)
    cagr_eq = fx.cagr(eq, T)
    cagr_set = {t: fx.cagr(R[:, i], T) for i, t in enumerate(tick)}
    miglior_set = max(cagr_set, key=cagr_set.get)
    peggior_set = min(cagr_set, key=cagr_set.get)
    _, best = fx.migliore_ex_post(R)
    cagr_best = fx.cagr(best, T)

    reg("prima_anno", a1, "annonum", "Primo anno solare del confronto", "config.py, ANNO_INIZIO")
    reg("ultima_anno", a2, "annonum", "Ultimo anno solare del confronto", "config.py, ANNO_FINE")
    reg("n_anni", T, "int", "Anni solari completi del confronto", "dati/")
    reg("n_settori", len(tick), "int", "Settori (ETF SPDR) usati", "config.py, SETTORI")
    reg("data_scarico", META["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("capitale_iniziale", config.CAPITALE_INIZIALE, "int", "Capitale di partenza (dollari)", "config.py, CAPITALE_INIZIALE")
    reg("cagr_pegg", cagr_pegg, "pct1", "Rendimento annuo composto scegliendo ogni anno il settore peggiore con il senno di poi")
    reg("cagr_best", cagr_best, "pct1", "Rendimento annuo composto scegliendo ogni anno il settore migliore con il senno di poi (specchio, articolo 523)")
    reg("cagr_spy", cagr_spy, "pct1", "Rendimento annuo composto dell'S&P 500 (SPY, dividendi reinvestiti), buy & hold")
    reg("cagr_media_settori", cagr_eq, "pct1", "Rendimento annuo composto della media dei nove settori ribilanciata ogni anno")
    reg("miglior_settore_bh", nomi[miglior_set], "testo", "Settore col miglior rendimento annuo composto tenuto per tutto il periodo")
    reg("miglior_settore_bh_cagr", cagr_set[miglior_set], "pct1", "Rendimento annuo composto di quel settore buy & hold")
    reg("peggior_settore_bh", nomi[peggior_set], "testo", "Settore col peggior rendimento annuo composto tenuto per tutto il periodo")
    reg("peggior_settore_bh_cagr", cagr_set[peggior_set], "pct1", "Rendimento annuo composto di quel settore buy & hold")
    reg("distanza_spy_pp", cagr_spy - cagr_pegg, "pp1", "Distacco annuo (punti percentuali) dell'S&P 500 sulla scelta del peggiore")
    reg("distanza_spy_pegg_bh_pp", cagr_set[peggior_set] - cagr_pegg, "pp1", "Rendimento annuo del peggior settore tenuto fermo meno quello della scelta del peggiore ogni anno (punti)")
    cap_pegg = fx.curva_capitale(pegg, config.CAPITALE_INIZIALE)
    cap_spy = fx.curva_capitale(spy, config.CAPITALE_INIZIALE)
    reg("cap_pegg", cap_pegg[-1], "int", "Capitale finale (lordo) della scelta del peggiore con il senno di poi, partendo dal capitale iniziale")
    reg("cap_spy", cap_spy[-1], "int", "Capitale finale (lordo) dell'S&P 500 (SPY), partendo dal capitale iniziale")
    reg("cap_rapporto", cap_spy[-1] / cap_pegg[-1], "int", "Rapporto tra capitale finale dell'S&P 500 e quello della scelta del peggiore")
    reg("perdita_pegg", 1 - cap_pegg[-1] / config.CAPITALE_INIZIALE, "pct0", "Quota del capitale iniziale persa (lordo) dalla scelta del peggiore")
    reg("pegg_mediano", float(np.median(pegg)), "pct0", "Rendimento mediano annuo del settore peggiore")
    reg("pegg_max", float(pegg.max()), "pct0", "Rendimento del settore peggiore nell'anno in cui è andato meglio")
    reg("pegg_max_anno", str(anni_lista[int(pegg.argmax())]), "testo", "Anno in cui il settore peggiore è andato meglio", "anni.csv")
    reg("pegg_min", float(pegg.min()), "pct0", "Rendimento del settore peggiore nell'anno in cui è andato peggio")
    reg("pegg_min_anno", str(anni_lista[int(pegg.argmin())]), "testo", "Anno in cui il settore peggiore è andato peggio", "anni.csv")
    reg("pegg_min_nome", nomi[tick[int(idx[pegg.argmin()])]], "testo", "Settore peggiore nell'anno record negativo", "anni.csv")
    reg("spy_mediano", float(np.median(spy)), "pct0", "Rendimento mediano annuo dell'S&P 500 (SPY)")
    guadagni = [(anni_lista[t], nomi[tick[idx[t]]], pegg[t]) for t in range(T) if pegg[t] > 0]
    reg("n_anni_pegg_guadagna", len(guadagni), "int", "Anni in cui anche il settore peggiore ha chiuso in guadagno", "anni.csv")
    reg("anni_pegg_guadagna", ", ".join(str(p[0]) for p in guadagni) if guadagni else "nessuno", "testo", "Quali anni", "anni.csv")
    reg("n_anni_pegg_sotto_10", int((pegg < -0.10).sum()), "int", "Anni in cui il settore peggiore ha perso più del 10%", "anni.csv")
    n_dist = len(set(idx.tolist()))
    reg("n_settori_perdenti", n_dist, "int", "Settori diversi che sono stati i peggiori almeno una volta", "anni.csv")
    conta = np.bincount(idx, minlength=len(tick))
    top = int(conta.argmax())
    reg("settore_piu_perdente", nomi[tick[top]], "testo", "Settore che è stato il peggiore più volte", "anni.csv")
    reg("settore_piu_perdente_n", int(conta[top]), "int", "Quante volte", "anni.csv")
    reg("anni_spy_batte_pegg", int((spy > pegg).sum()), "int", "Anni in cui l'S&P 500 ha battuto il settore peggiore", "anni.csv")
    reg("anni_spy_perde_pegg", int((spy < pegg).sum()), "int", "Anni in cui l'S&P 500 ha fatto peggio del settore peggiore", "anni.csv")

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
    p_pegg = (1 + np.sum(scim <= cagr_pegg)) / (1 + config.N_SCIMMIE)
    reg("n_scimmie_peggio_pegg", int((scim <= cagr_pegg).sum()), "int", "Scimmie che fanno peggio o uguale alla scelta del peggiore con il senno di poi")

    # ---------------- regola realizzabile: compra il perdente dell'anno prima ----------------
    copia = fx.perdente_precedente(R)
    Tc = len(copia)
    cagr_copia = fx.cagr(copia, Tc)
    scim_c = fx.scimmie(R[1:], config.N_SCIMMIE, Tc, rng)
    cagr_spy_c = fx.cagr(spy[1:], Tc)
    p_alto = (1 + np.sum(scim_c >= cagr_copia)) / (1 + config.N_SCIMMIE)
    p_basso = (1 + np.sum(scim_c <= cagr_copia)) / (1 + config.N_SCIMMIE)
    p_copia = min(1.0, 2 * min(p_alto, p_basso))     # bilaterale
    h = fx.holm({"pegg": p_pegg, "copia": p_copia})
    reg("n_anni_copia", Tc, "int", "Anni della regola «compra il perdente dell'anno prima» (il primo anno non ha un anno prima)")
    reg("cagr_copia", cagr_copia, "pct1", "Rendimento annuo composto della regola «compra il perdente dell'anno prima»")
    reg("cagr_spy_copia", cagr_spy_c, "pct1", "Rendimento annuo composto dell'S&P 500 sugli stessi anni")
    reg("copia_vs_spy_pp", cagr_copia - cagr_spy_c, "pp1", "Differenza annua (punti) della regola realizzabile sull'S&P 500, stessi anni")
    reg("copia_vs_spy_pp_abs", abs(cagr_copia - cagr_spy_c), "pp1", "Scarto assoluto annuo (punti) della regola realizzabile dall'S&P 500, stessi anni")
    reg("copia_batte_scimmie", float(np.mean(scim_c < cagr_copia)), "pct0", "Quota di scimmie (stessi anni) battute dalla regola realizzabile")
    reg("copia_anni_vinti_spy", int((copia > spy[1:]).sum()), "int", "Anni in cui la regola realizzabile batte l'S&P 500")
    reg("p_pegg_grezzo", p_pegg, "pval", "p-value (non corretto): scimmie con rendimento pari o inferiore alla scelta del peggiore")
    reg("p_copia_grezzo", p_copia, "pval", "p-value bilaterale (non corretto): regola realizzabile contro le scimmie")
    reg("p_pegg_holm", h["pegg"], "pval", "p-value corretto per Holm, scelta del peggiore")
    reg("p_copia_holm", h["copia"], "pval", "p-value corretto per Holm, regola realizzabile")
    reg("n_test_holm", 2, "int", "Test corretti con Holm (scelta del peggiore e regola realizzabile contro le scimmie)")
    rango = fx.rango_perdente_precedente(R)
    reg("rango_mediano", float(np.median(rango)), "num1", "Posizione mediana (1 = migliore, 9 = peggiore) nell'anno dopo del settore che ha perso di più l'anno prima")
    reg("rango_medio", float(rango.mean()), "num1", "Posizione media nell'anno dopo del perdente dell'anno prima (il caso darebbe 5,0)")
    reg("perde_ancora", int((rango == len(tick)).sum()), "int", "Volte in cui il perdente dell'anno prima perde ancora di più degli altri l'anno dopo")
    reg("vince_dopo", int((rango == 1).sum()), "int", "Volte in cui il perdente dell'anno prima è il migliore l'anno dopo")
    reg("rango_atteso", (len(tick) + 1) / 2, "num1", "Posizione media attesa col solo caso: (nove settori + 1) / 2")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello della fascia delle scimmie", "config.py, LIVELLO_CONFIDENZA")
    reg("perde_ancora_atteso", Tc / len(tick), "num1", "Volte attese col solo caso (anni diviso nove settori)")

    # ---------------- frequenze: anno, trimestre, mese ----------------
    righe_f = []
    cap_per_freq = {}
    for nome_f, alias in config.FREQUENZE.items():
        rf = fx.rendimenti_periodo(prezzi, alias, a1, a2)
        Rf = rf[tick].values
        _, bf = fx.peggiore_ex_post(Rf)
        cap = config.CAPITALE_INIZIALE * float(np.prod(1 + bf))
        cap_per_freq[nome_f] = cap
        righe_f.append({"frequenza": nome_f, "n_periodi": len(bf), "cagr": fx.cagr(bf, T), "capitale_finale": cap})
        reg(f"cap_{nome_f}", cap, "num4" if nome_f == "mese" else "num2", f"Capitale finale (lordo, dollari) scegliendo con il senno di poi il settore peggiore ogni {nome_f}")
        reg(f"cagr_{nome_f}", fx.cagr(bf, T), "pct0", f"Rendimento annuo composto scegliendo con il senno di poi il peggiore ogni {nome_f}")
        reg(f"n_periodi_{nome_f}", len(bf), "int", f"Numero di scelte fatte ({nome_f})")
        reg(f"pegg_medio_{nome_f}", float(bf.mean()), "pct1", f"Rendimento medio del settore peggiore in un {nome_f}")
    reg("frazione_mese_su_anno", cap_per_freq["mese"] / cap_per_freq["anno"], "num6", "Capitale finale mensile diviso quello annuale (peggiore con senno di poi)")
    reg("perdita_mese", 1 - cap_per_freq["mese"] / config.CAPITALE_INIZIALE, "pct2", "Quota del capitale iniziale persa scegliendo il peggiore ogni mese")

    # ---------------- netto di costi e tasse ----------------
    net_pegg, tasse_pegg = fx.capitale_netto_rotazione(pegg, config.CAPITALE_INIZIALE, config.COSTO_ORDINE, config.TASSA)
    net_pegg_senza, _ = fx.capitale_netto_rotazione(pegg, config.CAPITALE_INIZIALE, config.COSTO_ORDINE, 0.0)
    net_spy = fx.capitale_netto_buy_hold(spy, config.CAPITALE_INIZIALE, config.COSTO_ORDINE, config.TASSA)
    reg("costo_ordine", config.COSTO_ORDINE, "pct1", "Costo per ogni acquisto e ogni vendita", "config.py, COSTO_ORDINE")
    reg("tassa", config.TASSA, "pct0", "Tassa sulle plusvalenze", "config.py, TASSA")
    reg("net_pegg", net_pegg, "int", "Capitale finale netto (costi e tasse) della rotazione annuale del peggiore")
    reg("net_pegg_senza_tasse", net_pegg_senza, "int", "Capitale finale con i soli costi (tassa a zero) della rotazione annuale del peggiore")
    reg("net_spy", net_spy, "int", "Capitale finale netto (costi e tasse) dell'S&P 500 buy & hold")
    reg("tasse_pegg", tasse_pegg, "int", "Tasse pagate in tutto dalla rotazione annuale del peggiore (dollari)")
    reg("tasse_pegg_frazione", tasse_pegg / config.CAPITALE_INIZIALE, "pct1", "Tasse pagate in tutto, in quota del capitale iniziale")
    reg("net_frazione", net_pegg / cap_pegg[-1], "pct0", "Quota del capitale lordo che resta dopo costi e tasse (peggiore)")
    reg("net_frazione_spy", net_spy / cap_spy[-1], "pct0", "Quota del capitale lordo che resta dopo costi e tasse (S&P 500)")
    reg("net_cagr_pegg", float((net_pegg / config.CAPITALE_INIZIALE) ** (1 / T) - 1), "pct1", "Rendimento annuo composto netto della scelta del peggiore")
    reg("net_cagr_spy", float((net_spy / config.CAPITALE_INIZIALE) ** (1 / T) - 1), "pct1", "Rendimento annuo composto netto dell'S&P 500")

    # ---------------- soglie ----------------
    for k, f, d in (("ip1_pp", "int", "Soglia ipotesi 1: distacco annuo (punti) dall'S&P 500"),
                    ("ip2_quota", "pct0", "Soglia ipotesi 2: quota di scimmie che battono l'indice"),
                    ("ip3_perc", "pct0", "Soglia ipotesi 3: quota massima di scimmie che fanno peggio del peggiore"),
                    ("ip4_pp", "int", "Soglia ipotesi 4: scarto massimo (punti) della regola realizzabile"),
                    ("ip5_frazione", "pct0", "Soglia ipotesi 5: frazione del capitale annuale che resta con la scelta mensile"),
                    ("ip6_tasse", "pct0", "Soglia ipotesi 6: tasse massime in quota del capitale iniziale"),
                    ("ip8_lo", "int", "Soglia ipotesi 8: estremo basso della posizione mediana"),
                    ("ip8_hi", "int", "Soglia ipotesi 8: estremo alto della posizione mediana"),
                    ("alfa", "num2", "Soglia di significatività dopo Holm")):
        reg(f"s_{k}", S[k], f, d, "config.py, SOGLIE")

    # ---------------- tabelle ----------------
    anni_df = pd.DataFrame({"anno": anni_lista, "settore_peggiore": [tick[i] for i in idx], "rendimento_peggiore": pegg,
                            "rendimento_spy": spy, "media_settori": eq})
    anni_df["perdente_anno_prima"] = [""] + [tick[i] for i in idx[:-1]]
    anni_df["rendimento_perdente_anno_prima"] = [np.nan] + list(copia)
    anni_df["rango_perdente_anno_prima"] = [np.nan] + list(rango)
    anni_df.to_csv(config.RISULTATI / "anni.csv", index=False, float_format="%.5f")
    curve = pd.DataFrame({"anno": anni_lista, "peggiore_senno_di_poi": cap_pegg, "spy": cap_spy,
                          "media_settori": fx.curva_capitale(eq, config.CAPITALE_INIZIALE)})
    curve["regola_realizzabile"] = [np.nan] + list(fx.curva_capitale(copia, config.CAPITALE_INIZIALE))
    curve.to_csv(config.RISULTATI / "curve_capitale.csv", index=False, float_format="%.2f")
    pd.DataFrame({"cagr": scim}).to_csv(config.RISULTATI / "scimmie.csv", index=False, float_format="%.6f")
    pd.DataFrame({"cagr_copia_scimmie": scim_c}).to_csv(config.RISULTATI / "scimmie_stessi_anni_copia.csv", index=False, float_format="%.6f")
    pd.DataFrame(righe_f).to_csv(config.RISULTATI / "frequenze.csv", index=False, float_format="%.6g")
    pd.DataFrame([{"ticker": t, "nome": nomi[t], "cagr": cagr_set[t], "anni_peggiore": int(conta[i])} for i, t in enumerate(tick)]).to_csv(
        config.RISULTATI / "settori.csv", index=False, float_format="%.5f")
    reg("cagr_bh_nomi", "; ".join(f"{nomi[t]} {cagr_set[t]*100:.1f}%".replace(".", ",") for t in tick), "testo", "Rendimento annuo composto di ciascun settore buy & hold", "settori.csv")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    (config.RISULTATI / "indici_usati.json").write_text(json.dumps({"settori": tick, "benchmark": config.BENCHMARK[0]}, indent=1), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
