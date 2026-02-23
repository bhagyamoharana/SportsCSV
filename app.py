
import streamlit as st
import pandas as pd
import numpy as np
import os
import zipfile
import io
import tempfile

# ========================================================
# 🔬 PROCESSING FUNCTION (NO HARDCODED DEFAULTS)
# ========================================================

def grouped_behavior_with_totals(input_path, lipa_max, mpa_max):

    df = pd.read_csv(
        input_path,
        sep=';',
        skiprows=1,
        engine='python',
        index_col=False
    )

    df.rename(columns={'Time(approx)': 'Time_formatted'}, inplace=True)

    df['Time_formatted'] = pd.to_datetime(df['Time_formatted'], errors='coerce')
    df['Duration (s)'] = pd.to_numeric(df['Duration (s)'], errors='coerce')
    df['Event Type'] = pd.to_numeric(df['Event Type'], errors='coerce')
    df['Cumulative Step Count'] = (
        pd.to_numeric(df['Cumulative Step Count'], errors='coerce')
        .fillna(0).astype(int)
    )

    df = df.dropna(subset=['Time_formatted', 'Duration (s)', 'Event Type'])
    df = df[df['Duration (s)'] > 0]

    df['Event_Group'] = (df['Event Type'] != df['Event Type'].shift()).cumsum()
    df['Step_Diff'] = df['Cumulative Step Count'].diff().fillna(0).clip(lower=0)

    steps_by_group = df.groupby('Event_Group')['Step_Diff'].sum().astype(int)

    grouped = df.groupby('Event_Group').agg({
        'Time_formatted': 'first',
        'Duration (s)': 'sum',
        'Event Type': 'first',
        'Cumulative Step Count': 'last'
    }).reset_index(drop=True)

    grouped['Steps'] = steps_by_group.values
    grouped['Doubled Steps'] = grouped['Steps'] * 2
    grouped['Minutes'] = (grouped['Duration (s)'] / 60).round(3)

    grouped['Steps per Minute'] = (
        grouped['Doubled Steps'] / grouped['Minutes']
    ).replace([np.inf, -np.inf], 0).fillna(0).round(2)

    grouped['DayPeriod'] = 1
    grouped['Time'] = grouped['Time_formatted'].dt.strftime('%d/%m/%Y %H:%M:%S')
    grouped['Unix Timestamp'] = grouped['Time_formatted'].astype('int64') // 10**9

    # ------------------------------------------------
    # Behaviour (SED/STAND/LIPA/MPA/VPA)
    # ------------------------------------------------
    def behaviour_label(row):
        if row['Event Type'] == 0:
            return 'SED'
        elif row['Event Type'] == 1:
            return 'STAND'
        elif row['Event Type'] == 2:
            spm = row['Steps per Minute']
            if spm < lipa_max:
                return 'LIPA'
            elif lipa_max <= spm <= mpa_max:
                return 'MPA'
            else:
                return 'VPA'
        return 'UNKNOWN'

    grouped['Behaviour'] = grouped.apply(behaviour_label, axis=1)

    # ------------------------------------------------
    # Activity Category (ONLY LPA/MIVA/HPA)
    # ------------------------------------------------
    def activity_category(row):
        if row['Event Type'] != 2:
            return ""
        spm = row['Steps per Minute']
        if spm < lipa_max:
            return "LPA"
        elif lipa_max <= spm <= mpa_max:
            return "MIVA"
        else:
            return "HPA"

    grouped['Activity Category'] = grouped.apply(activity_category, axis=1)

    # Final table
    result_df = grouped[
        ['Time', 'Unix Timestamp', 'Duration (s)',
         'Behaviour', 'Steps', 'Doubled Steps',
         'Minutes', 'Steps per Minute', 'Activity Category']
    ].copy()

    result_df.columns = [
        'Time', 'Unix Timestamp', 'Event Duration (s)',
        'Behaviour', 'Steps', 'Doubled Steps',
        'Minutes', 'Steps per Minute', 'Activity Category'
    ]

    return result_df


# ========================================================
# 🌐 STREAMLIT FRONTEND
# ========================================================

