"""Passo 2 - Il costo di pareggio: a che costo per cambio ogni regola smette di battere il buy & hold.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json          ogni numero dell'articolo, con descrizione e origine
  pareggio.csv           per ogni regola: cambi all'anno, costo di pareggio su rendimento annuo e su Sharpe (periodo intero e due metà)
  curve_sharpe.csv       Sharpe di ogni regola per costi da 0 a 1%
  scimmie.csv            Sharpe delle scimmie a costo zero e a costo tipico
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


def it_pct(x: float, dec: int = 2) -> str:
    return f"{x * 100:.{dec}f}".replace(".", ",") + "%"


def testo_costo(c: float, stato: str) -> str:
    if stato == "gia_sotto":
        return "già sotto"
    if stato == "oltre":
        return "oltre " + it_pct(config.COSTO_MAX_RICERCA, 0)
    if 0 < c < 0.0001:
        return "meno di 0,01%"
    return it_pct(c)


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    date = close.index
    S0 = config.INIZIO_TEST_SEDUTE
    ids = list(config.STRATEGIE)
    regole = [i for i in ids if i != config.ID_BH]
    nome = {i: config.STRATEGIE[i][0] for i in ids}
    ret = close.pct_change().fillna(0.0)
    ret_s = ret.iloc[S0:]
    anni = (date[-1] - date[S0 - 1]).days / 365.25
    T = len(ret_s)
    meta = T // 2
    periodi = {"tutto": (0, T), "prima": (0, meta), "seconda": (meta, T)}
    anni_p = {k: (date[S0 + b - 1] - date[S0 + a - 1]).days / 365.25 for k, (a, b) in periodi.items()}
    pos = {i: fx.posizione_regola(close, config.STRATEGIE[i][1]).iloc[S0:] for i in ids}

    def serie(i, costo, periodo):
        a, b = periodi[periodo]
        return fx.rendimenti_netti(ret_s.iloc[a:b], pos[i].iloc[a:b], costo).to_numpy()

    def misura(i, periodo, tipo):
        if tipo == "sharpe":
            return lambda c: float(fx.sharpe(serie(i, c, periodo), config.SEDUTE_ANNO))
        return lambda c: float(fx.cagr(serie(i, c, periodo), anni_p[periodo]))

    cambi_anno = {i: float(pos[i].diff().abs().fillna(0.0).sum() + abs(pos[i].iloc[0])) / anni for i in ids}

    # --- Parametri e dati ---------------------------------------------------------------------------------------------------------
    reg("prima_data", str(date[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_inizio", str(date[S0].date()), "data_lunga", "Prima seduta in cui si misurano tutte le regole", "dati/ e config.py")
    reg("data_meta", str(date[S0 + meta].date()), "data_lunga", "Prima seduta della seconda metà del periodo misurato", "dati/")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("anni_campione", anni, "num1", "Anni dell'intero periodo misurato", "dati/")
    reg("anni_meta", anni_p["prima"], "num1", "Anni della prima metà del periodo misurato", "dati/")
    reg("n_regole", len(regole), "int", "Regole confrontate con il buy & hold", "config.py, STRATEGIE")
    reg("costo_tipico", config.COSTO_TIPICO, "pct1", "Costo tipico per cambio citato nel testo", "config.py, COSTO_TIPICO")
    reg("costo_ricerca_max", config.COSTO_MAX_RICERCA, "pct0", "Costo massimo cercato per il pareggio", "config.py, COSTO_MAX_RICERCA")
    reg("ordine_esempio", config.ORDINE_ESEMPIO, "int", "Euro di un ordine d'esempio per tradurre il costo percentuale in euro", "config.py, ORDINE_ESEMPIO")
    for w in (10, 20, 50, 100, 200):
        reg(f"w{w}", w, "annonum", f"Giorni della media mobile: regola 'Prezzo sopra la media a {w} giorni'", "config.py, STRATEGIE")
    reg("w_inc_lenta", config.STRATEGIE["cross"][1][2], "annonum", "Giorni della media lenta dell'incrocio 50/200", "config.py, STRATEGIE")
    reg("costo_tipico_euro", config.COSTO_TIPICO * config.ORDINE_ESEMPIO, "num2", "Euro di costo per ordine al costo tipico, su un ordine d'esempio", "config.py")
    reg("anno_bs", 2012, "annonum", "Anno di pubblicazione di Bajgrowicz e Scaillet, Journal of Financial Economics", "pagina IDEAS/RePEc dell'articolo, letta il giorno dell'esecuzione")
    reg("anno_bs_ini", 1897, "annonum", "Primo anno dei dati del Dow Jones usati da Bajgrowicz e Scaillet", "abstract dell'articolo, pagina IDEAS/RePEc")
    reg("anno_bs_fin", 2011, "annonum", "Ultimo anno dei dati del Dow Jones usati da Bajgrowicz e Scaillet", "abstract dell'articolo, pagina IDEAS/RePEc")
    reg("anno_nmv", 2016, "annonum", "Anno di pubblicazione di Novy-Marx e Velikov, Review of Financial Studies", "pagina IDEAS/RePEc dell'articolo, letta il giorno dell'esecuzione")
    reg("soglia_nmv", 0.5, "pct0", "Rotazione mensile sotto la quale, per Novy-Marx e Velikov, la maggior parte delle anomalie resta profittevole al netto dei costi", "abstract dell'articolo, pagina IDEAS/RePEc")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie estratte", "config.py")
    reg("soglia_spearman", config.SOGLIA_SPEARMAN, "num1", "Soglia di correlazione di rango per l'ipotesi 1", "config.py")
    reg("soglia_filtro", config.SOGLIA_FILTRO, "pct1", "Costo di pareggio minimo per il filtro a 200 giorni (ipotesi 2)", "config.py")
    reg("cambi_veloci_anno", config.CAMBI_VELOCI_ANNO, "annonum", "Cambi all'anno da cui una regola è 'veloce' (ipotesi 3)", "config.py")
    reg("fattore_instabilita", config.FATTORE_INSTABILITA, "annonum", "Rapporto tra i due costi di pareggio delle metà oltre il quale la regola è instabile (ipotesi 4)", "config.py")
    reg("soglia_scimmie", config.SOGLIA_SCIMMIE, "pct0", "Quota massima di scimmie sopra il buy & hold ammessa (ipotesi 5)", "config.py")
    reg("sharpe_bh_lordo", float(misura("bh", "tutto", "sharpe")(0.0)), "num2", "Sharpe del buy & hold senza costi", "costi calcolati sul periodo intero")
    reg("cagr_bh_lordo", float(misura("bh", "tutto", "cagr")(0.0)), "pct1", "Rendimento annuo composto del buy & hold senza costi", "calcolato sul periodo intero")

    # --- Costo di pareggio ---------------------------------------------------------------------------------------------------------
    righe = []
    BE = {}
    for i in regole:
        r = {"id": i, "nome": nome[i], "cambi_anno": cambi_anno[i]}
        for tipo in ("sharpe", "cagr"):
            for periodo in periodi:
                c, stato = fx.costo_pareggio(misura(i, periodo, tipo), misura("bh", periodo, tipo), config.COSTO_MAX_RICERCA)
                BE[(i, tipo, periodo)] = (c, stato)
                r[f"{tipo}_{periodo}"] = c
                r[f"{tipo}_{periodo}_stato"] = stato
        righe.append(r)
        sh0, shp = misura(i, "tutto", "sharpe")(0.0), misura(i, "tutto", "sharpe")(config.COSTO_TIPICO)
        cg0, cgp = misura(i, "tutto", "cagr")(0.0), misura(i, "tutto", "cagr")(config.COSTO_TIPICO)
        reg(f"cambi_anno_{i}", cambi_anno[i], "num1", f"Cambi di posizione all'anno: {nome[i]}", "posizioni sul periodo misurato")
        reg(f"sh_lordo_{i}", sh0, "num2", f"Sharpe senza costi: {nome[i]}", "periodo intero")
        reg(f"sh_tipico_{i}", shp, "num2", f"Sharpe con costo tipico: {nome[i]}", "periodo intero")
        reg(f"cg_lordo_{i}", cg0, "pct1", f"Rendimento annuo composto senza costi: {nome[i]}", "periodo intero")
        reg(f"cg_tipico_{i}", cgp, "pct1", f"Rendimento annuo composto con costo tipico: {nome[i]}", "periodo intero")
        for tipo, et in (("sharpe", "be_sh"), ("cagr", "be_cg")):
            c, stato = BE[(i, tipo, "tutto")]
            reg(f"{et}_{i}", c, "pct2", f"Costo di pareggio sul {'rapporto rendimento/rischio (Sharpe)' if tipo == 'sharpe' else 'rendimento annuo'}: {nome[i]}", "bisezione, periodo intero")
            reg(f"{et}_txt_{i}", testo_costo(c, stato), "testo", f"Costo di pareggio ({'Sharpe' if tipo == 'sharpe' else 'rendimento annuo'}) come testo, con i casi limite: {nome[i]}", "bisezione, periodo intero")
        for periodo, et in (("prima", "p1"), ("seconda", "p2")):
            c, stato = BE[(i, "sharpe", periodo)]
            reg(f"be_sh_{et}_txt_{i}", testo_costo(c, stato), "testo", f"Costo di pareggio sullo Sharpe nella {'prima' if periodo == 'prima' else 'seconda'} metà del periodo: {nome[i]}", "bisezione, mezzo periodo")
        c, _ = BE[(i, "sharpe", "tutto")]
        reg(f"be_sh_euro_{i}", c * config.ORDINE_ESEMPIO, "num2", f"Euro di costo per ordine, su un ordine d'esempio, a cui la regola pareggia lo Sharpe del buy & hold: {nome[i]}", "bisezione x ORDINE_ESEMPIO")
    pd.DataFrame(righe).to_csv(config.RISULTATI / "pareggio.csv", index=False, float_format="%.6f")

    # --- Riepilogo sul pareggio -------------------------------------------------------------------------------------------------------
    sh_tutto = {i: BE[(i, "sharpe", "tutto")] for i in regole}
    n_gia_sotto_sh = sum(1 for i in regole if sh_tutto[i][1] == "gia_sotto")
    n_gia_sotto_cg = sum(1 for i in regole if BE[(i, "cagr", "tutto")][1] == "gia_sotto")
    n_oltre_sh = sum(1 for i in regole if sh_tutto[i][1] == "oltre")
    reg("n_gia_sotto_sh", n_gia_sotto_sh, "int", "Regole che a costo zero hanno già Sharpe non superiore al buy & hold", "pareggio.csv")
    reg("n_gia_sotto_cg", n_gia_sotto_cg, "int", "Regole che a costo zero hanno già rendimento annuo non superiore al buy & hold", "pareggio.csv")
    reg("n_oltre_sh", n_oltre_sh, "int", "Regole che battono lo Sharpe del buy & hold anche con costo pari al massimo cercato", "pareggio.csv")
    n_vive_sh = sum(1 for i in regole if sh_tutto[i][0] > 0)
    reg("n_battono_sh_lordo", n_vive_sh, "int", "Regole con Sharpe più alto del buy & hold a costo zero", "pareggio.csv")
    n_vive_tipico = sum(1 for i in regole if sh_tutto[i][0] > config.COSTO_TIPICO)
    reg("n_battono_sh_tipico", n_vive_tipico, "int", "Regole con Sharpe più alto del buy & hold ancora al costo tipico", "pareggio.csv")
    n_vive_cg = sum(1 for i in regole if BE[(i, "cagr", "tutto")][0] > 0)
    reg("n_battono_cg_lordo", n_vive_cg, "int", "Regole con rendimento annuo più alto del buy & hold a costo zero", "pareggio.csv")
    # regola con il pareggio più basso tra quelle che a costo zero battono il buy & hold
    vive = [i for i in regole if sh_tutto[i][0] > 0]
    if vive:
        morta = min(vive, key=lambda i: sh_tutto[i][0])
        reg("regola_piu_fragile", nome[morta], "testo", "Regola con Sharpe sopra il buy & hold a costo zero e costo di pareggio più basso", "pareggio.csv")
        reg("regola_piu_fragile_be", sh_tutto[morta][0], "pct2", "Costo di pareggio (Sharpe) della regola più fragile tra quelle che partono sopra il buy & hold", "pareggio.csv")
        reg("regola_piu_fragile_euro", sh_tutto[morta][0] * config.ORDINE_ESEMPIO, "num2", "Euro su un ordine d'esempio del costo di pareggio della regola più fragile", "pareggio.csv")
        forte = max(vive, key=lambda i: sh_tutto[i][0])
        reg("regola_piu_robusta", nome[forte], "testo", "Regola con il costo di pareggio (Sharpe) più alto", "pareggio.csv")
        reg("regola_piu_robusta_be", sh_tutto[forte][0], "pct2", "Costo di pareggio (Sharpe) della regola più robusta", "pareggio.csv")
    reg("cambi_forte", cambi_anno[forte] if vive else 0.0, "num1", "Cambi all'anno della regola più robusta", "posizioni")

    # --- Curve dello Sharpe al crescere del costo ----------------------------------------------------------------------------------------
    righe_c = []
    for i in ids:
        f = misura(i, "tutto", "sharpe")
        for c in config.COSTO_CURVA:
            righe_c.append({"id": i, "nome": nome[i], "costo": c, "sharpe": f(c)})
    pd.DataFrame(righe_c).to_csv(config.RISULTATI / "curve_sharpe.csv", index=False, float_format="%.6f")

    # --- Ipotesi 1: Spearman ----------------------------------------------------------------------------------------------------------------
    rho = fx.spearman([cambi_anno[i] for i in regole], [sh_tutto[i][0] for i in regole])
    if not np.isfinite(rho):
        rho = 0.0                      # costi di pareggio tutti uguali (per esempio tutti zero): nessuna relazione misurabile
    reg("spearman", rho, "num2", "Correlazione di rango di Spearman tra cambi all'anno e costo di pareggio (Sharpe), sulle regole", "pareggio.csv")
    # --- Ipotesi 2 ---------------------------------------------------------------------------------------------------------------------------
    be200 = sh_tutto[config.ID_FILTRO]
    # --- Ipotesi 3 ---------------------------------------------------------------------------------------------------------------------------
    veloci = [i for i in regole if cambi_anno[i] >= config.CAMBI_VELOCI_ANNO]
    veloci_ok = [i for i in veloci if sh_tutto[i][0] < config.COSTO_TIPICO]
    reg("n_veloci", len(veloci), "int", "Regole con almeno il numero di cambi all'anno della soglia 'veloce'", "pareggio.csv")
    reg("n_veloci_ok", len(veloci_ok), "int", "Regole veloci con costo di pareggio sotto il costo tipico", "pareggio.csv")
    # --- Ipotesi 4: instabilità tra le due metà ---------------------------------------------------------------------------------------------
    instabili = 0
    for i in regole:
        a, b = BE[(i, "sharpe", "prima")][0], BE[(i, "sharpe", "seconda")][0]
        lo, hi = min(a, b), max(a, b)
        if hi > 0 and (lo == 0 or hi / lo > config.FATTORE_INSTABILITA):
            instabili += 1
    reg("n_instabili", instabili, "int", "Regole il cui costo di pareggio (Sharpe) nella metà migliore supera il fattore di instabilità volte quello della metà peggiore", "pareggio.csv")
    n_p1 = sum(1 for i in regole if BE[(i, "sharpe", "prima")][0] > 0)
    n_p2 = sum(1 for i in regole if BE[(i, "sharpe", "seconda")][0] > 0)
    reg("n_battono_prima", n_p1, "int", "Regole con Sharpe sopra il buy & hold a costo zero nella prima metà", "pareggio.csv")
    reg("n_battono_seconda", n_p2, "int", "Regole con Sharpe sopra il buy & hold a costo zero nella seconda metà", "pareggio.csv")

    # --- Ipotesi 5: scimmie ---------------------------------------------------------------------------------------------------------------------
    rng = np.random.default_rng(config.SEME)
    p_cambio = cambi_anno[config.ID_MEDIA] / config.SEDUTE_ANNO
    pos_s = fx.posizioni_scimmie(config.N_SCIMMIE, T, p_cambio, rng)
    cambi_s = float(np.abs(np.diff(pos_s, axis=1, prepend=np.zeros((config.N_SCIMMIE, 1)))).sum(axis=1).mean() / anni)
    ra = ret_s.to_numpy()
    sh0 = fx.sharpe(fx.rendimenti_scimmie(ra, pos_s, 0.0), config.SEDUTE_ANNO)
    shp = fx.sharpe(fx.rendimenti_scimmie(ra, pos_s, config.COSTO_TIPICO), config.SEDUTE_ANNO)
    pd.DataFrame({"sharpe_lordo": sh0, "sharpe_tipico": shp}).to_csv(config.RISULTATI / "scimmie.csv", index=False, float_format="%.6f")
    sh_bh0 = misura("bh", "tutto", "sharpe")(0.0)
    sh_bhp = misura("bh", "tutto", "sharpe")(config.COSTO_TIPICO)
    sopra0 = float((sh0 > sh_bh0).mean())
    sopra_p = float((shp > sh_bhp).mean())
    reg("scimmie_cambi_anno", cambi_s, "num1", "Cambi all'anno medi delle scimmie (stessa frequenza del prezzo sopra la media a 50 giorni)", "scimmie.csv")
    reg("scimmie_sopra_bh_lordo", sopra0, "pct1", "Quota di scimmie con Sharpe più alto del buy & hold a costo zero", "scimmie.csv")
    reg("scimmie_sopra_bh_tipico", sopra_p, "pct1", "Quota di scimmie con Sharpe più alto del buy & hold al costo tipico", "scimmie.csv")
    reg("scimmie_sharpe_mediano", float(np.median(sh0)), "num2", "Sharpe mediano delle scimmie a costo zero", "scimmie.csv")
    m50 = config.ID_MEDIA
    reg("media_batte_scimmie_lordo", float((misura(m50, "tutto", "sharpe")(0.0) > sh0).mean()), "pct0", "Quota di scimmie battute dal prezzo sopra la media a 50 giorni sullo Sharpe a costo zero", "scimmie.csv")
    reg("media_batte_scimmie_tipico", float((misura(m50, "tutto", "sharpe")(config.COSTO_TIPICO) > shp).mean()), "pct0", "Quota di scimmie battute dal prezzo sopra la media a 50 giorni sullo Sharpe al costo tipico", "scimmie.csv")

    h = {1: rho <= config.SOGLIA_SPEARMAN,
         2: be200[0] > config.SOGLIA_FILTRO,
         3: len(veloci_ok) == len(veloci),
         4: instabili * 2 >= len(regole),
         5: sopra0 < config.SOGLIA_SCIMMIE}
    for n, ok in h.items():
        reg(f"h{n}_ok", int(ok), "int", f"1 se l'ipotesi {n} è confermata, 0 se smentita", "02_backtest_e_test.py")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri; {T} sedute")
    print("ipotesi:", {n: int(ok) for n, ok in h.items()})


if __name__ == "__main__":
    main()
