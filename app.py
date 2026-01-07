import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import time
import re  # Untuk filter baris sampah

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Executive Sales Dashboard", layout="wide", page_icon="📈")

# ==========================================
# 1. KONFIGURASI DATABASE & TARGET
# ==========================================
# Target per Brand
TARGET_DATABASE = {
    "LISMAN": {
        "Bonavie": 50_000_000, "Whitelab": 150_000_000, "Goute": 50_000_000,
        "Dorskin": 20_000_000, "Gloow & Be": 130_000_000,
        "Javinci": 1_300_000_000, "Careso": 400_000_000,
        "Artist Inc": 130_000_000, "Newlab": 150_000_000, "Mlen": 100_000_000, "Madame G": 0
    },
    "AKBAR": {
        "Thai": 300_000_000, "Inesia": 100_000_000,
        "Y2000": 180_000_000, "Diosys": 520_000_000,
        "Sociolla": 600_000_000, "Skin1004": 300_000_000,
        "Masami": 40_000_000, "Cassandra": 50_000_000, "Clinelle": 80_000_000, "Rosanna": 0
    },
    "WILLIAM": {
        "The Face": 600_000_000, "Yu Chun Mei": 450_000_000, "Milano": 50_000_000, "Remar": 0,
        "Beautica": 100_000_000, "Walnutt": 30_000_000, "Elizabeth Rose": 50_000_000,
        "Maskit": 30_000_000, "Claresta": 300_000_000, "Birth Beyond": 120_000_000,
        "OtwooO": 200_000_000, "Saviosa": 0, "Rose All Day": 50_000_000
    },
    "MADONG": {
        "Ren & R & L": 20_000_000, "Sekawan": 350_000_000, "Avione": 250_000_000,
        "SYB": 150_000_000, "Mad For Make Up": 25_000_000, "Satto": 500_000_000,
        "Mykonos": 20_000_000, "Somethinc": 1_200_000_000, "Honor": 125_000_000, "Vlagio": 75_000_000
    }
}

# --- FITUR TAMBAHAN: HITUNG OTOMATIS TARGET SPV ---
SUPERVISOR_TOTAL_TARGETS = {k: sum(v.values()) for k, v in TARGET_DATABASE.items()}
TARGET_NASIONAL_VAL = sum(SUPERVISOR_TOTAL_TARGETS.values())

# Mapping Typo Brand
BRAND_ALIASES = {
    "Diosys": ["DIOSYS", "DYOSIS", "DIO"],
    "Y2000": ["Y2000", "Y 2000", "Y-2000"],
    "Masami": ["MASAMI", "JAYA"],
    "Cassandra": ["CASSANDRA", "CASANDRA"],
    "Thai": ["THAI"], "Inesia": ["INESIA"], "Honor": ["HONOR"], "Vlagio": ["VLAGIO"],
    "Sociolla": ["SOCIOLLA"], "Skin1004": ["SKIN1004", "SKIN 1004"],
    "Oimio": ["OIMIO"], "Clinelle": ["CLINELLE"],
    "Ren & R & L": ["REN", "R & L", "R&L"],
    "Sekawan": ["SEKAWAN", "AINIE"],
    "Mad For Make Up": ["MAD FOR", "MAKE UP", "MAJU", "MADFORMAKEUP"],
    "Avione": ["AVIONE"], "SYB": ["SYB"], "Satto": ["SATTO"],
    "Liora": ["LIORA"], "Mykonos": ["MYKONOS"], "Somethinc": ["SOMETHINC"],
    "Gloow & Be": ["GLOOW", "GLOOWBI", "GLOW"],
    "Artist Inc": ["ARTIST", "ARTIS"],
    "Bonavie": ["BONAVIE"], "Whitelab": ["WHITELAB"], "Goute": ["GOUTE"],
    "Dorskin": ["DORSKIN"], "Javinci": ["JAVINCI"], "Madam G": ["MADAM", "MADAME"],
    "Careso": ["CARESO"], "Newlab": ["NEWLAB"], "Mlen": ["MLEN"],
    "Walnutt": ["WALNUT", "WALNUTT"],
    "Elizabeth Rose": ["ELIZABETH"],
    "OtwooO": ["OTWOOO", "O.TWO.O", "O TWO O"],
    "Saviosa": ["SAVIOSA"],
    "The Face": ["THE FACE", "THEFACE"], "Yu Chun Mei": ["YU CHUN MEI", "YCM"],
    "Milano": ["MILANO"], "Remar": ["REMAR"], "Beautica": ["BEAUTICA"],
    "Maskit": ["MASKIT"], "Claresta": ["CLARESTA"], "Birth Beyond": ["BIRTH"],
    "Rose All Day": ["ROSE ALL DAY"]
}

