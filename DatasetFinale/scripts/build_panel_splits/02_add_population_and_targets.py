from pathlib import Path
import pandas as pd
import numpy as np


DEFAULT_INPUT = Path(__file__).parents[1] / "data" / "panel_clean.csv"
POP_CSV = Path(__file__).resolve().parents[2] / "Fase5_Normalizzazione" / "API_SP.POP.TOTL_DS2_en_csv_v2_127039.csv"
OUT_DATA = Path(__file__).parents[1] / "data" / "panel_targets.csv"
OUT_REPORT = Path(__file__).parents[1] / "reports" / "03_targets.md"


def add_population_and_targets(input_path: Path, pop_csv: Path, out_data: Path, out_report: Path) -> None:
    out_data.parent.mkdir(parents=True, exist_ok=True)
    out_report.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input clean panel not found: {input_path}")
    if not pop_csv.exists():
        raise FileNotFoundError(f"Population CSV not found: {pop_csv}")

    df = pd.read_csv(input_path)
    df_orig_rows = len(df)

    # Load population (World Bank CSV with 4 header rows)
    pop_raw = pd.read_csv(pop_csv, skiprows=4)
    # Melt to long format
    year_cols = [c for c in pop_raw.columns if c.isdigit()]
    pop_wide = pop_raw[["Country Code"] + year_cols].rename(columns={"Country Code": "economy"})
    pop_long = pop_wide.melt(id_vars="economy", var_name="year", value_name="population")
    pop_long["year"] = pop_long["year"].astype(int)
    pop_long["population"] = pd.to_numeric(pop_long["population"], errors="coerce")

    # Merge
    merged = df.merge(pop_long, on=["economy", "year"], how="left")

    missing_pop = merged[merged["population"].isna()][["economy", "year"]].drop_duplicates()
    n_missing_pop = len(missing_pop)

    # Decide: drop rows with missing population (documented)
    if n_missing_pop > 0:
        merged = merged.merge(pop_long, on=["economy", "year"], how="left")
        # For transparency, keep rows but will drop where population missing
        merged = merged.dropna(subset=["population"]).reset_index(drop=True)

    # Ensure cases present and non-negative (cases were clipped in previous step)
    if "cases" not in merged.columns:
        raise ValueError("Column 'cases' missing after merge")
    merged["cases"] = merged["cases"].fillna(0)
    neg_after = int((merged["cases"] < 0).sum())

    # Compute targets
    merged["cases_per_100k"] = (merged["cases"] / merged["population"]) * 100000.0
    merged["log_cases_per_100k"] = np.log1p(merged["cases_per_100k"])

    # Sanity checks
    n_nan_target = int(merged["cases_per_100k"].isna().sum()) + int(merged["log_cases_per_100k"].isna().sum())

    # Save outputs
    merged.to_csv(out_data, index=False)

    # Write report
    with open(out_report, "w", encoding="utf-8") as f:
        f.write("# Report - Targets e Popolazione (Fase7)\n\n")
        f.write(f"**Input clean panel**: {input_path}\n")
        f.write(f"**Population source**: {pop_csv}\n\n")
        f.write("## Merge & Copertura\n\n")
        f.write(f"- Righe nel panel originale: {df_orig_rows}\n")
        f.write(f"- Righe dopo merge e rimozione rows senza popolazione: {len(merged)}\n")
        f.write(f"- Righe senza popolazione trovate (unique economy-year): {n_missing_pop}\n")
        if n_missing_pop > 0:
            f.write("- Dettaglio anni/paesi senza popolazione (esempio):\n")
            sample_missing = missing_pop.head(10).to_dict(orient="records")
            for r in sample_missing:
                f.write(f"  - {r['economy']} - {r['year']}\n")

        f.write("\n## Target calcolati\n\n")
        for col in ["cases", "cases_per_100k", "log_cases_per_100k"]:
            s = merged[col]
            f.write(f"- {col}: min={float(s.min()):.4f}, median={float(s.median()):.4f}, mean={float(s.mean()):.4f}, max={float(s.max()):.4f}\n")

        f.write("\n## Note operative\n\n")
        f.write("- `cases_raw` è preservato dal passo precedente.\n")
        f.write("- `cases` è stato clippato a 0 in Fase7 e non interpolato.\n")
        f.write("- Le righe senza popolazione sono state rimosse prima del calcolo dei target e sono elencate sopra.\n")
        f.write("- Questo file `panel_targets.csv` è il dataset pronto per la creazione di lag e per gli step successivi in Fase7.\n")

    print(f"Targets calcolati e salvati in: {out_data}")
    print(f"Report generato in: {out_report}")


def main():
    add_population_and_targets(DEFAULT_INPUT, POP_CSV, OUT_DATA, OUT_REPORT)


if __name__ == "__main__":
    main()
