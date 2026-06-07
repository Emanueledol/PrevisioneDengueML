import pandas as pd
import glob
import os

# 1. Trova tutti i file excel nella cartella che iniziano con una certa parola o sono .xlsx
estensione = "*.xlsx" 
tutti_i_file = glob.glob(estensione)

lista_df = []

for file in tutti_i_file:
    print(f"Sto elaborando: {file}")
    # Legge il file Excel
    df = pd.read_excel(file)
    
    # Aggiunge il nome del file come colonna se vuoi sapere da quale file arriva
    df['provenienza_file'] = os.path.basename(file)
    
    lista_df.append(df)

# 2. Unisce tutto in un unico "muro" di dati
dataset_finale = pd.concat(lista_df, ignore_index=True)

# 3. Salva il risultato
dataset_finale.to_excel("dataset_dengue_unito.xlsx", index=False)
print("Fatto! Tutti i paesi sono ora nello stesso file.")