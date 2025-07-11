import os
import pandas as pd
import streamlit as st
from pandasai import SmartDataframe
from pandasai.llm.local_llm import LocalLLM
from pandasai.prompts.base import BasePrompt
import matplotlib.pyplot as plt
import seaborn as sns

# ========== Konfigurasi Awal ==========
st.set_page_config(layout="wide")
DATA_FOLDER = "agri_db"

# Load semua file CSV dalam folder
@st.cache_data
def load_datasets(folder_path):
    datasets = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            df = pd.read_csv(os.path.join(folder_path, filename), sep=None, engine='python')
            datasets[filename] = df
    return datasets

datasets = load_datasets(DATA_FOLDER)
dataset_names = list(datasets.keys())

# Inisialisasi SmartDataLake
@st.cache_resource
def init_smartdatalake(datasets):
    # Convert dictionary of DataFrames to SmartDataFrames
    smart_datasets = {
        name: SmartDataframe(df, config={"llm": LocalLLM(api_base=None)}) 
        for name, df in datasets.items()
    }
    return smart_datasets

smart_datalake = init_smartdatalake(datasets)

# ========== Layout UI ==========
tab1, tab2 = st.tabs(["📊 Dataset", "🤖 Dialog"])

# ========== Panel Dataset ==========
with tab1:
    st.header("📁 Pilih Dataset")
    selected_dataset_name = st.selectbox("Pilih nama file CSV:", dataset_names)
    st.subheader(f"Preview Dataset: {selected_dataset_name}")
    st.dataframe(datasets[selected_dataset_name].head(20), use_container_width=True)

# ========== Panel Dialog ==========
with tab2:
    st.header("💬 Tanyakan sesuatu ke SmartDataLake")
    prompt = st.text_area("Masukkan pertanyaan atau perintah:", height=100, placeholder="Contoh: Tampilkan rata-rata produksi per provinsi")

    if st.button("Jawab"):
        with st.spinner("Sedang memproses..."):
            try:
                # Gabungkan semua SmartDataframe ke dalam satu context
                combined_sdf = SmartDataframe(
                    datasets=None,
                    config={"llm": LocalLLM(api_base=None)},
                    dfs=smart_datalake  # Menggunakan seluruh dataset sebagai data lake
                )

                # Eksekusi prompt
                result = combined_sdf.chat(prompt)

                # Tampilkan output
                st.markdown("### 🔎 Hasil")
                if isinstance(result, pd.DataFrame):
                    st.dataframe(result, use_container_width=True)
                elif isinstance(result, plt.Figure):
                    st.pyplot(result)
                elif isinstance(result, str):
                    st.write(result)
                else:
                    st.info("Tidak dapat menampilkan hasil.")
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
