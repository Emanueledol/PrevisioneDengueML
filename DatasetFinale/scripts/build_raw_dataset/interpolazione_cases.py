import pandas as pd
import numpy as np

file_path = "dataset_dengue_unito.xlsx"
df = pd.read_excel(file_path)

# 1. Ordina i dati per paese e data
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by=['country', 'date'])

# 2. Applica l'interpolazione solo alla colonna dei casi
# Il metodo 'linear' creerà una crescita/decrescita fluida tra l'ultimo dato utile e il prossimo
df['cases'] = df['cases'].interpolate(method='linear')

# 3. Salva il file "riparato"
df.to_excel("dataset_unito_fixed.xlsx", index=False)

print("Riparazione completata! I buchi dell'Argentina sono stati riempiti.")