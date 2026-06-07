from pathlib import Path
import json
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib


BASE = Path(__file__).resolve().parents[1]
DATA = BASE / 'data'
RESULTS = BASE / 'results'
PLOTS = BASE / 'plots'
PLOTS.mkdir(exist_ok=True)


def load_models_results():
    jr = DATA / 'models_results.json'
    if jr.exists():
        return json.loads(jr.read_text())
    return {}


def df_from_models_results(d):
    rows = []
    for k, v in d.items():
        # only include entries where the value is a dict of metrics
        if isinstance(v, dict):
            row = {'method': k}
            row.update(v)
            rows.append(row)
        else:
            # skip non-dict entries (e.g. file path strings)
            continue
    return pd.DataFrame(rows)


def compute_model_preds():
    # MLP
    mlp_preds = None
    try:
        mlp = joblib.load(DATA / 'mlp_model.joblib')
        scaler = joblib.load(DATA / 'mlp_numeric_scaler.joblib')
        feat = json.loads((DATA / 'feature_columns.json').read_text())
        mlp_cols = feat['mlp']['numerical'] + feat['mlp']['categorical_dummies']
        test_mlp = pd.read_csv(DATA / 'test_main_mlp.csv')
        X_num = test_mlp[feat['mlp']['numerical']].values
        X_num_s = scaler.transform(X_num)
        X_dummy = test_mlp[feat['mlp']['categorical_dummies']].values
        X = np.hstack([X_num_s, X_dummy])
        preds = mlp.predict(X)
        mlp_preds = test_mlp[['year','month','economy','date']].copy()
        mlp_preds['y_true_log'] = test_mlp[feat['target']]
        mlp_preds['mlp_pred_log'] = preds
        mlp_preds.to_csv(RESULTS / 'mlp_predictions.csv', index=False)
    except Exception as e:
        print('MLP predict failed:', e)

    # CatBoost
    cat_preds = None
    try:
        from catboost import CatBoostRegressor
        cb = CatBoostRegressor()
        cb.load_model(str(DATA / 'catboost_model.cbm'))
        feat = json.loads((DATA / 'feature_columns.json').read_text())
        cb_cols = feat['catboost']['feature_columns']
        test_cb = pd.read_csv(DATA / 'test_main_catboost.csv')
        X_cb = test_cb[cb_cols]
        preds_cb = cb.predict(X_cb)
        cat_preds = test_cb[['year','month','economy','date']].copy()
        cat_preds['y_true_log'] = test_cb[feat['target']]
        cat_preds['catboost_pred_log'] = preds_cb
        cat_preds.to_csv(RESULTS / 'catboost_predictions.csv', index=False)
    except Exception as e:
        print('CatBoost predict failed:', e)

    return mlp_preds, cat_preds


def per_country_metrics(preds_df, pred_col, true_col='y_true_log'):
    df = preds_df.copy()
    records = []
    for econ, g in df.groupby('economy'):
        y = g[true_col].values
        p = g[pred_col].values
        mse = mean_squared_error(y, p)
        mae = mean_absolute_error(y, p)
        rmse = np.sqrt(mse)
        r2 = r2_score(y, p)
        records.append({'economy': econ, 'method': pred_col, 'mse': mse, 'mae': mae, 'rmse': rmse, 'r2': r2})
    return pd.DataFrame.from_records(records)


def main():
    RESULTS.mkdir(exist_ok=True)
    models = load_models_results()
    models_df = df_from_models_results(models)

    # load baseline global
    baseline_global = pd.read_csv(RESULTS / 'baseline_metrics_global.csv') if (RESULTS / 'baseline_metrics_global.csv').exists() else pd.DataFrame()
    if not baseline_global.empty:
        baseline_global = baseline_global.rename(columns={'baseline': 'method'})

    # combine for global comparison
    combined = pd.DataFrame()
    if not baseline_global.empty:
        combined = baseline_global.copy()
    if not models_df.empty:
        # models_df has method, mse, mae, rmse
        models_df = models_df.rename(columns={'method': 'method'})
        # ensure columns
        for c in ['mse','mae','rmse']:
            if c not in models_df.columns:
                models_df[c] = np.nan
        if combined.empty:
            combined = models_df
        else:
            combined = pd.concat([combined, models_df], ignore_index=True, sort=False)

    combined.to_csv(RESULTS / 'model_comparison_global.csv', index=False)

    # compute predictions and per-country metrics for models
    mlp_preds, cat_preds = compute_model_preds()

    by_country = pd.DataFrame()
    # load baseline by country
    if (RESULTS / 'baseline_metrics_by_country.csv').exists():
        bby = pd.read_csv(RESULTS / 'baseline_metrics_by_country.csv')
        bby = bby.rename(columns={'baseline': 'method'})
        by_country = bby[['economy','method','mse','mae','rmse','r2']].copy()

    if mlp_preds is not None:
        mdf = per_country_metrics(mlp_preds, 'mlp_pred_log')
        by_country = pd.concat([by_country, mdf.rename(columns={'method':'method'})], ignore_index=True, sort=False)
    if cat_preds is not None:
        cdf = per_country_metrics(cat_preds, 'catboost_pred_log')
        by_country = pd.concat([by_country, cdf.rename(columns={'method':'method'})], ignore_index=True, sort=False)

    if not by_country.empty:
        by_country.to_csv(RESULTS / 'model_comparison_by_country.csv', index=False)

    # plots: global rmse bar
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        sns.set(style='whitegrid')
        gdf = combined.copy()
        if 'rmse' in gdf.columns:
            plt.figure(figsize=(8,5))
            sns.barplot(data=gdf.sort_values('rmse', ascending=True), x='rmse', y='method', palette='viridis')
            plt.title('Global RMSE comparison')
            plt.tight_layout()
            plt.savefig(PLOTS / 'model_comparison_global_rmse.png')
            plt.close()

        # heatmap per-country rmse pivot
        if not by_country.empty:
            pivot = by_country.pivot_table(index='economy', columns='method', values='rmse')
            plt.figure(figsize=(10,6))
            sns.heatmap(pivot, annot=True, fmt='.2f', cmap='magma')
            plt.title('Per-country RMSE (rows=economy)')
            plt.tight_layout()
            plt.savefig(PLOTS / 'model_comparison_by_country_rmse.png')
            plt.close()
    except Exception as e:
        print('Plotting failed:', e)


if __name__ == '__main__':
    main()
