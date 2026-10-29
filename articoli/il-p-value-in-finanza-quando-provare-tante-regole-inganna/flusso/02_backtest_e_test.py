"""Passo 2 - Il p-value in finanza: cinquanta regole a media mobile sull'S&P 500, test multipli e replicazione.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine
  regole.csv        per ogni regola: t, p-value, p-value corretti (Holm, Benjamini-Hochberg), CAGR della regola
  nulla.csv         per ogni spostamento circolare: massimo |t| e numero di regole sopra la soglia
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
    L = list(config.LUNGHEZZE)
    K = len(L)
    S, r = fx.segnali_sma(close.to_numpy(), L, max(L))
    date = close.index[max(L) + 1:]
    m = len(r)
    rng = np.random.default_rng(config.SEME)
    ik = L.index(config.LUNGHEZZA_FAMOSA)

    reg("prima_data", str(date[0].date()), "data_lunga", "Prima seduta del campione comune alle regole", "dati/")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("n_sedute", m, "int", "Rendimenti giornalieri del campione comune", "dati/")
    reg("anni", m / GA, "num1", "Anni del campione comune (sedute diviso 252)", "dati/")
    reg("n_regole", K, "int", "Regole provate", "config.py, LUNGHEZZE")
    reg("lung_min", min(L), "int", "Lunghezza minima della media mobile", "config.py")
    reg("lung_max", max(L), "int", "Lunghezza massima della media mobile", "config.py")
    reg("lung_famosa", config.LUNGHEZZA_FAMOSA, "int", "Lunghezza della regola più nota, dichiarata in anticipo", "config.py")
    reg("soglia", config.SOGLIA, "pct0", "Livello di significatività", "config.py")
    reg("n_spost", config.N_SPOSTAMENTI, "int", "Spostamenti circolari del test a permutazione", "config.py")
    reg("h2_regole", config.H2_REGOLE, "int", "Ipotesi 2: soglia sul numero di regole significative", "config.py")
    reg("h3_regole", config.H3_REGOLE, "int", "Ipotesi 3: regole che devono restare significative dopo Holm", "config.py")

    # --- Test regola per regola -------------------------------------------------------------------------------------------
    t = fx.welch_t(r, S)
    p = fx.p_normale(t)
    p_holm, p_bh = fx.holm(p), fx.benjamini_hochberg(p)
    quota_inv = S.mean(axis=0)
    diff_ann = np.array([(r[S[:, k] == 1].mean() - r[S[:, k] == 0].mean()) * GA for k in range(K)])
    rule_cagr = np.array([fx.cagr(S[:, k] * r, GA) for k in range(K)])
    cagr_bh = fx.cagr(r, GA)
    pd.DataFrame({"lunghezza": L, "t": t, "p": p, "p_holm": p_holm, "p_bh": p_bh, "quota_investita": quota_inv,
                  "diff_annua": diff_ann, "cagr_regola": rule_cagr}).to_csv(config.RISULTATI / "regole.csv", index=False, float_format="%.6g")
    reg("t_famosa", float(t[ik]), "num2", "Statistica t di Welch della regola a 200 sedute", "funzioni.welch_t")
    reg("p_famosa", float(p[ik]), "pval", "P-value (due code) della regola a 200 sedute, presa da sola", "funzioni.p_normale")
    reg("diff_famosa", float(diff_ann[ik]), "pp1", "Differenza annualizzata tra rendimento medio dei giorni investiti e dei giorni fermi, regola a 200 sedute, in punti", "dati/")
    reg("quota_inv_famosa", float(quota_inv[ik]), "pct0", "Quota di giorni in cui la regola a 200 sedute è investita", "dati/")
    reg("n_sig", int((p < config.SOGLIA).sum()), "int", "Regole con p-value sotto il 5% (senza correzioni)", "funzioni.p_normale")
    reg("n_sig_holm", int((p_holm < config.SOGLIA).sum()), "int", "Regole significative al 5% dopo la correzione di Holm", "funzioni.holm")
    reg("n_sig_bh", int((p_bh < config.SOGLIA).sum()), "int", "Regole significative al 5% dopo la correzione di Benjamini-Hochberg", "funzioni.benjamini_hochberg")
    reg("n_sig_bonf", int((p < config.SOGLIA / K).sum()), "int", "Regole significative con la soglia di Bonferroni (5% diviso il numero di regole)", "funzioni.p_normale")
    reg("soglia_bonf", config.SOGLIA / K, "pct2", "Soglia di Bonferroni", "calcolo")
    reg("fwer_indip", 1 - (1 - config.SOGLIA) ** K, "pct0", "Probabilità di almeno un falso positivo con cinquanta test indipendenti al 5%", "formula 1 - 0,95^50")
    ib = int(np.argmax(np.abs(t)))
    reg("lung_migliore", L[ib], "int", "Lunghezza della regola con |t| massimo", "funzioni.welch_t")
    reg("t_migliore", float(t[ib]), "num2", "Statistica t della regola con |t| massimo", "funzioni.welch_t")
    reg("p_migliore", float(p[ib]), "pval", "P-value grezzo della regola con |t| massimo", "funzioni.p_normale")
    reg("t_min_sig", float(np.abs(t).min()), "num2", "|t| minimo tra le cinquanta regole", "funzioni.welch_t")
    reg("n_t_pos", int((t > 0).sum()), "int", "Regole con t positivo (i giorni investiti rendono più dei giorni fermi)", "funzioni.welch_t")

    # --- Spostamenti circolari: il massimo |t| sotto l'ipotesi nulla -----------------------------------------------------
    mx, cn = fx.spostamenti(r, S, config.N_SPOSTAMENTI, config.SPOSTAMENTO_MIN, rng)
    pd.DataFrame({"max_t": mx, "n_sig": cn}).to_csv(config.RISULTATI / "nulla.csv", index=False, float_format="%.5f")
    p_adj_best = float((1 + np.sum(mx >= abs(t[ib]))) / (config.N_SPOSTAMENTI + 1))
    p_adj_fam = float((1 + np.sum(mx >= abs(t[ik]))) / (config.N_SPOSTAMENTI + 1))
    soglia_t = float(np.percentile(mx, 95))
    reg("p_adj_migliore", p_adj_best, "pval", "P-value corretto (massimo |t| con spostamenti circolari) della regola migliore", "funzioni.spostamenti")
    reg("p_adj_famosa", p_adj_fam, "pval", "P-value corretto della regola a 200 sedute con lo stesso metodo", "funzioni.spostamenti")
    reg("t_soglia_max", soglia_t, "num2", "95° percentile del massimo |t| sotto l'ipotesi nulla", "funzioni.spostamenti")
    reg("max_t_mediano", float(np.median(mx)), "num2", "Massimo |t| mediano sotto l'ipotesi nulla", "funzioni.spostamenti")
    reg("n_sig_maxt", int((np.abs(t) > soglia_t).sum()), "int", "Regole con |t| sopra il 95° percentile del massimo nullo", "funzioni.spostamenti")
    reg("nulla_media", float(cn.mean()), "num1", "Numero medio di regole sopra la soglia per caso, negli spostamenti circolari", "funzioni.spostamenti")
    reg("nulla_quota_almeno1", float((cn >= 1).mean()), "pct0", "Quota di spostamenti con almeno una regola sopra la soglia per caso", "funzioni.spostamenti")
    reg("nulla_max", int(cn.max()), "int", "Massimo numero di regole sopra la soglia per caso in uno spostamento", "funzioni.spostamenti")

    # --- Replicazione: migliore della prima metà, misurata sulla seconda -------------------------------------------------
    h = m // 2
    t1 = fx.welch_t(r[:h], S[:h])
    j = int(np.argmax(np.abs(t1)))
    t2 = fx.welch_t(r[h:], S[h:])
    p2 = fx.p_normale(t2)
    reg("rep_lung", L[j], "int", "Lunghezza della regola migliore nella prima metà", "funzioni.welch_t")
    reg("rep_t1", float(t1[j]), "num2", "t della regola migliore nella prima metà", "funzioni.welch_t")
    reg("rep_t2", float(t2[j]), "num2", "t della stessa regola nella seconda metà", "funzioni.welch_t")
    reg("rep_p2", float(p2[j]), "pval", "P-value della stessa regola nella seconda metà", "funzioni.p_normale")
    reg("rep_anno", int(date[h].year), "annonum", "Anno in cui comincia la seconda metà", "dati/")
    reg("rep_n_sig2", int((p2 < config.SOGLIA).sum()), "int", "Regole con p-value sotto il 5% nella seconda metà", "funzioni.p_normale")
    reg("rep_n_sig1", int((fx.p_normale(t1) < config.SOGLIA).sum()), "int", "Regole con p-value sotto il 5% nella prima metà", "funzioni.p_normale")

    # --- Significativa non vuol dire redditizia ---------------------------------------------------------------------------
    reg("cagr_bh", cagr_bh, "pct1", "Rendimento annuo composto del buy & hold sul campione comune (indice di prezzo)", "funzioni.cagr")
    reg("cagr_migliore", float(rule_cagr[ib]), "pct1", "Rendimento annuo composto della regola migliore (ferma = rendimento zero)", "funzioni.cagr")
    reg("cagr_famosa", float(rule_cagr[ik]), "pct1", "Rendimento annuo composto della regola a 200 sedute", "funzioni.cagr")
    reg("n_cagr_sopra_bh", int((rule_cagr > cagr_bh).sum()), "int", "Regole con rendimento annuo composto sopra il buy & hold", "funzioni.cagr")
    reg("sharpe_bh", fx.sharpe(r, GA), "num2", "Sharpe del buy & hold nel campione comune", "funzioni.sharpe")
    reg("sharpe_migliore", fx.sharpe(S[:, ib] * r, GA), "num2", "Sharpe della regola migliore", "funzioni.sharpe")
    reg("quota_inv_migliore", float(quota_inv[ib]), "pct0", "Quota di giorni in cui la regola migliore è investita", "dati/")

    # --- Verdetti -----------------------------------------------------------------------------------------------------------
    hh = [p[ik] < config.SOGLIA,
          int((p < config.SOGLIA).sum()) > config.H2_REGOLE,
          int((p_holm < config.SOGLIA).sum()) >= config.H3_REGOLE,
          p_adj_best < config.SOGLIA,
          bool(p2[j] < config.SOGLIA and np.sign(t2[j]) == np.sign(t1[j])),
          rule_cagr[ib] < cagr_bh]
    for i, v in enumerate(hh, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in hh)), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "seme": config.SEME, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
