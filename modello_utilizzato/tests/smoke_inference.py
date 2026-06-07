"""
Smoke test for the production CatBoost dengue model.

Verifies that:
  1. The model loads without errors from modello_utilizzato/assets/
  2. Predictions on the reference test set fall within expected numerical ranges
  3. Per-country predictions are non-negative (as cases/100k are non-negative)

Run with: python modello_utilizzato/tests/smoke_inference.py
No manual path edits should be required.
"""

import sys
from pathlib import Path

# Make src importable regardless of working directory
_repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_repo_root / "modello_utilizzato" / "src"))

import numpy as np
import pandas as pd

from inference import load_model, predict_log, predict_cases


ASSETS = Path(__file__).resolve().parents[1] / "assets"
TEST_CSV = ASSETS / "test_reference.csv"

# Ranges validated against Fase8 results/catboost_predictions_final.csv
LOG_PRED_MIN = -1.0
LOG_PRED_MAX = 10.0
CASES_PER_100K_MAX = 12000.0


def main():
    print("Loading model...")
    model = load_model()
    print(f"  OK: {type(model).__name__} loaded from {ASSETS / 'catboost_dengue_2026.cbm'}")

    print("Loading reference test set...")
    df = pd.read_csv(TEST_CSV)
    print(f"  OK: {len(df)} rows, {df['economy'].nunique()} countries")

    print("Running log-space predictions...")
    log_preds = predict_log(df, model)
    assert log_preds.shape == (len(df),), "Prediction count mismatch"
    assert not np.isnan(log_preds).any(), "NaN values in log predictions"
    assert log_preds.min() >= LOG_PRED_MIN, (
        f"Minimum log prediction {log_preds.min():.4f} below expected floor {LOG_PRED_MIN}"
    )
    assert log_preds.max() <= LOG_PRED_MAX, (
        f"Maximum log prediction {log_preds.max():.4f} above expected ceiling {LOG_PRED_MAX}"
    )
    print(f"  OK: log predictions in [{log_preds.min():.3f}, {log_preds.max():.3f}]")

    print("Running absolute case predictions...")
    case_preds = predict_cases(df, model)
    assert (case_preds >= 0).all(), "Negative case predictions detected"
    assert case_preds.max() <= CASES_PER_100K_MAX * df["population"].max() / 100_000, (
        "Absolute case predictions unreasonably large"
    )
    print(f"  OK: case predictions non-negative, max={case_preds.max():.0f}")

    print("Per-country check...")
    df["_pred_log"] = log_preds
    for country, group in df.groupby("economy"):
        assert not np.isnan(group["_pred_log"].values).any(), f"NaN for {country}"
    print(f"  OK: all {df['economy'].nunique()} countries produce valid predictions")

    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    main()
