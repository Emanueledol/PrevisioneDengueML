import pandas as pd
import glob
import os
from pathlib import Path

EPID_DIR = Path(__file__).resolve().parents[3] / "DatiEpidemiologici"

pattern = str(EPID_DIR / "dengue-global-data-*.xlsx")
tutti_i_file = glob.glob(pattern)

lista_df = []

for file in tutti_i_file:
    print(f"Sto elaborando: {file}")
    df = pd.read_excel(file)
    df['provenienza_file'] = os.path.basename(file)
    lista_df.append(df)

dataset_finale = pd.concat(lista_df, ignore_index=True)

out_path = EPID_DIR / "dataset_dengue_unito.xlsx"
dataset_finale.to_excel(out_path, index=False)
print(f"Fatto! Tutti i paesi sono ora nello stesso file: {out_path}")
