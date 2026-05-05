import streamlit as st
import pandas as pd
import io
import plotly.graph_objects as go

# -------------------------
# 🔥 HIDE STREAMLIT UI (LOGO, MENU, FOOTER)
# -------------------------
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)

# -------------------------
# APP TITLE
# -------------------------
st.title("📊 GPM70 Test Rig Data Analysis Dashboard")

# -------------------------
# SESSION INIT
# -------------------------
if "final_df" not in st.session_state:
    st.session_state["final_df"] = None

# -------------------------
# FILE UPLOAD
# -------------------------
pa_file = st.file_uploader("Upload PA File", type=["xlsx"])
vs_file = st.file_uploader("Upload VS File", type=["xlsx"])
rig_file = st.file_uploader("Upload Rig File", type=["xlsx"])
final_template = st.file_uploader("Upload Final Template", type=["xlsx"])

# -------------------------
# FUNCTIONS
# -------------------------
def normalize(col):
    return str(col).strip().lower().replace(" ", "").replace("_", "")

def find_match(param, original_cols):
    param_norm = normalize(param)
    for col in original_cols:
        if normalize(col) == param_norm:
            return col
    for col in original_cols:
        if param_norm in normalize(col):
            return col
    return None

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
# PROCESS BUTTON
# -------------------------
if st.button("🚀 Process Files"):

    if not all([pa_file, vs_file, rig_file, final_template]):
        st.error("Please upload all files")
        st.stop()

    pa = clean_df(pd.read_excel(pa_file))
    vs = clean_df(pd.read_excel(vs_file))
    rig = clean_df(pd.read_excel(rig_file))

    pa_cols, vs_cols, rig_cols = pa.columns, vs.columns, rig.columns
    final = pd.read_excel(final_template, header=None, dtype=object)

    pa["Time"] = pa["Time"].astype(int)
    vs["Time"] = vs["Time"].astype(int)
    rig["Time"] = rig["Time"].astype(int)

    pa_avg = pa.groupby("Time").mean()
    vs_avg = vs.groupby("Time").mean()
    rig = rig.set_index("Time")

    # MOTOR CURRENT
    motor_cols = [
        find_match("Phase I RY", pa_cols),
        find_match("Phase I YB", pa_cols),
        find_match("Phase I RB", pa_cols)
    ]
    motor_cols = [c for c in motor_cols if c is not None]

    if len(motor_cols) == 3:
        mapped = []
        for mc in motor_cols:
            for c in pa_avg.columns:
                if normalize(c) == normalize(mc):
                    mapped.append(c)
                    break
        pa_avg["Motor Current"] = pa_avg[mapped].mean(axis=1)

    # TEMPLATE PROCESS
    headers = final.iloc[0]
    sources = final.iloc[1]

    for col in range(1, len(headers)):

        param = headers[col]
        source = sources[col]

        if pd.isna(param) or pd.isna(source):
            continue

        param = str(param).strip()
        source = str(source).strip()

        param_clean = param.replace("_PA","").replace("_VS","").replace("_Rig","").strip()

        if source == "PA":
            df, orig_cols = pa_avg, pa_cols
        elif source == "VS":
            df, orig_cols = vs_avg, vs_cols
        elif source == "Rig":
            df, orig_cols = rig, rig_cols
        else:
            continue

        if source == "PA" and param_clean.lower() == "motor current":
            matched_col = "Motor Current"
        else:
            m = find_match(param_clean, orig_cols)
            if m is None:
                continue

            matched_col = None
            for c in df.columns:
                if normalize(c) == normalize(m):
                    matched_col = c
                    break

            if matched_col is None:
                continue

        for row in range(2, len(final)):
            try:
                t = int(float(final.iloc[row, 0]))
                final.iloc[row, col] = df[matched_col].get(t, None)
            except:
                continue

    st.session_state["final_df"] = final.copy()
    st.success("✅ Processing complete")

# -------------------------
# GRAPH
# -------------------------
if st.session_state["final_df"] is not None:

    final = st.session_state["final_df"]

    plot_df = final.iloc[2:].copy()
    plot_df.columns = final.iloc[0].astype(str)
    plot_df = plot_df.loc[:, ~plot_df.columns.duplicated()]

    for col in plot_df.columns:
        plot_df[col] = pd.to_numeric(plot_df[col], errors='coerce')

    plot_df["Time"] = pd.to_numeric(plot_df["Time"], errors='coerce')
    plot_df = plot_df.dropna(subset=["Time"])
    plot_df = plot_df.set_index("Time")

    st.subheader("📊 Interactive Graph")

    all_params = list(plot_df.columns)

    primary = st.multiselect("Primary Axis", all_params)
    secondary = st.multiselect("Secondary Axis", all_params)

    scale = st.number_input("Secondary Axis Scale", value=1.0)

    fig = go.Figure()

    for p in primary:
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df[p], name=p, yaxis="y1"))

    for p in secondary:
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df[p]/scale, name=f"{p} (scaled)", yaxis="y2"))

    fig.update_layout(
        xaxis_title="Time",
        yaxis=dict(title="Primary Axis"),
        yaxis2=dict(title="Secondary Axis", overlaying="y", side="right"),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    # DOWNLOAD
    output = io.BytesIO()
    final.to_excel(output, index=False, header=False)
    output.seek(0)

    st.download_button("📥 Download Final Output", data=output, file_name="Final_Output.xlsx")

# -------------------------
# HOW TO USE
# -------------------------
st.markdown("---")
st.header("📘 How to Use")

st.markdown("""
1. Upload all files  
2. Click Process  
3. Select parameters  
4. Download output  

Motor Current = Avg (RY, YB, RB)
""")
