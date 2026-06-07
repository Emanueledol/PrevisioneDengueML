#!/usr/bin/env python3
"""Check dataset/features for target leakage.

Usage: py -3 check_leak.py

Exits with code 0 if no strong leak detected, 2 otherwise.
"""
from pathlib import Path
import json
import sys
import pandas as pd
import numpy as np


def locate_data_dir():
    local = Path(__file__).resolve().parents[1] / 'data'
    if local.exists() and any(local.iterdir()):
        return local
    for p in Path(__file__).resolve().parents:
        cand = p / 'Fase7_VariantePaper' / 'data'
        if cand.exists() and any(cand.iterdir()):
            return cand
    raise RuntimeError('Could not locate data directory')


def is_target_like(col, target):
    # exact matches that are forbidden as features
    forbidden = {target, 'cases', 'cases_raw', 'cases_per_100k', 'log_cases_per_100k'}
    return col in forbidden


def main():
    data_dir = locate_data_dir()
    feat_file = data_dir / 'feature_columns.json'
    if not feat_file.exists():
        print('feature_columns.json not found in', data_dir)
        sys.exit(2)

    feat = json.loads(open(feat_file, 'r', encoding='utf-8').read())
    target = feat.get('target')
    cb_features = feat.get('catboost', {}).get('feature_columns', [])
    mlp_num = feat.get('mlp', {}).get('numerical', [])

    train_path = data_dir / 'train_main_catboost.csv'
    if not train_path.exists():
        print('Train CSV not found:', train_path)
        sys.exit(2)

    df = pd.read_csv(train_path)

    issues = []

    # 1) direct-name leakage
    for f in sorted(set(cb_features) | set(mlp_num)):
        if is_target_like(f, target):
            issues.append((f, 'direct_target_name'))

    # 2) correlation checks
    pearson_thresh = 0.9
    spearman_thresh = 0.95
    corr_issues = []
    if target not in df.columns:
        print(f"Target column '{target}' not present in train CSV; skipping correlation checks")
    else:
        y = df[target].fillna(0)
        for f in sorted(set(cb_features) | set(mlp_num)):
            if f not in df.columns:
                continue
            # skip obviously lag/roll features (explicitly allowed)
            if any(suffix in f for suffix in ['_lag', '_roll']):
                continue
            try:
                x = pd.to_numeric(df[f], errors='coerce').fillna(0)
            except Exception:
                continue
            if x.nunique() <= 1:
                continue
            p = abs(x.corr(y))
            s = abs(x.corr(y, method='spearman'))
            if not np.isnan(p) and p >= pearson_thresh:
                corr_issues.append((f, 'pearson', float(p)))
            elif not np.isnan(s) and s >= spearman_thresh:
                corr_issues.append((f, 'spearman', float(s)))

    # Summarize
    if issues or corr_issues:
        print('\n=== LEAK DETECTED ===')
        if issues:
            print('\nDirect target-like columns present among features:')
            for f, kind in issues:
                print(f'- {f}  ({kind})')
        if corr_issues:
            print('\nHigh-correlation features (may indicate leakage):')
            for f, method, val in corr_issues:
                print(f'- {f}: {method} corr = {val:.4f}')
        print('\nAction: remove direct target columns from feature lists and re-run make_splits.py')
        # write a short report
        rpt = data_dir.parent / 'reports' / 'check_leak.md'
        rpt.parent.mkdir(parents=True, exist_ok=True)
        with open(rpt, 'w', encoding='utf-8') as fo:
            fo.write('# Leak check report\n\n')
            if issues:
                fo.write('Direct target-like columns found:\n')
                for f, k in issues:
                    fo.write(f'- {f}\n')
            if corr_issues:
                fo.write('\nHigh correlation features:\n')
                for f, method, val in corr_issues:
                    fo.write(f'- {f}: {method} = {val:.4f}\n')
        sys.exit(2)

    print('No direct target-like features found and no high correlations detected.')
    sys.exit(0)


if __name__ == '__main__':
    main()
