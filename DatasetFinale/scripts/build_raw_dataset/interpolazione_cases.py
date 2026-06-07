import pandas as pd
from pathlib import Path

EPID_DIR = Path(__file__).resolve().parents[3] / "DatiEpidemiologici"

file_path = EPID_DIR / "dataset_dengue_unito.xlsx"
df = pd.read_excel(file_path)

df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by=['country', 'date'])

df['cases'] = df['cases'].interpolate(method='linear')

out_path = EPID_DIR / "dataset_unito_fixed.xlsx"
df.to_excel(out_path, index=False)

print(f"Interpolazione completata. File salvato: {out_path}")
