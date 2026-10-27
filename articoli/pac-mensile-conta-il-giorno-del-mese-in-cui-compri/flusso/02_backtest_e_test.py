"""Passo 2 - Piano di accumulo mensile: il giorno del mese conta?

Per ogni indice:
  - prezzo di acquisto di ogni giorno 1..28 in ogni mese completo (chiusura della prima seduta >= quel giorno);
  - valore finale netto del piano per ogni giorno (versamento fisso, commissione per acquisto, tassa alla vendita finale);
  - serie senza calendario: i rendimenti giornalieri vengono rimescolati; lo scarto (migliore - peggiore) osservato
    viene confrontato con quelli ottenuti sulle serie rimescolate (stessa media e volatilità, nessun calendario);
  - scimmie: ogni mese un giorno a caso;
  - confronto prima/seconda metà della storia e trasferimento del giorno migliore sugli altri indici.
Scrive risultati/metriche.json (ogni numero dell'articolo) e i csv di supporto.
"""
import json
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config

RIS: dict = {}
SORGENTE = "risultati/ (calcolato da 02_backtest_e_test.py)"


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.integer,)):
        valore = int(valore)
    elif isinstance(valore, (np.floating,)):
        valore = float(valore)
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def slug(ticker: str) -> str:
    return ticker.replace("^", "").replace(".", "_").lower()


def indici_acquisto(close: pd.Series):
    """Posizioni (mesi, 28) delle sedute di acquisto e posizione della seduta finale.

    Si usano solo i mesi completi: dal primo mese intero all'ultimo mese chiuso. Per ogni mese e giorno d si prende la
    prima seduta con giorno >= d. Seduta finale = ultima seduta dell'ultimo mese incluso.
    """
    c = close.dropna()
    c = c[c > 0]
    ym = c.index.to_period("M")
    primo = c.index[0].to_period("M") + 1                     # il primo mese può essere parziale
    ultimo = c.index[-1].to_period("M") - 1                   # l'ultimo mese può essere in corso
    righe, ok_mesi = [], []
    for m in pd.period_range(primo, ultimo, freq="M"):
        pos = np.flatnonzero(ym == m)
        if len(pos) == 0:
            continue
        giorni = c.index[pos].day.values
        r = []
        for d in config.GIORNI:
            k = np.searchsorted(giorni, d, side="left")
            r.append(pos[k] if k < len(pos) else -1)
        if min(r) < 0:
            continue
        righe.append(r)
        ok_mesi.append(m)
    ultima_pos = int(np.flatnonzero(ym == ultimo)[-1])
    return c.values.astype(float), np.array(righe, dtype=int), pd.PeriodIndex(ok_mesi), ultima_pos


def valore_netto(quote: np.ndarray, n_acquisti: int, prezzo_finale: float) -> np.ndarray:
    """Valore finale netto: quote * prezzo - tassa sulla plusvalenza (la commissione è già nelle quote)."""
    versato = n_acquisti * config.VERSAMENTO
    lordo = quote * prezzo_finale
    plus = lordo - versato - config.COMMISSIONE   # commissione di vendita finale
    tassa = np.where(plus > 0, config.ALIQUOTA * plus, 0.0)
    return lordo - config.COMMISSIONE - tassa


def quote_per_giorno(P: np.ndarray) -> np.ndarray:
    """Quote acquistate per ogni giorno: ogni mese si versa VERSAMENTO e si paga la commissione (si compra con il resto)."""
    return ((config.VERSAMENTO - config.COMMISSIONE) / P).sum(axis=0)


def holm(p: dict) -> dict:
    chiavi = sorted(p, key=lambda k: p[k])
    m = len(chiavi)
    out, massimo = {}, 0.0
    for i, k in enumerate(chiavi):
        massimo = max(massimo, min(1.0, (m - i) * p[k]))
        out[k] = massimo
    return out


def scarto(valori: np.ndarray) -> float:
    return float((valori.max() - valori.min()) / valori.mean())


