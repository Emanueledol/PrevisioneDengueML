"""
CatBoost inference pipeline for dengue case forecasting.

Target: log_cases_per_100k (log1p-transformed). Use predict_cases() to
get absolute case estimates; use predict_log() if downstream processing
needs the log-space predictions directly (e.g., uncertainty propagation).
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd

_ASSETS = Path(__file__).resolve().parents[1] / "assets"
_MODEL_PATH = _ASSETS / "catboost_dengue_2026.cbm"
_FEATURE_SPEC_PATH = _ASSETS / "feature_columns.json"


def _load_feature_spec():
    with open(_FEATURE_SPEC_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_model():
    """Load the production CatBoost model from assets/."""
    try:
        from catboost import CatBoostRegressor
    except ImportError as e:
        raise ImportError("catboost package not installed. Run: pip install catboost") from e

    model = CatBoostRegressor()
    model.load_model(str(_MODEL_PATH))
    return model


def predict_log(df: pd.DataFrame, model=None) -> np.ndarray:
    """Return log_cases_per_100k predictions for each row in df.

    Notes: df must contain the 39 numeric features plus 'economy' (ISO3 country code).
    Feature list is defined in assets/feature_columns.json under catboost.feature_columns.
    """
    if model is None:
        model = load_model()

    spec = _load_feature_spec()
    feature_cols = spec["catboost"]["feature_columns"]
    cat_features = spec["catboost"].get("categorical", [])

    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input DataFrame missing required columns: {missing}")

    X = df[feature_cols]
    try:
        preds = model.predict(X)
    except Exception:
        # Fallback: pass categorical indices instead of names (older catboost versions)
        cat_idx = [X.columns.get_loc(c) for c in cat_features if c in X.columns]
        preds = model.predict(X, cat_features=cat_idx)

    return np.array(preds, dtype=float)


def predict_cases(df: pd.DataFrame, model=None) -> np.ndarray:
    """Return absolute case count predictions for each row in df.

    Notes: df must also contain 'population' (total population) for the inverse
    normalisation. Prediction = expm1(log_cases_per_100k) * population / 100_000.
    """
    if "population" not in df.columns:
        raise ValueError("'population' column required for absolute case conversion")

    log_preds = predict_log(df, model)
    # Clip to zero: expm1 of a slightly-negative log prediction gives a small
    # negative cases/100k, which is physically impossible.
    cases_per_100k = np.maximum(np.expm1(log_preds), 0.0)
    return cases_per_100k * df["population"].values / 100_000.0
