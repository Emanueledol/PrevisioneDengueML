from pathlib import Path
import pandas as pd
import numpy as np


DEFAULT_INPUT = Path(__file__).parents[2] / "Fase1" / "Dataset_Tesi_MENSILE_2014_2024_pivot_lags_cycles.csv"
OUT_DATA = Path(__file__).parents[1] / "data" / "panel_clean.csv"
OUT_REPORT = Path(__file__).parents[1] / "reports" / "02_panel_clean.md"


def build_clean_panel(input_path: Path, out_data: Path, out_report: Path) -> None:
    out_data.parent.mkdir(parents=True, exist_ok=True)
    out_report.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input pivot not found: {input_path}")

    df = pd.read_csv(input_path)
    original_rows = len(df)

    if "cases" not in df.columns:
        raise ValueError("Column 'cases' not found in input pivot")

    # Preserve raw target for audit
    df["cases_raw"] = df["cases"].where(pd.notna(df["cases"]), other=np.nan)

    # Count negatives in raw
    neg_before = int((df["cases_raw"] < 0).sum())
    neg_by_country = df[df["cases_raw"] < 0].groupby("economy")["cases_raw"].count().to_dict()
    unique_neg_values = sorted(df.loc[df["cases_raw"] < 0, "cases_raw"].dropna().unique().tolist())

    # Create clipped cases (do not interpolate target)
    df["cases"] = df["cases_raw"].clip(lower=0)

    # Interpolate only feature numeric columns (exclude year/month/cases/cases_raw)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    exclude = {"year", "month", "cases", "cases_raw"}
    feat_numeric = [c for c in numeric_cols if c not in exclude]

    if feat_numeric:
        df[feat_numeric] = df.sort_values(["economy", "year", "month"]).groupby("economy")[feat_numeric].transform(
            lambda g: g.interpolate(method="linear", limit_direction="both")
        )
        df[feat_numeric] = df.groupby("economy")[feat_numeric].transform(lambda g: g.ffill().bfill())

    # Drop rows where target is still missing after preserving cases_raw
    missing_cases_after = int(df["cases"].isna().sum())
    if missing_cases_after > 0:
        df = df.dropna(subset=["cases"]).reset_index(drop=True)

    # Uniqueness checks
    dup_count = int(df.duplicated(subset=["economy", "year", "month"]).sum())

    # Save cleaned panel
    df.to_csv(out_data, index=False)

    # Write a small report
    with open(out_report, "w", encoding="utf-8") as f:
        f.write("# Report - Panel Clean (Fase7)\n\n")
        f.write(f"**Input pivot**: {input_path}\n\n")
        f.write("## Statistiche generali\n\n")
        f.write(f"- Righe originali pivot: {original_rows}\n")
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
        f.write("- `cases_raw` è salvato nel dataset per audit.\n")
        f.write("- `cases` è `max(cases_raw, 0)` — non è stata interpolata.\n")
        f.write("- Questo file è la base per le fasi successive in `Fase7_VariantePaper`.\n")

    print(f"Panel pulito salvato in: {out_data}")
    print(f"Report generato in: {out_report}")


def main():
    build_clean_panel(DEFAULT_INPUT, OUT_DATA, OUT_REPORT)


if __name__ == "__main__":
    main()
