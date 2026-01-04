import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# --- 1. KONFIGURASI HALAMAN (Wajib Paling Atas) ---
st.set_page_config(
    page_title="Sales Executive Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS UNTUK TAMPILAN PREMIUM (Clean & Professional) ---
st.markdown("""
<style>
    /* Background Bersih */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Style Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Kartu KPI Minimalis */
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #0d47a1; /* Navy Blue Professional */
        margin: 0;
    }
    .kpi-label {
        font-size: 14px;
        color: #616161;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 5px;
    }
    
    /* Judul Halaman */
    h1 {
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
        color: #1a237e;
        font-size: 2.2rem;
    }
    
    /* Menghilangkan elemen bawaan Streamlit yang mengganggu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    # -----------------------------------------------------------
    # GANTI LINK DI BAWAH INI DENGAN LINK CSV GOOGLE SHEET ANDA
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    # -----------------------------------------------------------
    
    try:
        df = pd.read_csv(url)
    except Exception:
        return pd.DataFrame() # Return kosong jika error

    # DATA CLEANING (PEMBERSIHAN)
    # 1. Bersihkan kolom Jumlah (Omset)
    if 'Jumlah' in df.columns:
        # Hapus titik pemisah ribuan, ubah ke angka
        df['Jumlah'] = df['Jumlah'].astype(str).str.replace('.', '', regex=False)
        # Hapus koma desimal jika ada (ambil angka depan koma)
        df['Jumlah'] = df['Jumlah'].str.split(',').str[0]
        # Convert ke Numeric
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    # 2. Format Tanggal
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')

    # 3. Pastikan kolom lain bertipe String agar tidak error saat filter
    for col in ['Kota', 'Nama Outlet', 'Nama Barang', 'Merk', 'Penjualan']:
        if col in df.columns:
            df[col] = df[col].astype(str)

    return df

# --- 4. FUNGSI LOAD USER ---
def load_users():
    try:
        return pd.read_csv('users.csv')
    except:
        return pd.DataFrame()

# --- 5. HALAMAN LOGIN (SIMPLE & ELEGANT) ---
def login_page():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><h2 style='text-align: center; color: #0d47a1;'>Corporate Access</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: grey;'>Silakan login untuk mengakses data kinerja.</p>", unsafe_allow_html=True)
        
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                users = load_users()
                if not users.empty:
                    match = users[(users['username'] == username) & (users['password'] == password)]
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['role'] = match.iloc[0]['role']
                        st.session_state['sales_name'] = match.iloc[0]['sales_name']
                        st.rerun()
                    else:
                        st.error("Kredensial tidak valid.")
                else:
                    st.error("Database user tidak ditemukan.")

# --- 6. DASHBOARD UTAMA (INTI PROGRAM) ---
def main_dashboard():
    df = load_data()
    if df.empty:
        st.error("Gagal terhubung ke Database. Periksa Link Google Sheet Anda.")
        return

    # --- SIDEBAR: FILTER CONTROL ---
    with st.sidebar:
        st.write(f"User: **{st.session_state['sales_name']}**")
        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.rerun()
        
        st.markdown("---")
        st.subheader("🔍 Filter Data")
        
        # 1. LOGIKA HAK AKSES
        if st.session_state['role'] == 'manager':
            # Manager bisa pilih sales, Sales cuma bisa lihat dirinya sendiri
            sales_list = ["SEMUA"] + sorted(list(df['Penjualan'].unique()))
            selected_sales = st.selectbox("Pilih Sales Team:", sales_list)
            if selected_sales == "SEMUA":
                df_filtered = df
            else:
                df_filtered = df[df['Penjualan'] == selected_sales]
        else:
            # Filter otomatis untuk Sales
            df_filtered = df[df['Penjualan'] == st.session_state['sales_name']]

        # 2. FILTER TANGGAL (Opsional A)
        min_date = df_filtered['Tanggal'].min().date() if pd.notnull(df_filtered['Tanggal'].min()) else datetime.date.today()
        max_date = df_filtered['Tanggal'].max().date() if pd.notnull(df_filtered['Tanggal'].max()) else datetime.date.today()
        
        date_range = st.date_input("Periode Tanggal:", [min_date, max_date])
        
        # Terapkan Filter Tanggal
        if len(date_range) == 2:
            df_filtered = df_filtered[
                (df_filtered['Tanggal'].dt.date >= date_range[0]) & 
                (df_filtered['Tanggal'].dt.date <= date_range[1])
            ]

        # 3. FILTER KOTA (Opsional B)
        # Multiselect agar bisa pilih lebih dari 1 kota
        kota_options = sorted(df_filtered['Kota'].unique())
        selected_kota = st.multiselect("Pilih Kota:", kota_options)
        if selected_kota:
            df_filtered = df_filtered[df_filtered['Kota'].isin(selected_kota)]

        # 4. FILTER NAMA OUTLET (Opsional C)
        # List outlet menyesuaikan Kota yang dipilih di atas (Cascading)
        outlet_options = sorted(df_filtered['Nama Outlet'].unique())
        selected_outlet = st.multiselect("Pilih Outlet / Toko:", outlet_options)
        if selected_outlet:
            df_filtered = df_filtered[df_filtered['Nama Outlet'].isin(selected_outlet)]

        # 5. FILTER BARANG (Opsional D) - Pindah ke paling bawah karena listnya panjang
        barang_options = sorted(df_filtered['Nama Barang'].unique())
        selected_barang = st.multiselect("Filter Produk Tertentu:", barang_options)
        if selected_barang:
            df_filtered = df_filtered[df_filtered['Nama Barang'].isin(selected_barang)]


    # --- MAIN CONTENT ---
    st.title("Performance Overview")
    st.markdown("---")

    if df_filtered.empty:
        st.info("Tidak ada data yang cocok dengan filter yang Anda pilih.")
    else:
        # --- BAGIAN 1: KPI CARDS (Exclusive Style) ---
        # Menghitung KPI
        total_omset = df_filtered['Jumlah'].sum()
        total_toko = df_filtered['Nama Outlet'].nunique() # Menghitung toko unik (tidak double)
        
        c1, c2, c3 = st.columns([1, 1, 2]) # Kolom 3 kosong untuk spasi
        
        with c1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Omset (Rp)</div>
                <div class="kpi-value">{total_omset:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Jumlah Toko Aktif</div>
                <div class="kpi-value">{total_toko}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BAGIAN 2: CHART (Trend & Komposisi) ---
        col_chart1, col_chart2 = st.columns([2, 1])
        
        with col_chart1:
            st.subheader("Tren Penjualan (Harian)")
            daily_trend = df_filtered.groupby('Tanggal')['Jumlah'].sum().reset_index()
            # Grafik Line Area warna Navy
            fig_trend = px.area(daily_trend, x='Tanggal', y='Jumlah', template='plotly_white')
            fig_trend.update_traces(line_color='#1a237e', fill_color='rgba(26, 35, 126, 0.1)')
            fig_trend.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), yaxis_title=None, xaxis_title=None)
            st.plotly_chart(fig_trend, use_container_width=True)
            
        with col_chart2:
            st.subheader("Kontribusi Merk")
            if 'Merk' in df_filtered.columns:
                merk_trend = df_filtered.groupby('Merk')['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=True)
                # Bar Chart Horizontal
                fig_merk = px.bar(merk_trend, x='Jumlah', y='Merk', orientation='h', template='plotly_white')
                fig_merk.update_traces(marker_color='#0277bd')
                fig_merk.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), yaxis_title=None, xaxis_title=None)
                st.plotly_chart(fig_merk, use_container_width=True)

        # --- BAGIAN 3: TABEL RINCIAN (Sesuai Request) ---
        st.subheader("Rincian Transaksi")
        
        # Memilih hanya kolom yang diminta
        cols_to_show = ['Tanggal', 'Nama Outlet', 'Merk', 'Jumlah']
        
        # Cek apakah kolom ada di data, untuk menghindari error jika nama kolom di Excel berubah
        final_cols = [c for c in cols_to_show if c in df_filtered.columns]
        
        # Tampilkan tabel tanpa index (no urut 0,1,2..)
        st.dataframe(
            df_filtered[final_cols].sort_values('Tanggal', ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Jumlah": st.column_config.NumberColumn(
                    "Omset (Rp)",
                    format="Rp %d", # Format Rupiah
                ),
                "Tanggal": st.column_config.DateColumn(
                    "Tanggal",
                    format="DD/MM/YYYY" # Format Tanggal Indonesia
                )
            }
        )

# --- EXECUTION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()
