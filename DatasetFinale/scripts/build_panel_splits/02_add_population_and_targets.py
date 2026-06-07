from pathlib import Path
import pandas as pd
import numpy as np
import wbgapi as wb


DEFAULT_INPUT = Path(__file__).parents[1] / "data" / "panel_clean.csv"
OUT_DATA = Path(__file__).parents[1] / "data" / "panel_targets.csv"
OUT_REPORT = Path(__file__).parents[1] / "reports" / "03_targets.md"


def load_population(economies: list, years: range) -> pd.DataFrame:
    """Scarica popolazione totale da World Bank API (SP.POP.TOTL)."""
    pop = (
        wb.data.DataFrame(['SP.POP.TOTL'], economies=economies, time=years, numericTimeKeys=True)
        .reset_index()
        .drop(columns='series')
    )
    pop = pop.melt(id_vars='economy', var_name='year', value_name='population')
    pop['year'] = pop['year'].astype(int)
    pop['population'] = pd.to_numeric(pop['population'], errors='coerce')
    return pop[['economy', 'year', 'population']]


def add_population_and_targets(input_path: Path, out_data: Path, out_report: Path) -> None:
    out_data.parent.mkdir(parents=True, exist_ok=True)
    out_report.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input clean panel not found: {input_path}")

    df = pd.read_csv(input_path)
    df_orig_rows = len(df)

    economies = sorted(df['economy'].dropna().unique().tolist())
    years = range(int(df['year'].min()), int(df['year'].max()) + 2)
    pop_long = load_population(economies, years)

    merged = df.merge(pop_long, on=["economy", "year"], how="left")

    missing_pop = merged[merged["population"].isna()][["economy", "year"]].drop_duplicates()
    n_missing_pop = len(missing_pop)

    if n_missing_pop > 0:
        merged = merged.dropna(subset=["population"]).reset_index(drop=True)

    if "cases" not in merged.columns:
        raise ValueError("Column 'cases' missing after merge")
    merged["cases"] = merged["cases"].fillna(0)

    merged["cases_per_100k"] = (merged["cases"] / merged["population"]) * 100_000.0
    merged["log_cases_per_100k"] = np.log1p(merged["cases_per_100k"])

    merged.to_csv(out_data, index=False)

    with open(out_report, "w", encoding="utf-8") as f:
        f.write("# Report - Targets e Popolazione\n\n")
        f.write(f"**Input clean panel**: {input_path}\n")
        f.write("**Population source**: World Bank API (SP.POP.TOTL via wbgapi)\n\n")
        f.write("## Merge & Copertura\n\n")
        f.write(f"- Righe nel panel originale: {df_orig_rows}\n")
        f.write(f"- Righe dopo merge: {len(merged)}\n")
        f.write(f"- Righe senza popolazione (unique economy-year): {n_missing_pop}\n")
        if n_missing_pop > 0:
            f.write("- Dettaglio:\n")
            for r in missing_pop.head(10).to_dict(orient="records"):
                f.write(f"  - {r['economy']} - {r['year']}\n")
        f.write("\n## Target calcolati\n\n")
        for col in ["cases", "cases_per_100k", "log_cases_per_100k"]:
            s = merged[col]
            f.write(f"- {col}: min={float(s.min()):.4f}, median={float(s.median()):.4f}, "
                    f"mean={float(s.mean()):.4f}, max={float(s.max()):.4f}\n")
        f.write("\n## Note operative\n\n")
        f.write("- `cases_raw` e' preservato dal passo precedente.\n")
        f.write("- `cases` e' stato clippato a 0 nel passo precedente e non interpolato.\n")
        f.write("- Le righe senza popolazione sono state rimosse prima del calcolo dei target.\n")

    print(f"Targets calcolati e salvati in: {out_data}")
    print(f"Report generato in: {out_report}")


def main():
    add_population_and_targets(DEFAULT_INPUT, OUT_DATA, OUT_REPORT)


if __name__ == "__main__":
    main()
