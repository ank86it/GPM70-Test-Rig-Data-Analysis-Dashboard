import pandas as pd
import os

# -------------------------
# NORMALIZE FUNCTION
# -------------------------
def normalize(col):
    return str(col).strip().lower().replace(" ", "").replace("_", "")

# -------------------------
# FIND MATCH
# -------------------------
def find_match(param, original_cols):
    param_norm = normalize(param)

    for col in original_cols:
        if normalize(col) == param_norm:
            return col

    for col in original_cols:
        if param_norm in normalize(col):
            return col

    return None

# -------------------------
# CLEAN + FORCE NUMERIC
# -------------------------
def clean_df(df):
    df = df.loc[:, df.columns.notna()]
    df.rename(columns={df.columns[0]: "Time"}, inplace=True)

    df["Time"] = pd.to_numeric(df["Time"], errors='coerce')
    df = df.dropna(subset=["Time"])

    df.columns = df.columns.str.strip()

    for col in df.columns:
        if col != "Time":
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

# -------------------------
# LOAD FILES
# -------------------------
pa = clean_df(pd.read_excel("PA.xlsx"))
vs = clean_df(pd.read_excel("VS.xlsx"))
rig = clean_df(pd.read_excel("Rig.xlsx"))

pa_cols = pa.columns
vs_cols = vs.columns
rig_cols = rig.columns

final = pd.read_excel("Final.xlsx", header=None, dtype=object)

# -------------------------
# RESAMPLE
# -------------------------
pa["Time"] = pa["Time"].astype(int)
vs["Time"] = vs["Time"].astype(int)
rig["Time"] = rig["Time"].astype(int)

pa_avg = pa.groupby("Time").mean()
vs_avg = vs.groupby("Time").mean()
rig = rig.set_index("Time")

# -------------------------
# 🔥 MOTOR CURRENT CALCULATION
# -------------------------
motor_cols = [
    find_match("Phase I RY", pa_cols),
    find_match("Phase I YB", pa_cols),
    find_match("Phase I RB", pa_cols)
]

motor_cols = [c for c in motor_cols if c is not None]

if len(motor_cols) == 3:
    mapped_cols = []
    for mc in motor_cols:
        for c in pa_avg.columns:
            if normalize(c) == normalize(mc):
                mapped_cols.append(c)
                break

    pa_avg["Motor Current"] = pa_avg[mapped_cols].mean(axis=1)
    print("✅ Motor Current created successfully")
else:
    print("❌ Could not find all 3 phase current columns in PA file")

# -------------------------
# PROCESS TEMPLATE
# -------------------------
headers = final.iloc[0]
sources = final.iloc[1]

for col in range(1, len(headers)):

    param = headers[col]
    source = sources[col]

    if pd.isna(param) or pd.isna(source):
        continue

    param = str(param).strip()
    source = str(source).strip()

    param_clean = (
        param.replace("_PA", "")
             .replace("_VS", "")
             .replace("_Rig", "")
             .strip()
    )

    if source == "PA":
        df = pa_avg
        orig_cols = pa_cols
    elif source == "VS":
        df = vs_avg
        orig_cols = vs_cols
    elif source == "Rig":
        df = rig
        orig_cols = rig_cols
    else:
        continue

    # -------------------------
    # 🔥 SPECIAL CASE: MOTOR CURRENT
    # -------------------------
    if source == "PA" and param_clean.lower() == "motor current":
        matched_col = "Motor Current"
        print("✅ Using computed Motor Current")

    else:
        matched_original = find_match(param_clean, orig_cols)

        if matched_original is None:
            print(f"❌ No match for: {param_clean} in {source}")
            continue

        print(f"✅ {source}: {param_clean} → {matched_original}")

        matched_norm = normalize(matched_original)

        matched_col = None
        for c in df.columns:
            if normalize(c) == matched_norm:
                matched_col = c
                break

        if matched_col is None:
            print(f"❌ Still missing after grouping: {param_clean}")
            continue

    # -------------------------
    # FILL VALUES
    # -------------------------
    for row in range(2, len(final)):
        time_val = final.iloc[row, 0]

        try:
            t = int(float(time_val))
        except:
            continue

        val = df[matched_col].get(t, None)
        final.iloc[row, col] = val

# -------------------------
# SAVE OUTPUT
# -------------------------
output_file = "Final_Output.xlsx"

if os.path.exists(output_file):
    try:
        os.remove(output_file)
    except:
        print("❌ Close Final_Output.xlsx and rerun")
        exit()

final.to_excel(output_file, index=False, header=False)

print("✅ DONE: FINAL OUTPUT CREATED SUCCESSFULLY")