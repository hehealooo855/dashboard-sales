import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sales Dashboard", layout="wide")

# --- DATABASE TARGET (HARDCODED SESUAI REQUEST) ---
# Angka dalam Rupiah Penuh
TARGET_DATABASE = {
    "LISMAN": {
        "Bonavie": 50_000_000, "Whitelab": 100_000_000, "Goute": 50_000_000,
        "Dorskin": 50_000_000, "Gloow & Be": 100_000_000,
        "Javinci": 1_300_000_000, "Madam G": 100_000_000, "Careso": 400_000_000,
        "Artist Inc": 130_000_000, "Newlab": 150_000_000, "Mlen": 0
    },
    "AKBAR": {
        "Thai": 300_000_000, "Inesia": 100_000_000, "Honor": 125_000_000, "Vlagio": 75_000_000,
        "Y2000": 180_000_000, "Dyosis": 520_000_000,
        "Sociolla": 600_000_000, "Skin1004": 400_000_000,
        "Masami": 40_000_000, "Oimio": 0, "Cassandra": 30_000_000, "Clinelle": 80_000_000
    },
    "WILLIAM": {
        "The Face": 600_000_000, "Yu Chun Mei": 450_000_000, "Milano": 50_000_000, "Remar": 0,
        "Beautica": 100_000_000, "Walnutt": 50_000_000, "Elizabeth Rose": 50_000_000,
        "Maskit": 100_000_000, "Claresta": 350_000_000, "Birth Beyond": 120_000_000,
        "OtwooO": 200_000_000, "Saviosa": 0, "Rose All Day": 50_000_000
    },
    "MADONG": {
        "Ren & R & L": 20_000_000, "Sekawan": 350_000_000, "Avione": 250_000_000,
        "SYB": 100_000_000, "Mad For Makeup": 50_000_000, "Satto": 500_000_000,
        "Liora": 0, "Mykonos": 20_000_000, "Somethinc": 1_100_000_000
    }
}

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
        df['Penjualan'] = df['Penjualan'].astype(str).str.strip()
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

    # --- SETTING PERIODE TANGGAL ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter Tanggal")
    
    min_date = df['Tanggal'].min().date() if pd.notnull(df['Tanggal'].min()) else datetime.date.today()
    max_date = df['Tanggal'].max().date() if pd.notnull(df['Tanggal'].max()) else datetime.date.today()
    
    date_range = st.sidebar.date_input("Periode", [min_date, max_date])
    
    if len(date_range) == 2:
        df_global_period = df[
            (df['Tanggal'].dt.date >= date_range[0]) & 
            (df['Tanggal'].dt.date <= date_range[1])
        ]
    else:
        df_global_period = df

    total_omset_perusahaan = df_global_period['Jumlah'].sum()

    # --- LOGIKA FILTER SALES & VIEW DATA ---
    role = st.session_state['role']
    my_name = st.session_state['sales_name']
    target_sales_filter = "SEMUA" 

    if role == 'manager':
        sales_list = ["SEMUA"] + sorted(list(df_global_period['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Pantau Kinerja Sales:", sales_list)
        
        if target_sales_filter == "SEMUA":
            df_view = df_global_period
        else:
            df_view = df_global_period[df_global_period['Penjualan'] == target_sales_filter]
    else:
        target_sales_filter = my_name
        df_view = df_global_period[df_global_period['Penjualan'] == my_name]

    # --- FILTER LANJUTAN ---
    st.sidebar.subheader("Filter Lanjutan")
    if 'Kota' in df_view.columns:
        pilih_kota = st.sidebar.multiselect("Pilih Kota", sorted(df_view['Kota'].unique()))
        if pilih_kota: df_view = df_view[df_view['Kota'].isin(pilih_kota)]
    if 'Nama Outlet' in df_view.columns:
        pilih_outlet = st.sidebar.multiselect("Pilih Nama Outlet", sorted(df_view['Nama Outlet'].unique()))
        if pilih_outlet: df_view = df_view[df_view['Nama Outlet'].isin(pilih_outlet)]
    if 'Merk' in df_view.columns:
        pilih_merk = st.sidebar.multiselect("Pilih Merk", sorted(df_view['Merk'].unique()))
        if pilih_merk: df_view = df_view[df_view['Merk'].isin(pilih_merk)]

    # --- LOGIKA GROWTH (Indikator Panah) ---
    prev_omset = 0
    growth_html = "" 
    if len(date_range) == 2:
        start_date, end_date = date_range
        days_diff = (end_date - start_date).days + 1
        prev_start = start_date - datetime.timedelta(days=days_diff)
        prev_end = end_date - datetime.timedelta(days=days_diff)
        
        df_prev = df[(df['Tanggal'].dt.date >= prev_start) & (df['Tanggal'].dt.date <= prev_end)]
        
        if role == 'manager' and target_sales_filter != "SEMUA":
            df_prev = df_prev[df_prev['Penjualan'] == target_sales_filter]
        elif role != 'manager':
            df_prev = df_prev[df_prev['Penjualan'] == my_name]
            
        prev_omset = df_prev['Jumlah'].sum()

    # --- TAMPILAN DASHBOARD ---
    st.title("🚀 Dashboard Performa Sales")
    
    if df_view.empty:
        st.warning("Belum ada data penjualan yang cocok dengan filter.")
    else:
        # Hitung KPI Utama
        total_omset = df_view['Jumlah'].sum()
        total_toko = df_view['Nama Outlet'].nunique() 

        # HTML Growth
        if prev_omset > 0:
            diff = total_omset - prev_omset
            pct_change = (diff / prev_omset) * 100
            color = "#27ae60" if diff >= 0 else "#c0392b"
            arrow = "▲" if diff >= 0 else "▼"
            growth_html = f"<div style='color: {color}; font-size: 14px; margin-top: 5px;'>{arrow} <b>{pct_change:.1f}%</b> vs periode lalu</div>"
        else:
            growth_html = "<div style='color: #95a5a6; font-size: 12px; margin-top: 5px;'>- Data pembanding N/A -</div>"

        # --- KPI CARDS ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Omset", f"Rp {total_omset:,.0f}".replace(",", "."))
            st.markdown(growth_html, unsafe_allow_html=True)
        with col2:
            st.metric("Jumlah Toko Aktif", f"{total_toko} Outlet")
        with col3:
            # Pie Chart Logic (Manager vs Sales)
            if not df_global_period.empty:
                st.caption("Market Share / Kontribusi")
                if role == 'manager':
                    sales_breakdown = df_global_period.groupby('Penjualan')['Jumlah'].sum().reset_index()
                    fig_share = px.pie(sales_breakdown, names='Penjualan', values='Jumlah', hole=0.5)
                else:
                    omset_lainnya = total_omset_perusahaan - total_omset
                    if omset_lainnya < 0: omset_lainnya = 0
                    fig_share = px.pie(names=['Omset Saya', 'Sales Lain'], values=[total_omset, omset_lainnya], hole=0.5, color_discrete_sequence=['#3498db', '#ecf0f1'])
                
                fig_share.update_traces(textposition='inside', textinfo='percent')
                fig_share.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=120)
                st.plotly_chart(fig_share, use_container_width=True)

        st.divider()

        # --- FITUR BARU: TARGET vs REALISASI (THE GAME CHANGER) ---
        # Logika: Mencari apakah User yang dipilih punya data Target di Database
        active_target_data = {}
        target_name_key = target_sales_filter.strip().upper() # Pastikan Uppercase (LISMAN, MADONG)
        
        # Jika Manager pilih SEMUA, kita tampilkan Total Target Semua Supervisor (9.39 M)
        if target_sales_filter == "SEMUA":
             total_target_val = 9_390_000_000
             active_target_data = None # Tidak ada breakdown brand spesifik untuk "SEMUA"
             st.subheader(f"🎯 Target Nasional: Rp {total_target_val:,.0f}")
        
        # Jika Sales Spesifik (Lisman, Akbar, dll)
        elif target_name_key in TARGET_DATABASE:
            active_target_data = TARGET_DATABASE[target_name_key]
            total_target_val = sum(active_target_data.values())
            st.subheader(f"🎯 Target {target_sales_filter}: Rp {total_target_val:,.0f}")
        else:
            total_target_val = 0
            st.info("Data Target belum disetting untuk user ini.")

        # Tampilkan Progress Bar jika ada target
        if total_target_val > 0:
            achievement = (total_omset / total_target_val)
            st.progress(min(achievement, 1.0))
            st.caption(f"Pencapaian: **{achievement*100:.1f}%** dari Target")

            # Tampilkan Tabel Breakdown Per Brand (Jika Sales Spesifik)
            if active_target_data:
                with st.expander("Lihat Rincian Target per Brand"):
                    # Siapkan Data
                    brand_data = []
                    
                    # Loop semua brand di database target sales tersebut
                    for brand, target_brand in active_target_data.items():
                        # Cari realisasi di data transaksi (df_view)
                        # Kita pakai 'str.contains' agar fleksibel (misal target "WhiteLab" bisa match "Whitelab")
                        realisasi_brand = df_view[df_view['Merk'].str.contains(brand, case=False, na=False)]['Jumlah'].sum()
                        
                        pct = (realisasi_brand / target_brand) * 100 if target_brand > 0 else 0
                        status = "✅ Achieved" if pct >= 100 else "⚠️ On Process"
                        
                        brand_data.append({
                            "Brand": brand,
                            "Target (Rp)": f"{target_brand:,.0f}",
                            "Realisasi (Rp)": f"{realisasi_brand:,.0f}",
                            "Pencapaian": f"{pct:.1f}%",
                            "Status": status
                        })
                    
                    # Bikin Dataframe
                    df_target_breakdown = pd.DataFrame(brand_data)
                    st.dataframe(df_target_breakdown, use_container_width=True, hide_index=True)

        st.divider()

        # Grafik Tren Harian
        st.subheader("📈 Tren Penjualan Harian")
        if 'Tanggal' in df_view.columns:
            daily = df_view.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig = px.bar(daily, x='Tanggal', y='Jumlah')
            st.plotly_chart(fig, use_container_width=True)

        # TABEL RINCIAN
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

        # Tombol Download
        csv_data = df_view[final_cols].sort_values('Tanggal', ascending=False).to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Data Excel", data=csv_data, file_name="laporan_penjualan.csv", mime="text/csv")

# --- 5. ALUR UTAMA ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    main_dashboard()
