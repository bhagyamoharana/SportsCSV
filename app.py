
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

st.set_page_config(
    page_title="Sports Activity Processor",
    page_icon="📊",
    layout="wide"
)

st.title("📦 Sports Study ZIP Processor")
st.markdown("""
Upload your full study folder (T folders → ControlGroup / ExperimentalGroup → CSV files).
Set classification thresholds and download processed results instantly.
""")

st.info("🔒 Files are processed temporarily and are NOT stored on the server.")
st.markdown("---")

# Folder Structure Guide
with st.expander("📂 Click to view required folder structure"):
    st.markdown("""
    
⚠️ Important:
- Folder names must start with **T** (e.g., T1, T2)
- Each T folder must contain:
  - `ControlGroup`
  - `ExperimentalGroup`
- Only CSV files should be inside those subfolders
""")

st.markdown("---")

# Sidebar Threshold Settings
st.sidebar.header("⚙ Activity Threshold Settings")

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

st.sidebar.markdown("### 📊 Classification Preview")
st.sidebar.success(f"LPA: < {lipa_max}")
st.sidebar.info(f"MIVA: {lipa_max} – {mpa_max}")
st.sidebar.error(f"HPA: > {mpa_max}")

# ZIP Upload
st.subheader("📁 Upload Study ZIP File")
uploaded_zip = st.file_uploader("Drag and drop your ZIP file here", type=["zip"])

if uploaded_zip:
    st.success("ZIP uploaded successfully!")

    if st.button("🚀 Process Entire Study", use_container_width=True):
        with st.spinner("Processing files... Please wait ⏳"):
            with tempfile.TemporaryDirectory() as temp_dir:

                # Save uploaded ZIP temporarily
                zip_path = os.path.join(temp_dir, "study.zip")
                with open(zip_path, "wb") as f:
                    f.write(uploaded_zip.read())

                # Extract ZIP
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Build output ZIP in memory
                output_buffer = io.BytesIO()
                with zipfile.ZipFile(output_buffer, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:

                    processed_files = 0
                    errors = []

                    # Walk extracted folders, process every CSV
                    for root, _, files in os.walk(temp_dir):
                        for file in files:
                            if file.lower().endswith(".csv"):
                                input_file = os.path.join(root, file)

                                try:
                                    result_df = grouped_behavior_with_totals(
                                        input_file=input_file,
                                        lipa_max=lipa_max,
                                        mpa_max=mpa_max
                                    )

                                    # Save Excel to bytes
                                    excel_buffer = io.BytesIO()
                                    result_df.to_excel(excel_buffer, index=False)
                                    excel_buffer.seek(0)

                                    # Keep folder structure in output ZIP
                                    rel_dir = os.path.relpath(root, temp_dir)
                                    excel_name = os.path.splitext(file)[0] + "_processed.xlsx"
                                    zip_member_path = os.path.join(rel_dir, excel_name).replace("\\", "/")

                                    out_zip.writestr(zip_member_path, excel_buffer.read())
                                    processed_files += 1

                                except Exception as e:
                                    errors.append((file, str(e)))

                st.success(f"🎉 Processing complete! {processed_files} CSV files processed.")

                if errors:
                    st.warning(f"⚠️ {len(errors)} file(s) failed. Showing first 10:")
                    for fn, msg in errors[:10]:
                        st.write(f"- {fn}: {msg}")

                output_buffer.seek(0)
                st.download_button(
                    label="⬇ Download Processed ZIP",
                    data=output_buffer.getvalue(),
                    file_name="processed_study.zip",
                    mime="application/zip",
                    use_container_width=True
                )

st.markdown("---")
st.caption("Built with Streamlit | Sports Activity Classification Tool")

