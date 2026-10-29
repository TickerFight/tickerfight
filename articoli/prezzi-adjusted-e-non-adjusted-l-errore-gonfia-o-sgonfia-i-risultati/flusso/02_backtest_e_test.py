"""Passo 2 - Prezzi adjusted e non adjusted: quanto sbaglia chi usa la colonna sbagliata.

Legge SOLO dati/<ticker>.csv e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine di calcolo
  strumenti.csv     una riga per strumento con i rendimenti annui delle varie versioni
  curve_spy.csv     SPY: valore di 500 euro a soli prezzi e a rendimento totale (una seduta su cinque)
  aapl_prezzi.csv   Apple: chiusura corretta per gli split e prezzo grezzo ricostruito (una seduta su cinque)
Versioni della regola 50/200 (sempre con segnale di ieri, senza commissioni né tasse):
  A  segnale su Adj Close, rendimento su Adj Close   (riferimento corretto)
  B  segnale su Close,     rendimento su Adj Close   (solo il segnale è «sbagliato»)
  C  segnale su Close,     rendimento su Close       (si valuta anche il rendimento sui soli prezzi)
  D  segnale sul prezzo grezzo (senza correzione split), rendimento su Adj Close
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
    if x < 1e9:
        return f"{x:,.0f}".replace(",", ".") + " euro"
    return f"un numero con {int(np.floor(np.log10(x))) + 1} cifre"


def regola(prezzo_segnale: pd.Series, rend: pd.Series, i0: int) -> tuple[pd.Series, pd.Series]:
    s = m.segnale_medie(prezzo_segnale, config.SMA_VELOCE, config.SMA_LENTA)
    pos = m.posizione(s, config.RITARDO_ONESTO).iloc[i0:]
    return pos, m.valore(rend.iloc[i0:], pos)


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    i0 = config.INIZIO_TEST_SEDUTE
    righe = []
    for chiave, ticker, nome in config.STRUMENTI:
        df = pd.read_csv(config.DATI / f"{ticker}.csv", parse_dates=["Date"], index_col="Date").sort_index()
        close, adj = df["Close"].astype(float), df["Adj Close"].astype(float)
        div, spl = df["Dividends"].astype(float), df["Stock Splits"].astype(float)
        if len(df) <= i0 + 250:
            raise SystemExit(f"Dati troppo corti per {ticker}")
        grezzo = m.ricostruisci_grezzo(close, spl)
        r_close, r_adj, r_grezzo = m.rendimenti(close), m.rendimenti(adj), m.rendimenti(grezzo)
        date = close.index
        anni = (date[-1] - date[i0 - 1]).days / 365.25
        w = slice(i0, None)
        tutti = pd.Series(True, index=date[w])
        v_p, v_t = m.valore(r_close.iloc[w], tutti), m.valore(r_adj.iloc[w], tutti)
        c_p, c_t = m.cagr(v_p, anni), m.cagr(v_t, anni)
        yld = float((div.iloc[w] / close.shift(1).iloc[w]).fillna(0).sum() / anni)
        reg(f"{chiave}_nome", nome, "testo", f"Nome dello strumento {ticker}", "config.py, STRUMENTI")
        reg(f"{chiave}_inizio", str(date[i0].date()), "anno", f"Anno di inizio del test per {ticker}", f"dati/{ticker}.csv")
        reg(f"{chiave}_anni", anni, "num1", f"Anni del test per {ticker}")
        reg(f"{chiave}_cagr_prezzo", c_p, "pct1", f"Rendimento annuo del buy & hold sulla colonna Close (solo prezzo), {ticker}")
        reg(f"{chiave}_cagr_totale", c_t, "pct1", f"Rendimento annuo del buy & hold sulla colonna Adj Close (rendimento totale), {ticker}")
        reg(f"{chiave}_gap", c_t - c_p, "pp2", f"Divario: rendimento annuo totale meno rendimento annuo dei soli prezzi, punti percentuali, {ticker}")
        reg(f"{chiave}_yield", yld, "pct1", f"Dividend yield medio annuo (somma dei dividendi diviso la chiusura precedente, per anno), {ticker}")
        reg(f"{chiave}_finale_prezzo", importo(config.CAPITALE * v_p.iloc[-1]), "testo", f"Valore finale di {config.CAPITALE:.0f} euro sui soli prezzi, {ticker}")
        reg(f"{chiave}_finale_totale", importo(config.CAPITALE * v_t.iloc[-1]), "testo", f"Valore finale di {config.CAPITALE:.0f} euro a rendimento totale, {ticker}")
        rapporto = float(v_p.iloc[-1] / v_t.iloc[-1])
        reg(f"{chiave}_rapporto", rapporto, "pct0", f"Capitale finale a soli prezzi diviso capitale finale a rendimento totale, {ticker}")
        reg(f"{chiave}_n_split", int((spl > 0).sum()), "int", f"Split nella storia scaricata, {ticker}", f"dati/{ticker}.csv")
        reg(f"{chiave}_n_div", int((div.iloc[w] > 0).sum()), "int", f"Stacchi di dividendo nel periodo del test, {ticker}", f"dati/{ticker}.csv")

        # --- regola 50/200 ---
        pA, vA = regola(adj, r_adj, i0)
        pB, vB = regola(close, r_adj, i0)
        pC, vC = regola(close, r_close, i0)
        pD, vD = regola(grezzo, r_adj, i0)
        cA, cB, cC, cD = (m.cagr(v, anni) for v in (vA, vB, vC, vD))
        cambi = lambda p: int(p.astype(int).diff().abs().sum())
        reg(f"{chiave}_s_A", cA, "pct1", f"Regola 50/200, segnale su Adj Close, rendimento totale (versione corretta), {ticker}")
        reg(f"{chiave}_s_B", cB, "pct1", f"Regola 50/200, segnale su Close, rendimento totale, {ticker}")
        reg(f"{chiave}_s_C", cC, "pct1", f"Regola 50/200, segnale su Close, rendimento sui soli prezzi, {ticker}")
        reg(f"{chiave}_s_D", cD, "pct1", f"Regola 50/200, segnale sul prezzo grezzo senza correzione degli split, rendimento totale, {ticker}")
        reg(f"{chiave}_s_diff_segnale", cB - cA, "pp2", f"Cambio di rendimento annuo usando Close invece di Adj Close per il segnale, punti percentuali, {ticker}")
        reg(f"{chiave}_s_err_misura", cB - cC, "pp2", f"Errore sul rendimento annuo della regola valutata sui soli prezzi, punti percentuali, {ticker}")
        reg(f"{chiave}_s_quota", float(pB.mean()), "pct0", f"Quota di sedute investite, regola 50/200, {ticker}")
        reg(f"{chiave}_s_cambi_A", cambi(pA), "int", f"Cambi di posizione con prezzi corretti, {ticker}")
        reg(f"{chiave}_s_cambi_D", cambi(pD), "int", f"Cambi di posizione con prezzi grezzi, {ticker}")
        reg(f"{chiave}_peggior_grezzo", float(r_grezzo.iloc[w].min()), "pct0", f"Peggior rendimento giornaliero sui prezzi grezzi, {ticker}")
        reg(f"{chiave}_peggior_corretto", float(r_close.iloc[w].min()), "pct0", f"Peggior rendimento giornaliero sui prezzi corretti per gli split, {ticker}")
        righe.append({"chiave": chiave, "ticker": ticker, "yield": yld, "cagr_prezzo": c_p, "cagr_totale": c_t, "gap": c_t - c_p,
                      "A": cA, "B": cB, "C": cC, "D": cD, "err_misura": cB - cC, "diff_segnale": cB - cA,
                      "cambi_A": cambi(pA), "cambi_D": cambi(pD), "n_split": int((spl > 0).sum()), "rapporto": rapporto})
        if chiave == "spy":
            camp = np.r_[np.arange(0, len(v_p), 5), len(v_p) - 1]
            pd.DataFrame({"data": v_p.index[camp], "prezzo": config.CAPITALE * v_p.iloc[camp].to_numpy(),
                          "totale": config.CAPITALE * v_t.iloc[camp].to_numpy()}).to_csv(config.RISULTATI / "curve_spy.csv", index=False, float_format="%.6f")
        if chiave == "aapl":
            camp = np.r_[np.arange(0, len(close), 5), len(close) - 1]
            pd.DataFrame({"data": date[camp], "corretto": close.iloc[camp].to_numpy(), "grezzo": grezzo.iloc[camp].to_numpy()}
                         ).to_csv(config.RISULTATI / "aapl_prezzi.csv", index=False, float_format="%.6f")

    t = pd.DataFrame(righe)
    t.to_csv(config.RISULTATI / "strumenti.csv", index=False, float_format="%.6f")
    n = len(t)
    reg("n_strumenti", n, "int", "Strumenti analizzati", "config.py, STRUMENTI")
    reg("n_h1", int((t["gap"] > 0).sum()), "int", "Strumenti per cui il rendimento totale supera quello dei soli prezzi", "strumenti.csv")
    rho = float(t["yield"].rank().corr(t["gap"].rank()))
    reg("spearman", rho, "num2", "Correlazione di rango (Spearman) tra dividend yield medio e divario", "strumenti.csv")
    reg("h2_ok", int(rho > config.SOGLIA_SPEARMAN), "int", "1 se la correlazione di rango supera la soglia dell'ipotesi 2", "config.py, SOGLIA_SPEARMAN")
    reg("soglia_spearman", config.SOGLIA_SPEARMAN, "num1", "Soglia di correlazione dell'ipotesi 2", "config.py")
    spy = t.set_index("chiave").loc["spy"]
    reg("h3_ok", int(spy["rapporto"] < config.SOGLIA_RAPPORTO_SPY), "int", "1 se per SPY il capitale a soli prezzi è sotto la soglia del capitale totale", "config.py, SOGLIA_RAPPORTO_SPY")
    reg("soglia_rapporto", config.SOGLIA_RAPPORTO_SPY, "pct0", "Soglia dell'ipotesi 3", "config.py")
    reg("n_h4", int((t["diff_segnale"].abs() < config.SOGLIA_SEGNALE_PP).sum()), "int", "Strumenti per cui il segnale su Close cambia il rendimento annuo di meno della soglia", "strumenti.csv")
    reg("soglia_segnale", config.SOGLIA_SEGNALE_PP, "pp1", "Soglia dell'ipotesi 4, punti percentuali", "config.py")
    reg("diff_segnale_max", float(t["diff_segnale"].abs().max()), "pp2", "Massimo scarto assoluto di rendimento annuo dovuto al segnale su Close, punti percentuali", "strumenti.csv")
    reg("n_h5", int((t["err_misura"] < t["gap"]).sum()), "int", "Strumenti per cui l'errore di misura della regola è più piccolo del divario del buy & hold", "strumenti.csv")
    ap = t.set_index("chiave").loc["aapl"]
    reg("h6_ok", int(ap["cambi_D"] > ap["cambi_A"] and ap["D"] < ap["A"]), "int", "1 se per Apple i prezzi grezzi producono più cambi e meno rendimento", "strumenti.csv")
    reg("n_strumenti_split", int((t["n_split"] > 0).sum()), "int", "Strumenti con almeno uno split nella storia", "strumenti.csv")
    reg("hs_anno", 2019, "annonum", "Anno di pubblicazione di Hartzmark e Solomon, «The Dividend Disconnect», Journal of Finance", "doi.org/10.1111/jofi.12785")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale, solo per dare un'idea (valori lordi)", "config.py, CAPITALE")
    reg("sma_veloce", config.SMA_VELOCE, "annonum", "Giorni della media veloce", "config.py")
    reg("sma_lenta", config.SMA_LENTA, "annonum", "Giorni della media lenta", "config.py")
    reg("sedute_avvio", config.INIZIO_TEST_SEDUTE, "int", "Sedute iniziali usate solo per calcolare le medie", "config.py")
    reg("gap_max", float(t["gap"].max()), "pp2", "Divario massimo tra gli strumenti, punti percentuali", "strumenti.csv")
    reg("gap_min", float(t["gap"].min()), "pp2", "Divario minimo tra gli strumenti, punti percentuali", "strumenti.csv")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")
    print(t.round(4).to_string())


if __name__ == "__main__":
    main()
