#!/usr/bin/env python3
"""Fase7 - 06_train_models

Trains simple baseline, an MLP (sklearn) and CatBoost (if available).
Saves model artifacts and a results JSON. Designed to run quickly for
experimentation; heavy tuning should be done in later phases.
"""
from pathlib import Path
import json
import runpy
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.neural_network import MLPRegressor


BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "data"
OUT_DIR = DATA_DIR
REPORTS_DIR = BASE / "reports"

TRAIN_MLP = DATA_DIR / "train_main_mlp.csv"
TEST_MLP = DATA_DIR / "test_main_mlp.csv"
TRAIN_CB = DATA_DIR / "train_main_catboost.csv"
TEST_CB = DATA_DIR / "test_main_catboost.csv"
FEATURE_JSON = DATA_DIR / "feature_columns.json"


def scores(y_true, y_pred):
    mse = mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    return {"mse": float(mse), "mae": float(mae), "rmse": float(rmse)}


def baseline_mean(train_y, test_y):
    pred = np.full(shape=len(test_y), fill_value=float(np.mean(train_y)))
    return pred


def baseline_persistence(test_df):
    # use lag1 column if available
    lag_col = "log_cases_per_100k_lag1"
    if lag_col in test_df.columns:
        return test_df[lag_col].fillna(test_df[lag_col].mean()).values
    else:
        return None


def train_mlp():
    train = pd.read_csv(TRAIN_MLP)
    test = pd.read_csv(TEST_MLP)

    # id cols
    id_cols = ["year", "month", "economy", "date", "cases_raw", "population"]
    target = "log_cases_per_100k"
    # Prefer to use the same feature split and scaler used at prediction time
    feat_file = FEATURE_JSON
    try:
        feat = json.loads(open(feat_file, "r", encoding="utf-8").read())
        mlp_num = feat["mlp"]["numerical"]
        mlp_dummies = feat["mlp"]["categorical_dummies"]
        scaler = joblib.load(DATA_DIR / "mlp_numeric_scaler.joblib")

        X_train_num = train[mlp_num].values
        X_train_num_s = scaler.transform(X_train_num)
        X_train_dummy = train[mlp_dummies].values
        X_train = np.hstack([X_train_num_s, X_train_dummy])

        X_test_num = test[mlp_num].values
        X_test_num_s = scaler.transform(X_test_num)
        X_test_dummy = test[mlp_dummies].values
        X_test = np.hstack([X_test_num_s, X_test_dummy])

        y_train = train[target].values
        y_test = test[target].values

    except Exception as e:
        # fallback: use dataframe-drop approach but warn
        print("Warning: using fallback unscaled features for MLP training (", e, ")")
        X_train = train.drop(columns=id_cols + [target])
        y_train = train[target].values
        X_test = test.drop(columns=id_cols + [target])
        y_test = test[target].values

    clf = MLPRegressor(hidden_layer_sizes=(128, 64), max_iter=500, random_state=0)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    sc = scores(y_test, preds)

    joblib.dump(clf, OUT_DIR / "mlp_model.joblib")
    return sc


def train_catboost():
    try:
        from catboost import CatBoostRegressor, Pool
    except Exception:
        return None, "catboost_not_installed"

    train = pd.read_csv(TRAIN_CB)
    test = pd.read_csv(TEST_CB)

    id_cols = ["year", "month", "economy", "date", "cases_raw", "population"]
    target = "log_cases_per_100k"

    X_train = train.drop(columns=id_cols + [target])
    y_train = train[target].values
    X_test = test.drop(columns=id_cols + [target])
    y_test = test[target].values

    # identify categorical indices
    cat_feature = "economy"
    if cat_feature in X_train.columns:
        cat_idx = [X_train.columns.get_loc(cat_feature)]
    else:
        cat_idx = []

    model = CatBoostRegressor(iterations=200, learning_rate=0.1, verbose=0, random_seed=0)
    model.fit(X_train, y_train, cat_features=cat_idx)
    preds = model.predict(X_test)
    sc = scores(y_test, preds)

    model.save_model(str(OUT_DIR / "catboost_model.cbm"))
    return sc, "ok"


def main():
    results = {}

    # Load train target for mean baseline
    train_mlp_df = pd.read_csv(TRAIN_MLP)
    test_mlp_df = pd.read_csv(TEST_MLP)
    y_train = train_mlp_df["log_cases_per_100k"].values
    y_test = test_mlp_df["log_cases_per_100k"].values

    # Mean baseline
    pred_mean = baseline_mean(y_train, y_test)
    results["baseline_mean"] = scores(y_test, pred_mean)

    # Persistence baseline
    p = baseline_persistence(test_mlp_df)
    if p is not None:
        results["baseline_persistence"] = scores(y_test, p)

    # Run dedicated baselines script to compute full baseline metrics and predictions
    try:
        runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts' / '05_baselines.py'))
        # load baseline global metrics if produced
        baseline_global = Path(__file__).resolve().parents[1] / 'results' / 'baseline_metrics_global.csv'
        baseline_by_country = Path(__file__).resolve().parents[1] / 'results' / 'baseline_metrics_by_country.csv'
        if baseline_global.exists():
            results['baseline_global_csv'] = str(baseline_global)
        if baseline_by_country.exists():
            results['baseline_by_country_csv'] = str(baseline_by_country)
    except Exception as e:
        results['baseline_script_error'] = str(e)

    # MLP
    try:
        results["mlp"] = train_mlp()
    except Exception as e:
        results["mlp_error"] = str(e)

    # CatBoost
    cb_sc, status = train_catboost()
    if status == "catboost_not_installed":
        results["catboost"] = "skipped: catboost not installed"
    else:
        results["catboost"] = cb_sc

    # Save results
    with open(OUT_DIR / "models_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Append short report
    with open(REPORTS_DIR / "06_models.md", "w", encoding="utf-8") as f:
        f.write("# Fase 6 — Modelli\n\n")
        f.write("Modelli allenati: baseline (mean), baseline (persistence, se disponibile), MLP (sklearn), CatBoost (se installato).\n\n")
        f.write("Risultati (models_results.json):\n\n")
        f.write(json.dumps(results, indent=2, ensure_ascii=False))

    print("Training finished. Results saved to:", OUT_DIR / "models_results.json")


if __name__ == '__main__':
    main()
