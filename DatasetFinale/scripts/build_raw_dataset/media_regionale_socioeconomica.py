import pandas as pd
import numpy as np

# 1. Caricamento dati
df = pd.read_csv('dati_socio_economici_tesi.csv')

# 2. Definizione dei Cluster (Target: mancanti, Donatori: per la media)
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

# 3. Funzione di Imputazione
def impute_regional_media(df, series_name, clusters):
    df_imputed = df.copy()
    years = [col for col in df.columns if col.isnumeric()]
    
    for cluster_name, countries in clusters.items():
        targets = countries['target']
        donors = countries['donatori']
        
        for year in years:
            # Calcolo media dei donatori per l'anno specifico
            donor_values = df[(df['series'] == series_name) & (df['economy'].isin(donors))][year]
            donor_values = pd.to_numeric(donor_values, errors='coerce').dropna()
            
            if not donor_values.empty:
                mean_value = donor_values.mean()
                
                # Applichiamo la media ai target se il dato originale è NaN o 0
                mask = (df_imputed['series'] == series_name) & (df_imputed['economy'].isin(targets))
                for idx in df_imputed[mask].index:
                    current_val = pd.to_numeric(df_imputed.at[idx, year], errors='coerce')
                    if pd.isna(current_val) or current_val == 0:
                        df_imputed.at[idx, year] = mean_value
                        
    return df_imputed

# 4. Esecuzione e Salvataggio
df_final = impute_regional_media(df, 'Safe_water_access_pct', clusters)
df_final.to_csv('Dati_socioSanitari_media_regionale.csv', index=False)