# Mapping Nama Sales
SALES_MAPPING = {
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG",
    "ROZY AINIE": "ROZY", "NOVI AINIE": "NOVI", "NOVI AV": "NOVI",
    "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH", "HAMZA AV": "HAMZAH", "HAMZAH SYB": "HAMZAH",
    "RISKA AV": "RISKA", "RISKA BN": "RISKA", "RISKA CRS": "RISKA", "RISKA E-WL": "RISKA",
    "RISKA JV": "RISKA", "RISKA REN": "RISKA", "RISKA R&L": "RISKA", "RISKA SMT": "RISKA",
    "RISKA ST": "RISKA", "RISKA SYB": "RISKA", "RISKA - MILANO": "RISKA", "RISKA TF": "RISKA",
    "RISKA - YCM": "RISKA", "RISKA HONOR": "RISKA", "RISKA - VG": "RISKA", "RISKA TH": "RISKA",
    "RISKA - INESIA": "RISKA", "SSL - RISKA": "RISKA", "SKIN - RIZKA": "RISKA",
    "ADE CLA": "ADE", "ADE CRS": "ADE", "GLOOW - ADE": "ADE", "ADE JAVINCI": "ADE",
    "ADE SVD": "ADE", "ADE RAM PUTRA M.GIE": "ADE", "ADE - MLEN1": "ADE", "ADE NEWLAB": "ADE", "DORS - ADE": "ADE",
    "FANDI - BONAVIE": "FANDI", "DORS- FANDI": "FANDI", "FANDY CRS": "FANDI", "FANDI AFDILLAH": "FANDI",
    "FANDY WL": "FANDI", "GLOOW - FANDY": "FANDI", "FANDI - GOUTE": "FANDI", "FANDI MG": "FANDI",
    "FANDI - NEWLAB": "FANDI", "FANDY - YCM": "FANDI", "FANDY YLA": "FANDI",
    "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI", "GANI TF": "GANI",
    "GANI - YCM": "GANI", "GANI - MILANO": "GANI", "GANI - HONOR": "GANI", "GANI - VG": "GANI",
    "GANI - TH": "GANI", "GANI INESIA": "GANI", "GANI - KSM": "GANI",
    "BASTIAN CASANDRA": "BASTIAN", "SSL- BASTIAN": "BASTIAN", "SKIN - BASTIAN": "BASTIAN",
    "BASTIAN - HONOR": "BASTIAN", "BASTIAN - VG": "BASTIAN", "BASTIAN TH": "BASTIAN",
    "BASTIAN YL": "BASTIAN", "BASTIAN YL-DIO CAT": "BASTIAN", "BASTIAN SHMP": "BASTIAN", "BASTIAN-DIO 45": "BASTIAN",
    "YOGI REMAR": "YOGI", "YOGI THE FACE": "YOGI", "YOGI YCM": "YOGI", "MILANO - YOGI": "YOGI",
    "FERI - HONOR": "FERI", "FERI - VG": "FERI", "FERI THAI": "FERI", "FERI - INESIA": "FERI",
    "SSL - DEVI": "DEVI", "SKIN - DEVI": "DEVI", "DEVI Y- DIOSYS CAT": "DEVI", "DEVI YL": "DEVI",
    "DEVI SHMP": "DEVI", "DEVI-DIO 45": "DEVI", "DEVI YLA": "DEVI",
    "SSL- BAYU": "BAYU", "SKIN - BAYU": "BAYU", "BAYU-DIO 45": "BAYU", "BAYU YL-DIO CAT": "BAYU",
    "BAYU SHMP": "BAYU", "BAYU YL": "BAYU",
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

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def format_idr(value):
    try:
        return f"Rp {value:,.0f}".replace(",", ".")
    except:
        return "Rp 0"

def render_custom_progress(title, current, target):
    if target == 0: target = 1
    pct = (current / target) * 100
    visual_pct = min(pct, 100)
    
    if pct < 50:
        bar_color = "linear-gradient(90deg, #e74c3c, #c0392b)" # Merah
    elif 50 <= pct < 80:
        bar_color = "linear-gradient(90deg, #f1c40f, #f39c12)" # Kuning
    else:
        bar_color = "linear-gradient(90deg, #2ecc71, #27ae60)" # Hijau
    text_label = f"{pct:.1f}%"
    
    st.markdown(f"""
    <div style="margin-bottom: 20px; background-color: #fff; padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-weight: 700; font-size: 15px; color: #2c3e50;">{title}</span>
            <span style="font-weight: 600; color: #555; font-size: 14px;">{format_idr(current)} <span style="color:#999; font-weight:normal;">/ {format_idr(target)}</span></span>
        </div>
        <div style="width: 100%; background-color: #ecf0f1; border-radius: 20px; height: 26px; position: relative; overflow: hidden;">
            <div style="width: {visual_pct}%; background: {bar_color}; height: 100%; border-radius: 20px; transition: width 0.8s ease;"></div>
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                        display: flex; align-items: center; justify-content: center;
                        z-index: 10; font-weight: 800; font-size: 13px; color: #222;
                        text-shadow: 0px 0px 4px #ffffff, 0px 0px 4px #ffffff;">
                {text_label}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- FUNGSI LOAD DATA TERBARU ---
@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    try:
        url_with_ts = f"{url}&t={datetime.datetime.now().timestamp()}"
        df = pd.read_csv(url_with_ts)
    except Exception as e:
        return None
    
    required_cols = ['Penjualan', 'Merk', 'Jumlah', 'Tanggal']
    if not all(col in df.columns for col in required_cols):
        return None
    
    # Hapus Baris Sampah (Total/Subtotal)
    def is_sampah_row(row):
        return any(re.search(r'Total|Jumlah|Subtotal|Grand', str(val), re.IGNORECASE) for val in row)
    
    df = df[~df.apply(is_sampah_row, axis=1)]
    
    # Cleaning Ops
    df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(SALES_MAPPING)
    
    def normalize_brand(raw_brand):
        raw_upper = str(raw_brand).upper()
        for target_brand, keywords in BRAND_ALIASES.items():
            for keyword in keywords:
                if keyword in raw_upper:
                    return target_brand
        return raw_brand
    
    df['Merk'] = df['Merk'].apply(normalize_brand)
    
    # Format Angka
    df['Jumlah'] = df['Jumlah'].astype(str).str.replace(',', '.', regex=False)
    df['Jumlah'] = df['Jumlah'].str.replace(r'[^\d\.-]', '', regex=True)
    df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    # Format Tanggal
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce', format='mixed')
    
    def fix_swapped_date(d):
        if pd.isnull(d): return d
        try:
            if d.day <= 12 and d.day != d.month:
                return d.replace(day=d.month, month=d.day)
        except:
            pass
        return d
    
    df['Tanggal'] = df['Tanggal'].apply(fix_swapped_date)
    df = df.dropna(subset=['Tanggal', 'Penjualan', 'Merk', 'Jumlah'])
    
    for col in ['Kota', 'Nama Outlet', 'Nama Barang']:
        if col in df.columns:
            df[col] = df[col].astype(str)
    
    return df

def load_users():
    try:
        return pd.read_csv('users.csv')
    except:
        return pd.DataFrame()

# ==========================================
# 3. PAGES
# ==========================================
def login_page():
    st.markdown("<br><br><h1 style='text-align: center;'>🔒 Sales Command Center</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Masuk untuk melihat performa real-time</p>", unsafe_allow_html=True)
    
    users = load_users()
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Masuk Sistem", use_container_width=True)
            if submitted:
                if users.empty:
                    st.error("Database user tidak ditemukan (users.csv hilang).")
                else:
                    match = users[(users['username'] == username) & (users['password'] == password)]
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['role'] = match.iloc[0]['role']
                        st.session_state['sales_name'] = match.iloc[0]['sales_name']
                        st.rerun()
                    else:
                        st.error("Akses Ditolak: Username atau Password salah.")

def main_dashboard():
    # --- Sidebar Info ---
    with st.sidebar:
        st.info(f"👤 Login sebagai: **{st.session_state['sales_name']}**")
        st.caption(f"Role: {st.session_state['role'].upper()}")
        if st.button("Logout", type="primary"):
            st.session_state['logged_in'] = False
            st.rerun()
            
    df = load_data()
    if df is None or df.empty:
        st.error("⚠️ Gagal memuat data! Periksa koneksi internet atau Link Google Sheet.")
        return

    # --- 1. SCOPE LOGIC & DATE FILTER ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Filter Periode")

    default_start = df['Tanggal'].max().date().replace(day=1)
    default_end = df['Tanggal'].max().date()
    
    date_range = st.sidebar.date_input("Rentang Waktu", [default_start, default_end])

    # LOGIK SCOPE AWAL (Sebelum filter tanggal)
    role = st.session_state['role']
    my_name = st.session_state['sales_name']
    my_name_key = my_name.strip().upper()
    is_supervisor_account = my_name_key in TARGET_DATABASE
    target_sales_filter = "SEMUA"

    # -- Tentukan df_scope_all (Data milik sales/spv tsb sepanjang masa) --
    if role == 'manager':
        sales_list = ["SEMUA"] + sorted(list(df['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Pantau Kinerja Sales:", sales_list)
        if target_sales_filter == "SEMUA":
            df_scope_all = df
        else:
            df_scope_all = df[df['Penjualan'] == target_sales_filter]
            
    elif is_supervisor_account:
        my_brands = TARGET_DATABASE[my_name_key].keys()
        df_spv_raw = df[df['Merk'].isin(my_brands)]
        team_list = sorted(list(df_spv_raw['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Filter Tim (Brand Anda):", ["SEMUA"] + team_list)
        
        if target_sales_filter == "SEMUA":
            df_scope_all = df_spv_raw
        else:
            df_scope_all = df_spv_raw[df_spv_raw['Penjualan'] == target_sales_filter]
    else:
        df_scope_all = df[df['Penjualan'] == my_name]

    # -- Filter Lanjutan (Diterapkan ke df_scope_all) --
    st.sidebar.subheader("🔍 Filter Lanjutan")
    unique_brands = sorted(df_scope_all['Merk'].unique())
    pilih_merk = st.sidebar.multiselect("Pilih Merk", unique_brands)
    if pilih_merk: 
        df_scope_all = df_scope_all[df_scope_all['Merk'].isin(pilih_merk)]
        
    unique_outlets = sorted(df_scope_all['Nama Outlet'].unique())
    pilih_outlet = st.sidebar.multiselect("Pilih Outlet", unique_outlets)
    if pilih_outlet: 
        df_scope_all = df_scope_all[df_scope_all['Nama Outlet'].isin(pilih_outlet)]

    # -- Apply Filter Tanggal (Menjadi df_active) --
    if len(date_range) == 2:
        start_date, end_date = date_range
        # Filter untuk View Utama
        df_active = df_scope_all[(df_scope_all['Tanggal'].dt.date >= start_date) & (df_scope_all['Tanggal'].dt.date <= end_date)]
        # Reference Date untuk Hitungan Delta (H vs H-1)
        ref_date = end_date
    else:
        df_active = df_scope_all
        ref_date = df['Tanggal'].max().date()

    # --- HEADER ---
    st.title("🚀 Executive Dashboard")
    st.markdown("---")
    
    # --- 2. KPI METRICS (LOGIKA DELTA HARIAN) ---
    
    # A. Hitung Total Omset (Sesuai Range Tanggal yang dipilih)
    current_omset_total = df_active['Jumlah'].sum()
    
    # B. Hitung Delta (H vs H-1)
    # 1. Omset tepat pada tanggal terakhir pilihan user (ref_date)
    omset_hari_ini = df_scope_all[df_scope_all['Tanggal'].dt.date == ref_date]['Jumlah'].sum()
    
    # 2. Omset tepat satu hari sebelumnya (ref_date - 1)
    prev_date = ref_date - datetime.timedelta(days=1)
    omset_kemarin = df_scope_all[df_scope_all['Tanggal'].dt.date == prev_date]['Jumlah'].sum()
    
    # 3. Selisih
    delta_val = omset_hari_ini - omset_kemarin
    delta_label = f"vs {prev_date.strftime('%d %b')}"

    col1, col2, col3 = st.columns(3)
    with col1:
        # Menampilkan Total Omset Range, tapi Deltanya adalah Harian (Hari ini vs Kemarin)
        st.metric(
            label="💰 Total Omset (IJL)", 
            value=format_idr(current_omset_total), 
            delta=f"{format_idr(delta_val)} ({delta_label})"
        )
        # Caption untuk memperjelas omset hari terakhir
        st.caption(f"📅 Omset Tgl {ref_date.strftime('%d %b')}: **{format_idr(omset_hari_ini)}**")
        
    with col2:
        st.metric("🏪 Outlet Aktif", f"{df_active['Nama Outlet'].nunique()}")
    with col3:
        st.metric("🧾 Transaksi", f"{len(df_active)}")

    # --- PROGRESS BARS ---
    if role == 'manager' or is_supervisor_account:
        st.markdown("### 🎯 Target Monitor")
        
        # Note: Realisasi Nasional tetap mengambil dari Global Dataset yang di-filter tanggal saja
        # agar Manager tetap tau posisi perusahaan meski sedang filter sales tertentu
        realisasi_nasional = df[(df['Tanggal'].dt.date >= start_date) & (df['Tanggal'].dt.date <= end_date)]['Jumlah'].sum() if len(date_range)==2 else df['Jumlah'].sum()
        
        render_custom_progress("🏢 Target Nasional (All Team)", realisasi_nasional, TARGET_NASIONAL_VAL)
        
        if is_supervisor_account:
            target_pribadi = SUPERVISOR_TOTAL_TARGETS.get(my_name_key, 0)
            my_brands_list = TARGET_DATABASE[my_name_key].keys()
            # Realisasi Tim SPV (mengikuti filter tanggal)
            df_spv_only = df[df['Merk'].isin(my_brands_list)]
            if len(date_range)==2:
                df_spv_only = df_spv_only[(df_spv_only['Tanggal'].dt.date >= start_date) & (df_spv_only['Tanggal'].dt.date <= end_date)]
            
            realisasi_pribadi = df_spv_only['Jumlah'].sum()
            render_custom_progress(f"👤 Target Tim {my_name}", realisasi_pribadi, target_pribadi)
        
        st.markdown("---")

    # --- TABS ANALYTICS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Target Detail", "📈 Tren Harian", "🏆 Top Performance", "📋 Data Rincian"])
    
    with tab1:
        show_rapor_lengkap = (role == 'manager' and target_sales_filter == "SEMUA") or \
                             (is_supervisor_account and target_sales_filter == "SEMUA")
        
        if show_rapor_lengkap:
            st.subheader("Rapor Target per Brand")
            summary_data = []
            target_loop = TARGET_DATABASE.items() if role == 'manager' else {my_name_key: TARGET_DATABASE[my_name_key]}.items()
            
            for spv, brands_dict in target_loop:
                for brand, target in brands_dict.items():
                    # Realisasi per brand mengikuti df_active (sesuai filter tanggal & outlet)
                    realisasi = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                    pct_val = (realisasi / target) * 100 if target > 0 else 0
                    status_text = "✅" if pct_val >= 80 else "⚠️"
                    
                    summary_data.append({
                        "Supervisor": spv, "Brand": brand,
                        "Target": format_idr(target), "Realisasi": format_idr(realisasi),
                        "Ach (%)": f"{pct_val:.0f}%", "Pencapaian": pct_val / 100,
                        "Status": status_text, "Ach (Detail %)": pct_val
                    })
            
            df_summary = pd.DataFrame(summary_data)
            def color_row(row):
                return [f'background-color: {"#d4edda" if row["Ach (Detail %)"] >= 80 else "#f8d7da"}; color: black'] * len(row)
            
            st.dataframe(
                df_summary.style.apply(color_row, axis=1).hide(axis="columns", subset=['Ach (Detail %)']),
                use_container_width=True, hide_index=True,
                column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)}
            )
        else:
            st.info(f"Menampilkan kontribusi sales: **{target_sales_filter}**")
            sales_brands = df_active['Merk'].unique()
            brand_data = []
            for brand in sales_brands:
                target_found = 0
                spv_name = "-"
                for spv, brands_dict in TARGET_DATABASE.items():
                    if brand in brands_dict:
                        target_found = brands_dict[brand]
                        spv_name = spv
                        break
                
                if target_found > 0:
                    realisasi = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                    pct = (realisasi / target_found) * 100
                    brand_data.append({
                        "Brand": brand, "Owner": spv_name,
                        "Target Tim": format_idr(target_found), "Kontribusi Dia": format_idr(realisasi),
                        "Ach (%)": f"{pct:.1f}%", "Pencapaian": pct / 100, "_pct_val": pct
                    })
            
            if brand_data:
                df_indiv = pd.DataFrame(brand_data)
                st.dataframe(
                    df_indiv.style.hide(axis="columns", subset=['_pct_val']),
                    use_container_width=True, hide_index=True,
                    column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)}
                )
            else:
                st.warning("Tidak ada data penjualan brand yang memiliki target untuk sales ini.")

    with tab2:
        st.subheader("Grafik Tren Penjualan Harian")
        if not df_active.empty:
            daily_trend = df_active.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig = px.line(daily_trend, x='Tanggal', y='Jumlah', markers=True, title="Pergerakan Omset Harian")
            fig.update_layout(xaxis_title="", yaxis_title="Omset (Rp)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak ada data untuk ditampilkan.")

    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📦 Top 10 Produk")
            if not df_active.empty:
                top_prod = df_active.groupby('Nama Barang')['Jumlah'].sum().nlargest(10).reset_index()
                fig_prod = px.bar(top_prod, x='Jumlah', y='Nama Barang', orientation='h', text_auto='.2s')
                fig_prod.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_prod, use_container_width=True)
        with c2:
            st.subheader("🏪 Top 10 Toko")
            if not df_active.empty:
                top_outlet = df_active.groupby('Nama Outlet')['Jumlah'].sum().nlargest(10).reset_index()
                fig_outlet = px.bar(top_outlet, x='Jumlah', y='Nama Outlet', orientation='h', text_auto='.2s', color_discrete_sequence=['#2ecc71'])
                fig_outlet.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_outlet, use_container_width=True)

    with tab4:
        st.subheader("📋 Rincian Transaksi Lengkap")
        cols_to_show = ['Tanggal', 'Nama Outlet', 'Merk', 'Nama Barang', 'Jumlah', 'Penjualan']
        final_cols = [c for c in cols_to_show if c in df_active.columns]
        
        st.dataframe(
            df_active[final_cols].sort_values('Tanggal', ascending=False),
            use_container_width=True, hide_index=True,
            column_config={
                "Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"),
                "Jumlah": st.column_config.NumberColumn("Omset", format="Rp %d")
            }
        )
        
        csv = df_active[final_cols].to_csv(index=False).encode('utf-8')
        file_name = f"Laporan_Sales_{datetime.date.today()}.csv"
        st.download_button("📥 Download Data CSV", data=csv, file_name=file_name, mime="text/csv")

# --- 5. ALUR UTAMA ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    login_page()
else:
    main_dashboard()
