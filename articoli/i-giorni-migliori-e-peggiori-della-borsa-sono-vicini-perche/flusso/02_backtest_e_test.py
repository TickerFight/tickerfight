"""Passo 2 - Giorni migliori e peggiori vicini: distanze, caso, volatilità, filtro.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json            ogni numero dell'articolo, con descrizione e origine di calcolo
  curva_distanza.csv       S&P 500: quota di giorni peggiori con un giorno migliore entro d sedute (vera, caso medio, fascia 95%)
  quintili.csv             quota di giorni estremi in ciascun quinto di volatilità di ieri, per indice
  anni_estremi.csv         numero di giorni estremi per indice e anno
  estremi_sp500.csv        i dieci giorni peggiori e i dieci migliori dell'S&P 500
  filtro.csv               rendimento annuo composto di buy & hold, filtro e scimmie, per indice
  scimmie_sp500.csv        rendimento annuo composto di ciascuna scimmia (S&P 500)
  indici_usati.json        indici effettivamente usati
Nessun look-ahead: la volatilità usata per la seduta t contiene solo rendimenti fino a t-1.
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


def slug(ticker: str) -> str:
    return ticker.replace("^", "").replace(".", "_").lower()


def massimo_calo(r: np.ndarray) -> float:
    v = np.cumprod(1 + r)
    return float((v / np.maximum.accumulate(v) - 1).min())


def nulla(serie: np.ndarray, anni: np.ndarray, n: int, rng, griglia=None):
    """Statistiche di n storie rimescolate della serie."""
    med, qpm, qmp, atop = (np.empty(n) for _ in range(4))
    curva = np.empty((n, len(griglia))) if griglia is not None else None
    for k in range(n):
        q = rng.permutation(serie)
        s = fx.statistiche_vicinanza(q, config.QUOTA_ESTREMI, config.FINESTRA_VICINO)
        med[k], qpm[k], qmp[k] = s["mediana_peggiori_migliori"], s["quota_peggiori_con_migliore"], s["quota_migliori_con_peggiore"]
        atop[k] = fx.quota_anni_top(q, anni, config.QUOTA_ESTREMI, config.N_ANNI_TOP)
        if curva is not None:
            pe, mi = fx.posizioni_estreme(q, config.QUOTA_ESTREMI)
            d = np.sort(fx.distanza_vicino(pe, mi))
            curva[k] = np.searchsorted(d, griglia, side="right") / len(d)
    return med, qpm, qmp, atop, curva


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    META = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    rng = np.random.default_rng(config.SEME)
    a = (1 - config.LIVELLO_CONFIDENZA) / 2
    usati, righe_quint, righe_anni, righe_filtro = [], [], [], []
    p_grezzi: dict[str, float] = {}
    griglia = np.unique(np.round(np.geomspace(1, 500, 60)).astype(int))

    for ticker, nome, valuta in config.INDICI:
        f = config.file_dati(ticker)
        if not f.exists():
            print(f"{ticker}: file mancante, indice scartato")
            continue
        s = slug(ticker)
        df = pd.read_csv(f, index_col=0, parse_dates=True)
        rs = fx.rendimenti(df["Close"])
        r = rs.values.astype(float)
        date = rs.index
        anni = date.year.values
        n = len(r)
        usati.append({"ticker": ticker, "slug": s, "nome": nome, "valuta": valuta, "prima": str(date[0].date()), "ultima": str(date[-1].date()), "n": n})
        reg(f"{s}_nome", nome.split(" (")[0], "testo", f"Nome dell'indice {ticker}", "config.py, INDICI")
        reg(f"{s}_prima_data", str(date[0].date()), "data_lunga", f"Primo rendimento giornaliero di {nome}", "dati/")
        reg(f"{s}_prima_anno", str(date[0].date()), "anno", f"Anno del primo rendimento di {nome}", "dati/")
        reg(f"{s}_ultima_data", str(date[-1].date()), "data_lunga", f"Ultimo rendimento giornaliero di {nome}", "dati/")
        reg(f"{s}_n_sedute", n, "int", f"Sedute (rendimenti giornalieri) di {nome}", "dati/")

        # ---- vicinanza dei giorni estremi: dati veri contro storie rimescolate ----
        pe, mi = fx.posizioni_estreme(r, config.QUOTA_ESTREMI)
        k = len(pe)
        reg(f"{s}_n_estremi", k, "int", f"Giorni peggiori (e altrettanti migliori) di {nome}: l'1% delle sedute")
        vero = fx.statistiche_vicinanza(r, config.QUOTA_ESTREMI, config.FINESTRA_VICINO)
        med0, qpm0 = vero["mediana_peggiori_migliori"], vero["quota_peggiori_con_migliore"]
        qmp0 = vero["quota_migliori_con_peggiore"]
        atop0 = fx.quota_anni_top(r, anni, config.QUOTA_ESTREMI, config.N_ANNI_TOP)
        principale = ticker == config.INDICE_PRINCIPALE
        med, qpm, qmp, atop, curva = nulla(r, anni, config.N_RIMESCOLATE, rng, griglia if principale else None)
        reg(f"{s}_med_dist", med0, "num1", f"Distanza mediana (sedute) tra un giorno peggiore e il giorno migliore più vicino, {nome}")
        reg(f"{s}_null_med_dist", float(med.mean()), "num1", f"Stessa distanza mediana, media delle storie rimescolate, {nome}")
        reg(f"{s}_quota_pm", qpm0, "pct0", f"Quota di giorni peggiori con un giorno migliore entro {config.FINESTRA_VICINO} sedute, {nome}")
        reg(f"{s}_null_quota_pm", float(qpm.mean()), "pct0", f"Stessa quota, media delle storie rimescolate, {nome}")
        reg(f"{s}_null_quota_pm_lo", float(np.quantile(qpm, a)), "pct0", f"Stessa quota, estremo basso della fascia 95% delle storie rimescolate, {nome}")
        reg(f"{s}_null_quota_pm_hi", float(np.quantile(qpm, 1 - a)), "pct0", f"Stessa quota, estremo alto della fascia 95% delle storie rimescolate, {nome}")
        reg(f"{s}_rapporto_pm", qpm0 / qpm.mean(), "num1", f"Rapporto tra quota vera e quota media del caso (giorni peggiori con un migliore vicino), {nome}")
        reg(f"{s}_quota_mp", qmp0, "pct0", f"Quota di giorni migliori con un giorno peggiore entro {config.FINESTRA_VICINO} sedute, {nome}")
        reg(f"{s}_null_quota_mp", float(qmp.mean()), "pct0", f"Stessa quota, media delle storie rimescolate, {nome}")
        p_med = (1 + np.sum(med <= med0)) / (1 + config.N_RIMESCOLATE)
        p_grezzi[f"{s}_raw"] = p_med
        reg(f"{s}_p_med_grezzo", p_med, "pval", f"p-value (non corretto): quante storie rimescolate hanno una distanza mediana pari o minore, {nome}")
        reg(f"{s}_anni_top_quota", atop0, "pct0", f"Quota dei giorni estremi che cade nei {config.N_ANNI_TOP} anni con più giorni estremi, {nome}")
        reg(f"{s}_null_anni_top_quota", float(atop.mean()), "pct0", f"Stessa quota, media delle storie rimescolate, {nome}")
        reg(f"{s}_quota_consecutivi", float(np.mean(fx.distanza_vicino(pe, mi) <= 1)), "pct0", f"Quota di giorni peggiori con un giorno migliore nella seduta prima o dopo, {nome}")
        if principale:
            curva_df = pd.DataFrame({"d": griglia, "vera": [np.mean(fx.distanza_vicino(pe, mi) <= d) for d in griglia],
                                     "caso_media": curva.mean(axis=0), "caso_lo": np.quantile(curva, a, axis=0),
                                     "caso_hi": np.quantile(curva, 1 - a, axis=0)})
            curva_df.to_csv(config.RISULTATI / "curva_distanza.csv", index=False, float_format="%.5f")

        # ---- anni con più giorni estremi ----
        tutti = np.concatenate([pe, mi])
        per_anno = pd.DataFrame({"anno": anni[tutti], "tipo": ["peggiore"] * k + ["migliore"] * k})
        tab = per_anno.groupby(["anno", "tipo"]).size().unstack(fill_value=0)
        for c in ("peggiore", "migliore"):
            if c not in tab:
                tab[c] = 0
        tab = tab.reindex(range(int(anni.min()), int(anni.max()) + 1), fill_value=0)
        for anno, rr in tab.iterrows():
            righe_anni.append({"ticker": ticker, "anno": int(anno), "peggiori": int(rr["peggiore"]), "migliori": int(rr["migliore"])})
        tot_anno = tab.sum(axis=1)
        reg(f"{s}_anno_max", str(int(tot_anno.idxmax())), "testo", f"Anno con più giorni estremi, {nome}", "anni_estremi.csv")
        reg(f"{s}_anno_max_n", int(tot_anno.max()), "int", f"Giorni estremi nell'anno che ne ha di più, {nome}", "anni_estremi.csv")
        reg(f"{s}_anni_senza", int((tot_anno == 0).sum()), "int", f"Anni senza nessun giorno estremo, {nome}", "anni_estremi.csv")
        reg(f"{s}_anni_totali", int(len(tot_anno)), "int", f"Anni di dati, {nome}", "anni_estremi.csv")

        # ---- rendimenti standardizzati per la volatilità di ieri ----
        sig = fx.vol_ewma_ieri(r, config.LAMBDA_EWMA, config.RODAGGIO)
        z = (r / sig)[config.RODAGGIO:]
        anni_z = anni[config.RODAGGIO:]
        vz = fx.statistiche_vicinanza(z, config.QUOTA_ESTREMI, config.FINESTRA_VICINO)
        _, qpm_z, _, _, _ = nulla(z, anni_z, config.N_RIMESCOLATE, rng)
        reg(f"{s}_z_quota_pm", vz["quota_peggiori_con_migliore"], "pct0", f"Come {s}_quota_pm, ma sui rendimenti divisi per la volatilità di ieri, {nome}")
        reg(f"{s}_z_null_quota_pm", float(qpm_z.mean()), "pct0", f"Stessa quota standardizzata, media delle storie rimescolate, {nome}")
        rap_z = vz["quota_peggiori_con_migliore"] / qpm_z.mean()
        reg(f"{s}_z_rapporto_pm", rap_z, "num1", f"Rapporto vero/caso dopo la standardizzazione, {nome}")
        p_z = (1 + np.sum(qpm_z >= vz["quota_peggiori_con_migliore"])) / (1 + config.N_RIMESCOLATE)
        p_grezzi[f"{s}_z"] = p_z
        reg(f"{s}_z_p_grezzo", p_z, "pval", f"p-value (non corretto) della vicinanza dopo la standardizzazione, {nome}")
        ecc_raw = qpm0 / qpm.mean() - 1
        ecc_z = rap_z - 1
        reg(f"{s}_eccesso_raw", ecc_raw, "num2", f"Eccesso di vicinanza sul caso (rapporto meno uno), dati grezzi, {nome}")
        reg(f"{s}_eccesso_z", ecc_z, "num2", f"Eccesso di vicinanza sul caso (rapporto meno uno), dati standardizzati, {nome}")
        reg(f"{s}_eccesso_spiegato", 1 - ecc_z / ecc_raw, "pct0", f"Quota dell'eccesso di vicinanza che sparisce standardizzando, {nome}")

        # ---- volatilità di ieri (deviazione standard delle ultime sedute) ----
        vol = fx.vol_mobile_ieri(r, config.FINESTRA_VOL)
        qp = fx.quote_per_quintile(vol, pe)
        qm = fx.quote_per_quintile(vol, mi)
        qt = fx.quote_per_quintile(vol, np.concatenate([pe, mi]))
        for j in range(5):
            righe_quint.append({"ticker": ticker, "quinto": j + 1, "peggiori": qp[j], "migliori": qm[j], "tutti": qt[j]})
        reg(f"{s}_q_peggiori_top", float(qp[4]), "pct0", f"Quota dei giorni peggiori nel quinto di sedute con volatilità di ieri più alta, {nome}")
        reg(f"{s}_q_migliori_top", float(qm[4]), "pct0", f"Quota dei giorni migliori nel quinto con volatilità di ieri più alta, {nome}")
        reg(f"{s}_q_estremi_top", float(qt[4]), "pct0", f"Quota dei giorni estremi nel quinto con volatilità di ieri più alta, {nome}")
        reg(f"{s}_q_estremi_bassa", float(qt[0]), "pct0", f"Quota dei giorni estremi nel quinto con volatilità di ieri più bassa, {nome}")

        # ---- il filtro ----
        liq = fx.segnale_filtro(r, config.FINESTRA_FILTRO, config.PERCENTILE_FILTRO, config.STORIA_MINIMA)
        sel = slice(config.STORIA_MINIMA, None)
        r_p, liq_p = r[sel], liq[sel]
        anni_cal = (date[-1] - date[config.STORIA_MINIMA]).days / 365.25
        in_per = lambda pos: pos[pos >= config.STORIA_MINIMA] - config.STORIA_MINIMA
        ev_pe = float(np.mean(liq_p[in_per(pe)]))
        ev_mi = float(np.mean(liq_p[in_per(mi)]))
        lordo = np.where(liq_p, 0.0, r_p)
        netto = fx.rendimenti_filtro(r_p, liq_p, config.COSTO_CAMBIO)
        c_bh, c_l, c_n = fx.cagr(r_p, anni_cal), fx.cagr(lordo, anni_cal), fx.cagr(netto, anni_cal)
        scim = fx.cagr_scimmie(r_p, int(liq_p.sum()), anni_cal, config.N_SCIMMIE, rng)
        reg(f"{s}_filtro_quota_liq", float(liq_p.mean()), "pct0", f"Quota di sedute in liquidità con il filtro, {nome}")
        reg(f"{s}_filtro_cambi", int(np.sum(liq_p[1:] != liq_p[:-1])), "int", f"Passaggi tra mercato e liquidità, {nome}")
        reg(f"{s}_evitati_peggiori", ev_pe, "pct0", f"Quota dei giorni peggiori evitati dal filtro (in liquidità quel giorno), {nome}")
        reg(f"{s}_evitati_migliori", ev_mi, "pct0", f"Quota dei giorni migliori evitati dal filtro, {nome}")
        reg(f"{s}_rapporto_evitati", ev_pe / ev_mi if ev_mi > 0 else 99.0, "num2", f"Rapporto tra quota di peggiori evitati e di migliori evitati, {nome}")
        reg(f"{s}_cagr_bh", c_bh, "pct2", f"Rendimento annuo composto del buy & hold (indice di prezzo, dalla storia minima), {nome}")
        reg(f"{s}_cagr_filtro", c_l, "pct2", f"Rendimento annuo composto del filtro senza costi, {nome}")
        reg(f"{s}_cagr_filtro_netto", c_n, "pct2", f"Rendimento annuo composto del filtro con costo di {config.COSTO_CAMBIO * 100:.1f}% a ogni passaggio, {nome}")
        reg(f"{s}_diff_pp", (c_l - c_bh) * 100, "num2", f"Filtro senza costi meno buy & hold, punti percentuali di rendimento annuo, {nome}")
        reg(f"{s}_diff_netto_pp", (c_n - c_bh) * 100, "num2", f"Filtro con costi meno buy & hold, punti percentuali, {nome}")
        reg(f"{s}_scimmie_mediana", float(np.median(scim)), "pct2", f"Rendimento annuo composto della scimmia mediana (stesse sedute fuori), {nome}")
        reg(f"{s}_scimmie_battute", float(np.mean(c_l > scim)), "pct1", f"Quota di scimmie battute dal filtro senza costi, {nome}")
        reg(f"{s}_scimmie_battute_netto", float(np.mean(c_n > scim)), "pct1", f"Quota di scimmie battute dal filtro con costi, {nome}")
        reg(f"{s}_vol_bh", float(r_p.std() * np.sqrt(252)), "pct1", f"Volatilità annua del buy & hold, {nome}")
        reg(f"{s}_vol_filtro", float(lordo.std() * np.sqrt(252)), "pct1", f"Volatilità annua del filtro, {nome}")
        reg(f"{s}_dd_bh", massimo_calo(r_p), "pct0", f"Massimo calo dal picco del buy & hold, {nome}")
        reg(f"{s}_dd_filtro", massimo_calo(lordo), "pct0", f"Massimo calo dal picco del filtro, {nome}")
        righe_filtro.append({"ticker": ticker, "cagr_bh": c_bh, "cagr_filtro": c_l, "cagr_filtro_netto": c_n, "scimmie_mediana": float(np.median(scim))})
        if principale:
            pd.DataFrame({"cagr": scim}).to_csv(config.RISULTATI / "scimmie_sp500.csv", index=False, float_format="%.6f")
            reg(f"{s}_n_fuori", int(liq_p.sum()), "int", f"Sedute in liquidità del filtro, {nome}")
            reg(f"{s}_anni_filtro", anni_cal, "num1", f"Anni del periodo di confronto del filtro, {nome}")
            # i giorni più estremi
            ordine = np.argsort(r)
            righe = [{"tipo": "peggiore", "data": str(date[i].date()), "rendimento": r[i]} for i in ordine[:10]]
            righe += [{"tipo": "migliore", "data": str(date[i].date()), "rendimento": r[i]} for i in ordine[::-1][:10]]
            pd.DataFrame(righe).to_csv(config.RISULTATI / "estremi_sp500.csv", index=False, float_format="%.5f")
            i_p, i_m = ordine[0], ordine[-1]
            reg(f"{s}_peggiore_data", str(date[i_p].date()), "data_lunga", f"Data del giorno peggiore di sempre, {nome}")
            reg(f"{s}_peggiore_ret", r[i_p], "pct1", f"Rendimento del giorno peggiore, {nome}")
            reg(f"{s}_migliore_data", str(date[i_m].date()), "data_lunga", f"Data del giorno migliore di sempre, {nome}")
            reg(f"{s}_migliore_ret", r[i_m], "pct1", f"Rendimento del giorno migliore, {nome}")
            d_pe = fx.distanza_vicino(np.array([i_p]), mi)[0]
            j = mi[np.argmin(np.abs(mi - i_p))]
            reg(f"{s}_peggiore_dist", int(d_pe), "int", f"Sedute tra il giorno peggiore e il giorno migliore (tra l'1% migliori) più vicino, {nome}")
            reg(f"{s}_peggiore_vicino_data", str(date[j].date()), "data_lunga", f"Data di quel giorno migliore vicino, {nome}")
            reg(f"{s}_peggiore_vicino_ret", r[j], "pct1", f"Rendimento di quel giorno migliore vicino, {nome}")
            reg(f"{s}_soglia_peggiori", float(np.sort(r)[k - 1]), "pct1", f"Rendimento sotto il quale una seduta è tra l'1% peggiore, {nome}")
            reg(f"{s}_soglia_migliori", float(np.sort(r)[-k]), "pct1", f"Rendimento sopra il quale una seduta è tra l'1% migliore, {nome}")

    # ---- correzione di Holm sui test (indici x due versioni) ----
    holm = fx.holm(p_grezzi)
    for chiave, v in holm.items():
        reg(f"{chiave.rsplit('_', 1)[0]}_p_holm_{chiave.rsplit('_', 1)[1]}", v, "pval", f"p-value corretto per Holm ({chiave})")
    reg("n_test_holm", len(p_grezzi), "int", "Test corretti con Holm (indici per due versioni dei dati)")
    reg("n_indici", len(usati), "int", "Indici usati", "config.py, INDICI")
    reg("quota_estremi", config.QUOTA_ESTREMI, "pct0", "Quota di sedute definite giorni estremi, per lato", "config.py, QUOTA_ESTREMI")
    reg("finestra", config.FINESTRA_VICINO, "int", "Finestra (sedute) che definisce «vicino»", "config.py, FINESTRA_VICINO")
    reg("n_top_anni", config.N_ANNI_TOP, "int", "Numero di anni con più giorni estremi", "config.py, N_ANNI_TOP")
    reg("lambda_ewma", config.LAMBDA_EWMA, "num2", "Parametro della volatilità EWMA", "config.py, LAMBDA_EWMA")
    reg("finestra_vol", config.FINESTRA_VOL, "int", "Sedute della volatilità usata per i quintili", "config.py, FINESTRA_VOL")
    reg("finestra_filtro", config.FINESTRA_FILTRO, "int", "Sedute della volatilità usata dal filtro", "config.py, FINESTRA_FILTRO")
    reg("percentile_filtro", config.PERCENTILE_FILTRO, "pct0", "Percentile della soglia del filtro", "config.py, PERCENTILE_FILTRO")
    reg("storia_minima", config.STORIA_MINIMA, "int", "Sedute di storia prima che il filtro possa scattare", "config.py, STORIA_MINIMA")
    reg("costo_cambio", config.COSTO_CAMBIO, "pct1", "Costo per passaggio tra mercato e liquidità", "config.py, COSTO_CAMBIO")
    reg("n_rimescolate", config.N_RIMESCOLATE, "int", "Storie rimescolate per indice", "config.py, N_RIMESCOLATE")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie del filtro", "config.py, N_SCIMMIE")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello delle fasce del caso", "config.py, LIVELLO_CONFIDENZA")
    S = config.SOGLIE
    reg("s_ip1_alfa", S["ip1_alfa"], "num2", "Soglia di significatività dopo Holm", "config.py, SOGLIE")
    reg("s_ip2_rapporto", S["ip2_rapporto"], "int", "Soglia della seconda ipotesi: rapporto tra quota vera e caso", "config.py, SOGLIE")
    reg("s_ip3_quota", S["ip3_quota"], "pct0", "Soglia della terza ipotesi: quota di giorni estremi nel quinto più volatile", "config.py, SOGLIE")
    reg("s_ip4_dimezza", S["ip4_dimezza"], "pct0", "Soglia della quarta ipotesi: quota dell'eccesso che sparisce", "config.py, SOGLIE")
    reg("s_ip5_evitati", S["ip5_evitati"], "pct0", "Soglia della quinta ipotesi: quota di giorni evitati", "config.py, SOGLIE")
    reg("s_ip5_rapp_lo", S["ip5_rapp_lo"], "num1", "Estremo basso del rapporto della quinta ipotesi", "config.py, SOGLIE")
    reg("s_ip5_rapp_hi", S["ip5_rapp_hi"], "num1", "Estremo alto del rapporto della quinta ipotesi", "config.py, SOGLIE")
    reg("s_ip6_perc", S["ip6_perc"], "pct0", "Soglia della sesta ipotesi: quota di scimmie battute", "config.py, SOGLIE")
    reg("s_ip6_cagr", S["ip6_cagr_pp"], "int", "Soglia della sesta ipotesi: vantaggio massimo sul buy & hold (punti)", "config.py, SOGLIE")
    reg("s_ip7_top", S["ip7_top"], "pct0", "Soglia della settima ipotesi: quota di giorni estremi nei cinque anni peggiori", "config.py, SOGLIE")
    reg("data_scarico", META["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")

    pd.DataFrame(righe_quint).to_csv(config.RISULTATI / "quintili.csv", index=False, float_format="%.5f")
    pd.DataFrame(righe_anni).to_csv(config.RISULTATI / "anni_estremi.csv", index=False)
    pd.DataFrame(righe_filtro).to_csv(config.RISULTATI / "filtro.csv", index=False, float_format="%.6f")
    (config.RISULTATI / "indici_usati.json").write_text(json.dumps(usati, ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri su {len(usati)} indici")


if __name__ == "__main__":
    main()
