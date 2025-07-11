import streamlit as st
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, inspect, text
import ollama

st.set_page_config(page_title="Natural Language SQL App", layout="wide")

# --- 1. Koneksi Database ---
st.sidebar.title("🛠 Database Connection")
host = st.sidebar.text_input("Host", "localhost")
port = st.sidebar.text_input("Port", "5432")
user = st.sidebar.text_input("Username", "postgres")
password = st.sidebar.text_input("Password", type="password")
dbname = st.sidebar.text_input("Database Name", "your_db_name")

conn_status = st.sidebar.empty()

@st.cache_resource(show_spinner=False)
def connect_db():
    try:
        engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{dbname}")
        return engine
    except Exception as e:
        return None

engine = None
if st.sidebar.button("Connect"):
    engine = connect_db()
    if engine:
        conn_status.success("✅ Connected to DB")
    else:
        conn_status.error("❌ Connection Failed")

# --- 2. Menampilkan Tabel ---
st.header("📄 Tabel dalam Database")
if engine:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    st.write("Tabel yang tersedia:", tables)
else:
    st.warning("Silakan koneksi ke database terlebih dahulu.")

# --- 3. Query Builder ---
st.header("🔧 Query Builder")
if engine and tables:
    col1, col2, col3 = st.columns(3)
    with col1:
        table1 = st.selectbox("Tabel 1", tables)
    with col2:
        table2 = st.selectbox("Tabel 2", tables)
    with col3:
        join_type = st.selectbox("Jenis JOIN", ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"])

    cols1 = inspector.get_columns(table1)
    cols2 = inspector.get_columns(table2)
    colnames1 = [col["name"] for col in cols1]
    colnames2 = [col["name"] for col in cols2]

    selected_cols1 = st.multiselect("Kolom dari Tabel 1", colnames1)
    selected_cols2 = st.multiselect("Kolom dari Tabel 2", colnames2)

    join_col1 = st.selectbox("Kolom JOIN dari Tabel 1", colnames1)
    join_col2 = st.selectbox("Kolom JOIN dari Tabel 2", colnames2)

    if st.button("Generate SQL"):
        selected_all = selected_cols1 + selected_cols2
        sql = f"SELECT {', '.join([f'{table1}.{col}' for col in selected_cols1] + [f'{table2}.{col}' for col in selected_cols2])} " \
              f"FROM {table1} {join_type} {table2} ON {table1}.{join_col1} = {table2}.{join_col2}"
        st.code(sql, language="sql")
        try:
            df = pd.read_sql(sql, engine)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Gagal eksekusi: {e}")

# --- 4. Dialog Interaktif ---
st.header("💬 Natural Language to SQL (Dialog Mode)")
nl_input = st.text_input("Masukkan pertanyaan atau permintaan dalam Bahasa Natural")

def generate_sql(nl_query):
    prompt = f"""
You are a SQL expert. Translate the following natural language query into a valid PostgreSQL query.

Database schema:
{', '.join(tables)}

User question:
{nl_query}

Only return the SQL query.
"""
    response = ollama.chat(model="codellama:7b", messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

if st.button("Tanya"):
    if engine and nl_input:
        with st.spinner("Men-generate query..."):
            sql = generate_sql(nl_input)
            st.code(sql, language="sql")
            try:
                df = pd.read_sql(sql, engine)
                # Otomatis tampilkan bentuk grafik jika ada kolom numerik
                st.dataframe(df)
                num_cols = df.select_dtypes(include="number").columns
                if len(num_cols) >= 1:
                    st.subheader("📊 Grafik Otomatis")
                    st.bar_chart(df[num_cols])
            except Exception as e:
                st.error(f"Gagal eksekusi: {e}")
    else:
        st.warning("Masukkan pertanyaan dan pastikan sudah terkoneksi ke DB.")
