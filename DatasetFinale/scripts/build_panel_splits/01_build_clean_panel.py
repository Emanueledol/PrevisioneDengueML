from pathlib import Path
import pandas as pd
import numpy as np


DEFAULT_INPUT = Path(__file__).resolve().parents[2] / "dataset_raw.csv"
OUT_DATA = Path(__file__).parents[1] / "data" / "panel_clean.csv"
OUT_REPORT = Path(__file__).parents[1] / "reports" / "02_panel_clean.md"


def pivot_raw(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot dataset_raw.csv da formato long (series/value) a panel wide."""
    base_keys = ['year', 'month', 'economy', 't2m', 'tp', 'sp', 'lai_hv', 'lai_lv', 'tp_mm', 'cases']
    id_cols = [c for c in base_keys if c in df.columns]
    base = df[id_cols].drop_duplicates(subset=['economy', 'year', 'month'])

    socio = df[['economy', 'year', 'series', 'value']].dropna(subset=['series'])
    socio_wide = (
        socio.pivot_table(index=['economy', 'year'], columns='series', values='value', aggfunc='first')
        .reset_index()
    )
    socio_wide.columns.name = None

    return base.merge(socio_wide, on=['economy', 'year'], how='left')


def build_clean_panel(input_path: Path, out_data: Path, out_report: Path) -> None:
    out_data.parent.mkdir(parents=True, exist_ok=True)
    out_report.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    df = pd.read_csv(input_path)

    # Pivot long -> wide se il dataset grezzo usa colonne series/value
    if 'series' in df.columns and 'value' in df.columns:
        df = pivot_raw(df)

    original_rows = len(df)

    if "cases" not in df.columns:
        raise ValueError("Column 'cases' not found in input")

    df["cases_raw"] = df["cases"].where(pd.notna(df["cases"]), other=np.nan)

    neg_before = int((df["cases_raw"] < 0).sum())
    neg_by_country = df[df["cases_raw"] < 0].groupby("economy")["cases_raw"].count().to_dict()
    unique_neg_values = sorted(df.loc[df["cases_raw"] < 0, "cases_raw"].dropna().unique().tolist())

    df["cases"] = df["cases_raw"].clip(lower=0)

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    exclude = {"year", "month", "cases", "cases_raw"}
    feat_numeric = [c for c in numeric_cols if c not in exclude]

    if feat_numeric:
        df[feat_numeric] = df.sort_values(["economy", "year", "month"]).groupby("economy")[feat_numeric].transform(
            lambda g: g.interpolate(method="linear", limit_direction="both")
        )
        df[feat_numeric] = df.groupby("economy")[feat_numeric].transform(lambda g: g.ffill().bfill())

    missing_cases_after = int(df["cases"].isna().sum())
    if missing_cases_after > 0:
        df = df.dropna(subset=["cases"]).reset_index(drop=True)

    dup_count = int(df.duplicated(subset=["economy", "year", "month"]).sum())

    df.to_csv(out_data, index=False)

    with open(out_report, "w", encoding="utf-8") as f:
        f.write("# Report - Panel Clean\n\n")
        f.write(f"**Input**: {input_path}\n\n")
        f.write("## Statistiche generali\n\n")
        f.write(f"- Righe originali: {original_rows}\n")
        f.write(f"- Righe dopo pulizia: {len(df)}\n")
        f.write(f"- Duplicati (economy/year/month): {dup_count}\n\n")
        f.write("## Target `cases`\n\n")
        f.write(f"- Casi negativi originali (cases_raw < 0): {neg_before}\n")
        if neg_by_country:
            f.write("- Negativi per paese:\n")
            for k, v in sorted(neg_by_country.items()):
                f.write(f"  - {k}: {v}\n")
        if unique_neg_values:
            f.write(f"- Valori negativi unici: {unique_neg_values}\n")
        f.write(f"- Righe con `cases` mancanti rimosse: {missing_cases_after}\n\n")
        f.write("## Interpolazione\n\n")
        f.write("- Interpolazione applicata SOLO alle feature numeriche (escluso `cases` e `cases_raw`).\n")
        f.write(f"- Colonne numeriche interpolate: {feat_numeric}\n\n")
        f.write("## Note operative\n\n")
        f.write("- `cases_raw` e' preservato per audit.\n")
        f.write("- `cases` e' `max(cases_raw, 0)` - non interpolata.\n")

    print(f"Panel pulito salvato in: {out_data}")
    print(f"Report generato in: {out_report}")


def main():
    build_clean_panel(DEFAULT_INPUT, OUT_DATA, OUT_REPORT)


if __name__ == "__main__":
    main()
