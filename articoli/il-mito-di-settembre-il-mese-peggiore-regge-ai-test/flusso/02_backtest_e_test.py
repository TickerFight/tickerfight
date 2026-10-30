"""Passo 2 - Il mito di settembre sull'S&P 500.

Legge SOLO dati/gspc_giornaliero.csv; produce in risultati/: metriche.json, medie_mensili.csv, settembri.csv.
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
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def mese_peggiore(x: pd.Series) -> int:
    return int(x.groupby(x.index.month).mean().idxmin())


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(config.SEME)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    rs = fx.rendimenti_mensili(close)
    mm = rs.index.month.to_numpy()
    sett = (mm == config.MESE)
    reg("prima_data", str(close.index[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_ultima", str(close.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("n_mesi", len(rs), "int", "Mesi completi", "dati/")
    reg("n_sett", int(sett.sum()), "int", "Settembri nel campione", "dati/")
    reg("n_perm", config.N_PERMUTAZIONI, "int", "Permutazioni", "config.py")
    reg("soglia_p", config.SOGLIA_P, "num2", "Soglia di significatività", "config.py")
    reg("n_peggiori", config.N_PEGGIORI, "int", "Settembri peggiori tolti nell'ipotesi 6", "config.py")

    medie = rs.groupby(rs.index.month).mean()
    pd.DataFrame({"mese": MESI, "media": medie.to_numpy()}).to_csv(config.RISULTATI / "medie_mensili.csv", index=False, float_format="%.6f")
    ordine = medie.sort_values().index.tolist()
    reg("rango_sett", ordine.index(config.MESE) + 1, "int", "Posizione di settembre dal peggiore (1 = il più basso)", "pandas")
    reg("sett_media", float(medie.loc[config.MESE]), "pct2", "Rendimento medio di settembre", "pandas")
    reg("altri_media", float(rs[~sett].mean()), "pct2", "Rendimento medio degli altri undici mesi", "pandas")
    reg("sett_mediana", float(rs[sett].median()), "pct2", "Rendimento mediano di settembre", "pandas")
    reg("sett_neg", float((rs[sett] < 0).mean()), "pct0", "Quota di settembri in calo", "pandas")
    reg("altri_neg", float((rs[~sett] < 0).mean()), "pct0", "Quota degli altri mesi in calo", "pandas")
    secondo = ordine[1]
    reg("secondo_nome", MESI[secondo - 1], "testo", "Secondo mese peggiore", "pandas")
    reg("secondo_media", float(medie.loc[secondo]), "pct2", "Rendimento medio del secondo mese peggiore", "pandas")
    reg("migliore_nome", MESI[ordine[-1] - 1], "testo", "Mese migliore", "pandas")
    reg("migliore_media", float(medie.loc[ordine[-1]]), "pct2", "Rendimento medio del mese migliore", "pandas")

    d, p = fx.permutazione_differenza(rs.to_numpy(), sett, config.N_PERMUTAZIONI, rng)
    reg("diff", d, "pp2", "Settembre meno gli altri mesi, punti percentuali", "funzioni")
    reg("pval", p, "pval", "P-value di permutazione di settembre contro gli altri mesi", "funzioni.permutazione_differenza")
    mn, pm = fx.minimo_permutazione(rs.to_numpy(), mm, config.N_PERMUTAZIONI, rng)
    reg("minimo", mn, "pct2", "Media più bassa tra i dodici mesi", "funzioni.minimo_permutazione")
    reg("pval_min", pm, "pval", "P-value della media più bassa dei dodici mesi, per permutazione dei rendimenti tra i mesi", "funzioni.minimo_permutazione")

    anni = sorted(set(rs.index.year))
    meta_anno = anni[len(anni) // 2]
    reg("anno_meta", meta_anno, "annonum", "Anno che divide il campione a metà", "dati/")
    for tag, sel in (("p", rs.index.year < meta_anno), ("d", rs.index.year >= meta_anno)):
        x = rs[sel]
        mp = mese_peggiore(x)
        reg(f"peggiore_{tag}", MESI[mp - 1], "testo", f"Mese con la media più bassa, metà {'prima' if tag == 'p' else 'seconda'}", "pandas")
        reg(f"sett_media_{tag}", float(x[x.index.month == config.MESE].mean()), "pct2", f"Rendimento medio di settembre, metà {'prima' if tag == 'p' else 'seconda'}", "pandas")
        reg(f"sett_rango_{tag}", int(x.groupby(x.index.month).mean().sort_values().index.tolist().index(config.MESE) + 1), "int", f"Posizione di settembre dal peggiore, metà {'prima' if tag == 'p' else 'seconda'}", "pandas")

    s = rs[sett].sort_values()
    pd.DataFrame({"anno": s.index.year, "rendimento": s.to_numpy()}).to_csv(config.RISULTATI / "settembri.csv", index=False, float_format="%.5f")
    reg("peggiore1", float(s.iloc[0]), "pct1", "Il settembre peggiore", "pandas")
    reg("anno_peggiore1", str(int(s.index[0].year)), "testo", "Anno del settembre peggiore", "pandas")
    senza = s.iloc[config.N_PEGGIORI:]
    reg("sett_media_senza", float(senza.mean()), "pct2", "Rendimento medio di settembre senza i tre peggiori", "pandas")

    h = [RIS["rango_sett"]["valore"] == 1, p < config.SOGLIA_P, pm >= config.SOGLIA_P,
         RIS["peggiore_p"]["valore"] == "settembre" and RIS["peggiore_d"]["valore"] == "settembre",
         RIS["sett_neg"]["valore"] > 0.5, float(senza.mean()) > 0]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "seme": config.SEME, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
