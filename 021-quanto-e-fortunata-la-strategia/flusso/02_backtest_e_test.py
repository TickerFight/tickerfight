"""Passo 2 - Backtest della regola 50/200 e test sulla fortuna.

Legge SOLO dati/gspc_giornaliero.csv (scaricato dal passo 1) e produce:
  risultati/metriche.json                    ogni numero dell'articolo, con
                                             descrizione e origine di calcolo
  risultati/curve.csv                        equity curve e drawdown giornalieri
  risultati/test_casuale_periodo_intero.csv  risultati delle strategie a timing casuale
  risultati/bootstrap_diff_sharpe.csv        differenze di Sharpe ricampionate
  risultati/sottoperiodi.csv                 tabella dei sotto-periodi

Idea del test. La regola 50/200 è "investito" oppure "in cash". Per sapere se il
suo risultato è merito o caso la confrontiamo con strategie che hanno la STESSA
esposizione (stessi giorni investiti, stesso numero di cambi di posizione) ma
timing casuale: si rimescolano le durate dei periodi investiti e dei periodi in cash.
Se la regola vera batte quasi tutte le versioni a timing casuale, il suo timing
contiene informazione; altrimenti il risultato è compatibile con la fortuna.
"""
import hashlib
import json
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config

RIS: dict = {}
ORIGINE_DATI = "dati/gspc_giornaliero.csv (Yahoo Finance, ticker ^GSPC)"
RF_GIORNALIERO = config.TASSO_SENZA_RISCHIO / config.GIORNI_ANNO_BORSA
RAD = np.sqrt(config.GIORNI_ANNO_BORSA)


def mille(n: int) -> str:
    """Numero intero con il punto come separatore delle migliaia (10000 -> 10.000)."""
    return f"{n:,}".replace(",", ".")


def reg(chiave, valore, formato, descrizione, origine):
    """Registra un numero con la sua giustificazione (finisce nelle note dell'articolo)."""
    if isinstance(valore, np.floating):
        valore = float(valore)
    elif isinstance(valore, np.integer):
        valore = int(valore)
    RIS[chiave] = {
        "valore": valore,
        "formato": formato,
        "descrizione": descrizione,
        "origine": origine,
    }


# ---------------------------------------------------------------------------
# Dati e strategia
# ---------------------------------------------------------------------------
def carica_dati() -> pd.Series:
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"]).set_index("Date").sort_index()
    if df["Close"].isna().any() or (df["Close"] <= 0).any():
        raise SystemExit("Il file dati contiene chiusure mancanti o non positive.")
    return df["Close"].astype(float)


def carica_metadati() -> dict:
    if config.FILE_METADATI.exists():
        return json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    # Caso "file CSV scaricato a mano dal sito di Yahoo Finance": ricostruiamo il minimo.
    sha = hashlib.sha256(config.FILE_DATI.read_bytes()).hexdigest()
    return {
        "fonte": "Yahoo Finance (file CSV fornito manualmente)",
        "libreria": "download manuale dal sito, nessuna libreria",
        "scaricato_il_utc": "non registrato",
        "sha256_file": sha,
    }


def costruisci_serie(close: pd.Series) -> pd.DataFrame:
    """Segnale a fine giornata t -> posizione tenuta nella giornata t+1.

    Il segnale usa solo informazioni disponibili alla chiusura di t (media a 50 e
    a 200 giorni fino a t incluso); la posizione viene applicata al rendimento da
    t a t+1 (shift di un giorno), per non usare informazioni dal futuro.
    """
    sma_v = close.rolling(config.SMA_VELOCE).mean()
    sma_l = close.rolling(config.SMA_LENTA).mean()
    segnale = (sma_v > sma_l).astype(float).where(sma_l.notna())
    pos = segnale.shift(1)
    ret = close.pct_change()
    df = pd.DataFrame(
        {"close": close, "sma_veloce": sma_v, "sma_lenta": sma_l,
         "posizione": pos, "rend_bh": ret}
    ).dropna(subset=["posizione", "rend_bh"])
    df["rend_strategia"] = df["posizione"] * df["rend_bh"] + (1 - df["posizione"]) * RF_GIORNALIERO
    return df


# ---------------------------------------------------------------------------
# Metriche
# ---------------------------------------------------------------------------
def max_drawdown(r: np.ndarray) -> float:
    """Perdita massima dal picco, come numero positivo (0,55 = -55%)."""
    eq = np.concatenate(([1.0], np.cumprod(1.0 + r)))
    picco = np.maximum.accumulate(eq)
    return float(-(eq / picco - 1.0).min())


