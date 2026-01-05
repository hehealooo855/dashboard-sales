import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sales Dashboard", layout="wide")

# --- KAMUS PERBAIKAN NAMA SALES (DATA DARI EXCEL ANDA) ---
SALES_MAPPING = {
    # GRUP MADONG
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG",
    # GRUP ROZY
    "ROZY AINIE": "ROZY",
    # GRUP NOVI
    "NOVI AINIE": "NOVI", "NOVI AV": "NOVI",
    # GRUP HAMZAH
    "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH",
    "HAMZA AV": "HAMZAH", "HAMZAH SYB": "HAMZAH",
    # GRUP RISKA
    "RISKA AV": "RISKA", "RISKA BN": "RISKA", "RISKA CRS": "RISKA",
    "RISKA  E-WL": "RISKA", "RISKA JV": "RISKA", "RISKA REN": "RISKA",
    "RISKA R&L": "RISKA", "RISKA SMT": "RISKA", "RISKA ST": "RISKA",
    "RISKA SYB": "RISKA", "RISKA - MILANO": "RISKA", "RISKA TF": "RISKA",
    "RISKA - YCM": "RISKA", "RISKA HONOR": "RISKA", "RISKA - VG": "RISKA",
    "RISKA TH": "RISKA", "RISKA - INESIA": "RISKA", "SSL - RISKA": "RISKA",
    "SKIN - RIZKA": "RISKA", 
    # GRUP ADE
    "ADE CLA": "ADE", "ADE CRS": "ADE", "GLOOW - ADE": "ADE",
    "ADE JAVINCI": "ADE", "ADE SVD": "ADE", "ADE RAM PUTRA M.GIE": "ADE",
    "ADE - MLEN1": "ADE", "ADE NEWLAB": "ADE", "DORS - ADE": "ADE",
    # GRUP FANDI
    "FANDI - BONAVIE": "FANDI", "DORS- FANDI": "FANDI", "FANDY CRS": "FANDI",
    "FANDI AFDILLAH": "FANDI", "FANDY WL": "FANDI", "GLOOW - FANDY": "FANDI",
    "FANDI - GOUTE": "FANDI", "FANDI MG": "FANDI", "FANDI - NEWLAB": "FANDI",
    "FANDY - YCM": "FANDI", "FANDY YLA": "FANDI",
    # GRUP GANI
    "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI",
    "GANI TF": "GANI", "GANI - YCM": "GANI", "GANI - MILANO": "GANI",
    "GANI - HONOR": "GANI", "GANI - VG": "GANI", "GANI - TH": "GANI",
    "GANI INESIA": "GANI", "GANI - KSM": "GANI",
    # GRUP BASTIAN
    "BASTIAN CASANDRA": "BASTIAN", "SSL- BASTIAN": "BASTIAN", "SKIN - BASTIAN": "BASTIAN",
    "BASTIAN - HONOR": "BASTIAN", "BASTIAN - VG": "BASTIAN", "BASTIAN TH": "BASTIAN",
    "BASTIAN YL": "BASTIAN", "BASTIAN YL-DIO CAT": "BASTIAN", "BASTIAN SHMP": "BASTIAN",
    "BASTIAN-DIO 45": "BASTIAN",
    # GRUP YOGI
    "YOGI REMAR": "YOGI", "YOGI THE FACE": "YOGI", "YOGI YCM": "YOGI",
    "MILANO - YOGI": "YOGI",
    # LAINNYA
    "FERI - HONOR": "FERI", "FERI - VG": "FERI", "FERI THAI": "FERI", "FERI - INESIA": "FERI",
    "SSL - DEVI": "DEVI", "SKIN - DEVI": "DEVI", "DEVI Y- DIOSYS CAT": "DEVI", "DEVI YL": "DEVI", "DEVI SHMP": "DEVI", "DEVI-DIO 45": "DEVI", "DEVI YLA": "DEVI",
    "SSL- BAYU": "BAYU", "SKIN - BAYU": "BAYU", "BAYU-DIO 45": "BAYU", "BAYU YL-DIO CAT": "BAYU", "BAYU SHMP": "BAYU", "BAYU YL": "BAYU",
    "PMT-WIRA": "WIRA", "WIRA SOMETHINC": "WIRA", "WIRA SYB": "WIRA",
    "SANTI BONAVIE": "SANTI", "SANTI WHITELAB": "SANTI", "SANTI GOUTE": "SANTI",
    "HABIBI - FZ": "HABIBI", "HABIBI SYB": "HABIBI", "HABIBI TH": "HABIBI",
    "MAS - MITHA": "MITHA", "MITHA ": "MITHA", "SSL BABY - MITHA ": "MITHA", "SAVIOSA - MITHA": "MITHA",
    "GLOOW - LISMAN": "LISMAN", "LISMAN - NEWLAB": "LISMAN",
    "WILLIAM BTC": "WILLIAM", "WILLI - ROS": "WILLIAM", "WILLI - WAL": "WILLIAM",
    "NAUFAL - JAVINCI": "NAUFAL", "NAUFAL SVD": "NAUFAL",
    "RIZKI JV": "RIZKI", "RIZKI SVD": "RIZKI",
    "RINI JV": "RINI", "RINI SYB": "RINI",
    "SAHRUL JAVINCI": "SAHRUL", "SAHRUL TF": "SAHRUL",
    "DWI CRS": "DWI", "DWI NLAB": "DWI",
    "FAUZIAH CLA": "FAUZIAH", "FAUZIAH ST": "FAUZIAH",
    "MARIANA CLIN": "MARIANA", "JAYA - MARIANA": "MARIANA"
}

