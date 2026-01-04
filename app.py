import streamlit as st
import pandas as pd
import plotly.express as px
import datetime # Tambahan untuk filter tanggal

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sales Dashboard", layout="wide")

# --- 1. FUNGSI LOAD DATA ---
# ttl=3600 artinya data akan kadaluarsa/refresh otomatis tiap 3600 detik (1 jam)
@st.cache_data(ttl=3600) 
def load_data():
    # ---------------------------------------------------------
    # LINK CSV GOOGLE SHEET ANDA
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    # ---------------------------------------------------------
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        return None

    # CLEANING DATA
    if 'Jumlah' in df.columns:
        df['Jumlah'] = df['Jumlah'].astype(str).str.replace('.', '', regex=False)
        df['Jumlah'] = df['Jumlah'].str.split(',').str[0]
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    # Format Tanggal
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')

    # Pastikan kolom filter terbaca sebagai text agar tidak error
    for col in ['Kota', 'Nama Outlet', 'Merk', 'Nama Barang']:
        if col in df.columns:
            df[col] = df[col].astype(str)

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

    # --- LOGIKA FILTER UTAMA (ROLE) ---
    role = st.session_state['role']
    my_name = st.session_state['sales_name']

    if role == 'manager':
        sales_list = ["SEMUA"] + sorted(list(df['Penjualan'].dropna().unique()))
        selected_sales = st.sidebar.selectbox("Pantau Kinerja Sales:", sales_list)
        
        if selected_sales == "SEMUA":
            df_view = df
        else:
            df_view = df[df['Penjualan'] == selected_sales]
    else:
        # Sales dipaksa hanya lihat datanya sendiri
        df_view = df[df['Penjualan'] == my_name]

    # --- LOGIKA FILTER TAMBAHAN (A-D) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter Lanjutan")

    # 1. Filter Tanggal (Wajib A)
    min_date = df_view['Tanggal'].min().date() if pd.notnull(df_view['Tanggal'].min()) else datetime.date.today()
    max_date = df_view['Tanggal'].max().date() if pd.notnull(df_view['Tanggal'].max()) else datetime.date.today()
    
    date_range = st.sidebar.date_input("Periode Tanggal", [min_date, max_date])
    
    if len(date_range) == 2:
        df_view = df_view[
            (df_view['Tanggal'].dt.date >= date_range[0]) & 
            (df_view['Tanggal'].dt.date <= date_range[1])
        ]

    # 2. Filter Kota (Wajib B)
    if 'Kota' in df_view.columns:
        list_kota = sorted(df_view['Kota'].unique())
        pilih_kota = st.sidebar.multiselect("Pilih Kota", list_kota)
        if pilih_kota:
            df_view = df_view[df_view['Kota'].isin(pilih_kota)]

    # 3. Filter Nama Outlet (Wajib C)
    if 'Nama Outlet' in df_view.columns:
        list_outlet = sorted(df_view['Nama Outlet'].unique())
        pilih_outlet = st.sidebar.multiselect("Pilih Nama Outlet", list_outlet)
        if pilih_outlet:
            df_view = df_view[df_view['Nama Outlet'].isin(pilih_outlet)]

    # 4. Filter Merk (Wajib D)
    if 'Merk' in df_view.columns:
        list_merk = sorted(df_view['Merk'].unique())
        pilih_merk = st.sidebar.multiselect("Pilih Merk", list_merk)
        if pilih_merk:
            df_view = df_view[df_view['Merk'].isin(pilih_merk)]


    # --- TAMPILAN DASHBOARD ---
    st.title("🚀 Dashboard Performa Sales")
    
    if df_view.empty:
        st.warning("Belum ada data penjualan yang cocok dengan filter.")
    else:
        # Hitung KPI
        total_omset = df_view['Jumlah'].sum()
        # KPI YANG DIMINTA: JUMLAH TOKO (Unik)
        total_toko = df_view['Nama Outlet'].nunique() 

        # Kartu Skor (Scorecard)
        c1, c2 = st.columns(2)
        c1.metric("Total Omset", f"Rp {total_omset:,.0f}".replace(",", "."))
        c2.metric("Jumlah Toko Aktif", f"{total_toko} Outlet") # Diubah sesuai request

        st.divider()

        # Grafik Tren Harian
        st.subheader("📈 Tren Penjualan Harian")
        if 'Tanggal' in df_view.columns:
            daily = df_view.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig = px.bar(daily, x='Tanggal', y='Jumlah')
            st.plotly_chart(fig, use_container_width=True)

        # TABEL RINCIAN (FITUR BARU)
        st.divider()
        st.subheader("📋 Rincian Transaksi")
        
        # Kolom yang diminta: Tanggal, Nama Outlet, Merk, Jumlah
        target_cols = ['Tanggal', 'Nama Outlet', 'Merk', 'Jumlah']
        
        # Validasi kolom ada di data
        final_cols = [c for c in target_cols if c in df_view.columns]
        
        st.dataframe(
            df_view[final_cols].sort_values('Tanggal', ascending=False), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"),
                "Jumlah": st.column_config.NumberColumn("Omset (Rp)", format="Rp %d")
            }
        )

# --- 5. ALUR UTAMA ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    main_dashboard()
