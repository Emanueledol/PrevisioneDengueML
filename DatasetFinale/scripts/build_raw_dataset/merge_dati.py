import xarray as xr
import pandas as pd
import os
from pathlib import Path

# 1. PERCORSI DEI FILE
ROOT = Path(__file__).resolve().parents[3]
folder_geologici = str(ROOT / "DatiGeologici")
folder_socio = str(ROOT / "DatiSocioEconomici")
folder_epidemiologici = str(ROOT / "DatiEpidemiologici")
file_dengue = f"{folder_epidemiologici}/dataset_unito_fixed.xlsx"

# 2. MAPPA REGIONI/PAESI
region_map = {
    'Sud_America_Messico': {
        'countries': ['ARG', 'BOL', 'URY', 'BRA', 'PRY', 'PER', 'MEX', 'HND', 'GTM', 'CRI'],
        'file': f'{folder_geologici}/Copernicus_SudAmerica_Messico.nc'
    },
    'India': {
        'countries': ['IND'],
        'file': f'{folder_geologici}/Copernicus_India.nc'
    },
    'Thailandia': {
        'countries': ['THA'],
        'file': f'{folder_geologici}/Copernicus_Thai.nc'
    }
}

def process_nc_monthly(file_path):
    """Estrae dati climatici mensili e filtra dal 2014 in poi"""
    if not os.path.exists(file_path):
        print(f"File non trovato: {file_path}")
        return None
        
    print(f"Elaborazione clima (2014+): {file_path}")
    ds = xr.open_dataset(file_path)
    
    # Media spaziale
    df_clim = ds.mean(dim=['latitude', 'longitude']).to_dataframe().reset_index()
    
    # Trova colonna tempo
    t_col = next((c for c in ['time', 'valid_time'] if c in df_clim.columns), None)
    if not t_col: return None

    df_clim['year'] = pd.to_datetime(df_clim[t_col]).dt.year
    df_clim['month'] = pd.to_datetime(df_clim[t_col]).dt.month
    
    # FILTRO TEMPORALE: Solo dal 2014
    df_clim = df_clim[df_clim['year'] >= 2014].copy()
    
    # Conversione Celsius
    if 't2m' in df_clim.columns and df_clim['t2m'].mean() > 200:
        df_clim['t2m'] = df_clim['t2m'] - 273.15
    
    # Media per Anno/Mese
    df_clim = df_clim.groupby(['year', 'month']).mean(numeric_only=True).reset_index()
    
    cols_geo = ['year', 'month', 't2m', 'tp', 'sp', 'lai_hv', 'lai_lv']
    return df_clim[[c for c in cols_geo if c in df_clim.columns]]

# 3. CARICAMENTO DATI DENGUE (Excel) - Filtro 2014+
print(f"Caricamento dati Dengue (2014+)...")
try:
    df_d = pd.read_excel(file_dengue)
    df_d['date'] = pd.to_datetime(df_d['date'])
    df_d['year'] = df_d['date'].dt.year
    df_d['month'] = df_d['date'].dt.month
    
    # Filtro 2014+
    df_d = df_d[df_d['year'] >= 2014].copy()
    df_d = df_d[['iso3', 'year', 'month', 'cases']].rename(columns={'iso3': 'economy'})
except Exception as e:
    print(f"Errore file Dengue: {e}")
    df_d = pd.DataFrame()

# 4. ELABORAZIONE CLIMA
all_clim = []
for region, info in region_map.items():
    df_c = process_nc_monthly(info['file'])
    if df_c is not None:
        for country in info['countries']:
            temp_df = df_c.copy()
            temp_df['economy'] = country
            all_clim.append(temp_df)
df_climate_monthly = pd.concat(all_clim, ignore_index=True)

# 5. CARICAMENTO SOCIO-ECONOMICO - Filtro 2014+
file_s_path = f'{folder_socio}/Dati_socioeconomici_media_regionale.csv'
print(f"Caricamento dati Socio-Economici (2014+)...")
df_s = pd.read_csv(file_s_path)
df_s_long = df_s.melt(id_vars=['economy', 'series'], var_name='year', value_name='value')
df_s_long['year'] = pd.to_numeric(df_s_long['year'], errors='coerce')
df_s_long = df_s_long.dropna(subset=['year']).copy()
df_s_long['year'] = df_s_long['year'].astype(int)

# Filtro 2014+
df_s_long = df_s_long[df_s_long['year'] >= 2014].copy()

# 6. MERGE FINALE
# Uniamo Clima e Dengue
df_merge = pd.merge(df_climate_monthly, df_d, on=['economy', 'year', 'month'], how='left')

# Uniamo il Socio-Economico
df_final = pd.merge(df_merge, df_s_long, on=['economy', 'year'], how='left')

# 7. PULIZIA E SALVATAGGIO
if 'tp' in df_final.columns:
    df_final['tp_mm'] = df_final['tp'] * 1000

# Rimuoviamo colonne completamente vuote per pulizia
df_final = df_final.dropna(axis=1, how='all')
df_final = df_final[df_final['year'] < 2024]


out_csv = Path(__file__).resolve().parents[2] / "dataset_raw.csv"
df_final.to_csv(out_csv, index=False)

print("\n------------------------------------------------")
print("SUCCESSO: Dataset Mensile (2014-2024) Creato!")
print(f"File salvato: {out_csv}")
print(f"Totale righe: {len(df_final)}")
print("------------------------------------------------")