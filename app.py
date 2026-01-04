import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sales Dashboard", layout="wide")

# --- 1. FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    # ---------------------------------------------------------
    # GANTI LINK DI BAWAH INI DENGAN LINK CSV GOOGLE SHEET ANDA
    url = "PASTE_LINK_GOOGLE_SHEET_DISINI"
    # ---------------------------------------------------------
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        return None

    # CLEANING DATA (Pembersihan Angka)
    # Kita buang tanda titik (.) agar bisa dihitung
    if 'Jumlah' in df.columns:
        df['Jumlah'] = df['Jumlah'].astype(str).str.replace('.', '', regex=False)
        # Hapus jika ada koma desimal, ambil angka utamanya saja
        df['Jumlah'] = df['Jumlah'].str.split(',').str[0]
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    # Format Tanggal
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')

    return df

# --- 2. FUNGSI LOAD USER ---
def load_users():
    try:
        return pd.read_csv('users.csv')
    except:
        return pd.DataFrame()

# --- 3. HALAMAN LOGIN ---
def login_page():
    st.markdown("<h1 style='text-align: center;'>🔒 Login Sales Dashboard</h1>", unsafe_allow_html=True)
    
    users = load_users()
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Masuk", use_container_width=True)
            
            if submitted:
                if users.empty:
                    st.error("File users.csv tidak ditemukan!")
                else:
                    match = users[(users['username'] == username) & (users['password'] == password)]
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['role'] = match.iloc[0]['role']
                        st.session_state['sales_name'] = match.iloc[0]['sales_name']
                        st.rerun()
                    else:
                        st.error("Username atau Password salah!")

# --- 4. DASHBOARD UTAMA ---
def main_dashboard():
    # Sidebar Logout
    with st.sidebar:
        st.write(f"Halo, **{st.session_state['sales_name']}**")
        if st.button("Logout", type="primary"):
            st.session_state['logged_in'] = False
            st.rerun()

    df = load_data()
    
    if df is None:
        st.error("⚠️ Gagal memuat data! Pastikan Link Google Sheet sudah benar dan dipublish ke CSV.")
        return

    # LOGIKA FILTER
    role = st.session_state['role']
    my_name = st.session_state['sales_name']

    if role == 'manager':
        sales_list = ["SEMUA"] + sorted(list(df['Penjualan'].dropna().unique()))
        selected_sales = st.selectbox("Pantau Kinerja Sales:", sales_list)
        
        if selected_sales == "SEMUA":
            df_view = df
        else:
            df_view = df[df['Penjualan'] == selected_sales]
    else:
        # Sales dipaksa hanya lihat datanya sendiri
        df_view = df[df['Penjualan'] == my_name]

    # TAMPILAN DASHBOARD
    st.title("🚀 Dashboard Performa Sales")
    
    if df_view.empty:
        st.warning("Belum ada data penjualan.")
    else:
        total_omset = df_view['Jumlah'].sum()
        total_trx = len(df_view)

        # Kartu Skor (Scorecard)
        c1, c2 = st.columns(2)
        c1.metric("Total Omset", f"Rp {total_omset:,.0f}".replace(",", "."))
        c2.metric("Total Faktur", f"{total_trx}")

        st.divider()

        # Grafik Tren Harian
        st.subheader("📈 Tren Penjualan Harian")
        if 'Tanggal' in df_view.columns:
            daily = df_view.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig = px.bar(daily, x='Tanggal', y='Jumlah')
            st.plotly_chart(fig, use_container_width=True)

        # Tabel Top Produk
        st.subheader("🏆 Top 5 Produk Terlaris")
        if 'Nama Barang' in df_view.columns:
            top_prod = df_view.groupby('Nama Barang')['Jumlah'].sum().reset_index()
            top_prod = top_prod.sort_values('Jumlah', ascending=False).head(5)
            st.dataframe(top_prod.style.format({"Jumlah": "Rp {:,.0f}"}), use_container_width=True, hide_index=True)

# --- 5. ALUR UTAMA ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    main_dashboard()
