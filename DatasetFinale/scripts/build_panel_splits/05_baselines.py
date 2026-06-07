#!/usr/bin/env python3
"""Fase7 - 05_baselines

Compute the required baselines and save prediction and metric files.
Produces:
- results/baseline_predictions.csv
- results/baseline_metrics_global.csv
- results/baseline_metrics_by_country.csv
"""
from pathlib import Path
import pandas as pd
import numpy as np
import json
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, explained_variance_score


BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "data"
RESULTS_DIR = BASE / "results"
REPORTS_DIR = BASE / "reports"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_PATH = DATA_DIR / "train_main_catboost.csv"
TEST_PATH = DATA_DIR / "test_main_catboost.csv"


def score_log(y_true, y_pred):
    mse = mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    evs = explained_variance_score(y_true, y_pred)
    return {"mse": float(mse), "mae": float(mae), "rmse": float(rmse), "r2": float(r2), "evs": float(evs)}


def invert_log_to_cases(pred_log, population):
    # pred_log = log1p(cases_per_100k)
    pred_c_per_100k = np.expm1(pred_log)
    pred_cases = pred_c_per_100k * population / 100000.0
    return pred_c_per_100k, pred_cases


def interpretative_metrics(y_true_cases, y_pred_cases):
    mae = float(mean_absolute_error(y_true_cases, y_pred_cases))
    mse = float(mean_squared_error(y_true_cases, y_pred_cases))
    rmse = float(np.sqrt(mse))
    # WAPE = sum(|e|) / sum(actual)
    wape = float(np.sum(np.abs(y_true_cases - y_pred_cases)) / (np.sum(np.abs(y_true_cases)) + 1e-9))
    # sMAPE
    denom = (np.abs(y_true_cases) + np.abs(y_pred_cases))
    smape = float(np.mean(2.0 * np.abs(y_pred_cases - y_true_cases) / (denom + 1e-9)))
    return {"mae_cases": mae, "rmse_cases": rmse, "wape_cases": wape, "smape_cases": smape}


def main():
    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)

    id_cols = ["year", "month", "economy", "date", "cases_raw", "population"]
    target = "log_cases_per_100k"

    y_test = test[target].values

    baselines = {}
    preds_df_list = []

    # 1) lag12_same_month
    if "log_cases_per_100k_lag12" in test.columns:
        pred = test["log_cases_per_100k_lag12"].fillna(0).values
        baselines["lag12_same_month"] = pred

    # 2) lag1_last_month
    if "log_cases_per_100k_lag1" in test.columns:
        baselines["lag1_last_month"] = test["log_cases_per_100k_lag1"].fillna(test["log_cases_per_100k_lag1"].mean()).values

    # 3) seasonal_country_month_median
    # compute train medians by country and month
    med = train.groupby(["economy", "month"])[target].median().rename("median").reset_index()
    merged = test.merge(med, on=["economy", "month"], how="left")
    baselines["seasonal_country_month_median"] = merged["median"].fillna(train[target].median()).values

    # 4) rolling12_mean (already computed as feature)
    if "log_cases_per_100k_roll12_mean" in test.columns:
        baselines["rolling12_mean"] = test["log_cases_per_100k_roll12_mean"].fillna(0).values

    # Evaluate baselines
    global_metrics = []
    by_country_records = []
    all_preds_rows = []

    # actual cases (for interpretative metrics)
    actual_cases_per_100k = np.expm1(y_test)
    actual_cases = actual_cases_per_100k * test["population"].values / 100000.0

    for name, pred in baselines.items():
        sc = score_log(y_test, pred)

        # invert to cases
        pred_c_per_100k, pred_cases = invert_log_to_cases(pred, test["population"].values)
        interp = interpretative_metrics(actual_cases, pred_cases)

        combined = {**sc, **interp}
        combined["baseline"] = name
        global_metrics.append(combined)

        # per-country metrics
        df_tmp = pd.DataFrame({"economy": test["economy"].values, "y_true_log": y_test, "y_pred_log": pred, "population": test["population"].values})
        df_tmp["y_true_cases_per_100k"] = np.expm1(df_tmp["y_true_log"])
        df_tmp["y_true_cases"] = df_tmp["y_true_cases_per_100k"] * df_tmp["population"] / 100000.0
        df_tmp["y_pred_cases_per_100k"] = np.expm1(df_tmp["y_pred_log"]) 
        df_tmp["y_pred_cases"] = df_tmp["y_pred_cases_per_100k"] * df_tmp["population"] / 100000.0

        for econ, g in df_tmp.groupby("economy"):
            y_true = g["y_true_log"].values
            y_pred = g["y_pred_log"].values
            sc_c = score_log(y_true, y_pred)
            interp_c = interpretative_metrics(g["y_true_cases"].values, g["y_pred_cases"].values)
            rec = {"economy": econ, "baseline": name, **sc_c, **interp_c}
            by_country_records.append(rec)

        # store predictions rows
        rows = test[id_cols].copy()
        rows = rows.reset_index(drop=True)
        rows["y_true_log"] = y_test
        rows["y_pred_log"] = pred
        rows["baseline"] = name
        rows["y_pred_cases_per_100k"] = np.expm1(pred)
        rows["y_pred_cases"] = rows["y_pred_cases_per_100k"] * rows["population"] / 100000.0
        all_preds_rows.append(rows)

    # concat and save
    preds_all = pd.concat(all_preds_rows, ignore_index=True)
    preds_all.to_csv(RESULTS_DIR / "baseline_predictions.csv", index=False)

    pd.DataFrame(global_metrics).to_csv(RESULTS_DIR / "baseline_metrics_global.csv", index=False)
    pd.DataFrame(by_country_records).to_csv(RESULTS_DIR / "baseline_metrics_by_country.csv", index=False)

    # write simple report
    with open(REPORTS_DIR / "06_baselines.md", "w", encoding="utf-8") as f:
        f.write("# Fase 6 - Baseline\n\n")
        f.write("Baselines calcolate: \n")
        for n in baselines.keys():
            f.write(f"- {n}\n")
        f.write("\nFiles generati in results/: baseline_predictions.csv, baseline_metrics_global.csv, baseline_metrics_by_country.csv\n")

    print("Baselines computed and saved to results/")


if __name__ == '__main__':
    main()
