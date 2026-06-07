"""
Script per la generazione completa dei risultati del modello CatBoost dengue.

Output in risultati/:
  predictions/  - predizioni complete su train e test
  metrics/      - metriche globali, per paese, per anno
  plots/        - un grafico per paese + scatter + residui + feature importance
  parameters/   - parametri del modello e della pipeline
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "modello_utilizzato" / "src"))
from inference import load_model, predict_log, predict_cases

RISULTATI = ROOT / "risultati"
(RISULTATI / "predictions").mkdir(parents=True, exist_ok=True)
(RISULTATI / "metrics").mkdir(parents=True, exist_ok=True)
(RISULTATI / "plots").mkdir(parents=True, exist_ok=True)
(RISULTATI / "parameters").mkdir(parents=True, exist_ok=True)

COUNTRY_NAMES = {
    "ARG": "Argentina", "BOL": "Bolivia", "BRA": "Brasile",
    "CRI": "Costa Rica", "GTM": "Guatemala", "HND": "Honduras",
    "MEX": "Messico", "PER": "Perù", "PRY": "Paraguay",
    "THA": "Tailandia", "URY": "Uruguay",
}

PLOT_STYLE = {
    "real":  {"color": "#2c7bb6", "lw": 1.8, "label": "Casi reali"},
    "pred":  {"color": "#d7191c", "lw": 1.8, "ls": "--", "label": "Predetti (CatBoost)"},
}


def smape(y_true, y_pred):
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2
    mask = denom > 0
    return 100 * np.mean(np.abs(y_true[mask] - y_pred[mask]) / denom[mask])


def compute_metrics(y_true, y_pred, label=""):
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    sm   = smape(np.array(y_true), np.array(y_pred))
    return {"subset": label, "MAE": round(mae, 4), "RMSE": round(rmse, 4),
            "R2": round(r2, 4), "sMAPE_%": round(sm, 2)}


def run():
    print("Caricamento modello...")
    model = load_model()

    print("Caricamento dati...")
    train = pd.read_csv(ROOT / "DatasetFinale" / "train.csv", parse_dates=["date"])
    test  = pd.read_csv(ROOT / "DatasetFinale" / "test.csv",  parse_dates=["date"])

    # ── PREDIZIONI ────────────────────────────────────────────────────────────
    print("Calcolo predizioni...")
    for df, split in [(train, "train"), (test, "test")]:
        df["log_pred"]        = predict_log(df, model)
        df["cases_pred"]      = predict_cases(df, model)
        df["cases_per_100k_pred"] = np.maximum(np.expm1(df["log_pred"]), 0.0)
        df["cases_real"]      = df["cases_raw"]
        df["log_real"]        = df["log_cases_per_100k"]

    train.to_csv(RISULTATI / "predictions" / "train_predictions.csv", index=False)
    test.to_csv( RISULTATI / "predictions" / "test_predictions.csv",  index=False)
    print("  → predictions/ salvato")

    # ── METRICHE ─────────────────────────────────────────────────────────────
    print("Calcolo metriche...")
    rows = []
    # Globali
    for df, split in [(train, "train"), (test, "test")]:
        rows.append(compute_metrics(df["log_real"], df["log_pred"], f"{split}_global_log"))
        rows.append(compute_metrics(df["cases_real"], df["cases_pred"], f"{split}_global_cases"))

    # Per paese (solo test)
    per_country = []
    for eco, grp in test.groupby("economy"):
        m = compute_metrics(grp["log_real"], grp["log_pred"], eco)
        m["country"] = COUNTRY_NAMES.get(eco, eco)
        m["iso3"] = eco
        m["n_months"] = len(grp)
        per_country.append(m)

    metrics_df = pd.DataFrame(rows)
    per_country_df = pd.DataFrame(per_country).sort_values("R2", ascending=False)

    metrics_df.to_csv(RISULTATI / "metrics" / "metrics_global.csv", index=False)
    per_country_df.to_csv(RISULTATI / "metrics" / "metrics_per_country.csv", index=False)

    # Per anno (test)
    per_year = []
    for yr, grp in test.groupby("year"):
        per_year.append(compute_metrics(grp["log_real"], grp["log_pred"], str(yr)))
    pd.DataFrame(per_year).to_csv(RISULTATI / "metrics" / "metrics_per_year.csv", index=False)
    print("  → metrics/ salvato")

    # ── PLOT PER PAESE ────────────────────────────────────────────────────────
    print("Generazione plots per paese...")
    countries = sorted(test["economy"].unique())
    for eco in countries:
        name = COUNTRY_NAMES.get(eco, eco)
        tr = train[train["economy"] == eco].sort_values("date")
        te = test[test["economy"]  == eco].sort_values("date")

        fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=False)
        fig.suptitle(f"{name} ({eco}) — Dengue: Casi Reali vs Predetti", fontsize=14, fontweight="bold")

        # Top: casi assoluti
        ax = axes[0]
        ax.plot(tr["date"], tr["cases_real"], color="#2c7bb6", lw=1.4, label="Reali (train)")
        ax.plot(te["date"], te["cases_real"], color="#2c7bb6", lw=2.0, label="Reali (test)")
        ax.plot(te["date"], te["cases_pred"], color="#d7191c", lw=2.0, ls="--", label="Predetti (test)")
        ax.axvline(pd.Timestamp("2022-01-01"), color="gray", ls=":", lw=1.2, label="Inizio test")
        ax.set_ylabel("Casi assoluti")
        ax.legend(fontsize=8, loc="upper left")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=7)
        ax.set_title("Casi assoluti (train 2014-2021 + test 2022-2023)")

        # Bottom: log_cases_per_100k (test)
        ax2 = axes[1]
        ax2.plot(te["date"], te["log_real"], color="#2c7bb6", lw=2.0, label="Reali log(casi/100k)")
        ax2.plot(te["date"], te["log_pred"], color="#d7191c", lw=2.0, ls="--", label="Predetti log(casi/100k)")
        r2 = r2_score(te["log_real"], te["log_pred"])
        mae_val = mean_absolute_error(te["log_real"], te["log_pred"])
        ax2.set_ylabel("log(casi/100k)")
        ax2.set_title(f"Test 2022-2023 (log-space) — R²={r2:.3f}  MAE={mae_val:.3f}")
        ax2.legend(fontsize=8, loc="upper left")
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax2.get_xticklabels(), rotation=30, ha="right", fontsize=7)

        plt.tight_layout()
        out_path = RISULTATI / "plots" / f"{eco}_pred_vs_real.png"
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  → {eco}_pred_vs_real.png")

    # ── SCATTER PLOT (tutti i paesi, test) ───────────────────────────────────
    print("Scatter plot globale...")
    fig, ax = plt.subplots(figsize=(8, 8))
    colors_map = plt.cm.get_cmap("tab20", len(countries))
    for i, eco in enumerate(countries):
        grp = test[test["economy"] == eco]
        ax.scatter(grp["log_real"], grp["log_pred"], label=COUNTRY_NAMES.get(eco, eco),
                   color=colors_map(i), s=30, alpha=0.75)
    lo = test["log_real"].min(); hi = test["log_real"].max()
    ax.plot([lo, hi], [lo, hi], "k--", lw=1.2, label="Perfetto (y=x)")
    ax.set_xlabel("log(casi/100k) — Reali")
    ax.set_ylabel("log(casi/100k) — Predetti")
    r2_all = r2_score(test["log_real"], test["log_pred"])
    ax.set_title(f"Scatter Reali vs Predetti — Test 2022-2023 (R²={r2_all:.3f})")
    ax.legend(fontsize=7, ncol=2, loc="upper left")
    plt.tight_layout()
    plt.savefig(RISULTATI / "plots" / "scatter_all_countries.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → scatter_all_countries.png")

    # ── RESIDUI PER PAESE ─────────────────────────────────────────────────────
    print("Residui per paese...")
    fig, ax = plt.subplots(figsize=(13, 6))
    residuals_by_country = [
        (test[test["economy"] == eco]["log_pred"] - test[test["economy"] == eco]["log_real"]).values
        for eco in countries
    ]
    bp = ax.boxplot(residuals_by_country, labels=[COUNTRY_NAMES.get(e, e) for e in countries],
                    patch_artist=True, medianprops={"color": "black", "lw": 2})
    colors_bp = plt.cm.get_cmap("tab20", len(countries))
    for patch, color in zip(bp["boxes"], [colors_bp(i) for i in range(len(countries))]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.axhline(0, color="red", ls="--", lw=1.2)
    ax.set_ylabel("Residuo (predetto − reale) in log-space")
    ax.set_title("Distribuzione dei residui per paese — Test 2022-2023")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(RISULTATI / "plots" / "residuals_per_country.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → residuals_per_country.png")

    # ── FEATURE IMPORTANCE ────────────────────────────────────────────────────
    print("Feature importance...")
    fi = model.get_feature_importance()
    fi_names = model.feature_names_
    fi_df = pd.DataFrame({"feature": fi_names, "importance": fi}).sort_values("importance", ascending=False)
    fi_df.to_csv(RISULTATI / "metrics" / "feature_importance.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 9))
    top_n = fi_df.head(20)
    ax.barh(top_n["feature"][::-1], top_n["importance"][::-1], color="#2c7bb6")
    ax.set_xlabel("Importanza (%)")
    ax.set_title("CatBoost — Top 20 Feature Importance (test set)")
    plt.tight_layout()
    plt.savefig(RISULTATI / "plots" / "feature_importance.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → feature_importance.png")

    # ── ANDAMENTO MENSILE AGGREGATO (tutti i paesi, test) ────────────────────
    print("Plot andamento mensile aggregato...")
    monthly = test.groupby("date").agg(
        cases_real=("cases_real", "sum"),
        cases_pred=("cases_pred", "sum")
    ).reset_index()
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(monthly["date"], monthly["cases_real"], color="#2c7bb6", lw=2.0, label="Totale reale (11 paesi)")
    ax.plot(monthly["date"], monthly["cases_pred"], color="#d7191c", lw=2.0, ls="--", label="Totale predetto")
    ax.set_ylabel("Casi totali")
    ax.set_title("Totale mensile casi dengue — 11 paesi aggregati (test 2022-2023)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)
    plt.tight_layout()
    plt.savefig(RISULTATI / "plots" / "totale_mensile_aggregato.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → totale_mensile_aggregato.png")

    # ── PARAMETRI MODELLO ─────────────────────────────────────────────────────
    print("Salvataggio parametri...")
    params = model.get_all_params()
    with open(RISULTATI / "parameters" / "catboost_params.json", "w", encoding="utf-8") as f:
        json.dump({k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v))
                   for k, v in params.items()}, f, indent=2, ensure_ascii=False)

    spec = json.loads((ROOT / "modello_utilizzato" / "assets" / "feature_columns.json").read_text())
    with open(RISULTATI / "parameters" / "feature_spec.json", "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)

    meta = json.loads((ROOT / "modello_utilizzato" / "assets" / "metadata_production.json").read_text())
    with open(RISULTATI / "parameters" / "metadata_production.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print("  → parameters/ salvato")

    # ── RIEPILOGO PER CONSOLE ─────────────────────────────────────────────────
    print("\n" + "="*60)
    print("METRICHE TEST (log-space):")
    print(f"  MAE  = {mean_absolute_error(test['log_real'], test['log_pred']):.4f}")
    print(f"  RMSE = {np.sqrt(mean_squared_error(test['log_real'], test['log_pred'])):.4f}")
    print(f"  R²   = {r2_score(test['log_real'], test['log_pred']):.4f}")
    print(f"  sMAPE= {smape(test['log_real'].values, test['log_pred'].values):.2f}%")
    print("\nPer paese (R²):")
    for _, row in per_country_df.iterrows():
        print(f"  {row['iso3']} ({row['country']:<12}): R²={row['R2']:.3f}  MAE={row['MAE']:.3f}")
    print("="*60)

    return per_country_df, metrics_df, fi_df, test


if __name__ == "__main__":
    per_country_df, metrics_df, fi_df, test = run()
    print("\nScript completato. Output in risultati/")
