"""Passo 2 - Una volta o ogni mese: lump sum contro PAC su tutti i mesi di partenza, contro il caso.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json          ogni numero dell'articolo, con descrizione e origine di calcolo
  partenze.csv           per ogni indice, orizzonte e mese di partenza: valore di lump sum, PAC e differenza
  rimescolate.csv        quota di vittorie del lump sum in ciascuna storia rimescolata (per indice e orizzonte)
  per_mese_calendario.csv  quota di vittorie del lump sum per mese di calendario di partenza (partenze non sovrapposte)
  indici_usati.json      indici effettivamente usati

Lump sum: tutto il budget al primo giorno di Borsa del mese di partenza. PAC: un dodicesimo del budget al primo giorno di
Borsa di ciascuno dei 12 mesi. Valutazione al primo giorno di Borsa del mese t+h. Nessun look-ahead: le date delle rate
sono decise alla partenza.
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


def ic_cluster(vinto: np.ndarray, anni: np.ndarray, rng) -> tuple[float, float]:
    """Intervallo di confidenza della quota di vittorie, ricampionando gli anni di partenza (le partenze vicine si sovrappongono)."""
    ua = np.unique(anni)
    somme = np.array([vinto[anni == a].sum() for a in ua], float)
    conti = np.array([(anni == a).sum() for a in ua], float)
    q = []
    for _ in range(config.N_BOOTSTRAP):
        k = rng.integers(0, len(ua), len(ua))
        q.append(somme[k].sum() / conti[k].sum())
    a = (1 - config.LIVELLO_CONFIDENZA) / 2
    return float(np.quantile(q, a)), float(np.quantile(q, 1 - a))


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    global META
    META = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    rng = np.random.default_rng(config.SEME)
    B, R = config.BUDGET, config.N_RATE
    righe_part, righe_rim, righe_cal, usati = [], [], [], []
    pval_grezzi: dict[str, float] = {}
    nulle: dict[str, np.ndarray] = {}

    for ticker, nome, valuta in config.INDICI:
        f = config.file_dati(ticker)
        if not f.exists():
            print(f"{ticker}: file mancante, indice scartato")
            continue
        df = pd.read_csv(f, index_col=0, parse_dates=True)
        pm = fx.prezzi_mensili(df["Close"])
        p = pm.values.astype(float)
        date_m = pm.index
        sl = slug(ticker)
        usati.append({"ticker": ticker, "slug": sl, "nome": nome})
        reg(f"{sl}_prima_data", str(date_m[0].date()), "data_lunga", f"Primo mese di dati di {nome}", "dati/")
        reg(f"{sl}_ultima_data", str(date_m[-1].date()), "data_lunga", f"Ultimo mese di dati di {nome}", "dati/")
        reg(f"{sl}_anno_inizio", str(date_m[0].date()), "anno", f"Anno del primo dato di {nome}", "dati/")
        reg(f"{sl}_n_mesi", len(p), "int", f"Mesi di prezzi disponibili per {nome}", "dati/")

        for h in config.ORIZZONTI:
            n = len(p) - h
            part = date_m[:n]
            anni = np.array([d.year for d in part])
            lump0 = fx.valore_lump(p, h, B, 0.0)
            pac0 = fx.valore_pac(p, h, B, R, 0.0)
            diff = (pac0 - lump0) / B * 100                     # punti percentuali del budget; > 0 vince il PAC
            vince_lump = lump0 > pac0
            q = float(vince_lump.mean())
            lo, hi = ic_cluster(vince_lump, anni, rng)
            tag = f"{sl}_{h}"
            reg(f"{tag}_n_part", n, "int", f"Mesi di partenza usati per {nome}, orizzonte {h} mesi", "numero di mesi meno l'orizzonte")
            reg(f"{tag}_quota_lump", q, "pct0", f"Quota di partenze in cui il lump sum batte il PAC, {nome}, {h} mesi")
            reg(f"{tag}_quota_lump_lo", lo, "pct0", f"Estremo inferiore dell'intervallo di confidenza della quota di vittorie del lump sum, {nome}, {h} mesi", "ricampionamento degli anni di partenza (N_BOOTSTRAP)")
            reg(f"{tag}_quota_lump_hi", hi, "pct0", f"Estremo superiore dell'intervallo di confidenza della quota di vittorie del lump sum, {nome}, {h} mesi", "ricampionamento degli anni di partenza (N_BOOTSTRAP)")
            reg(f"{tag}_diff_med", float(np.median(diff)), "num1", f"Differenza mediana PAC meno lump sum in punti percentuali del budget, {nome}, {h} mesi")
            reg(f"{tag}_diff_medio", float(diff.mean()), "num1", f"Differenza media PAC meno lump sum in punti percentuali del budget, {nome}, {h} mesi")
            reg(f"{tag}_diff_p5", float(np.quantile(diff, 0.05)), "num1", f"Quinto percentile della differenza PAC meno lump sum (punti del budget), {nome}, {h} mesi")
            reg(f"{tag}_diff_p95", float(np.quantile(diff, 0.95)), "num1", f"Novantacinquesimo percentile della differenza PAC meno lump sum (punti del budget), {nome}, {h} mesi")
            i_max, i_min = int(np.argmax(diff)), int(np.argmin(diff))
            reg(f"{tag}_diff_max", float(diff[i_max]), "num1", f"Massimo vantaggio del PAC sul lump sum (punti del budget), {nome}, {h} mesi")
            reg(f"{tag}_diff_max_data", str(part[i_max].date()), "data_lunga", f"Mese di partenza in cui il PAC ha il massimo vantaggio, {nome}, {h} mesi")
            reg(f"{tag}_diff_max_euro", float(pac0[i_max] - lump0[i_max]), "int", f"Massimo vantaggio del PAC sul lump sum in euro, {nome}, {h} mesi")
            reg(f"{tag}_diff_min", float(-diff[i_min]), "num1", f"Massimo vantaggio del lump sum sul PAC (punti del budget), {nome}, {h} mesi")
            reg(f"{tag}_diff_min_data", str(part[i_min].date()), "data_lunga", f"Mese di partenza in cui il lump sum ha il massimo vantaggio, {nome}, {h} mesi")
            reg(f"{tag}_diff_min_euro", float(lump0[i_min] - pac0[i_min]), "int", f"Massimo vantaggio del lump sum sul PAC in euro, {nome}, {h} mesi")
            reg(f"{tag}_media_vantaggio_lump", float((-diff[vince_lump]).mean()), "num1", f"Vantaggio medio del lump sum nelle partenze che vince (punti del budget), {nome}, {h} mesi")
            reg(f"{tag}_media_vantaggio_pac", float(diff[~vince_lump].mean()) if (~vince_lump).any() else 0.0, "num1", f"Vantaggio medio del PAC nelle partenze che vince (punti del budget), {nome}, {h} mesi")

            # direzione del mercato
            sale = p[h:h + n] > p[:n]
            reg(f"{tag}_quota_mercato_sale", float(sale.mean()), "pct0", f"Quota di partenze in cui l'indice sale tra la partenza e la valutazione, {nome}, {h} mesi")
            reg(f"{tag}_pac_vince_se_scende", float((~vince_lump)[~sale].mean()) if (~sale).any() else 0.0, "pct0", f"Quota di vittorie del PAC tra le partenze in cui l'indice scende, {nome}, {h} mesi")
            reg(f"{tag}_pac_vince_se_sale", float((~vince_lump)[sale].mean()) if sale.any() else 0.0, "pct0", f"Quota di vittorie del PAC tra le partenze in cui l'indice sale, {nome}, {h} mesi")
            reg(f"{tag}_n_scende", int((~sale).sum()), "int", f"Partenze in cui l'indice scende tra partenza e valutazione, {nome}, {h} mesi")

            # commissioni
            for c in config.COMMISSIONI:
                if c == 0:
                    continue
                qc = float((fx.valore_lump(p, h, B, c) > fx.valore_pac(p, h, B, R, c)).mean())
                reg(f"{tag}_quota_lump_comm", qc, "pct0", f"Quota di vittorie del lump sum con {c:g} euro a ordine, {nome}, {h} mesi")
                reg(f"{tag}_salto_comm", (qc - q) * 100, "num1", f"Aumento della quota di vittorie del lump sum con {c:g} euro a ordine (punti percentuali), {nome}, {h} mesi")
                reg("comm_euro", c, "int", "Commissione per ordine dello scenario con costi", "config.py, COMMISSIONI")

            # partenze non sovrapposte (h=12): mesi di calendario
            if h == config.ORIZZONTE_PRINCIPALE:
                mesi_cal = np.array([d.month for d in part])
                qm = []
                for m in range(1, 13):
                    sel = mesi_cal == m
                    qm.append(float(vince_lump[sel].mean()))
                    righe_cal.append({"ticker": ticker, "mese": m, "quota_lump": qm[-1], "n": int(sel.sum())})
                reg(f"{tag}_cal_min", min(qm), "pct0", f"Quota di vittorie del lump sum nel mese di calendario di partenza peggiore, {nome}, {h} mesi (partenze non sovrapposte)")
                reg(f"{tag}_cal_max", max(qm), "pct0", f"Quota di vittorie del lump sum nel mese di calendario di partenza migliore, {nome}, {h} mesi (partenze non sovrapposte)")

            # caso: stesse mosse mensili, ordine rimescolato
            nul = fx.quota_lump_rimescolate(p, h, B, R, config.N_RIMESCOLATE, rng)
            nulle[tag] = nul
            reg(f"{tag}_null_media", float(nul.mean()), "pct0", f"Quota media di vittorie del lump sum nelle storie rimescolate, {nome}, {h} mesi", "funzioni.quota_lump_rimescolate")
            reg(f"{tag}_null_lo", float(np.quantile(nul, 0.025)), "pct0", f"Percentile 2,5 della quota di vittorie del lump sum nelle storie rimescolate, {nome}, {h} mesi", "funzioni.quota_lump_rimescolate")
            reg(f"{tag}_null_hi", float(np.quantile(nul, 0.975)), "pct0", f"Percentile 97,5 della quota di vittorie del lump sum nelle storie rimescolate, {nome}, {h} mesi", "funzioni.quota_lump_rimescolate")
            reg(f"{tag}_dist_null", (q - float(nul.mean())) * 100, "num1", f"Quota vera meno quota media delle storie rimescolate, punti percentuali, {nome}, {h} mesi")
            p2 = (1 + np.sum(np.abs(nul - nul.mean()) >= abs(q - nul.mean()))) / (len(nul) + 1)
            pval_grezzi[tag] = float(p2)
            reg(f"{tag}_p_null", float(p2), "pval", f"p-value bilaterale: quanto spesso una storia rimescolata si discosta dalla media quanto la storia vera, {nome}, {h} mesi", "scarto assoluto dalla media delle rimescolate")
            for k, v in enumerate(nul):
                righe_rim.append({"ticker": ticker, "orizzonte": h, "storia": k, "quota_lump": v})

            # scimmie: rate in mesi a caso (solo orizzonte principale, senza costi)
            if h == config.ORIZZONTE_PRINCIPALE:
                sm = fx.valore_scimmia(p, h, B, R, config.N_SCIMMIE, rng)
                batte_pac = (pac0[:, None] > sm).mean(axis=1)        # quota di scimmie battute dal PAC regolare, per partenza
                reg(f"{tag}_pac_batte_scimmia_mediana", float((batte_pac > 0.5).mean()), "pct0", f"Quota di partenze in cui il PAC regolare batte più della metà delle scimmie, {nome}, {h} mesi", "funzioni.valore_scimmia")
                reg(f"{tag}_lump_batte_scimmie", float((lump0[:, None] > sm).mean()), "pct0", f"Quota di coppie partenza-scimmia in cui il lump sum batte la scimmia, {nome}, {h} mesi", "funzioni.valore_scimmia")
                reg(f"{tag}_scimmia_diff_med", float(np.median((sm.mean(axis=1) - pac0) / B * 100)), "num2", f"Differenza mediana tra valore medio delle scimmie e PAC regolare (punti del budget), {nome}, {h} mesi", "funzioni.valore_scimmia")

            righe_part.append(pd.DataFrame({"ticker": ticker, "orizzonte": h, "partenza": part.date, "lump": lump0, "pac": pac0,
                                            "diff_pp": diff, "mercato_sale": sale}))

    # Holm su tutti i test del rimescolamento (indici x orizzonti)
    ad = fx.holm(pval_grezzi)
    for tag, v in ad.items():
        reg(f"{tag}_p_holm", float(v), "pval", f"p-value del confronto con le storie rimescolate, corretto per Holm ({len(ad)} test: indici per orizzonti)", "correzione di Holm")
    reg("n_test_holm", len(ad), "int", "Test del rimescolamento corretti insieme con Holm (indici per orizzonti)", "numero di indici per numero di orizzonti")
    reg("n_test_holm_rifiutati", int(sum(v < 0.05 for v in ad.values())), "int", "Test del rimescolamento che restano significativi dopo Holm (p corretto sotto 0,05)", "correzione di Holm")
    reg("n_indici", len(usati), "int", "Indici usati", "dati/")
    reg("budget", config.BUDGET, "int", "Budget totale da investire in euro", "config.py, BUDGET")
    reg("rata", config.BUDGET / config.N_RATE, "int", "Rata mensile del PAC in euro", "config.py, BUDGET / N_RATE")
    reg("n_rate", config.N_RATE, "int", "Numero di rate del PAC", "config.py, N_RATE")
    reg("h1", config.ORIZZONTI[0], "int", "Primo orizzonte in mesi", "config.py, ORIZZONTI")
    reg("h2", config.ORIZZONTI[1], "int", "Secondo orizzonte in mesi", "config.py, ORIZZONTI")
    reg("n_rimescolate", config.N_RIMESCOLATE, "int", "Storie rimescolate per indice e orizzonte", "config.py, N_RIMESCOLATE")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie per ogni mese di partenza", "config.py, N_SCIMMIE")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py, LIVELLO_CONFIDENZA")
    reg("soglia_parita", config.SOGLIA_PARITA_PP, "int", "Soglia in punti percentuali dell'ipotesi 3", "config.py, SOGLIA_PARITA_PP")
    reg("s_ip1_quota", config.SOGLIE["ip1_quota"], "pct0", "Soglia della prima ipotesi: quota di vittorie del lump sum", "config.py, SOGLIE")
    reg("s_ip2_scende", config.SOGLIE["ip2_scende"], "pct0", "Soglia della seconda ipotesi: vittorie del PAC quando l'indice scende", "config.py, SOGLIE")
    reg("s_ip2_sale", config.SOGLIE["ip2_sale"], "pct0", "Soglia della seconda ipotesi: vittorie del PAC quando l'indice sale", "config.py, SOGLIE")
    reg("s_ip5_salto", config.SOGLIE["ip5_salto_pp"], "int", "Soglia della quinta ipotesi: aumento della quota del lump sum con i costi (punti)", "config.py, SOGLIE")
    reg("s_ip6_lo", config.SOGLIE["ip6_lo"], "pct0", "Estremo inferiore della sesta ipotesi", "config.py, SOGLIE")
    reg("s_ip6_hi", config.SOGLIE["ip6_hi"], "pct0", "Estremo superiore della sesta ipotesi", "config.py, SOGLIE")
    reg("s_alfa", config.SOGLIE["alfa"], "num2", "Soglia di significatività dopo la correzione di Holm", "config.py, SOGLIE")
    reg("data_scarico", META["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")

    pd.concat(righe_part).to_csv(config.RISULTATI / "partenze.csv", index=False, float_format="%.4f")
    pd.DataFrame(righe_rim).to_csv(config.RISULTATI / "rimescolate.csv", index=False, float_format="%.5f")
    pd.DataFrame(righe_cal).to_csv(config.RISULTATI / "per_mese_calendario.csv", index=False, float_format="%.4f")
    (config.RISULTATI / "indici_usati.json").write_text(json.dumps(usati, ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri su {len(usati)} indici")


if __name__ == "__main__":
    main()
