#!/usr/bin/env python3
"""Fase7 - 04_make_splits

Creates train/test splits (Scenario B), produces CatBoost-ready and MLP-ready
CSV files, saves `feature_columns.json`, `folds_rolling.json` and a scaler
for the MLP features.

Decisions applied (user approved):
- Scenario B: train years 2014-2021, test years 2022-2023
- Drop rows missing `log_cases_per_100k_lag12`
- Clip negatives already applied earlier; `cases_raw` kept for audit
"""
from pathlib import Path
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib


BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "data"
OUT_DIR = DATA_DIR
REPORTS_DIR = BASE / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

IN_PATH = DATA_DIR / "panel_features.csv"


def load_panel(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # create a datetime index for convenience
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    df["date"] = pd.to_datetime(df["year"].astype(str) + "-" + df["month"].astype(str) + "-01")
    return df


def main():
    df = load_panel(IN_PATH)

    # 1) Drop rows that miss the 12-month lag for the log-target (user requested)
    before = len(df)
    df = df.dropna(subset=["log_cases_per_100k_lag12"]) 
    after = len(df)

    # 2) Split by Scenario B: train <=2021, test >=2022
    train_df = df[df["year"] <= 2021].copy()
    test_df = df[df["year"] >= 2022].copy()

    # 3) Define target and identifiers
    target_col = "log_cases_per_100k"
    id_cols = ["year", "month", "economy", "date", "cases_raw", "population"]

    # 4) Features: everything except id cols and the target
    all_cols = list(df.columns)
    # Explicitly exclude target-like columns to avoid leakage
    forbidden = set([target_col, 'cases', 'cases_raw', 'cases_per_100k', 'log_cases_per_100k'])
    feature_cols = [c for c in all_cols if c not in id_cols + [target_col] and c not in forbidden]

    # 5) Save CatBoost-ready datasets (economy left as categorical)
    cb_train = train_df[id_cols + feature_cols + [target_col]]
    cb_test = test_df[id_cols + feature_cols + [target_col]]
    cb_train_path = OUT_DIR / "train_main_catboost.csv"
    cb_test_path = OUT_DIR / "test_main_catboost.csv"
    cb_train.to_csv(cb_train_path, index=False)
    cb_test.to_csv(cb_test_path, index=False)

    # 6) Prepare MLP-ready datasets: one-hot economy + scale numeric features
    cat_col = "economy"
    numeric_features = [c for c in feature_cols if c != cat_col]

    # Fit scaler on train numeric features only
    scaler = StandardScaler()
    X_train_num = train_df[numeric_features].fillna(0).values
    scaler.fit(X_train_num)

    # transform train/test numeric
    train_num_scaled = pd.DataFrame(scaler.transform(train_df[numeric_features].fillna(0).values),
                                    columns=numeric_features, index=train_df.index)
    test_num_scaled = pd.DataFrame(scaler.transform(test_df[numeric_features].fillna(0).values),
                                   columns=numeric_features, index=test_df.index)

    # One-hot economy using categories seen in training (guarantee same columns)
    train_econ_cats = sorted(train_df[cat_col].dropna().unique().tolist())
    def make_econ_dummies(series: pd.Series, cats: list):
        d = pd.get_dummies(series).astype(int)
        # ensure columns for all training categories
        for c in cats:
            if c not in d.columns:
                d[c] = 0
        # keep consistent order
        return d[cats]

    train_econ = make_econ_dummies(train_df[cat_col], train_econ_cats)
    test_econ = make_econ_dummies(test_df[cat_col], train_econ_cats)

    # Assemble MLP tables
    mlp_train = pd.concat([train_df[id_cols].reset_index(drop=True), train_num_scaled.reset_index(drop=True), train_econ.reset_index(drop=True), train_df[[target_col]].reset_index(drop=True)], axis=1)
    mlp_test = pd.concat([test_df[id_cols].reset_index(drop=True), test_num_scaled.reset_index(drop=True), test_econ.reset_index(drop=True), test_df[[target_col]].reset_index(drop=True)], axis=1)

    mlp_train_path = OUT_DIR / "train_main_mlp.csv"
    mlp_test_path = OUT_DIR / "test_main_mlp.csv"
    mlp_train.to_csv(mlp_train_path, index=False)
    mlp_test.to_csv(mlp_test_path, index=False)

    # Save scaler
    joblib.dump(scaler, OUT_DIR / "mlp_numeric_scaler.joblib")

    # 7) Save feature_columns.json
    feature_columns = {
        "target": target_col,
        "id_cols": id_cols,
        "features": feature_cols,
        "catboost": {"categorical": [cat_col], "feature_columns": feature_cols},
        "mlp": {"numerical": numeric_features, "categorical_dummies": train_econ_cats}
    }
    with open(OUT_DIR / "feature_columns.json", "w", encoding="utf-8") as f:
        json.dump(feature_columns, f, indent=2, ensure_ascii=False)

    # 8) Save simple folds_rolling.json describing Scenario B (train up to 2021)
    folds = {
        "scenario": "B",
        "train_years": list(range(int(df["year"].min()), 2022)),
        "test_years": [2022, 2023],
        "notes": "User approved Scenario B: train 2014-2021, test 2022-2023."
    }
    with open(OUT_DIR / "folds_rolling.json", "w", encoding="utf-8") as f:
        json.dump(folds, f, indent=2)

    # 9) Write a short report
    with open(REPORTS_DIR / "05_splits.md", "w", encoding="utf-8") as f:
        f.write(f"# Fase 5 — Splits e feature sets\n\n")
        f.write(f"Righe prima della rimozione lag12: {before}\n\n")
        f.write(f"Righe dopo rimozione lag12: {after}\n\n")
        f.write("Files generati:\n")
        f.write(f"- {cb_train_path}\n")
        f.write(f"- {cb_test_path}\n")
        f.write(f"- {mlp_train_path}\n")
        f.write(f"- {mlp_test_path}\n")
        f.write(f"- {OUT_DIR / 'feature_columns.json'}\n")
        f.write(f"- {OUT_DIR / 'folds_rolling.json'}\n")
        f.write("\nDecisioni applicate: Scenario B, drop log_cases_per_100k_lag12 rows, economy one-hot for MLP, economy categorical for CatBoost.\n")

    print("Splits and feature sets created:")
    print(f"- CatBoost train: {cb_train_path}")
    print(f"- CatBoost test: {cb_test_path}")
    print(f"- MLP train: {mlp_train_path}")
    print(f"- MLP test: {mlp_test_path}")
    print(f"- Feature columns: {OUT_DIR / 'feature_columns.json'}")
    print(f"- Folds: {OUT_DIR / 'folds_rolling.json'}")


if __name__ == '__main__':
    main()
