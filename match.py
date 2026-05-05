import pandas as pd

def normalize(col):
    return str(col).strip().lower().replace(" ", "").replace("_", "")

# Load files
pa = pd.read_excel("PA.xlsx")
vs = pd.read_excel("VS.xlsx")
final = pd.read_excel("Final.xlsx", header=None)

# Extract headers
final_headers = final.iloc[0]
final_sources = final.iloc[1]

pa_cols = [normalize(c) for c in pa.columns]
vs_cols = [normalize(c) for c in vs.columns]

print("\n===== HEADER MATCH CHECK =====\n")

for i in range(1, len(final_headers)):
    param = final_headers[i]
    source = final_sources[i]

    if pd.isna(param) or pd.isna(source):
        continue

    param_clean = str(param).replace("_PA","").replace("_VS","").replace("_Rig","")
    param_norm = normalize(param_clean)

    if source == "PA":
        match = param_norm in pa_cols
    elif source == "VS":
        match = param_norm in vs_cols
    else:
        continue

    print(f"{param_clean} ({source}) → {'✅ MATCH' if match else '❌ NOT MATCH'}")