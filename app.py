import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import ollama

# Sidebar Koneksi DB
st.sidebar.title("🛠 Database Connection")
host = st.sidebar.text_input("Host", "localhost")
port = st.sidebar.text_input("Port", "5432")
user = st.sidebar.text_input("Username", "postgres")
password = st.sidebar.text_input("Password", type="password")
dbname = st.sidebar.text_input("Database Name", "your_db_name")

@st.cache_resource(show_spinner=False)
def connect_db():
    try:
        engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{dbname}")
        return engine
    except:
        return None

engine = None
if st.sidebar.button("Connect"):
    engine = connect_db()
    if engine:
        st.sidebar.success("✅ Connected")
    else:
        st.sidebar.error("❌ Failed to connect")

if not engine:
    st.warning("Silakan koneksi ke database terlebih dahulu.")
    st.stop()

inspector = inspect(engine)
tables = inspector.get_table_names()

# Tabs
tab1, tab2, tab3 = st.tabs(["📄 Tabel", "🔧 Query Builder", "💬 Dialog"])

# ==============================
# 📄 Tab 1: TABEL
# ==============================
with tab1:
    st.subheader("Daftar Tabel dalam Database")
    if tables:
        selected_table = st.selectbox("Pilih Tabel untuk Preview", tables)
        if selected_table:
            try:
                df_preview = pd.read_sql(f"SELECT * FROM {selected_table} LIMIT 50", engine)
                st.dataframe(df_preview)
            except Exception as e:
                st.error(f"Error preview: {e}")
    else:
        st.warning("Tidak ada tabel ditemukan.")

# ==============================
# 🔧 Tab 2: QUERY BUILDER
# ==============================
with tab2:
    st.subheader("🔧 Builder Query JOIN dan Manual")

    if tables:
        col1, col2, col3 = st.columns(3)
        with col1:
            table1 = st.selectbox("Tabel 1", tables, key="t1")
        with col2:
            table2 = st.selectbox("Tabel 2", tables, key="t2")
        with col3:
            join_type = st.selectbox("Jenis JOIN", ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"])

        cols1 = [c["name"] for c in inspector.get_columns(table1)]
        cols2 = [c["name"] for c in inspector.get_columns(table2)]

        selected_cols1 = st.multiselect("Kolom dari Tabel 1", cols1)
        selected_cols2 = st.multiselect("Kolom dari Tabel 2", cols2)
        join_col1 = st.selectbox("Kolom JOIN dari Tabel 1", cols1)
        join_col2 = st.selectbox("Kolom JOIN dari Tabel 2", cols2)

        if st.button("🔄 Buat Query Join"):
            sql = f"""
SELECT {', '.join([f'{table1}.{col}' for col in selected_cols1] + [f'{table2}.{col}' for col in selected_cols2])}
FROM {table1}
{join_type} {table2}
ON {table1}.{join_col1} = {table2}.{join_col2}
            """.strip()
            st.code(sql, language="sql")
            st.session_state["generated_sql"] = sql

    st.subheader("📝 Query SQL Manual / Edit")
    sql_editor = st.text_area("Masukkan atau edit SQL Query", value=st.session_state.get("generated_sql", ""), height=150)
    
    if st.button("▶️ Jalankan Query"):
        try:
            df_result = pd.read_sql(sql_editor, engine)
            st.success("✅ Query berhasil dijalankan.")
            st.dataframe(df_result)
        except Exception as e:
            st.error(f"❌ Gagal: {e}")

# ==============================
# 💬 Tab 3: DIALOG (Natural Language to SQL)
# ==============================
with tab3:
    st.subheader("💬 Dialog Bahasa Natural ke SQL")

    nl_input = st.text_area("Masukkan permintaan atau pertanyaan (natural language)", height=100)

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

    if st.button("💡 Buat & Jalankan SQL dari Prompt"):
        if nl_input:
            try:
                sql = generate_sql(nl_input)
                st.code(sql, language="sql")
                df = pd.read_sql(sql, engine)
                st.dataframe(df)

                # Visualisasi otomatis (jika ada kolom numerik)
                num_cols = df.select_dtypes(include='number').columns
                if len(num_cols) >= 1:
                    st.subheader("📊 Visualisasi Otomatis")
                    st.bar_chart(df[num_cols])
            except Exception as e:
                st.error(f"Gagal: {e}")
        else:
            st.warning("Masukkan prompt terlebih dahulu.")
