import wbgapi as wb
import pandas as pd #libreria per gestione dati

# Sud America, Messico, Thailandia + India
my_countries = ['ARG', 'BOL', 'BRA', 'CRI', 'GTM', 'HND', 'MEX', 'PRY', 'PER', 'URY', 'THA', 'IND']

# 2. Definizione degli indicatori
indicators = {
    'EN.POP.DNST': 'Pop_Density',
    'NY.GDP.PCAP.PP.CD': 'GDP_per_capita_PPP',
    'NY.GDP.MKTP.CD': 'GDP_nominal',
    'NE.GDI.FTOT.ZS': 'Gross_capital_formation_pct',
    'AG.LND.FRST.ZS': 'Forest_area_pct',
    'SP.RUR.TOTL.ZS': 'Rural_pop_pct',
    'SP.URB.TOTL.IN.ZS': 'Urban_pop_pct',
    'SH.H2O.SMDW.ZS': 'Safe_water_access_pct'
}

print("Download dei dati socio-economici...")

# 3. Scarico i dati dal 2014 al 2024
df = wb.data.DataFrame(indicators.keys(), my_countries, time=range(2000, 2026), numericTimeKeys=True)

# 4. Pulizia e rinomina
df = df.reset_index()
df['series'] = df['series'].map(indicators)

# 5. Gestione dati mancanti (Gap Filling) 
# Applichiamo una media mobile o riempiamo i valori vuoti con il valore precedente/successivo
df = df.groupby(['economy', 'series']).apply(lambda x: x.interpolate(limit_direction='both')).reset_index(drop=True)

# 6. Salvataggio in CSV
df.to_csv('dati_socio_economici_tesi.csv', index=False)

print("File salvato come: dati_socio_economici_tesi.csv")
print(df.head())