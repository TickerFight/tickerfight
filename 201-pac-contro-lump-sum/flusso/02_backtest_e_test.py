"""Passo 2 - PAC contro lump sum: cinque lunghezze di PAC, valutazione a 60 mesi, su ogni mese di partenza.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json            ogni numero dell'articolo, con descrizione e origine di calcolo
  partenze_sp500.csv       per ogni mese di partenza dell'S&P 500: valore di lump sum e PAC per ogni lunghezza, massimi, decennio
  quote_per_lunghezza.csv  quota di vittorie del lump sum per indice e lunghezza del PAC
  per_decennio.csv         quota di vittorie del lump sum per decennio di partenza (S&P 500, PAC di riferimento)
  indici_usati.json        indici effettivamente usati

Lump sum: tutto il budget al primo giorno di Borsa del mese di partenza. PAC a N rate: un N-esimo del budget al primo giorno di
Borsa di ciascuno degli N mesi di partenza. Valutazione al primo giorno di Borsa del mese t+60. Nessun look-ahead: le date delle
rate sono decise alla partenza e il segnale "ai massimi" usa solo i prezzi fino al mese di partenza.
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
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    rng = np.random.default_rng(config.SEME)
    B, H, NP = config.BUDGET, config.ORIZZONTE, config.N_PRINCIPALE
    righe_quote, usati = [], []
    quote_ind: dict[str, list[float]] = {}

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
        principale = ticker == config.INDICE_PRINCIPALE
        n = len(p) - H
        part = date_m[:n]
        anni = np.array([d.year for d in part])
        reg(f"{sl}_prima_data", str(date_m[0].date()), "data_lunga", f"Primo mese di dati di {nome}", "dati/")
        reg(f"{sl}_anno_inizio", str(date_m[0].date()), "anno", f"Anno del primo dato di {nome}", "dati/")
        reg(f"{sl}_n_part", n, "int", f"Mesi di partenza usati per {nome} (con valutazione a {H} mesi)", "numero di mesi meno l'orizzonte")
        reg(f"{sl}_ultima_partenza", str(part[-1].date()), "data_lunga", f"Ultimo mese di partenza di {nome}", "dati/")

        lump = fx.valore_lump(p, H, B)
        quote = []
        pacs = {}
        for N in config.RATE:
            pac = fx.valore_pac(p, H, B, N)
            pacs[N] = pac
            diff = (pac - lump) / B * 100                      # punti percentuali del budget; > 0 vince il PAC
            vince_lump = lump > pac
            q = float(vince_lump.mean())
            quote.append(q)
            lo, hi = ic_cluster(vince_lump, anni, rng)
            tag = f"{sl}_n{N}"
            reg(f"{tag}_quota_lump", q, "pct0", f"Quota di partenze in cui il lump sum batte il PAC a {N} rate, {nome}, valutazione a {H} mesi")
            reg(f"{tag}_quota_lump_lo", lo, "pct0", f"Estremo inferiore dell'intervallo di confidenza della quota di vittorie del lump sum, PAC a {N} rate, {nome}", "ricampionamento degli anni di partenza (N_BOOTSTRAP)")
            reg(f"{tag}_quota_lump_hi", hi, "pct0", f"Estremo superiore dell'intervallo di confidenza della quota di vittorie del lump sum, PAC a {N} rate, {nome}", "ricampionamento degli anni di partenza (N_BOOTSTRAP)")
            reg(f"{tag}_diff_med", float(np.median(diff)), "num1", f"Differenza mediana PAC meno lump sum in punti percentuali del budget, PAC a {N} rate, {nome}")
            reg(f"{tag}_media_vantaggio_lump", float((-diff[vince_lump]).mean()) if vince_lump.any() else 0.0, "num1", f"Vantaggio medio del lump sum nelle partenze che vince (punti del budget), PAC a {N} rate, {nome}")
            reg(f"{tag}_media_vantaggio_pac", float(diff[~vince_lump].mean()) if (~vince_lump).any() else 0.0, "num1", f"Vantaggio medio del PAC nelle partenze che vince (punti del budget), PAC a {N} rate, {nome}")
            righe_quote.append({"ticker": ticker, "rate": N, "quota_lump": q, "ic_lo": lo, "ic_hi": hi, "diff_mediana_pp": float(np.median(diff)), "n_partenze": n})
        crescente = all(b > a for a, b in zip(quote, quote[1:]))
        quote_ind[sl] = quote
        reg(f"{sl}_crescente", int(crescente), "int", f"1 se la quota di vittorie del lump sum cresce a ogni passo da {config.RATE[0]} a {config.RATE[-1]} rate, 0 altrimenti ({nome})", "confronto tra quote consecutive")
        reg(f"{sl}_quota_min", min(quote), "pct0", f"Quota più bassa di vittorie del lump sum tra le cinque lunghezze del PAC, {nome}")

        if principale:
            sp = sl
            pac = pacs[NP]
            diff = (pac - lump) / B * 100
            vince_lump = lump > pac
            part_df = pd.DataFrame({"partenza": part.date, "decennio": [fx.decennio(d) for d in part], "lump": lump})
            for N in config.RATE:
                part_df[f"pac_{N}"] = pacs[N]
            vicino = fx.vicino_ai_massimi(p, config.SOGLIA_MASSIMI)[:n]
            part_df["ai_massimi"] = vicino
            part_df.to_csv(config.RISULTATI / "partenze_sp500.csv", index=False, float_format="%.4f")

            # ipotesi 1: tutte e cinque le lunghezze sopra la soglia
            reg("sp_quota_min", min(quote), "pct0", f"Quota più bassa di vittorie del lump sum tra le cinque lunghezze del PAC, {nome}")
            reg("sp_n_lunghezze_sopra", int(sum(q > config.SOGLIE["ip1_quota"] for q in quote)), "int", f"Lunghezze del PAC (su cinque) con quota di vittorie del lump sum sopra la soglia della prima ipotesi, {nome}", "confronto con config.SOGLIE")

            reg("sp_range_lunghezza", (max(quote) - min(quote)) * 100, "num1", f"Distanza in punti percentuali tra la quota più alta e la più bassa di vittorie del lump sum tra le cinque lunghezze del PAC, {nome}")

            # vantaggio in euro del lump sum su 60 mesi: multiplo del budget
            reg("sp_lump_multiplo_mediano", float(np.median(lump) / B), "num2", f"Valore mediano del lump sum a {H} mesi diviso il budget, {nome} (indice di prezzo, senza dividendi)")
            reg("sp_pac_multiplo_mediano", float(np.median(pac) / B), "num2", f"Valore mediano del PAC a {NP} rate a {H} mesi diviso il budget, {nome}")
            reg("sp_quota_mercato_sale", float((p[H:H + n] > p[:n]).mean()), "pct0", f"Quota di partenze in cui l'indice sale tra la partenza e la valutazione a {H} mesi, {nome}")
            sale = p[H:H + n] > p[:n]
            reg("sp_pac_vince_se_scende", float((~vince_lump)[~sale].mean()), "pct0", f"Quota di vittorie del PAC a {NP} rate tra le partenze in cui l'indice scende nei {H} mesi, {nome}")
            reg("sp_pac_vince_se_sale", float((~vince_lump)[sale].mean()), "pct0", f"Quota di vittorie del PAC a {NP} rate tra le partenze in cui l'indice sale nei {H} mesi, {nome}")
            reg("sp_n_scende", int((~sale).sum()), "int", f"Partenze in cui l'indice scende nei {H} mesi, {nome}")

            # decenni
            dec = np.array([fx.decennio(d) for d in part])
            righe_dec = []
            n_pac_magg = 0
            for d in config.DECENNI:
                sel = dec == d
                qd = float(vince_lump[sel].mean())
                righe_dec.append({"decennio": d, "n_partenze": int(sel.sum()), "quota_lump": qd,
                                  "diff_mediana_pp": float(np.median(diff[sel])), "sale": float(sale[sel].mean())})
                reg(f"dec{d}_quota_lump", qd, "pct0", f"Quota di vittorie del lump sum con il PAC a {NP} rate, partenze del decennio {d}, {nome}")
                reg(f"dec{d}_anno", d, "annonum", f"Decennio di partenza {d} (etichetta)", "config.py, DECENNI")
                reg(f"dec{d}_n", int(sel.sum()), "int", f"Mesi di partenza del decennio {d}, {nome}")
                reg(f"dec{d}_diff_med", float(np.median(diff[sel])), "num1", f"Differenza mediana PAC meno lump sum (punti del budget), partenze del decennio {d}, {nome}")
                n_pac_magg += int(qd < 0.5)
            pd.DataFrame(righe_dec).to_csv(config.RISULTATI / "per_decennio.csv", index=False, float_format="%.4f")
            qs = {r["decennio"]: r["quota_lump"] for r in righe_dec}
            d_pac = min(qs, key=qs.get)
            d_lump = max(qs, key=qs.get)
            reg("dec_n_pac_maggioranza", n_pac_magg, "int", f"Decenni di partenza in cui il PAC a {NP} rate vince la maggioranza delle partenze, {nome}", "conteggio dei decenni con quota del lump sum sotto il 50%")
            reg("dec_n_decenni", len(config.DECENNI), "int", "Decenni di partenza considerati", "config.py, DECENNI")
            reg("dec_migliore_pac", d_pac, "annonum", f"Decennio di partenza più favorevole al PAC a {NP} rate, {nome}", "per_decennio.csv")
            reg("dec_migliore_pac_quota_pac", 1 - qs[d_pac], "pct0", f"Quota di vittorie del PAC nel decennio più favorevole al PAC, {nome}", "per_decennio.csv")
            reg("dec_migliore_lump", d_lump, "annonum", f"Decennio di partenza più favorevole al lump sum, {nome}", "per_decennio.csv")
            reg("dec_migliore_lump_quota", qs[d_lump], "pct0", f"Quota di vittorie del lump sum nel decennio più favorevole al lump sum, {nome}", "per_decennio.csv")
            reg("dec_range", (max(qs.values()) - min(qs.values())) * 100, "num1", f"Distanza in punti percentuali tra il decennio con la quota più alta e quello con la quota più bassa di vittorie del lump sum, {nome}", "per_decennio.csv")
            reg("dec_prima", config.DECENNI[0], "annonum", "Primo decennio di partenza considerato", "config.py, DECENNI")
            reg("dec_ultima", config.DECENNI[-1], "annonum", "Ultimo decennio di partenza considerato", "config.py, DECENNI")
            reg("dec_fuori", int(n - sum(int((dec == d).sum()) for d in config.DECENNI)), "int", f"Mesi di partenza di {nome} fuori dai decenni considerati (1927-1929 e dal 2020)", "n_part meno partenze nei decenni")

            # partenze vicino ai massimi
            q_mass = float(vince_lump[vicino].mean())
            q_altre = float(vince_lump[~vicino].mean())
            reg("mass_soglia", config.SOGLIA_MASSIMI, "pct0", "Distanza dal massimo storico entro cui una partenza è «ai massimi»", "config.py, SOGLIA_MASSIMI")
            reg("mass_n", int(vicino.sum()), "int", f"Mesi di partenza ai massimi, {nome}", "funzioni.vicino_ai_massimi")
            reg("mass_n_altre", int((~vicino).sum()), "int", f"Mesi di partenza non ai massimi, {nome}", "funzioni.vicino_ai_massimi")
            reg("mass_quota_lump", q_mass, "pct0", f"Quota di vittorie del lump sum con PAC a {NP} rate nelle partenze ai massimi, {nome}")
            reg("mass_quota_lump_altre", q_altre, "pct0", f"Quota di vittorie del lump sum con PAC a {NP} rate nelle altre partenze, {nome}")
            reg("mass_distanza", abs(q_mass - q_altre) * 100, "num1", f"Distanza in punti percentuali tra le due quote (ai massimi e altre), {nome}", "differenza in valore assoluto")
            reg("mass_diff_med", float(np.median(diff[vicino])), "num1", f"Differenza mediana PAC meno lump sum (punti del budget) nelle partenze ai massimi, {nome}")
            reg("mass_diff_med_altre", float(np.median(diff[~vicino])), "num1", f"Differenza mediana PAC meno lump sum (punti del budget) nelle altre partenze, {nome}")

            # esiti peggiori
            reg("code_lump_p5", float(np.quantile(lump, 0.05)), "int", f"Quinto percentile del valore finale in euro del lump sum a {H} mesi, {nome} (budget {B:.0f} euro)")
            reg("code_pac_p5", float(np.quantile(pac, 0.05)), "int", f"Quinto percentile del valore finale in euro del PAC a {NP} rate a {H} mesi, {nome}")
            reg("code_med_diff", float(np.median(lump) - np.median(pac)), "int", f"Valore mediano del lump sum meno valore mediano del PAC a {NP} rate, in euro, {nome}")
            reg("code_p5_diff", float(np.quantile(pac, 0.05) - np.quantile(lump, 0.05)), "int", f"Quinto percentile del PAC a {NP} rate meno quinto percentile del lump sum, in euro, {nome}")
            reg("code_lump_min", float(lump.min()), "int", f"Valore finale minimo in euro del lump sum a {H} mesi, {nome}")
            reg("code_pac_min", float(pac.min()), "int", f"Valore finale minimo in euro del PAC a {NP} rate a {H} mesi, {nome}")
            reg("code_lump_med", float(np.median(lump)), "int", f"Valore finale mediano in euro del lump sum a {H} mesi, {nome}")
            reg("code_pac_med", float(np.median(pac)), "int", f"Valore finale mediano in euro del PAC a {NP} rate a {H} mesi, {nome}")
            reg("code_lump_p95", float(np.quantile(lump, 0.95)), "int", f"Novantacinquesimo percentile del valore finale in euro del lump sum a {H} mesi, {nome}")
            reg("code_pac_p95", float(np.quantile(pac, 0.95)), "int", f"Novantacinquesimo percentile del valore finale in euro del PAC a {NP} rate a {H} mesi, {nome}")
            reg("code_lump_perde", float((lump < B).mean()), "pct0", f"Quota di partenze in cui il lump sum vale meno del budget dopo {H} mesi, {nome}")
            reg("code_pac_perde", float((pac < B).mean()), "pct0", f"Quota di partenze in cui il PAC a {NP} rate vale meno del budget dopo {H} mesi, {nome}")
            i_l, i_p = int(np.argmin(lump)), int(np.argmin(pac))
            reg("code_lump_min_data", str(part[i_l].date()), "data_lunga", f"Mese di partenza del peggior esito del lump sum, {nome}")
            reg("code_pac_min_data", str(part[i_p].date()), "data_lunga", f"Mese di partenza del peggior esito del PAC a {NP} rate, {nome}")
            i_max, i_min = int(np.argmax(diff)), int(np.argmin(diff))
            reg("sp_diff_max", float(diff[i_max]), "num1", f"Massimo vantaggio del PAC a {NP} rate sul lump sum (punti del budget), {nome}")
            reg("sp_diff_max_data", str(part[i_max].date()), "data_lunga", f"Mese di partenza del massimo vantaggio del PAC, {nome}")
            reg("sp_diff_min", float(-diff[i_min]), "num1", f"Massimo vantaggio del lump sum sul PAC a {NP} rate (punti del budget), {nome}")
            reg("sp_diff_min_data", str(part[i_min].date()), "data_lunga", f"Mese di partenza del massimo vantaggio del lump sum, {nome}")

            # scimmie
            sm = fx.valore_scimmia(p, H, B, NP, config.N_SCIMMIE, rng)
            batte_pac = (pac[:, None] > sm).mean(axis=1)
            reg("scim_pac_batte_mediana", float((batte_pac > 0.5).mean()), "pct0", f"Quota di partenze in cui il PAC regolare a {NP} rate batte più della metà delle scimmie, {nome}", "funzioni.valore_scimmia")
            reg("scim_lump_batte", float((lump[:, None] > sm).mean()), "pct0", f"Quota di coppie partenza-scimmia in cui il lump sum batte la scimmia, {nome}", "funzioni.valore_scimmia")
            reg("scim_diff_med", float(np.median((sm.mean(axis=1) - pac) / B * 100)), "num2", f"Differenza mediana tra valore medio delle scimmie e PAC regolare (punti del budget), {nome}", "funzioni.valore_scimmia")

    # ipotesi 2: monotonia in tutti gli indici
    reg("n_indici", len(usati), "int", "Indici usati", "dati/")
    reg("n_indici_crescenti", int(sum(all(b > a for a, b in zip(q, q[1:])) for q in quote_ind.values())), "int",
        "Indici in cui la quota di vittorie del lump sum cresce a ogni passo di lunghezza del PAC", "conteggio dei flag *_crescente")
    reg("budget", config.BUDGET, "int", "Budget totale da investire in euro", "config.py, BUDGET")
    reg("orizzonte", config.ORIZZONTE, "int", "Mesi tra la partenza e la valutazione", "config.py, ORIZZONTE")
    reg("orizzonte_anni", config.ORIZZONTE // 12, "int", "Anni tra la partenza e la valutazione", "config.py, ORIZZONTE")
    for k, N in enumerate(config.RATE, 1):
        reg(f"r{k}", N, "int", f"Lunghezza {k} del PAC in rate mensili", "config.py, RATE")
        reg(f"rata{k}", config.BUDGET / N, "int", f"Importo di ogni rata del PAC a {N} rate, in euro", "config.py, BUDGET / RATE")
    reg("n_principale", config.N_PRINCIPALE, "int", "Lunghezza del PAC di riferimento", "config.py, N_PRINCIPALE")
    reg("rata_principale", config.BUDGET / config.N_PRINCIPALE, "int", "Importo di ogni rata del PAC di riferimento, in euro", "config.py, BUDGET / N_PRINCIPALE")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie per ogni mese di partenza", "config.py, N_SCIMMIE")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py, LIVELLO_CONFIDENZA")
    reg("s_ip1_quota", config.SOGLIE["ip1_quota"], "pct0", "Soglia della prima ipotesi: quota di vittorie del lump sum", "config.py, SOGLIE")
    reg("s_ip3_min", config.SOGLIE["ip3_min_dec"], "int", "Soglia minima della terza ipotesi: decenni con PAC in maggioranza", "config.py, SOGLIE")
    reg("s_ip3_max", config.SOGLIE["ip3_max_dec"], "int", "Soglia massima della terza ipotesi: decenni con PAC in maggioranza", "config.py, SOGLIE")
    reg("s_ip4_pp", config.SOGLIE["ip4_pp"], "int", "Soglia della quarta ipotesi: distanza in punti percentuali tra le due quote", "config.py, SOGLIE")
    reg("s_ip6_lo", config.SOGLIE["ip6_lo"], "pct0", "Estremo inferiore della sesta ipotesi", "config.py, SOGLIE")
    reg("s_ip6_hi", config.SOGLIE["ip6_hi"], "pct0", "Estremo superiore della sesta ipotesi", "config.py, SOGLIE")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")

    pd.DataFrame(righe_quote).to_csv(config.RISULTATI / "quote_per_lunghezza.csv", index=False, float_format="%.4f")
    (config.RISULTATI / "indici_usati.json").write_text(json.dumps(usati, ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri su {len(usati)} indici")


if __name__ == "__main__":
    main()