def metriche(r: np.ndarray, anni: float) -> dict:
    sd = r.std(ddof=1)
    return {
        "cagr": float(np.exp(np.log1p(r).sum() / anni) - 1.0),
        "vol": float(sd * RAD),
        "sharpe": float((r.mean() - RF_GIORNALIERO) / sd * RAD),
        "maxdd": max_drawdown(r),
        "molt": float(np.prod(1.0 + r)),
    }


def anni_del_periodo(indice_slice, indice_completo) -> float:
    """Anni di calendario coperti dai rendimenti: dal giorno prima del primo rendimento all'ultimo."""
    prima = indice_completo[indice_completo.get_loc(indice_slice[0]) - 1]
    return (indice_slice[-1] - prima).days / config.GIORNI_ANNO_CALENDARIO


# ---------------------------------------------------------------------------
# Test 1: strategie a timing casuale con la stessa esposizione
# ---------------------------------------------------------------------------
def blocchi(pos: np.ndarray):
    cambi = np.flatnonzero(np.diff(pos) != 0) + 1
    inizi = np.concatenate(([0], cambi))
    fini = np.concatenate((cambi, [len(pos)]))
    return pos[inizi].astype(int), (fini - inizi)


def posizione_casuale(valori, lunghezze, rng):
    """Rimescola le durate dei blocchi 'investito' tra loro e quelle 'in cash' tra loro.

    L'alternanza investito/cash resta quella originale, quindi restano identici il
    numero di giorni investiti e il numero di cambi di posizione.
    """
    lun = lunghezze.copy()
    for v in (0, 1):
        m = valori == v
        lun[m] = rng.permutation(lunghezze[m])
    return np.repeat(valori, lun)


def test_timing_casuale(pos, ret, anni, n, rng) -> pd.DataFrame:
    valori, lunghezze = blocchi(pos)
    sh = np.empty(n)
    cg = np.empty(n)
    dd = np.empty(n)
    for i in range(n):
        p = posizione_casuale(valori, lunghezze, rng)
        r = p * ret + (1 - p) * RF_GIORNALIERO
        sd = r.std(ddof=1)
        sh[i] = (r.mean() - RF_GIORNALIERO) / sd * RAD
        cg[i] = np.exp(np.log1p(r).sum() / anni) - 1.0
        dd[i] = max_drawdown(r)
    return pd.DataFrame({"sharpe": sh, "cagr": cg, "maxdd": dd})


def p_value_maggiore(nulla: np.ndarray, osservato: float) -> float:
    """Quota di strategie casuali che fanno almeno quanto quella vera (con correzione +1)."""
    return float((1 + np.sum(nulla >= osservato)) / (len(nulla) + 1))


def p_value_minore(nulla: np.ndarray, osservato: float) -> float:
    return float((1 + np.sum(nulla <= osservato)) / (len(nulla) + 1))


# ---------------------------------------------------------------------------
# Test 2: block bootstrap (circolare) delle differenze di Sharpe
# ---------------------------------------------------------------------------
def bootstrap_sharpe(rs, rb, blocco, n_boot, rng, lotto=250):
    n = len(rs)
    n_blocchi = int(np.ceil(n / blocco))
    out_s, out_b = [], []
    for _ in range(int(np.ceil(n_boot / lotto))):
        quanti = min(lotto, n_boot - len(out_s) * lotto)
        inizi = rng.integers(0, n, size=(quanti, n_blocchi))
        idx = (inizi[:, :, None] + np.arange(blocco)[None, None, :]).reshape(quanti, -1)[:, :n] % n
        s, b = rs[idx], rb[idx]
        out_s.append((s.mean(1) - RF_GIORNALIERO) / s.std(1, ddof=1) * RAD)
        out_b.append((b.mean(1) - RF_GIORNALIERO) / b.std(1, ddof=1) * RAD)
    return np.concatenate(out_s), np.concatenate(out_b)


def intervallo(x: np.ndarray):
    alfa = (1 - config.LIVELLO_CONFIDENZA) / 2
    return float(np.quantile(x, alfa)), float(np.quantile(x, 1 - alfa))


