from pathlib import Path
import pandas as pd
import numpy as np


IN_CSV = Path(__file__).parents[1] / "data" / "panel_targets.csv"
OUT_CSV = Path(__file__).parents[1] / "data" / "panel_features.csv"
OUT_REPORT = Path(__file__).parents[1] / "reports" / "04_temporal_features.md"


def add_lags_and_rolls(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["economy", "year", "month"]).copy()

    # Lag epidemiologici
    lag_cols = ["cases", "cases_per_100k", "log_cases_per_100k"]
    lags = [1, 2, 3, 12]
    for col in lag_cols:
        for lag in lags:
            df[f"{col}_lag{lag}"] = df.groupby("economy")[col].shift(lag)

    # Lag climatici (t2m e tp_mm con lag 1, 2, 3)
    for col in ["t2m", "tp_mm"]:
        if col in df.columns:
            for lag in [1, 2, 3]:
                df[f"{col}_lag{lag}"] = df.groupby("economy")[col].shift(lag)

    # Rolling means - use shifted series to avoid leakage
    roll_defs = [("cases_per_100k", [3, 6, 12]), ("log_cases_per_100k", [3, 6, 12])]
    for col, windows in roll_defs:
        for w in windows:
            df[f"{col}_roll{w}_mean"] = df.groupby("economy")[col].apply(lambda s: s.shift(1).rolling(window=w, min_periods=1).mean()).reset_index(level=0, drop=True)

    # Cyclical month features
    df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12)
    df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12)

    return df


def main():
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Input not found: {IN_CSV}")

    df = pd.read_csv(IN_CSV)
    before_rows = len(df)

    df_feat = add_lags_and_rolls(df)

    # Rows to drop: those without lag12 for log_cases_per_100k
    required_col = "log_cases_per_100k_lag12"
    missing_lag12 = df_feat[required_col].isna().sum()
    df_model = df_feat.dropna(subset=[required_col]).reset_index(drop=True)
    dropped = before_rows - len(df_model)

    # Save
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_model.to_csv(OUT_CSV, index=False)

    # Report
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write("# Report - Temporal Features (Fase7)\n\n")
        f.write(f"**Input**: {IN_CSV}\n\n")
        f.write("## Lag e rolling creati\n\n")
        f.write("- Lag creati per: cases, cases_per_100k, log_cases_per_100k (lag 1,2,3,12)\n")
        f.write("- Rolling mean (shifted di 1) per country:\n")
        f.write("  - cases_per_100k_roll3_mean, roll6, roll12\n")
        f.write("  - log_cases_per_100k_roll3_mean, roll6, roll12\n\n")
        f.write("## Righe eliminate per lag12 mancante\n\n")
        f.write(f"- Righe prima: {before_rows}\n")
        f.write(f"- Righe dopo: {len(df_model)}\n")
        f.write(f"- Righe eliminate: {dropped}\n")
        f.write(f"- Righe con {required_col} mancanti: {missing_lag12}\n\n")
        f.write("## Note operative\n\n")
        f.write("- Rolling sono calcolate su serie shiftata di 1 mese per evitare leakage.\n")
        f.write("- `panel_features.csv` è il dataset modellabile per gli esperimenti in Fase7.\n")

    print(f"Panel features salvato in: {OUT_CSV}")
    print(f"Report generato in: {OUT_REPORT}")


if __name__ == '__main__':
    main()
