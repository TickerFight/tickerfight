"""Passo 2 - Il look-ahead bias: quanto vale l'illusione, e come si riconosce.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json       ogni numero dell'articolo, con descrizione e origine di calcolo
  curve.csv           valore giorno per giorno (una seduta su cinque) della regola 50/200: con look-ahead, onesta, buy & hold
  ritardi.csv         rendimento annuo di ogni regola per ogni ritardo del segnale (zero = look-ahead)
  griglia.csv         rendimento annuo con look-ahead e onesto per una griglia di coppie di medie
  sottoperiodi.csv    la regola 50/200 nei tre sottoperiodi

Tutte le versioni usano lo stesso motore (motore_vettoriale.py): cambia solo il ritardo con cui il segnale è noto.
Nessuna commissione, nessuna tassa: l'obiettivo è isolare l'effetto del look-ahead.
"""
import json
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import motore_vettoriale as m

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con motore_vettoriale.py"


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def importo(x: float) -> str:
    """Un importo in euro; se è assurdamente grande si dice solo quante cifre ha."""
    if x < 1e9:
        return f"{x:,.0f}".replace(",", ".") + " euro"
    return f"un numero con {int(np.floor(np.log10(x))) + 1} cifre"


def segnali(close: pd.Series) -> dict[str, pd.Series]:
    return {"un_giorno": m.segnale_un_giorno(close),
            "media_20": m.segnale_sopra_media(close, config.SMA_BREVE),
            "medie_50_200": m.segnale_medie(close, config.SMA_VELOCE, config.SMA_LENTA)}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    rend_pieno = m.rendimenti(close)
    sig = segnali(close)
    i0 = config.INIZIO_TEST_SEDUTE
    date = close.index
    sl = slice(i0, None)
    rend = rend_pieno.iloc[sl]
    anni = (date[-1] - date[i0 - 1]).days / 365.25

    def versione(segnale: pd.Series, ritardo: int, rend_x=None, sl_x=None):
        pos = m.posizione(segnale, ritardo).iloc[sl_x or sl]
        r = rend if rend_x is None else rend_x
        return pos, m.valore(r, pos)

    bh_pos = pd.Series(True, index=rend.index)
    v_bh = m.valore(rend, bh_pos)
    reg("prima_data", str(date[0].date()), "data_lunga", "Prima seduta dei dati scaricati", "dati/gspc_giornaliero.csv")
    reg("data_inizio", str(date[i0].date()), "data_lunga", "Prima seduta del test (le precedenti servono per le medie)", "dati/ e config.py, INIZIO_TEST_SEDUTE")
    reg("data_fine", str(date[-1].date()), "data_lunga", "Ultima seduta del test", "dati/gspc_giornaliero.csv")
    reg("sedute_avvio", config.INIZIO_TEST_SEDUTE, "int", "Sedute iniziali usate solo per calcolare le medie, prima dell'inizio del test", "config.py, INIZIO_TEST_SEDUTE")
    reg("n_sedute", len(rend), "int", "Sedute nel periodo del test", "dati/")
    reg("anni_test", anni, "num1", "Anni del test")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale, solo per dare un'idea (valori lordi)", "config.py, CAPITALE")
    reg("sma_breve", config.SMA_BREVE, "annonum", "Giorni della media breve", "config.py")
    reg("sma_veloce", config.SMA_VELOCE, "annonum", "Giorni della media veloce", "config.py")
    reg("sma_lenta", config.SMA_LENTA, "annonum", "Giorni della media lenta", "config.py")
    reg("cagr_bh", m.cagr(v_bh, anni), "pct1", "Rendimento annuo composto del buy & hold sul S&P 500, senza costi né tasse")
    reg("dd_bh", -m.perdita_massima(v_bh), "pct0", "Perdita massima dal picco del buy & hold")
    reg("finale_bh", importo(config.CAPITALE * v_bh.iloc[-1]), "testo", "Valore finale del buy & hold, partendo dal capitale iniziale")

    righe_rit, curva = [], None
    n_h1 = 0
    gap = {}
    drop_ok = 0
    for sl_id, _ in config.REGOLE:
        s = sig[sl_id]
        pos0, v0 = versione(s, 0)
        pos1, v1 = versione(s, config.RITARDO_ONESTO)
        c0, c1 = m.cagr(v0, anni), m.cagr(v1, anni)
        gap[sl_id] = c0 - c1
        n_h1 += int(c0 > c1)
        reg(f"{sl_id}_cagr_cheat", c0, "pct1", f"Rendimento annuo con look-ahead, regola «{sl_id}»")
        reg(f"{sl_id}_cagr_onesto", c1, "pct1", f"Rendimento annuo con segnale onesto (ritardo di un giorno), regola «{sl_id}»")
        reg(f"{sl_id}_illusione", c0 - c1, "pp2", f"Illusione: rendimento annuo con look-ahead meno quello onesto, in punti percentuali, regola «{sl_id}»")
        reg(f"{sl_id}_finale_cheat", importo(config.CAPITALE * v0.iloc[-1]), "testo", f"Valore finale con look-ahead, regola «{sl_id}»")
        reg(f"{sl_id}_finale_onesto", importo(config.CAPITALE * v1.iloc[-1]), "testo", f"Valore finale con segnale onesto, regola «{sl_id}»")
        reg(f"{sl_id}_dd_onesto", -m.perdita_massima(v1), "pct0", f"Perdita massima dal picco, versione onesta, regola «{sl_id}»")
        reg(f"{sl_id}_quota_investito", float(pos1.mean()), "pct0", f"Quota di sedute investite, versione onesta, regola «{sl_id}»")
        reg(f"{sl_id}_n_cambi", int(pos1.astype(int).diff().abs().sum()), "int", f"Numero di cambi di posizione (acquisti e vendite), regola «{sl_id}»")
        reg(f"{sl_id}_cambi_anno", int(pos1.astype(int).diff().abs().sum()) / anni, "int", f"Cambi di posizione all'anno, regola «{sl_id}»")
        reg(f"{sl_id}_costo_decimo", int(pos1.astype(int).diff().abs().sum()) / anni * 0.001, "pp1",
            f"Costo annuo, in punti percentuali, se ogni cambio di posizione costasse un decimo di punto percentuale, regola «{sl_id}»")
        rubati = pos0 & ~pos1       # giorni in cui il look-ahead è investito e l'onesto no: ha già "visto" il rialzo
        evitati = ~pos0 & pos1      # giorni in cui il look-ahead è già fuori e l'onesto no: ha già "visto" il ribasso
        reg(f"{sl_id}_n_rubati", int(rubati.sum()), "int", f"Giorni in cui la versione con look-ahead è dentro e quella onesta no, regola «{sl_id}»")
        reg(f"{sl_id}_ret_rubati", float(rend[rubati].mean()), "pct2", f"Rendimento medio di quei giorni (guadagno «rubato»), regola «{sl_id}»")
        reg(f"{sl_id}_n_evitati", int(evitati.sum()), "int", f"Giorni in cui la versione con look-ahead è fuori e quella onesta no, regola «{sl_id}»")
        reg(f"{sl_id}_ret_evitati", float(rend[evitati].mean()), "pct2", f"Rendimento medio di quei giorni (perdita «evitata»), regola «{sl_id}»")
        # test del ritardo
        cr = []
        for d in config.RITARDI:
            _, vd = versione(s, d)
            cr.append(m.cagr(vd, anni))
            righe_rit.append({"regola": sl_id, "ritardo": d, "cagr": cr[-1]})
        cali = [cr[k] - cr[k + 1] for k in range(len(cr) - 1)]
        ok = int(np.argmax(cali) == 0)
        drop_ok += ok
        reg(f"{sl_id}_calo_0_1", cali[0], "pp2", f"Calo del rendimento annuo passando da ritardo zero a ritardo uno, punti percentuali, regola «{sl_id}»")
        reg(f"{sl_id}_calo_1_2", cali[1], "pp2", f"Calo del rendimento annuo passando da ritardo uno a ritardo due, punti percentuali, regola «{sl_id}»")
        reg(f"{sl_id}_calo_max_dopo", max(cali[1:]), "pp2", f"Il calo più grande tra due ritardi successivi dopo il primo, punti percentuali, regola «{sl_id}»")
        reg(f"{sl_id}_cagr_ritardo_10", cr[-1], "pct1", f"Rendimento annuo con dieci sedute di ritardo, regola «{sl_id}»")
        reg(f"{sl_id}_h4_ok", ok, "int", f"1 se il calo più grande è tra ritardo zero e uno, regola «{sl_id}»")
        if sl_id == "medie_50_200":
            camp = np.r_[np.arange(0, len(rend), 5), len(rend) - 1]
            curva = pd.DataFrame({"data": rend.index[camp], "valore_bh": v_bh.iloc[camp].to_numpy(),
                                  "valore_cheat": v0.iloc[camp].to_numpy(), "valore_onesto": v1.iloc[camp].to_numpy()})

    reg("n_h1", n_h1, "int", "Regole per cui il look-ahead rende più della versione onesta", "calcolo sopra")
    ordine_ok = int(gap["un_giorno"] > gap["media_20"] > gap["medie_50_200"])
    reg("h2_ordine_ok", ordine_ok, "int", "1 se l'illusione è decrescente: regola di un giorno, media a 20 giorni, medie 50/200", "calcolo sopra")
    reg("n_h4_ok", drop_ok, "int", "Regole per cui il calo più grande è tra ritardo zero e ritardo uno", "ritardi.csv")
    reg("n_regole", len(config.REGOLE), "int", "Regole confrontate", "config.py, REGOLE")

    # --- sottoperiodi della regola 50/200 -----------------------------------------------------------------------
    s = sig["medie_50_200"]
    rsp = []
    n_sotto = 0
    for k, (nome, a, b) in enumerate(config.SOTTOPERIODI, 1):
        idx = rend.index
        msk = np.ones(len(idx), bool)
        if a: msk &= idx >= pd.Timestamp(a)
        if b: msk &= idx <= pd.Timestamp(b)
        r_p = rend[msk]
        p0 = m.posizione(s, 0).iloc[sl][msk]
        p1 = m.posizione(s, 1).iloc[sl][msk]
        an = (r_p.index[-1] - r_p.index[0]).days / 365.25
        c0, c1, cb = (m.cagr(m.valore(r_p, p), an) for p in (p0, p1, pd.Series(True, index=r_p.index)))
        n_sotto += int(c0 - c1 < 0.02)
        rsp.append({"periodo": nome, "cagr_cheat": c0, "cagr_onesto": c1, "cagr_bh": cb, "illusione": c0 - c1})
        reg(f"sp{k}_nome", nome, "testo", "Nome del sottoperiodo", "config.py, SOTTOPERIODI")
        reg(f"sp{k}_cagr_cheat", c0, "pct1", f"Rendimento annuo con look-ahead, medie 50/200, {nome}")
        reg(f"sp{k}_cagr_onesto", c1, "pct1", f"Rendimento annuo onesto, medie 50/200, {nome}")
        reg(f"sp{k}_illusione", c0 - c1, "pp2", f"Illusione in punti percentuali, medie 50/200, {nome}")
    reg("n_sp_sotto_2pp", n_sotto, "int", "Sottoperiodi in cui l'illusione delle medie 50/200 è sotto i due punti percentuali", "sottoperiodi.csv")
    pd.DataFrame(rsp).to_csv(config.RISULTATI / "sottoperiodi.csv", index=False, float_format="%.6f")

    # --- griglia di medie -------------------------------------------------------------------------------------
    gr = []
    for f in config.GRIGLIA_VELOCE:
        for l in config.GRIGLIA_LENTA:
            if f >= l:
                continue
            sg = m.segnale_medie(close, f, l)
            c0 = m.cagr(m.valore(rend, m.posizione(sg, 0).iloc[sl]), anni)
            c1 = m.cagr(m.valore(rend, m.posizione(sg, 1).iloc[sl]), anni)
            gr.append({"veloce": f, "lenta": l, "cagr_cheat": c0, "cagr_onesto": c1, "illusione": c0 - c1})
    gr = pd.DataFrame(gr)
    imax, imin = gr["illusione"].idxmax(), gr["illusione"].idxmin()
    reg("griglia_n", len(gr), "int", "Coppie di medie provate", "griglia.csv")
    reg("griglia_max", float(gr.loc[imax, "illusione"]), "pp2", "Illusione massima della griglia, punti percentuali", "griglia.csv")
    reg("griglia_max_veloce", int(gr.loc[imax, "veloce"]), "annonum", "Media veloce della coppia con l'illusione massima", "griglia.csv")
    reg("griglia_max_lenta", int(gr.loc[imax, "lenta"]), "annonum", "Media lenta della coppia con l'illusione massima", "griglia.csv")
    reg("griglia_min", float(gr.loc[imin, "illusione"]), "pp2", "Illusione minima della griglia, punti percentuali", "griglia.csv")
    reg("griglia_min_veloce", int(gr.loc[imin, "veloce"]), "annonum", "Media veloce della coppia con l'illusione minima", "griglia.csv")
    reg("griglia_min_lenta", int(gr.loc[imin, "lenta"]), "annonum", "Media lenta della coppia con l'illusione minima", "griglia.csv")
    reg("griglia_mediana", float(gr["illusione"].median()), "pp2", "Illusione mediana della griglia, punti percentuali", "griglia.csv")
    reg("griglia_tutte_positive", int((gr["illusione"] > 0).all()), "int", "1 se l'illusione è positiva per ogni coppia della griglia", "griglia.csv")
    gr.to_csv(config.RISULTATI / "griglia.csv", index=False, float_format="%.6f")
    pd.DataFrame(righe_rit).to_csv(config.RISULTATI / "ritardi.csv", index=False, float_format="%.6f")
    curva.to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.6f")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")
    for sid, _ in config.REGOLE:
        print(f"{sid}: look-ahead {RIS[sid + '_cagr_cheat']['valore']:.1%}, onesto {RIS[sid + '_cagr_onesto']['valore']:.1%}, "
              f"buy & hold {RIS['cagr_bh']['valore']:.1%}")


if __name__ == "__main__":
    main()