# --- 1. FUNGSI LOAD DATA ---
@st.cache_data(ttl=3600) 
def load_data():
    # LINK CSV GOOGLE SHEET ANDA
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        return None

    # --- FITUR 1: STANDARDISASI NAMA SALES ---
    if 'Penjualan' in df.columns:
        # Bersihkan spasi
        df['Penjualan'] = df['Penjualan'].astype(str).str.strip()
        # Ganti nama sesuai kamus
        df['Penjualan'] = df['Penjualan'].replace(SALES_MAPPING)

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

    # --- SETTING PERIODE TANGGAL (Harus di awal agar bisa hitung Total Perusahaan) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter Tanggal")
    
    min_date = df['Tanggal'].min().date() if pd.notnull(df['Tanggal'].min()) else datetime.date.today()
    max_date = df['Tanggal'].max().date() if pd.notnull(df['Tanggal'].max()) else datetime.date.today()
    
    date_range = st.sidebar.date_input("Periode", [min_date, max_date])
    
    # 1. Buat Dataframe Global (Berdasarkan Tanggal Saja)
    # Ini untuk menghitung Total Omset Seluruh Perusahaan
    if len(date_range) == 2:
        df_global_period = df[
            (df['Tanggal'].dt.date >= date_range[0]) & 
            (df['Tanggal'].dt.date <= date_range[1])
        ]
    else:
        df_global_period = df

    # --- LOGIKA FILTER SALES ---
    role = st.session_state['role']
    my_name = st.session_state['sales_name']

    # Filter dari Dataframe Global yang sudah difilter tanggal
    if role == 'manager':
        sales_list = ["SEMUA"] + sorted(list(df_global_period['Penjualan'].dropna().unique()))
        selected_sales = st.sidebar.selectbox("Pantau Kinerja Sales:", sales_list)
        
        if selected_sales == "SEMUA":
            df_view = df_global_period
        else:
            df_view = df_global_period[df_global_period['Penjualan'] == selected_sales]
    else:
        # Sales dipaksa hanya lihat datanya sendiri
        df_view = df_global_period[df_global_period['Penjualan'] == my_name]

    # --- FILTER LANJUTAN (B, C, D) ---
    st.sidebar.subheader("Filter Lanjutan")

    # Filter Kota
    if 'Kota' in df_view.columns:
        list_kota = sorted(df_view['Kota'].unique())
        pilih_kota = st.sidebar.multiselect("Pilih Kota", list_kota)
        if pilih_kota:
            df_view = df_view[df_view['Kota'].isin(pilih_kota)]

    # Filter Nama Outlet
    if 'Nama Outlet' in df_view.columns:
        list_outlet = sorted(df_view['Nama Outlet'].unique())
        pilih_outlet = st.sidebar.multiselect("Pilih Nama Outlet", list_outlet)
        if pilih_outlet:
            df_view = df_view[df_view['Nama Outlet'].isin(pilih_outlet)]

    # Filter Merk
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
        # Hitung KPI Utama
        total_omset = df_view['Jumlah'].sum()
        total_toko = df_view['Nama Outlet'].nunique() 

        # Kartu Skor (Scorecard)
        col1, col2, col3 = st.columns(3) # Ubah jadi 3 kolom untuk Chart
        col1.metric("Total Omset", f"Rp {total_omset:,.0f}".replace(",", "."))
        col2.metric("Jumlah Toko Aktif", f"{total_toko} Outlet")
        
        # --- FITUR 2: CHART PIE RINCIAN SALES (TOTAL SALES BREAKDOWN) ---
        with col3:
            if not df_global_period.empty:
                # Mengelompokkan data global berdasarkan Sales untuk Pie Chart
                # Ini akan menampilkan persentase tiap sales (contoh: Lisman 0.4%, Fauziah 1%)
                sales_breakdown = df_global_period.groupby('Penjualan')['Jumlah'].sum().reset_index()
                
                st.caption("Kontribusi Sales (Market Share)")
                
                # Buat Pie Chart
                fig_share = px.pie(
                    sales_breakdown,
                    names='Penjualan',
                    values='Jumlah',
                    hole=0.5
                )
                
                # Menampilkan persentase di dalam chart, nama muncul saat di-hover (agar tidak berantakan)
                fig_share.update_traces(textposition='inside', textinfo='percent')
                fig_share.update_layout(
                    showlegend=False, 
                    margin=dict(t=0, b=0, l=0, r=0), 
                    height=120
                )
                st.plotly_chart(fig_share, use_container_width=True)

        st.divider()

        # Grafik Tren Harian
        st.subheader("📈 Tren Penjualan Harian")
        if 'Tanggal' in df_view.columns:
            daily = df_view.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig = px.bar(daily, x='Tanggal', y='Jumlah')
            st.plotly_chart(fig, use_container_width=True)

        # TABEL RINCIAN
        st.divider()
        st.subheader("📋 Rincian Transaksi")
        
        target_cols = ['Tanggal', 'Nama Outlet', 'Merk', 'Jumlah']
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