# ---------------------------------------------------------------------------
def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    close = carica_dati()
    meta = carica_metadati()
    df = costruisci_serie(close)

    pos = df["posizione"].to_numpy().astype(int)
    ret = df["rend_bh"].to_numpy()
    rs = df["rend_strategia"].to_numpy()
    anni = anni_del_periodo(df.index, close.index)
    semi = np.random.SeedSequence(config.SEED).spawn(8)

    # ---- Dati ----------------------------------------------------------
    reg("n_osservazioni_dati", len(close), "int",
        "Numero di giornate di borsa presenti nel file scaricato.",
        f"Righe di {ORIGINE_DATI}.")
    reg("data_inizio_dati", str(close.index[0].date()), "data",
        "Prima data disponibile nella serie scaricata da Yahoo Finance.",
        f"Prima riga di {ORIGINE_DATI}.")
    reg("data_fine_dati", str(close.index[-1].date()), "data",
        "Ultima data della serie scaricata (ultima seduta completa).",
        f"Ultima riga di {ORIGINE_DATI}.")
    grezzo = pd.read_csv(config.FILE_DATI, parse_dates=["Date"]).set_index("Date")
    if "Volume" in grezzo.columns and (grezzo["Volume"] > 0).any():
        reg("data_primo_volume", str(grezzo.index[grezzo["Volume"] > 0][0].date()), "data",
            "Prima data con un volume di scambi diverso da zero: prima di allora Yahoo riporta solo il prezzo.",
            f"Colonna Volume di {ORIGINE_DATI}: prima riga con volume maggiore di zero.")
    reg("data_scarico", meta.get("scaricato_il_utc", "non registrato")[:10], "data",
        "Giorno in cui i dati sono stati scaricati da Yahoo Finance.",
        "dati/gspc_metadati.json, campo scaricato_il_utc (scritto da 01_scarica_dati.py).")
    reg("versione_libreria", meta.get("libreria", "n.d."), "testo",
        "Libreria usata per scaricare i dati.",
        "dati/gspc_metadati.json, campo libreria.")
    reg("sha256_dati", meta.get("sha256_file", "n.d.")[:16] + "...", "testo",
        "Impronta SHA-256 (prime 16 cifre) del file dati: se cambia, i dati sono diversi.",
        "dati/gspc_metadati.json; si ricalcola con sha256sum dati/gspc_giornaliero.csv.")
    reg("data_inizio_test", str(df.index[0].date()), "data",
        "Primo giorno con rendimento della strategia: servono 200 chiusure per la media lenta "
        "e uno shift di un giorno.",
        "02_backtest_e_test.py, costruisci_serie(): prima riga dopo dropna.")
    reg("n_giorni_test", len(df), "int",
        "Giornate di borsa su cui si confrontano strategia e buy & hold.",
        "02_backtest_e_test.py: righe di df dopo costruisci_serie().")
    reg("anni_test", anni, "num1",
        "Anni di calendario coperti dal test (giorni / 365,25).",
        "02_backtest_e_test.py, anni_del_periodo().")

    # ---- Parametri -----------------------------------------------------
    reg("sma_veloce", config.SMA_VELOCE, "int", "Giorni della media mobile veloce.",
        "flusso/config.py, SMA_VELOCE (scelta a priori, non ottimizzata).")
    reg("sma_lenta", config.SMA_LENTA, "int", "Giorni della media mobile lenta.",
        "flusso/config.py, SMA_LENTA (scelta a priori, non ottimizzata).")
    reg("n_sim", config.N_SIMULAZIONI_CASUALI, "int", "Numero di strategie a timing casuale simulate.",
        "flusso/config.py, N_SIMULAZIONI_CASUALI.")
    reg("n_boot", config.N_BOOTSTRAP, "int", "Numero di ricampionamenti bootstrap.",
        "flusso/config.py, N_BOOTSTRAP.")
    reg("blocco_boot", config.BLOCCO_BOOTSTRAP, "int",
        "Giorni di borsa per blocco nel bootstrap (circa un mese): mantiene la dipendenza tra giorni vicini.",
        "flusso/config.py, BLOCCO_BOOTSTRAP (convenzione, non ottimizzata).")
    reg("blocco_boot_a", config.BLOCCHI_ROBUSTEZZA[0], "int",
        "Lunghezza di blocco alternativa (corta) per il controllo di robustezza.",
        "flusso/config.py, BLOCCHI_ROBUSTEZZA.")
    reg("blocco_boot_b", config.BLOCCHI_ROBUSTEZZA[1], "int",
        "Lunghezza di blocco alternativa (lunga, circa un trimestre) per il controllo di robustezza.",
        "flusso/config.py, BLOCCHI_ROBUSTEZZA.")
    reg("seed", config.SEED, "annonum",
        "Seme del generatore casuale: con lo stesso seme si ottengono gli stessi risultati.",
        "flusso/config.py, SEED.")
    reg("livello_conf", config.LIVELLO_CONFIDENZA, "pct0",
        "Livello degli intervalli di confidenza.", "flusso/config.py, LIVELLO_CONFIDENZA.")
    reg("giorni_anno_borsa", config.GIORNI_ANNO_BORSA, "int",
        "Giornate di borsa per anno usate per annualizzare volatilità e Sharpe.",
        "flusso/config.py, GIORNI_ANNO_BORSA (convenzione).")

    # ---- Esposizione della strategia ----------------------------------
    valori, lunghezze = blocchi(pos)
    reg("esposizione", float(pos.mean()), "pct1",
        "Quota dei giorni in cui la strategia è investita (il resto è cash).",
        "02_backtest_e_test.py: media della colonna posizione (0 = cash, 1 = investito).")
    reg("n_cambi", len(valori) - 1, "int",
        "Numero di cambi di posizione (da investito a cash o viceversa) nel periodo.",
        "02_backtest_e_test.py, blocchi(): numero di blocchi meno uno.")
    reg("n_ingressi", int(np.sum((pos[1:] == 1) & (pos[:-1] == 0))), "int",
        "Numero di volte in cui la strategia rientra sul mercato.",
        "02_backtest_e_test.py: passaggi da posizione 0 a posizione 1.")

    # ---- Esempio didattico: un'uscita e il successivo rientro ------------
    segn = (df["sma_veloce"] > df["sma_lenta"])
    cambi = segn[segn != segn.shift()].iloc[1:]
    cambi = cambi[cambi.index >= pd.Timestamp(config.ESEMPIO_DAL)]
    t_out = cambi[~cambi].index[0]
    t_in = cambi[cambi & (cambi.index > t_out)].index[0]
    i_out, i_in = df.index.get_loc(t_out), df.index.get_loc(t_in)
    orig = (f"02_backtest_e_test.py, esempio didattico: primo segnale di uscita dopo il {config.ESEMPIO_DAL} "
            f"({t_out.date()}) e successivo segnale di rientro ({t_in.date()}); medie calcolate su dati/gspc_giornaliero.csv.")
    finestra = df.loc[t_out - pd.Timedelta(days=200): t_in + pd.Timedelta(days=120),
                      ["close", "sma_veloce", "sma_lenta"]]
    finestra.round(4).to_csv(config.RISULTATI / "esempio_media_mobile.csv")

    # ---- Una gemella "tipica" per il grafico di confronto -----------------
    valori_b, lunghezze_b = blocchi(pos)
    rng_g = np.random.default_rng(config.SEED + 1)
    cand = [posizione_casuale(valori_b, lunghezze_b, rng_g) for _ in range(1000)]
    sh_c = np.array([metriche(c * ret, anni)["sharpe"] for c in cand])
    gem = cand[int(np.argmin(np.abs(sh_c - np.median(sh_c))))]
    mg = metriche(gem * ret, anni)
    pd.DataFrame({"close": df["close"].to_numpy(), "posizione": pos, "posizione_gemella": gem},
                 index=df.index).to_csv(config.RISULTATI / "esempio_gemella.csv")
    origg = ("02_backtest_e_test.py, esempio grafico: tra 1000 strategie a timing casuale (stessi periodi dentro/fuori "
             "della regola, rimescolati) si sceglie quella con Sharpe più vicino alla mediana; metriche con le stesse formule della regola.")
    # ---- Una griglia di gemelle estratte a caso (solo posizioni) ------------
    N_GR = 12
    rng_r = np.random.default_rng(config.SEED + 3)
    griglia = {"regola": pos}
    for k in range(N_GR):
        griglia[f"g{k + 1:02d}"] = posizione_casuale(valori_b, lunghezze_b, rng_r)
    pd.DataFrame(griglia, index=df.index).astype(int).to_csv(config.RISULTATI / "esempio_griglia_gemelle.csv", index_label="Date")
    reg("gr_n", N_GR, "int", "Numero di gemelle mostrate nella griglia.",
        f"02_backtest_e_test.py, esempio grafico: {N_GR} strategie a timing casuale estratte a caso (stessi periodi dentro/fuori della regola, rimescolati), non selezionate.")
    reg("gem_cagr", mg["cagr"], "pct2", "Rendimento annuo composto della gemella mostrata nel grafico di confronto.", origg)
    reg("gem_sharpe", mg["sharpe"], "num2", "Indice di Sharpe della gemella mostrata nel grafico di confronto.", origg)
    reg("gem_maxdd", mg["maxdd"], "pct1", "Perdita massima della gemella mostrata nel grafico di confronto.", origg)
    reg("es_data_uscita", str(t_out.date()), "data_lunga", "Giorno del segnale di uscita nell'esempio.", orig)
    reg("es_anno_uscita", str(t_out.date()), "anno", "Anno del segnale di uscita nell'esempio.", orig)
    reg("es_close_uscita", float(df["close"].iloc[i_out]), "int", "Chiusura dell'indice nel giorno del segnale di uscita (punti indice).", orig)
    reg("es_sma_v_prima", float(df["sma_veloce"].iloc[i_out - 1]), "num1", "Media a 50 giorni il giorno prima dell'uscita.", orig)
    reg("es_sma_l_prima", float(df["sma_lenta"].iloc[i_out - 1]), "num1", "Media a 200 giorni il giorno prima dell'uscita.", orig)
    reg("es_sma_v_uscita", float(df["sma_veloce"].iloc[i_out]), "num1", "Media a 50 giorni nel giorno dell'uscita.", orig)
    reg("es_sma_l_uscita", float(df["sma_lenta"].iloc[i_out]), "num1", "Media a 200 giorni nel giorno dell'uscita.", orig)
    reg("es_data_rientro", str(t_in.date()), "data_lunga", "Giorno del segnale di rientro nell'esempio.", orig)
    reg("es_close_rientro", float(df["close"].iloc[i_in]), "int", "Chiusura dell'indice nel giorno del segnale di rientro (punti indice).", orig)
    reg("es_var_indice", float(df["close"].iloc[i_in] / df["close"].iloc[i_out] - 1), "pct0",
        "Variazione dell'indice tra il segnale di uscita e quello di rientro.", orig)
    reg("es_anni_fuori", (t_in - t_out).days / config.GIORNI_ANNO_CALENDARIO, "num1",
        "Anni trascorsi in cash tra uscita e rientro (giorni di calendario / 365,25).", orig)

    # ---- Metriche principali ------------------------------------------
    mb = metriche(ret, anni)
    ms = metriche(rs, anni)
    formule = {
        "cagr": ("Rendimento annuo composto", "exp(somma di ln(1+r) / anni) - 1"),
        "vol": ("Volatilità annualizzata", "deviazione standard dei rendimenti giornalieri x radice(252)"),
        "sharpe": ("Indice di Sharpe annualizzato (tasso privo di rischio = 0)",
                   "media dei rendimenti giornalieri / deviazione standard x radice(252)"),
        "maxdd": ("Perdita massima dal picco (drawdown massimo)", "minimo di equity / massimo precedente - 1"),
        "molt": ("Moltiplicatore finale di 1 investito all'inizio (indice di prezzo, senza dividendi)",
                 "prodotto di (1 + r)"),
    }
    fm = {"cagr": "pct2", "vol": "pct1", "sharpe": "num2", "maxdd": "pct1", "molt": "num1"}
    for k, (nome, formula) in formule.items():
        reg(f"{k}_bh", mb[k], fm[k], f"{nome}: buy & hold sull'S&P 500.",
            f"02_backtest_e_test.py, metriche(); formula: {formula}; serie: {ORIGINE_DATI}.")
        reg(f"{k}_str", ms[k], fm[k], f"{nome}: strategia 50/200 (investito o cash).",
            f"02_backtest_e_test.py, metriche(); formula: {formula}; serie: {ORIGINE_DATI}.")

    reg("quota_cash", 1.0 - float(pos.mean()), "pct1",
        "Quota dei giorni in cui la strategia è in cash (complemento dell'esposizione).",
        "02_backtest_e_test.py: 1 - media della colonna posizione.")
    reg("anni_per_ingresso", anni / int(np.sum((pos[1:] == 1) & (pos[:-1] == 0))), "num1",
        "Anni di calendario in media tra un rientro sul mercato e il successivo.",
        "02_backtest_e_test.py: anni del test / numero di ingressi.")
    reg("diff_cagr", ms["cagr"] - mb["cagr"], "pp2",
        "Differenza di rendimento annuo composto tra strategia e buy & hold, in punti percentuali.",
        "02_backtest_e_test.py: cagr_str - cagr_bh.")
    reg("sharpe_atteso_casuale", mb["sharpe"] * float(np.sqrt(pos.mean())), "num2",
        "Sharpe del buy & hold moltiplicato per la radice dell'esposizione: è lo Sharpe che ci si aspetta da "
        "una strategia investita a caso per la stessa quota di giorni, perché restare in cash a rendimento zero "
        "riduce il rendimento medio in proporzione all'esposizione e la volatilità solo con la sua radice.",
        "02_backtest_e_test.py: sharpe_bh x radice(esposizione).")
    alfa = 1.0 - config.LIVELLO_CONFIDENZA
    reg("alfa", alfa, "pct0", "Soglia convenzionale di significatività.",
        "flusso/config.py: 1 - LIVELLO_CONFIDENZA.")
    reg("n_sottoperiodi", len(config.SOTTOPERIODI), "int", "Numero di sotto-periodi esaminati dopo il test principale.",
        "flusso/config.py, SOTTOPERIODI.")
    reg("soglia_corretta", alfa / len(config.SOTTOPERIODI), "pval",
        "Soglia di significatività corretta per i sotto-periodi (correzione di Bonferroni): "
        "la soglia convenzionale divisa per il numero di sotto-periodi esaminati.",
        "02_backtest_e_test.py: alfa / numero di sotto-periodi.")

    # ---- Test 1: timing casuale, periodo intero -----------------------
    nulla = test_timing_casuale(pos, ret, anni, config.N_SIMULAZIONI_CASUALI, np.random.default_rng(semi[0]))
    nulla.to_csv(config.RISULTATI / "test_casuale_periodo_intero.csv", index=False, float_format="%.8f")
    origine_test = ("02_backtest_e_test.py, test_timing_casuale(): "
                    f"{mille(config.N_SIMULAZIONI_CASUALI)} strategie con gli stessi giorni investiti e gli stessi cambi di "
                    "posizione della regola vera, ma durate dei blocchi rimescolate")
    reg("p_sharpe", p_value_maggiore(nulla["sharpe"].to_numpy(), ms["sharpe"]), "pval",
        "Quota di strategie a timing casuale con Sharpe almeno pari a quello della regola 50/200 (valore p, con correzione +1).",
        f"{origine_test}; p = (1 + #{{Sharpe casuale >= Sharpe vero}}) / (N + 1).")
    reg("p_cagr", p_value_maggiore(nulla["cagr"].to_numpy(), ms["cagr"]), "pval",
        "Quota di strategie a timing casuale con rendimento annuo composto almeno pari a quello della regola 50/200.",
        f"{origine_test}; stessa formula del valore p.")
    reg("p_maxdd", p_value_minore(nulla["maxdd"].to_numpy(), ms["maxdd"]), "pval",
        "Quota di strategie a timing casuale con perdita massima non più profonda di quella della regola 50/200.",
        f"{origine_test}; stessa formula, con perdita massima <= quella vera.")
    for col, nome, f in (("sharpe", "Sharpe", "num2"), ("cagr", "rendimento annuo composto", "pct2"),
                         ("maxdd", "perdita massima", "pct1")):
        reg(f"null_{col}_mediana", float(nulla[col].median()), f,
            f"Mediana di {nome} tra le strategie a timing casuale.", origine_test + "; mediana della colonna.")
    reg("quantile_null", 0.95, "pct0",
        "Quota di strategie a timing casuale che sta al di sotto dei valori soglia null_sharpe_p95 e null_cagr_p95.",
        "02_backtest_e_test.py: quantile 0,95 usato per i due valori soglia.")
    reg("null_sharpe_p95", float(nulla["sharpe"].quantile(0.95)), "num2",
        "95o percentile dello Sharpe tra le strategie a timing casuale: solo il 5% fa meglio.",
        origine_test + "; quantile 0,95 della colonna sharpe.")
    reg("null_cagr_p95", float(nulla["cagr"].quantile(0.95)), "pct2",
        "95o percentile del rendimento annuo composto tra le strategie a timing casuale.",
        origine_test + "; quantile 0,95 della colonna cagr.")
    reg("null_maxdd_p5", float(nulla["maxdd"].quantile(0.05)), "pct1",
        "5o percentile della perdita massima tra le strategie a timing casuale: solo il 5% ha una perdita minore.",
        origine_test + "; quantile 0,05 della colonna maxdd.")

    # ---- Test 2: bootstrap delle differenze di Sharpe -----------------
    obs_diff = ms["sharpe"] - mb["sharpe"]
    reg("diff_sharpe_obs", obs_diff, "num2",
        "Differenza di Sharpe osservata: strategia meno buy & hold.",
        "02_backtest_e_test.py: sharpe_str - sharpe_bh.")
    origine_boot = ("02_backtest_e_test.py, bootstrap_sharpe(): ricampionamento a blocchi circolari, "
                    "stesse date per strategia e buy & hold")
    boot_s, boot_b = bootstrap_sharpe(rs, ret, config.BLOCCO_BOOTSTRAP, config.N_BOOTSTRAP, np.random.default_rng(semi[1]))
    diff = boot_s - boot_b
    pd.DataFrame({"sharpe_strategia": boot_s, "sharpe_bh": boot_b, "differenza": diff}).to_csv(
        config.RISULTATI / "bootstrap_diff_sharpe.csv", index=False, float_format="%.8f")
    lo, hi = intervallo(diff)
    reg("boot_diff_lo", lo, "num2", "Estremo inferiore dell'intervallo di confidenza al 95% della differenza di Sharpe.",
        origine_boot + f" (blocchi da {config.BLOCCO_BOOTSTRAP} giorni); percentile 2,5 delle differenze.")
    reg("boot_diff_hi", hi, "num2", "Estremo superiore dell'intervallo di confidenza al 95% della differenza di Sharpe.",
        origine_boot + f" (blocchi da {config.BLOCCO_BOOTSTRAP} giorni); percentile 97,5 delle differenze.")
    reg("boot_prob_pos", float(np.mean(diff > 0)), "pct1",
        "Quota di ricampionamenti in cui la strategia ha Sharpe superiore al buy & hold.",
        origine_boot + "; media di (differenza > 0).")
    for nome, arr, k in (("della strategia", boot_s, "str"), ("del buy & hold", boot_b, "bh")):
        a, b = intervallo(arr)
        reg(f"boot_sharpe_{k}_lo", a, "num2", f"Estremo inferiore dell'intervallo al 95% dello Sharpe {nome}.",
            origine_boot + "; percentile 2,5.")
        reg(f"boot_sharpe_{k}_hi", b, "num2", f"Estremo superiore dell'intervallo al 95% dello Sharpe {nome}.",
            origine_boot + "; percentile 97,5.")
    for tag, L, seme in (("a", config.BLOCCHI_ROBUSTEZZA[0], semi[2]), ("b", config.BLOCCHI_ROBUSTEZZA[1], semi[3])):
        s2, b2 = bootstrap_sharpe(rs, ret, L, config.N_BOOTSTRAP, np.random.default_rng(seme))
        a, b = intervallo(s2 - b2)
        reg(f"boot_diff_lo_{tag}", a, "num2",
            f"Controllo di robustezza: estremo inferiore dell'intervallo al 95% con blocchi da {L} giorni.",
            origine_boot + f" (blocchi da {L} giorni).")
        reg(f"boot_diff_hi_{tag}", b, "num2",
            f"Controllo di robustezza: estremo superiore dell'intervallo al 95% con blocchi da {L} giorni.",
            origine_boot + f" (blocchi da {L} giorni).")

    # ---- Sotto-periodi ------------------------------------------------
    righe = []
    for i, (etichetta, d0, d1) in enumerate(config.SOTTOPERIODI):
        sl = df.loc[d0:d1] if (d0 or d1) else df
        p_sp = sl["posizione"].to_numpy().astype(int)
        r_b = sl["rend_bh"].to_numpy()
        r_s = sl["rend_strategia"].to_numpy()
        a_sp = anni_del_periodo(sl.index, close.index)
        m_b, m_s = metriche(r_b, a_sp), metriche(r_s, a_sp)
        n_sp = test_timing_casuale(p_sp, r_b, a_sp, config.N_SIMULAZIONI_CASUALI, np.random.default_rng(semi[4 + i]))
        pc = {
            "p_sharpe": p_value_maggiore(n_sp["sharpe"].to_numpy(), m_s["sharpe"]),
            "p_cagr": p_value_maggiore(n_sp["cagr"].to_numpy(), m_s["cagr"]),
            "p_maxdd": p_value_minore(n_sp["maxdd"].to_numpy(), m_s["maxdd"]),
        }
        righe.append({"periodo": etichetta, "inizio": str(sl.index[0].date()), "fine": str(sl.index[-1].date()),
                      "giorni": len(sl), "esposizione": float(p_sp.mean()),
                      "sharpe_str": m_s["sharpe"], "sharpe_bh": m_b["sharpe"],
                      "cagr_str": m_s["cagr"], "cagr_bh": m_b["cagr"],
                      "maxdd_str": m_s["maxdd"], "maxdd_bh": m_b["maxdd"], **pc})
        o = (f"02_backtest_e_test.py, sotto-periodo '{etichetta}' ({sl.index[0].date()} - {sl.index[-1].date()}): "
             f"stesse metriche e stesso test a timing casuale ({mille(config.N_SIMULAZIONI_CASUALI)} simulazioni) "
             "applicati ai soli giorni del sotto-periodo")
        reg(f"sp{i}_etichetta", etichetta, "testo", "Nome del sotto-periodo.", "flusso/config.py, SOTTOPERIODI.")
        reg(f"sp{i}_inizio", str(sl.index[0].date()), "data", f"Primo giorno del sotto-periodo '{etichetta}'.", o)
        reg(f"sp{i}_fine", str(sl.index[-1].date()), "data", f"Ultimo giorno del sotto-periodo '{etichetta}'.", o)
        reg(f"sp{i}_giorni", len(sl), "int", f"Giornate di borsa nel sotto-periodo '{etichetta}'.", o)
        reg(f"sp{i}_esposizione", float(p_sp.mean()), "pct1", f"Quota di giorni investiti nel sotto-periodo '{etichetta}'.", o)
        for k, f, nome in (("sharpe", "num2", "Sharpe"), ("cagr", "pct2", "rendimento annuo composto"),
                           ("maxdd", "pct1", "perdita massima")):
            reg(f"sp{i}_{k}_str", m_s[k], f,
                f"{nome} della strategia nel sotto-periodo '{etichetta}'.", o)
            reg(f"sp{i}_{k}_bh", m_b[k], f,
                f"{nome} del buy & hold nel sotto-periodo '{etichetta}'.", o)
        for k, nome in (("p_sharpe", "Sharpe"), ("p_cagr", "rendimento annuo composto"), ("p_maxdd", "perdita massima")):
            reg(f"sp{i}_{k}", pc[k], "pval", f"Valore p sul {nome} nel sotto-periodo '{etichetta}'.", o)
    pd.DataFrame(righe).to_csv(config.RISULTATI / "sottoperiodi.csv", index=False, float_format="%.8f")

    # ---- Curve per i grafici ------------------------------------------
    prima = close.index[close.index.get_loc(df.index[0]) - 1]
    date = pd.DatetimeIndex([prima]).append(df.index)
    eq_s = np.concatenate(([1.0], np.cumprod(1.0 + rs)))
    eq_b = np.concatenate(([1.0], np.cumprod(1.0 + ret)))
    curve = pd.DataFrame({
        "Date": date,
        "posizione": np.concatenate(([np.nan], pos)),
        "eq_strategia": eq_s,
        "eq_bh": eq_b,
        "dd_strategia": eq_s / np.maximum.accumulate(eq_s) - 1.0,
        "dd_bh": eq_b / np.maximum.accumulate(eq_b) - 1.0,
    })
    curve.to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.8f")
    for k, col, nome in (("bh", "dd_bh", "il buy & hold"), ("str", "dd_strategia", "la strategia")):
        reg(f"data_minimo_{k}", str(curve.loc[curve[col].idxmin(), "Date"].date()), "data",
            f"Giorno in cui {nome} tocca la perdita massima dal picco.",
            "02_backtest_e_test.py: data del minimo della colonna drawdown in risultati/curve.csv.")

    payload = {
        "generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ambiente": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
        "valori": RIS,
    }
    (config.RISULTATI / "metriche.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri in risultati/metriche.json")
    for k in ("sharpe_bh", "sharpe_str", "cagr_bh", "cagr_str", "maxdd_bh", "maxdd_str",
              "esposizione", "n_cambi", "p_sharpe", "p_cagr", "p_maxdd",
              "boot_diff_lo", "boot_diff_hi", "boot_prob_pos"):
        print(f"  {k:16s} {RIS[k]['valore']}")


if __name__ == "__main__":
    main()
