"""Passo 2 - RSI a 14 sedute sull'S&P 500: studio degli eventi e regola «compra sotto 30, esci sopra 50».

Legge SOLO dati/gspc_giornaliero.csv; produce in risultati/: metriche.json, eventi.csv, spostamenti.csv, curve.csv.
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
GA = config.GIORNI_ANNO


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    c = close.to_numpy()
    date = close.index
    rend = np.concatenate([[0.0], c[1:] / c[:-1] - 1.0])
    rng = np.random.default_rng(config.SEME)
    r = fx.rsi(c, config.RSI_N)
    avanti = fx.rendimenti_avanti(c, config.ORIZZONTE)
    ok_av = ~np.isnan(avanti)

    reg("prima_data", str(date[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("n_rend", len(c) - 1, "int", "Rendimenti giornalieri", "dati/")
    reg("anni_tot", (len(c) - 1) / GA, "num1", "Anni di borsa nei dati (sedute diviso 252)", "dati/")
    reg("rsi_n", config.RSI_N, "int", "Periodo dell'RSI", "config.py")
    reg("soglia_bassa", config.SOGLIA_BASSA, "int", "Soglia di ipervenduto", "config.py")
    reg("soglia_alta", config.SOGLIA_ALTA, "int", "Soglia di ipercomprato", "config.py")
    reg("soglia_uscita", config.SOGLIA_USCITA, "int", "Soglia di uscita della regola", "config.py")
    reg("orizzonte", config.ORIZZONTE, "int", "Sedute dell'orizzonte dello studio degli eventi", "config.py")
    reg("h3_eccesso", config.H3_ECCESSO, "pct1", "Ipotesi 3: eccesso minimo del rendimento a dieci sedute", "config.py")
    reg("h5_pval", config.H5_PVAL, "num2", "Ipotesi 5: soglia del p-value", "config.py")
    reg("h6_tol", config.H6_TOLLERANZA, "pct2", "Ipotesi 6: tolleranza sotto la media dopo l'ipercomprato", "config.py")
    reg("n_spostamenti", config.N_SPOSTAMENTI, "int", "Spostamenti circolari della posizione", "config.py")

    # --- Studio degli eventi ------------------------------------------------------------------------------------------------
    sotto = fx.primi_incroci(r, config.SOGLIA_BASSA, "sotto")
    sopra = fx.primi_incroci(r, config.SOGLIA_ALTA, "sopra")
    spart = np.searchsorted(date.values, np.datetime64(config.SPARTIACQUE))
    ev_righe = []

    def blocco(nome, idx, lim_lo, lim_hi):
        idx = idx[(idx >= lim_lo) & (idx < lim_hi)]
        idx = idx[ok_av[idx]]
        tutti = avanti[lim_lo:lim_hi]
        tutti = tutti[~np.isnan(tutti)]
        return idx, float(np.mean(avanti[idx])) if len(idx) else float("nan"), float(np.mean(tutti)), len(idx)

    n = len(c)
    for nome, idx in (("sotto", sotto), ("sopra", sopra)):
        ix, m, mt, k = blocco(nome, idx, 0, n)
        reg(f"n_{nome}", k, "int", f"Prime chiusure con attraversamento della soglia ({nome}) con dieci sedute successive disponibili", "funzioni.primi_incroci")
        reg(f"m10_{nome}", m, "pct2", f"Rendimento medio a dieci sedute dopo l'attraversamento ({nome})", "funzioni")
        reg(f"ecc_{nome}", m - mt, "pp2", f"Rendimento medio a dieci sedute dopo l'attraversamento ({nome}) meno quello di un giorno qualunque, punti percentuali", "funzioni")
        if nome == "sotto":
            reg("m10_tutti", mt, "pct2", "Rendimento medio a dieci sedute di un giorno qualunque", "funzioni")
            reg("quota_pos_sotto", float(np.mean(avanti[ix] > 0)), "pct0", "Quota di eventi sotto la soglia con rendimento a dieci sedute positivo", "funzioni")
            reg("quota_pos_tutti", float(np.mean(avanti[ok_av] > 0)), "pct0", "Quota di giorni qualunque con rendimento a dieci sedute positivo", "funzioni")
        for d in ix:
            ev_righe.append({"evento": nome, "data": str(date[d].date()), "rsi": r[d], "avanti10": avanti[d]})
    for nome, lo, hi, tag in (("prima", 0, spart, "p"), ("dopo", spart, n, "d")):
        ix, m, mt, k = blocco("sotto", sotto, lo, hi)
        reg(f"n_sotto_{tag}", k, "int", f"Eventi sotto la soglia, periodo {nome} lo spartiacque", "funzioni")
        reg(f"ecc_sotto_{tag}", m - mt, "pp2", f"Eccesso del rendimento a dieci sedute dopo l'RSI sotto la soglia, periodo {nome} lo spartiacque", "funzioni")
    pd.DataFrame(ev_righe).to_csv(config.RISULTATI / "eventi.csv", index=False, float_format="%.5f")
    reg("spartiacque", config.SPARTIACQUE, "data_lunga", "Data che divide il campione in due metà", "config.py")

    # --- Regola ----------------------------------------------------------------------------------------------------------------------
    pos = fx.posizione_regola(r, config.SOGLIA_BASSA, config.SOGLIA_USCITA)
    rr = fx.rendimenti_regola(rend, pos)
    rr, bh = rr[1:], rend[1:]
    reg("reg_cagr", fx.cagr(rr, GA), "pct2", "Rendimento annuo composto della regola", "funzioni.cagr")
    reg("bh_cagr", fx.cagr(bh, GA), "pct2", "Rendimento annuo composto del buy & hold", "funzioni.cagr")
    reg("reg_sr", fx.sharpe(rr, GA), "num2", "Sharpe della regola", "funzioni.sharpe")
    reg("bh_sr", fx.sharpe(bh, GA), "num2", "Sharpe del buy & hold", "funzioni.sharpe")
    p_eff = np.concatenate([[0.0], pos[:-1]])[1:]
    reg("reg_quota", float(np.mean(p_eff)), "pct0", "Quota di giorni in cui la regola è investita", "funzioni")
    entrate = int(np.sum((pos[1:] == 1) & (pos[:-1] == 0)) + (1 if pos[0] == 1 else 0))
    reg("reg_entrate", entrate, "int", "Numero di ingressi della regola", "funzioni")
    reg("reg_durata", float(np.sum(p_eff)) / max(entrate, 1), "num1", "Sedute medie di ogni periodo investito", "funzioni")
    sh = fx.sharpe_spostamenti(rend, pos, config.N_SPOSTAMENTI, GA, rng)
    sr_oss = fx.sharpe(rr, GA)
    pval = float((1 + np.sum(sh >= sr_oss)) / (config.N_SPOSTAMENTI + 1))
    reg("pval", pval, "pval", "Quota di spostamenti circolari con Sharpe almeno pari a quello della regola", "funzioni.sharpe_spostamenti")
    reg("sr_spost_med", float(np.median(sh)), "num2", "Sharpe mediano delle posizioni spostate a caso", "funzioni.sharpe_spostamenti")
    pd.DataFrame({"sharpe": sh}).to_csv(config.RISULTATI / "spostamenti.csv", index=False, float_format="%.5f")
    curve = pd.DataFrame({"regola": np.cumprod(1 + rr), "buy_hold": np.cumprod(1 + bh)}, index=date[1:])
    curve.resample("YE").last().to_csv(config.RISULTATI / "curve.csv", float_format="%.5f")

    h = [RIS["reg_sr"]["valore"] < RIS["bh_sr"]["valore"],
         RIS["reg_cagr"]["valore"] < RIS["bh_cagr"]["valore"],
         RIS["ecc_sotto"]["valore"] >= config.H3_ECCESSO,
         RIS["ecc_sotto_d"]["valore"] < RIS["ecc_sotto_p"]["valore"],
         pval < config.H5_PVAL and sr_oss > float(np.median(sh)),
         RIS["ecc_sopra"]["valore"] >= -config.H6_TOLLERANZA]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "seme": config.SEME, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
