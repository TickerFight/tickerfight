"""Passo 2 - La data di partenza cambia il verdetto: filtro a 200 sedute contro buy & hold da ogni mese di partenza.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine
  finestre_5.csv, finestre_10.csv, finestre_20.csv   per ogni mese di partenza: rendimento annuo, Sharpe e perdita massima di regola e buy & hold
  curve.csv         valore di 1 per regola e buy & hold sull'intero periodo (una seduta su cinque)
"""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import funzioni as f

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
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep="last")]
    c = df["Close"].astype(float)
    if (c <= 0).any() or c.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    date, close = c.index, c.to_numpy()
    n = len(close)
    strat, bh, pos = f.rendimenti_regola(close, config.MEDIA, config.COSTO_BP / 10000.0)
    prima = config.MEDIA + 2                       # prima posizione con segnale in vigore
    anni_tot = (date[-1] - date[prima]).days / 365.25

    reg("dati_prima_data", str(date[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("dati_ultima_data", str(date[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("partenza_prima", str(date[prima].date()), "data_lunga", "Prima seduta con la regola in vigore", "dati/")
    reg("anni_tot", anni_tot, "num1", "Anni dalla prima seduta con la regola in vigore all'ultima")
    reg("media", config.MEDIA, "int", "Sedute della media mobile", "config.py")
    reg("costo_bp", config.COSTO_BP, "int", "Costo di ogni cambio di posizione in punti base", "config.py")
    reg("giorni_anno", GA, "int", "Sedute in un anno", "config.py")

    # intero periodo
    cs, ss, ds = f.metriche_finestra(strat[prima:], GA)
    cb, sb, db = f.metriche_finestra(bh[prima:], GA)
    reg("tot_cagr_regola", cs, "pct1", "Rendimento annuo composto della regola sull'intero periodo")
    reg("tot_cagr_bh", cb, "pct1", "Rendimento annuo composto del buy & hold sull'intero periodo")
    reg("tot_sharpe_regola", ss, "num2", "Sharpe della regola sull'intero periodo")
    reg("tot_sharpe_bh", sb, "num2", "Sharpe del buy & hold sull'intero periodo")
    reg("tot_dd_regola", ds, "pct0", "Perdita massima della regola sull'intero periodo")
    reg("tot_dd_bh", db, "pct0", "Perdita massima del buy & hold sull'intero periodo")
    reg("quota_investito", float(pos[prima:].mean()), "pct0", "Quota di sedute con la regola investita")
    reg("cambi_anno", float(np.abs(np.diff(pos[prima - 1:])).sum() / anni_tot), "num1", "Cambi di posizione all'anno")

    inizi = f.inizi_mese(date, prima)
    esiti = {}
    for h in config.ORIZZONTI:
        lung = h * GA
        righe = []
        for i in inizi:
            if i + lung >= n:
                break
            a, sa, da = f.metriche_finestra(strat[i + 1:i + 1 + lung], GA)
            b, sb_, db_ = f.metriche_finestra(bh[i + 1:i + 1 + lung], GA)
            righe.append((str(date[i].date()), a, b, sa, sb_, da, db_))
        W = pd.DataFrame(righe, columns=["data", "cagr_r", "cagr_b", "sh_r", "sh_b", "dd_r", "dd_b"])
        W.to_csv(config.RISULTATI / f"finestre_{h}.csv", index=False, float_format="%.6f")
        diff = (W["cagr_r"] - W["cagr_b"]).to_numpy()
        reg(f"h{h}_n", len(W), "int", f"Mesi di partenza con una finestra di {h} anni completa")
        reg(f"h{h}_quota_rend", float((diff > 0).mean()), "pct0", f"Quota di partenze in cui la regola batte il buy & hold sul rendimento annuo, finestre di {h} anni")
        reg(f"h{h}_quota_sharpe", float((W["sh_r"] > W["sh_b"]).mean()), "pct0", f"Quota di partenze in cui la regola ha uno Sharpe più alto, finestre di {h} anni")
        reg(f"h{h}_quota_dd", float((W["dd_r"] < W["dd_b"]).mean()), "pct0", f"Quota di partenze in cui la regola ha una perdita massima minore, finestre di {h} anni")
        reg(f"h{h}_diff_media", float(diff.mean()), "pp1", f"Differenza media di rendimento annuo (regola meno buy & hold), finestre di {h} anni")
        reg(f"h{h}_cagr_r_media", float(W["cagr_r"].mean()), "pct1", f"Rendimento annuo medio della regola, finestre di {h} anni")
        reg(f"h{h}_cagr_b_media", float(W["cagr_b"].mean()), "pct1", f"Rendimento annuo medio del buy & hold, finestre di {h} anni")
        reg(f"h{h}_diff_max", float(diff.max()), "pp1", f"Differenza massima, finestre di {h} anni")
        reg(f"h{h}_diff_min", float(diff.min()), "pp1", f"Differenza minima, finestre di {h} anni")
        reg(f"h{h}_anno_max", int(pd.Timestamp(W["data"][int(diff.argmax())]).year), "annonum", f"Anno di partenza con la differenza massima, finestre di {h} anni")
        reg(f"h{h}_anno_min", int(pd.Timestamp(W["data"][int(diff.argmin())]).year), "annonum", f"Anno di partenza con la differenza minima, finestre di {h} anni")
        reg(f"h{h}_ampiezza", float(diff.max() - diff.min()), "pp1", f"Ampiezza della differenza tra la partenza migliore e la peggiore, finestre di {h} anni")
        reg(f"h{h}_tre_su_tre", float(((diff > 0) & (W["sh_r"] > W["sh_b"]) & (W["dd_r"] < W["dd_b"])).mean()), "pct0", f"Quota di partenze in cui la regola vince su rendimento, Sharpe e perdita massima insieme, finestre di {h} anni")
        reg(f"h{h}_zero_su_tre", float(((diff <= 0) & (W["sh_r"] <= W["sh_b"]) & (W["dd_r"] >= W["dd_b"])).mean()), "pct0", f"Quota di partenze in cui la regola perde su tutte e tre le misure, finestre di {h} anni")
        esiti[h] = dict(W=W, diff=diff)

    # casi di studio: decenni che partono a gennaio di un anno
    Wp = esiti[config.ORIZZONTE_PRINCIPALE]["W"]
    for nome, anno in (("fav", config.ANNO_FAVOREVOLE), ("sfav", config.ANNO_SFAVOREVOLE)):
        r = Wp[Wp["data"].str.startswith(f"{anno}-01")].iloc[0]
        reg(f"caso_{nome}_anno", anno, "annonum", f"Anno di partenza del caso «{nome}»", "config.py")
        reg(f"caso_{nome}_regola", float(r["cagr_r"]), "pct1", f"Rendimento annuo della regola, decennio del caso «{nome}»")
        reg(f"caso_{nome}_bh", float(r["cagr_b"]), "pct1", f"Rendimento annuo del buy & hold, decennio del caso «{nome}»")
        reg(f"caso_{nome}_diff", float(r["cagr_r"] - r["cagr_b"]), "pp1", f"Differenza di rendimento annuo, decennio del caso «{nome}»")
        reg(f"caso_{nome}_dd_regola", float(r["dd_r"]), "pct0", f"Perdita massima della regola, decennio del caso «{nome}»")
        reg(f"caso_{nome}_dd_bh", float(r["dd_b"]), "pct0", f"Perdita massima del buy & hold, decennio del caso «{nome}»")

    P = config.ORIZZONTE_PRINCIPALE
    d10 = esiti[P]["diff"]
    reg("orizzonte", P, "annonum", "Anni della finestra principale", "config.py")
    reg("h1_min", config.H1_MIN, "pct0", "Ipotesi 1: quota minima", "config.py")
    reg("h1_max", config.H1_MAX, "pct0", "Ipotesi 1: quota massima", "config.py")
    reg("h2_quota", config.H2_QUOTA, "pct0", "Ipotesi 2: quota minima sulla perdita massima", "config.py")
    reg("h3_vantaggio", config.H3_VANTAGGIO, "pp1", "Ipotesi 3: vantaggio minimo nel decennio favorevole, punti", "config.py")
    reg("h3_svantaggio", config.H3_SVANTAGGIO, "pp1", "Ipotesi 3: svantaggio minimo nel decennio sfavorevole, punti", "config.py")
    reg("h5_ampiezza", config.H5_AMPIEZZA, "pp1", "Ipotesi 5: ampiezza minima, punti", "config.py")
    h = [config.H1_MIN <= RIS[f"h{P}_quota_rend"]["valore"] <= config.H1_MAX,
         RIS[f"h{P}_quota_dd"]["valore"] >= config.H2_QUOTA,
         RIS["caso_fav_diff"]["valore"] >= config.H3_VANTAGGIO and RIS["caso_sfav_diff"]["valore"] <= -config.H3_SVANTAGGIO,
         RIS[f"h{P}_cagr_r_media"]["valore"] < RIS[f"h{P}_cagr_b_media"]["valore"],
         RIS[f"h{P}_ampiezza"]["valore"] > config.H5_AMPIEZZA,
         RIS["h20_quota_rend"]["valore"] < RIS[f"h{P}_quota_rend"]["valore"]]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(v), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(h)), "int", "Ipotesi confermate (su sei)", "confronto con config.py")
    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi")
    json.dump({"valori": RIS}, open(config.RISULTATI / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    camp = np.arange(prima, n, 5)
    er, eb = np.cumprod(1.0 + strat[prima:]), np.cumprod(1.0 + bh[prima:])
    pd.DataFrame({"data": date[camp].strftime("%Y-%m-%d"), "regola": er[camp - prima], "buyhold": eb[camp - prima]}).to_csv(
        config.RISULTATI / "curve.csv", index=False, float_format="%.5f")
    print(f"Scritti {len(RIS)} numeri in metriche.json; esiti {h}")


if __name__ == "__main__":
    main()
