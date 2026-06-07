import pandas as pd
from pathlib import Path

SOCIO_DIR = Path(__file__).resolve().parents[3] / "DatiSocioEconomici"

df = pd.read_csv(SOCIO_DIR / 'dati_socio_economici_tesi.csv')

clusters = {
    'Sud_America': {
        'target': ['ARG', 'BOL', 'URY'],
        'donatori': ['BRA', 'PRY', 'PER']
    },
    'Sud_Est_Asiatico': {
        'target': ['THA'],
        'donatori': ['IND']
    }
}


def impute_regional_media(df, series_name, clusters):
    df_imputed = df.copy()
    years = [col for col in df.columns if col.isnumeric()]

    for cluster_name, countries in clusters.items():
        targets = countries['target']
        donors = countries['donatori']

        for year in years:
            donor_values = df[(df['series'] == series_name) & (df['economy'].isin(donors))][year]
            donor_values = pd.to_numeric(donor_values, errors='coerce').dropna()

            if not donor_values.empty:
                mean_value = donor_values.mean()

                mask = (df_imputed['series'] == series_name) & (df_imputed['economy'].isin(targets))
                for idx in df_imputed[mask].index:
                    current_val = pd.to_numeric(df_imputed.at[idx, year], errors='coerce')
                    if pd.isna(current_val) or current_val == 0:
                        df_imputed.at[idx, year] = mean_value

    return df_imputed


df_final = impute_regional_media(df, 'Safe_water_access_pct', clusters)
out_path = SOCIO_DIR / 'Dati_socioeconomici_media_regionale.csv'
df_final.to_csv(out_path, index=False)
print(f"File salvato: {out_path}")