def analizza(tk: str, nome: str, valuta: str, rng) -> dict | None:
    df = pd.read_csv(config.file_dati(tk), index_col=0, parse_dates=True)
    prezzo, IDX, mesi, ultima = indici_acquisto(df["Close"])
    if len(mesi) < config.MESI_MINIMI:
        return None
    P = prezzo[IDX]
    finale = float(prezzo[ultima])
    n = len(mesi)
    inv = (config.VERSAMENTO - config.COMMISSIONE) / P                      # quote per mese e giorno
    quote = inv.sum(axis=0)
    val = valore_netto(quote, n, finale)
    sc = scarto(val)
    giorno_mig, giorno_peg = int(np.argmax(val)) + 1, int(np.argmin(val)) + 1

    # serie senza calendario: i rendimenti giornalieri vengono rimescolati nell'intera storia (stessa media e
    # stessa volatilità, ma nessun giorno del mese è speciale); su ogni serie si rifà tutto il confronto
    lr = np.diff(np.log(prezzo))
    scarti_perm = np.empty(config.N_PERMUTAZIONI)
    for k in range(config.N_PERMUTAZIONI):
        pr = prezzo[0] * np.exp(np.concatenate([[0.0], np.cumsum(rng.permutation(lr))]))
        q = ((config.VERSAMENTO - config.COMMISSIONE) / pr[IDX]).sum(axis=0)
        v = valore_netto(q, n, float(pr[ultima]))
        scarti_perm[k] = scarto(v)
    p_perm = float((np.sum(scarti_perm >= sc) + 1) / (config.N_PERMUTAZIONI + 1))

    # scimmie: ogni mese un giorno a caso
    sg = rng.integers(0, len(config.GIORNI), size=(config.N_SCIMMIE, n))
    q_sc = np.take_along_axis(np.broadcast_to(inv, (config.N_SCIMMIE, n, len(config.GIORNI))), sg[:, :, None], axis=2).sum(axis=(1, 2))
    v_sc = valore_netto(q_sc, n, finale)

    # prima e seconda metà della storia
    meta = n // 2
    # per ogni metà si confrontano le quote comprate per ogni unità versata (il prezzo finale è comune)
    q1 = inv[:meta].sum(axis=0) / meta
    q2 = inv[meta:].sum(axis=0) / (n - meta)
    g1, g2 = int(np.argmax(q1)) + 1, int(np.argmax(q2)) + 1

    q_fine = inv[:, [d - 1 for d in config.GIORNI_FINE_MESE]].sum() / (n * len(config.GIORNI_FINE_MESE))
    q_inizio = inv[:, [d - 1 for d in config.GIORNI_INIZIO_MESE]].sum() / (n * len(config.GIORNI_INIZIO_MESE))
    return {"tk": tk, "sl": slug(tk), "nome": nome, "valuta": valuta, "n": n, "val": val, "scarto": sc,
            "gm": giorno_mig, "gp": giorno_peg, "p_perm": p_perm, "scarti_perm": scarti_perm,
            "sc_mediana": float(np.median(v_sc)), "sc_p5": float(np.percentile(v_sc, 5)), "sc_p95": float(np.percentile(v_sc, 95)),
            "v_sc": v_sc, "g1": g1, "g2": g2, "fine_su_inizio": float(q_fine / q_inizio - 1),
            "prima_data": str(mesi[0]), "ultimo_mese": str(mesi[-1]), "finale": finale,
            "versato": n * config.VERSAMENTO, "rango_mediana_giorni": float(np.median(val)),
            "inv_tot": quote}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta_dati = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    rng = np.random.default_rng(config.SEME)
    res = []
    for riga in meta_dati["indici"]:
        if riga.get("stato") != "ok":
            continue
        r = analizza(riga["ticker"], riga["nome"], riga["valuta"], rng)
        if r is not None:
            res.append(r)
            print(f"{r['nome']}: {r['n']} mesi, scarto {r['scarto']:.3%}, giorno migliore {r['gm']}, p perm {r['p_perm']:.4f}")
    if len(res) < 4:
        raise SystemExit("Troppi pochi indici utilizzabili.")
    ph = holm({r["tk"]: r["p_perm"] for r in res})

    # trasferimento del giorno migliore: percentile del giorno migliore di A dentro la distribuzione dei 28 giorni di B
    trasf = []
    for a in res:
        for b in res:
            if a["tk"] == b["tk"]:
                continue
            ordine = np.argsort(np.argsort(b["val"]))                        # 0 = peggiore, 27 = migliore
            trasf.append({"da": a["nome"], "su": b["nome"], "posizione": int(ordine[a["gm"] - 1]) + 1,
                          "sopra_mediana": bool(b["val"][a["gm"] - 1] > np.median(b["val"]))})
    trasf = pd.DataFrame(trasf)

    for r in res:
        sl = r["sl"]
        reg(f"{sl}_nome", r["nome"], "testo", "Nome dell'indice", "config.py, INDICI")
        reg(f"{sl}_valuta", r["valuta"], "testo", "Valuta dell'indice", "config.py, INDICI")
        reg(f"{sl}_mesi", r["n"], "int", f"Mesi completi di versamento del piano, {r['nome']}", "giorni.csv")
        reg(f"{sl}_anni", r["n"] / 12, "num1", f"Anni di versamenti, {r['nome']}", "giorni.csv")
        reg(f"{sl}_inizio", r["prima_data"], "testo", f"Primo mese di versamento, {r['nome']} (anno-mese)", "dati/")
        reg(f"{sl}_versato", r["versato"], "int", f"Totale versato nel piano, {r['nome']}", "giorni.csv")
        reg(f"{sl}_val_mig", float(r["val"].max()), "int", f"Valore finale netto del giorno migliore, {r['nome']}", "giorni.csv")
        reg(f"{sl}_val_peg", float(r["val"].min()), "int", f"Valore finale netto del giorno peggiore, {r['nome']}", "giorni.csv")
        reg(f"{sl}_val_med", float(np.median(r["val"])), "int", f"Valore finale netto mediano tra i 28 giorni, {r['nome']}", "giorni.csv")
        reg(f"{sl}_giorno_mig", r["gm"], "int", f"Giorno del mese con il valore finale più alto, {r['nome']}", "giorni.csv")
        reg(f"{sl}_giorno_peg", r["gp"], "int", f"Giorno del mese con il valore finale più basso, {r['nome']}", "giorni.csv")
        reg(f"{sl}_scarto", r["scarto"], "pct1", f"Scarto tra giorno migliore e peggiore, in percentuale del valore medio, {r['nome']}", "giorni.csv")
        reg(f"{sl}_perm_mediana", float(np.median(r["scarti_perm"])), "pct1", f"Scarto mediano ottenuto su serie con i rendimenti giornalieri rimescolati, {r['nome']}", "serie rimescolate")
        reg(f"{sl}_p_perm", r["p_perm"], "pval", f"p-value: quota di serie rimescolate con scarto almeno pari a quello osservato, {r['nome']}", "serie rimescolate")
        reg(f"{sl}_p_holm", ph[r["tk"]], "pval", f"p-value delle serie rimescolate corretto con il metodo di Holm sugli indici, {r['nome']}", "serie rimescolate")
        reg(f"{sl}_sc_mediana", r["sc_mediana"], "int", f"Valore finale netto mediano delle scimmie (giorno a caso ogni mese), {r['nome']}", "scimmie")
        reg(f"{sl}_sc_p5", r["sc_p5"], "int", f"Quinto percentile del valore finale delle scimmie, {r['nome']}", "scimmie")
        reg(f"{sl}_sc_p95", r["sc_p95"], "int", f"Novantacinquesimo percentile del valore finale delle scimmie, {r['nome']}", "scimmie")
        reg(f"{sl}_mig_sopra_sc", float((r["v_sc"] < r["val"].max()).mean()), "pct0", f"Quota di scimmie sotto il giorno migliore, {r['nome']}", "scimmie")
        reg(f"{sl}_g_prima", r["g1"], "int", f"Giorno migliore nella prima metà della storia, {r['nome']}", "giorni.csv")
        reg(f"{sl}_g_dopo", r["g2"], "int", f"Giorno migliore nella seconda metà della storia, {r['nome']}", "giorni.csv")
        reg(f"{sl}_fine_su_inizio", r["fine_su_inizio"], "pct1", f"Quote in più (+) o in meno (-) comprando il 24-28 invece che il 1-5 del mese, per ogni somma versata, {r['nome']}", "giorni.csv")
    n_ind = len(res)
    reg("n_indici", n_ind, "int", "Indici utilizzabili nel test", "config.py, INDICI e dati/")
    reg("n_scartati", len(config.INDICI) - n_ind, "int", "Indici scartati (nessun dato o storia troppo corta)", "metadati.json")
    reg("n_scarto_sotto", sum(r["scarto"] < config.SOGLIA_SCARTO for r in res), "int", "Indici in cui lo scarto tra giorno migliore e peggiore è sotto la soglia", "giorni.csv")
    reg("scarto_max", max(r["scarto"] for r in res), "pct1", "Scarto massimo tra giorno migliore e peggiore, tra gli indici", "giorni.csv")
    reg("scarto_min", min(r["scarto"] for r in res), "pct1", "Scarto minimo tra giorno migliore e peggiore, tra gli indici", "giorni.csv")
    reg("n_holm_signif", sum(ph[r["tk"]] < 0.05 for r in res), "int", "Indici in cui lo scarto osservato supera quello delle serie rimescolate, con p-value corretto sotto il cinque per cento", "serie rimescolate")
    reg("n_trasf_coppie", len(trasf), "int", "Coppie ordinate di indici per il test di trasferimento", "trasferimento.csv")
    reg("n_trasf_sopra", int(trasf["sopra_mediana"].sum()), "int", "Coppie in cui il giorno migliore di un indice, usato sull'altro, supera la mediana dei 28 giorni", "trasferimento.csv")
    reg("n_trasf_sotto", int((~trasf["sopra_mediana"]).sum()), "int", "Coppie in cui il giorno migliore di un indice, usato sull'altro, non supera la mediana dei 28 giorni", "trasferimento.csv")
    reg("quota_trasf_sopra", float(trasf["sopra_mediana"].mean()), "pct0", "Quota di coppie in cui il giorno migliore trasferito supera la mediana", "trasferimento.csv")
    reg("posizione_media_trasf", float(trasf["posizione"].mean()), "num1", "Posizione media (da 1 peggiore a 28 migliore) del giorno migliore trasferito su un altro indice", "trasferimento.csv")
    reg("n_instabile", sum(abs(r["g1"] - r["g2"]) > config.TOLLERANZA_GIORNI for r in res), "int", "Indici in cui il giorno migliore delle due metà differisce di più della tolleranza", "giorni.csv")
    reg("n_fine_meglio", sum(r["fine_su_inizio"] > 0 for r in res), "int", "Indici in cui comprare a fine mese dà più quote che comprare a inizio mese", "giorni.csv")
    reg("fine_su_inizio_media", float(np.mean([r["fine_su_inizio"] for r in res])), "pct1", "Media, sugli indici, della differenza di quote tra fine e inizio mese", "giorni.csv")
    reg("versamento", config.VERSAMENTO, "int", "Versamento mensile, nella valuta dell'indice", "config.py, VERSAMENTO")
    reg("commissione", config.COMMISSIONE, "num2", "Commissione per ogni acquisto, nella valuta dell'indice", "config.py, COMMISSIONE")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    reg("n_permutazioni", config.N_PERMUTAZIONI, "int", "Serie rimescolate per indice", "config.py, N_PERMUTAZIONI")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie simulate per ogni indice", "config.py, N_SCIMMIE")
    reg("n_giorni", len(config.GIORNI), "int", "Giorni del mese provati", "config.py, GIORNI")
    reg("soglia_scarto", config.SOGLIA_SCARTO, "pct0", "Soglia dell'ipotesi sullo scarto", "config.py, SOGLIA_SCARTO")
    reg("tolleranza_giorni", config.TOLLERANZA_GIORNI, "int", "Tolleranza in giorni dell'ipotesi sulla stabilità", "config.py, TOLLERANZA_GIORNI")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py, SEME")
    reg("anno_tur", 2008, "annonum", "Anno dell'articolo di McConnell e Xu", "McConnell e Xu, Financial Analysts Journal 64(2)")
    reg("lit_tur_paesi", 31, "int", "Paesi in cui compare l'effetto di fine mese, secondo l'abstract di McConnell e Xu", "McConnell e Xu (2008), abstract")
    reg("lit_tur_campione", 35, "int", "Paesi del campione di McConnell e Xu", "McConnell e Xu (2008), abstract")
    reg("lit_tur_giorni", 4, "int", "Giorni del turn of the month nell'abstract di McConnell e Xu", "McConnell e Xu (2008), abstract")
    reg("anno_ros", 2004, "annonum", "Anno dell'articolo di Rosenberg", "Rosenberg, The American Economist 48(2)")
    meta = meta_dati
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    u = pd.Period(max(r["ultimo_mese"] for r in res), freq="M")
    reg("data_ultima", f"{MESI_IT[u.month - 1]} {u.year}", "testo", "Ultimo mese di versamento incluso nei test", "dati/")

    pd.DataFrame({r["nome"]: r["val"] for r in res}, index=config.GIORNI).rename_axis("giorno").to_csv(config.RISULTATI / "giorni.csv", float_format="%.2f")
    trasf.to_csv(config.RISULTATI / "trasferimento.csv", index=False)
    pd.DataFrame({r["tk"]: r["scarti_perm"] for r in res}).to_csv(config.RISULTATI / "scarti_permutati.csv", index=False, float_format="%.6f")
    (config.RISULTATI / "indici_usati.json").write_text(json.dumps([{"ticker": r["tk"], "slug": r["sl"], "nome": r["nome"]} for r in res], ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