# ========================================================
# 🌐 STREAMLIT FRONTEND (POLISHED VERSION)
# ========================================================

# ========================================================
# 🌐 STREAMLIT UI (ONLY)
# ========================================================

# ========================================================
# 🎨 STREAMLIT UI (DESIGN UPGRADE)
# Assumes grouped_behavior_with_totals(input_file, lipa_max, mpa_max) exists above
# Also assumes you imported: os, zipfile, io, tempfile, streamlit as st
# ========================================================

st.set_page_config(page_title="Sports Activity Processor", page_icon="📊", layout="wide")

# ------------------------------
# Custom CSS
# ------------------------------
st.markdown("""
<style>
/* Page background */
.stApp {
    background: linear-gradient(180deg, rgba(240,246,255,0.9) 0%, rgba(255,255,255,1) 40%);
}

/* Top banner */
.banner {
    padding: 18px 22px;
    border-radius: 16px;
    background: linear-gradient(90deg, #1f77b4 0%, #4fa3ff 55%, #7cc3ff 100%);
    color: white;
    box-shadow: 0 10px 24px rgba(31,119,180,0.25);
    margin-bottom: 18px;
}
.banner h1 {
    margin: 0;
    font-size: 30px;
    font-weight: 800;
    letter-spacing: 0.2px;
}
.banner p {
    margin: 6px 0 0 0;
    opacity: 0.92;
    font-size: 15px;
}

/* Card containers */
.card {
    background: white;
    border: 1px solid rgba(15,23,42,0.08);
    border-radius: 16px;
    padding: 18px 18px 14px 18px;
    box-shadow: 0 8px 18px rgba(15,23,42,0.06);
}

/* Section titles */
.section-title {
    font-size: 18px;
    font-weight: 750;
    margin: 0 0 10px 0;
    color: #0f172a;
}

/* Helper text */
.helper {
    color: rgba(15,23,42,0.75);
    font-size: 13.5px;
    margin-top: 6px;
}

/* Make the main button look more prominent */
div.stButton > button {
    border-radius: 12px;
    padding: 0.65rem 1rem;
    font-weight: 700;
}

/* Download button container spacing */
.download-wrap {
    margin-top: 12px;
}

/* Sidebar "chips" */
.chip {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    margin: 4px 6px 0 0;
}
.chip-green { background: rgba(34,197,94,0.15); color: rgb(22,163,74); }
.chip-blue  { background: rgba(59,130,246,0.14); color: rgb(37,99,235); }
.chip-red   { background: rgba(239,68,68,0.14);  color: rgb(220,38,38); }

/* Info box spacing */
div[data-testid="stAlert"] {
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Banner
# ------------------------------

st.markdown("""
<style>

/* ===== PRIMARY PROCESS BUTTON ===== */
div.stButton > button {
    background: linear-gradient(90deg, #7c3aed, #a855f7);
    color: white;
    border: none;
    border-radius: 14px;
    padding: 0.75em 1.4em;
    font-weight: 700;
    font-size: 16px;
    box-shadow: 0 8px 20px rgba(124,58,237,0.35);
    transition: all 0.25s ease-in-out;
}

/* Hover */
div.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 28px rgba(124,58,237,0.45);
    background: linear-gradient(90deg, #6d28d9, #9333ea);
}

/* Click */
div.stButton > button:active {
    transform: scale(0.97);
}


/* ===== DOWNLOAD BUTTON ===== */
div.stDownloadButton > button {
    background: linear-gradient(90deg, #14b8a6, #10b981);
    color: white;
    border: none;
    border-radius: 14px;
    padding: 0.75em 1.4em;
    font-weight: 700;
    font-size: 16px;
    box-shadow: 0 8px 20px rgba(16,185,129,0.35);
    transition: all 0.25s ease-in-out;
}

/* Hover */
div.stDownloadButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 28px rgba(16,185,129,0.45);
    background: linear-gradient(90deg, #0d9488, #059669);
}

/* Click */
div.stDownloadButton > button:active {
    transform: scale(0.97);
}


/* ===== DISABLED BUTTON ===== */
div.stButton > button:disabled {
    background: #d4d4d8;
    color: #6b7280;
    box-shadow: none;
}

</style>
""", unsafe_allow_html=True)
st.markdown("""
<div class="banner">
  <h1>📦 Sports Study ZIP Processor</h1>
  <p>Upload your study ZIP → set thresholds → process → download results. No data is stored.</p>
</div>
""", unsafe_allow_html=True)

st.info("🔒 Files are processed temporarily and are NOT stored on the server.")

# ------------------------------
# Folder Structure (Collapsible)
# ------------------------------
with st.expander("📂 Click to view required folder structure"):
    st.markdown("""
    
⚠️ Important:
- Folder names must start with **T** (e.g., T1, T2)
- Each T folder must contain:
  - `ControlGroup`
  - `ExperimentalGroup`
- Only `.csv` files should be inside those subfolders
""")

# ------------------------------
# Sidebar controls
# ------------------------------
st.sidebar.header("⚙ Threshold Settings")

lipa_max = st.sidebar.number_input(
    "Upper limit for LPA (steps/min)",
    min_value=0,
    value=100,
    step=1
)
mpa_max = st.sidebar.number_input(
    "Upper limit for MIVA (steps/min)",
    min_value=int(lipa_max) + 1,
    value=130,
    step=1
)

st.sidebar.markdown("### 📌 Classification Preview")
st.sidebar.markdown(
    f'<span class="chip chip-green">LPA: &lt; {lipa_max}</span>'
    f'<span class="chip chip-blue">MIVA: {lipa_max}–{mpa_max}</span>'
    f'<span class="chip chip-red">HPA: &gt; {mpa_max}</span>',
    unsafe_allow_html=True
)

st.sidebar.markdown("---")
st.sidebar.caption("Tip: Use smaller ZIPs for faster processing.")

# ------------------------------
# Main layout: two columns
# ------------------------------
left, right = st.columns([1.25, 1])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📁 Upload Study ZIP</div>', unsafe_allow_html=True)
    uploaded_zip = st.file_uploader("Drag & drop your ZIP here", type=["zip"], label_visibility="visible")
    st.markdown('<div class="helper">Your ZIP should include T* folders with ControlGroup and ExperimentalGroup.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">✅ Run Processing</div>', unsafe_allow_html=True)
    st.write("When ready, click the button below to process all CSVs inside the ZIP.")
    run_clicked = st.button("🚀 Process Entire Study", use_container_width=True, disabled=(uploaded_zip is None))
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------
# Processing + Download
# ------------------------------
if uploaded_zip and run_clicked:
    with st.spinner("Processing files... Please wait ⏳"):
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "study.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.read())

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            output_buffer = io.BytesIO()
            processed_files = 0
            errors = []

            with zipfile.ZipFile(output_buffer, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower().endswith(".csv"):
                            input_file = os.path.join(root, file)
                            try:
                                result_df = grouped_behavior_with_totals(
                                    input_path=input_file,
                                    lipa_max=lipa_max,
                                    mpa_max=mpa_max
                                )

                                excel_buffer = io.BytesIO()
                                result_df.to_excel(excel_buffer, index=False)
                                excel_buffer.seek(0)

                                rel_dir = os.path.relpath(root, temp_dir)
                                excel_name = os.path.splitext(file)[0] + "_processed.xlsx"
                                zip_member_path = os.path.join(rel_dir, excel_name).replace("\\", "/")

                                out_zip.writestr(zip_member_path, excel_buffer.read())
                                processed_files += 1
                            except Exception as e:
                                errors.append((file, str(e)))

            st.success(f"🎉 Done! Processed {processed_files} CSV file(s).")

            if errors:
                st.warning(f"⚠️ {len(errors)} file(s) failed. Showing first 10:")
                for fn, msg in errors[:10]:
                    st.write(f"- {fn}: {msg}")

            output_buffer.seek(0)

            st.markdown('<div class="download-wrap">', unsafe_allow_html=True)
            st.download_button(
                label="⬇ Download Processed ZIP",
                data=output_buffer.getvalue(),
                file_name="processed_study.zip",
                mime="application/zip",
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("Built with Streamlit | Sports Activity Classification Tool")



