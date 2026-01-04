import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# --- 1. KONFIGURASI HALAMAN (Wajib Paling Atas) ---
st.set_page_config(
    page_title="Executive Sales Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS CUSTOM (RAHASIA TAMPILAN EXCLUSIVE) ---
# Ini tidak mengubah logika, hanya mempercantik tampilan agar terlihat "Mahal"
st.markdown("""
<style>
    /* Background & Font Utama */
    .stApp {
        background-color: #f4f7f6; /* Abu-abu sangat muda, nyaman di mata */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }

    /* Style untuk Kartu KPI (Kotak Angka) */
    .kpi-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); /* Bayangan halus */
        border-left: 5px solid #1a237e; /* Aksen Biru Navy */
        text-align: center;
        margin-bottom: 15px;
    }
    
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #2c3e50;
        margin-top: 5px;
    }
    
    .kpi-label {
        font-size: 13px;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    /* Header Halaman */
    .header-style {
        font-size: 28px;
        font-weight: 700;
        color: #1a237e;
        margin-bottom: 20px;
    }
    
    /* Menghilangkan elemen bawaan Streamlit yang mengganggu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    # LINK ANDA SUDAH SAYA MASUKKAN DI SINI
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        return pd.DataFrame()

    # CLEANING DATA
    # 1. Bersihkan Kolom Jumlah (Omset)
    if 'Jumlah' in df.columns:
        df['Jumlah'] = df['Jumlah'].astype(str).str.replace('.', '', regex=False)
        df['Jumlah'] = df['Jumlah'].str.split(',').str[0]
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    # 2. Format Tanggal
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')

    # 3. Pastikan kolom Filter bertipe String agar tidak error
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

# --- 5. HALAMAN LOGIN (SIMPLE & BERSIH) ---
def login_page():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Judul Login dengan warna Corporate
        st.markdown("<h2 style='text-align: center; color: #1a237e;'>🔐 Sales Portal</h2>", unsafe_allow_html=True)
        st.info("Masukkan username dan password Anda.")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("LOGIN", use_container_width=True)
            
            if submitted:
                users = load_users()
                if not users.empty:
                    match = users[(users['username'] == username) & (users['password'] == password)]
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['role'] = match.iloc[0]['role']
                        st.session_state['sales_name'] = match.iloc[0]['sales_name']
                        st.rerun()
                    else:
                        st.error("Login Gagal: Username/Password salah.")
                else:
                    st.error("Database User tidak ditemukan.")

# --- 6. DASHBOARD UTAMA (CORE SYSTEM) ---
def main_dashboard():
    df = load_data()
    if df.empty:
        st.error("Gagal memuat data. Periksa koneksi internet atau Link Google Sheet.")
        return

    # --- BAGIAN SIDEBAR (FILTER SYSTEM) ---
    with st.sidebar:
        # Menampilkan Nama User
        st.write(f"Halo, **{st.session_state['sales_name']}**")
        
        if st.button("Log Out", type="secondary", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
            
        st.markdown("---")
        st.subheader("🔍 Filter Pencarian")
        
        # 1. FILTER SALES (Sesuai Role)
        if st.session_state['role'] == 'manager':
            sales_list = ["SEMUA"] + sorted(list(df['Penjualan'].unique()))
            selected_sales = st.selectbox("Tim Sales:", sales_list)
            if selected_sales == "SEMUA":
                df_filtered = df
            else:
                df_filtered = df[df['Penjualan'] == selected_sales]
        else:
            # Sales otomatis terkunci ke namanya sendiri
            df_filtered = df[df['Penjualan'] == st.session_state['sales_name']]

        # 2. FILTER TANGGAL (Wajib A)
        min_d = df_filtered['Tanggal'].min().date() if pd.notnull(df_filtered['Tanggal'].min()) else datetime.date.today()
        max_d = df_filtered['Tanggal'].max().date() if pd.notnull(df_filtered['Tanggal'].max()) else datetime.date.today()
        
        date_range = st.date_input("Periode:", [min_d, max_d])
        if len(date_range) == 2:
            df_filtered = df_filtered[
                (df_filtered['Tanggal'].dt.date >= date_range[0]) & 
                (df_filtered['Tanggal'].dt.date <= date_range[1])
            ]

        # 3. FILTER KOTA (Wajib B)
        kota_list = sorted(df_filtered['Kota'].unique())
        selected_kota = st.multiselect("Pilih Kota:", kota_list)
        if selected_kota:
            df_filtered = df_filtered[df_filtered['Kota'].isin(selected_kota)]

        # 4. FILTER OUTLET (Wajib C - Cascading/Bertingkat)
        # List outlet menyesuaikan kota yang dipilih
        outlet_list = sorted(df_filtered['Nama Outlet'].unique())
        selected_outlet = st.multiselect("Pilih Toko/Outlet:", outlet_list)
        if selected_outlet:
            df_filtered = df_filtered[df_filtered['Nama Outlet'].isin(selected_outlet)]

        # 5. FILTER MERK/BARANG (Wajib D)
        if 'Merk' in df_filtered.columns:
            merk_list = sorted(df_filtered['Merk'].unique())
            selected_merk = st.multiselect("Pilih Merk:", merk_list)
            if selected_merk:
                df_filtered = df_filtered[df_filtered['Merk'].isin(selected_merk)]

    # --- MAIN CONTENT ---
    st.markdown("<div class='header-style'>Dashboard Performa Sales</div>", unsafe_allow_html=True)

    if df_filtered.empty:
        st.info("⚠️ Data tidak ditemukan dengan filter yang Anda pilih.")
    else:
        # --- BAGIAN 1: KPI CARDS (Sesuai Request: Omset & Jumlah Toko) ---
        total_omset = df_filtered['Jumlah'].sum()
        total_toko_aktif = df_filtered['Nama Outlet'].nunique() # Menghitung jumlah toko unik
        
        col1, col2, col3 = st.columns([1, 1, 2]) 
        
        with col1:
            # Kartu Custom HTML untuk Tampilan Exclusive
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Omset</div>
                <div class="kpi-value" style="color: #27ae60;">Rp {total_omset:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Jumlah Toko Aktif</div>
                <div class="kpi-value" style="color: #2980b9;">{total_toko_aktif}</div>
            </div>
            """, unsafe_allow_html=True)
            
        # --- BAGIAN 2: CHARTS ---
        c_chart1, c_chart2 = st.columns([2, 1])
        
        with c_chart1:
            st.subheader("Tren Penjualan (Harian)")
            daily_trend = df_filtered.groupby('Tanggal')['Jumlah'].sum().reset_index()
            # Grafik Area Biru Navy (Exclusive)
            fig1 = px.area(daily_trend, x='Tanggal', y='Jumlah', template='plotly_white')
            fig1.update_traces(line_color='#1a237e', fill_color='rgba(26, 35, 126, 0.2)')
            fig1.update_layout(height=350, margin=dict(t=10, b=0, l=0, r=0), xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig1, use_container_width=True)
            
        with c_chart2:
            st.subheader("Top 5 Merk")
            if 'Merk' in df_filtered.columns:
                top_merk = df_filtered.groupby('Merk')['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=False).head(5)
                # Grafik Bar Horizontal
                fig2 = px.bar(top_merk, x='Jumlah', y='Merk', orientation='h', template='plotly_white')
                fig2.update_traces(marker_color='#00897b') 
                fig2.update_layout(height=350, margin=dict(t=10, b=0, l=0, r=0), xaxis_title=None, yaxis_title=None, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig2, use_container_width=True)

        # --- BAGIAN 3: TABEL RINCIAN (Sesuai Request Kolom) ---
        st.markdown("### 📋 Rincian Transaksi")
        
        # Kolom wajib yang diminta: Tanggal, Nama Outlet, Merk, Jumlah
        cols_needed = ['Tanggal', 'Nama Outlet', 'Merk', 'Jumlah']
        
        # Validasi kolom (jaga-jaga kalau nama kolom di excel beda sedikit)
        final_cols = [c for c in cols_needed if c in df_filtered.columns]
        
        st.dataframe(
            df_filtered[final_cols].sort_values('Tanggal', ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"),
                "Jumlah": st.column_config.NumberColumn("Omset", format="Rp %d"),
                "Nama Outlet": "Nama Toko",
                "Merk": "Brand"
            }
        )

# --- JALANKAN APLIKASI ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()
