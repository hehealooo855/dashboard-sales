import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import time
import re
import pytz  

# --- 1. KONFIGURASI HALAMAN & CSS PREMIUM ---import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import time
import re
import pytz 

# --- 1. KONFIGURASI HALAMAN & CSS PREMIUM ---
st.set_page_config(
    page_title="Dashboard Sales", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        border: 1px solid #e6e6e6; padding: 20px; border-radius: 10px;
        background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #e74c3c, #f1c40f, #2ecc71);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONFIGURASI DATABASE & TARGET
# ==========================================
TARGET_DATABASE = {
    "MADONG": {
        "Somethinc": 1_200_000_000, 
        "SYB": 150_000_000, 
        "Sekawan": 600_000_000, # AINIE
        "Avione": 300_000_000, 
        "Honor": 125_000_000, 
        "Vlagio": 75_000_000,
        "Ren & R & L": 20_000_000, 
        "Mad For Make Up": 25_000_000, 
        "Satto": 500_000_000,
        "Mykonos": 20_000_000
    },
    "LISMAN": {
        "Javinci": 1_300_000_000, 
        "Careso": 400_000_000, 
        "Newlab": 150_000_000, 
        "Gloow & Be": 130_000_000, # Glowbe
        "Dorskin": 20_000_000, 
        "Whitelab": 150_000_000, 
        "Bonavie": 50_000_000, 
        "Goute": 50_000_000, 
        "Mlen": 100_000_000, 
        "Artist Inc": 130_000_000
    },
    "AKBAR": {
        "Sociolla": 600_000_000, 
        "Thai": 300_000_000, 
        "Inesia": 100_000_000, 
        "Y2000": 180_000_000, 
        "Diosys": 520_000_000,
        "Masami": 40_000_000, 
        "Cassandra": 50_000_000, 
        "Clinelle": 80_000_000
    },
    "WILLIAM": {
        "The Face": 600_000_000, 
        "Yu Chun Mei": 450_000_000, 
        "Milano": 50_000_000, 
        "Remar": 0,
        "Beautica": 100_000_000, 
        "Walnutt": 30_000_000, 
        "Elizabeth Rose": 50_000_000, 
        "Maskit": 30_000_000, 
        "Claresta": 300_000_000, 
        "Birth Beyond": 120_000_000, 
        "OtwooO": 200_000_000, 
        "Rose All Day": 50_000_000
    }
}

# --- DATABASE TARGET INDIVIDU ---
INDIVIDUAL_TARGETS = {
    "WIRA": { "Somethinc": 660_000_000, "SYB": 75_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000 },
    "HAMZAH": { "Somethinc": 540_000_000, "SYB": 75_000_000, "Sekawan": 60_000_000, "Avione": 60_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000 },
    "ROZY": { "Sekawan": 100_000_000, "Avione": 100_000_000 },
    "NOVI": { "Sekawan": 90_000_000, "Avione": 90_000_000 },
    "DANI": { "Sekawan": 50_000_000, "Avione": 50_000_000 }, 
    "FERI": { "Honor": 50_000_000, "Vlagio": 30_000_000 }
}

SUPERVISOR_TOTAL_TARGETS = {k: sum(v.values()) for k, v in TARGET_DATABASE.items()}
TARGET_NASIONAL_VAL = sum(SUPERVISOR_TOTAL_TARGETS.values())

BRAND_ALIASES = {
    "Diosys": ["DIOSYS", "DYOSIS", "DIO"], "Y2000": ["Y2000", "Y 2000", "Y-2000"],
    "Masami": ["MASAMI", "JAYA"], "Cassandra": ["CASSANDRA", "CASANDRA"],
    "Thai": ["THAI"], "Inesia": ["INESIA"], "Honor": ["HONOR"], "Vlagio": ["VLAGIO"],
    "Sociolla": ["SOCIOLLA"], "Skin1004": ["SKIN1004", "SKIN 1004"], "Oimio": ["OIMIO"],
    "Clinelle": ["CLINELLE"], "Ren & R & L": ["REN", "R & L", "R&L"], "Sekawan": ["SEKAWAN", "AINIE"],
    "Mad For Make Up": ["MAD FOR", "MAKE UP", "MAJU", "MADFORMAKEUP"], "Avione": ["AVIONE"],
    "SYB": ["SYB"], "Satto": ["SATTO"], "Liora": ["LIORA"], "Mykonos": ["MYKONOS"],
    "Somethinc": ["SOMETHINC"], "Gloow & Be": ["GLOOW", "GLOOWBI", "GLOW"],
    "Artist Inc": ["ARTIST", "ARTIS"], "Bonavie": ["BONAVIE"], "Whitelab": ["WHITELAB"],
    "Goute": ["GOUTE"], "Dorskin": ["DORSKIN"], "Javinci": ["JAVINCI"], "Madam G": ["MADAM", "MADAME"],
    "Careso": ["CARESO"], "Newlab": ["NEWLAB"], "Mlen": ["MLEN"], "Walnutt": ["WALNUT", "WALNUTT"],
    "Elizabeth Rose": ["ELIZABETH"], "OtwooO": ["OTWOOO", "O.TWO.O", "O TWO O"],
    "Saviosa": ["SAVIOSA"], "The Face": ["THE FACE", "THEFACE"], "Yu Chun Mei": ["YU CHUN MEI", "YCM"],
    "Milano": ["MILANO"], "Remar": ["REMAR"], "Beautica": ["BEAUTICA"], "Maskit": ["MASKIT"],
    "Claresta": ["CLARESTA"], "Birth Beyond": ["BIRTH"], "Rose All Day": ["ROSE ALL DAY"]
}

SALES_MAPPING = {
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG", "ROZY AINIE": "ROZY", 
    "NOVI AINIE": "NOVI", "NOVI AV": "NOVI", "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH",
    "HAMZA AV": "HAMZAH", "HAMZAH SYB": "HAMZAH", "RISKA AV": "RISKA", "RISKA BN": "RISKA",
    "RISKA CRS": "RISKA", "RISKA E-WL": "RISKA", "RISKA JV": "RISKA", "RISKA REN": "RISKA",
    "RISKA R&L": "RISKA", "RISKA SMT": "RISKA", "RISKA ST": "RISKA", "RISKA SYB": "RISKA",
    "RISKA - MILANO": "RISKA", "RISKA TF": "RISKA", "RISKA - YCM": "RISKA", "RISKA HONOR": "RISKA",
    "RISKA - VG": "RISKA", "RISKA TH": "RISKA", "RISKA - INESIA": "RISKA", "SSL - RISKA": "RISKA",
    "SKIN - RIZKA": "RISKA", "ADE CLA": "ADE", "ADE CRS": "ADE", "GLOOW - ADE": "ADE",
    "ADE JAVINCI": "ADE", "ADE SVD": "ADE", "ADE RAM PUTRA M.GIE": "ADE", "ADE - MLEN1": "ADE",
    "ADE NEWLAB": "ADE", "DORS - ADE": "ADE", "FANDI - BONAVIE": "FANDI", "DORS- FANDI": "FANDI",
    "FANDY CRS": "FANDI", "FANDI AFDILLAH": "FANDI", "FANDY WL": "FANDI", "GLOOW - FANDY": "FANDI",
    "FANDI - GOUTE": "FANDI", "FANDI MG": "FANDI", "FANDI - NEWLAB": "FANDI", "FANDY - YCM": "FANDI",
    "FANDY YLA": "FANDI", "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI",
    "GANI TF": "GANI", "GANI - YCM": "GANI", "GANI - MILANO": "GANI", "GANI - HONOR": "GANI",
    "GANI - VG": "GANI", "GANI - TH": "GANI", "GANI INESIA": "GANI", "GANI - KSM": "GANI",
    "BASTIAN CASANDRA": "BASTIAN", "SSL- BASTIAN": "BASTIAN", "SKIN - BASTIAN": "BASTIAN",
    "BASTIAN - HONOR": "BASTIAN", "BASTIAN - VG": "BASTIAN", "BASTIAN TH": "BASTIAN",
    "BASTIAN YL": "BASTIAN", "BASTIAN YL-DIO CAT": "BASTIAN", "BASTIAN SHMP": "BASTIAN",
    "BASTIAN-DIO 45": "BASTIAN", "YOGI REMAR": "YOGI", "YOGI THE FACE": "YOGI", "YOGI YCM": "YOGI",
    "MILANO - YOGI": "YOGI", "FERI - HONOR": "FERI", "FERI - VG": "FERI", "FERI THAI": "FERI",
    "FERI - INESIA": "FERI", "SSL - DEVI": "DEVI", "SKIN - DEVI": "DEVI", "DEVI Y- DIOSYS CAT": "DEVI",
    "DEVI YL": "DEVI", "DEVI SHMP": "DEVI", "DEVI-DIO 45": "DEVI", "DEVI YLA": "DEVI",
    "SSL- BAYU": "BAYU", "SKIN - BAYU": "BAYU", "BAYU-DIO 45": "BAYU", "BAYU YL-DIO CAT": "BAYU",
    "BAYU SHMP": "BAYU", "BAYU YL": "BAYU", "PMT-WIRA": "WIRA", "WIRA SOMETHINC": "WIRA",
    "WIRA SYB": "WIRA", "SANTI BONAVIE": "SANTI", "SANTI WHITELAB": "SANTI", "SANTI GOUTE": "SANTI",
    "HABIBI - FZ": "HABIBI", "HABIBI SYB": "HABIBI", "HABIBI TH": "HABIBI", "MAS - MITHA": "MITHA",
    "MITHA ": "MITHA", "SSL BABY - MITHA ": "MITHA", "SAVIOSA - MITHA": "MITHA",
    "GLOOW - LISMAN": "LISMAN", "LISMAN - NEWLAB": "LISMAN", "WILLIAM BTC": "WILLIAM",
    "WILLI - ROS": "WILLIAM", "WILLI - WAL": "WILLIAM", "NAUFAL - JAVINCI": "NAUFAL",
    "NAUFAL SVD": "NAUFAL", "RIZKI JV": "RIZKI", "RIZKI SVD": "RIZKI", "RINI JV": "RINI",
    "RINI SYB": "RINI", "SAHRUL JAVINCI": "SAHRUL", "SAHRUL TF": "SAHRUL", "DWI CRS": "DWI",
    "DWI NLAB": "DWI", "FAUZIAH CLA": "FAUZIAH", "FAUZIAH ST": "FAUZIAH", "MARIANA CLIN": "MARIANA",
    "JAYA - MARIANA": "MARIANA", "DANI AINIE": "DANI", "DANI AV": "DANI", "DANI SEKAWAN": "DANI"
}

# ==========================================
# 3. CORE LOGIC
# ==========================================

def get_current_time_wib():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

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
        bar_color = "linear-gradient(90deg, #e74c3c, #c0392b)" 
    elif 50 <= pct < 80:
        bar_color = "linear-gradient(90deg, #f1c40f, #f39c12)" 
    else:
        bar_color = "linear-gradient(90deg, #2ecc71, #27ae60)" 
    
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

# --- FUNGSI LOAD DATA TERBARU (STRICT & SMART CLEANING) ---
@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    try:
        url_with_ts = f"{url}&t={int(time.time())}"
        df = pd.read_csv(url_with_ts, dtype=str) # Baca semua sebagai string
    except Exception as e:
        return None

    # Normalisasi Nama Kolom
    df.columns = df.columns.str.strip()

    required_cols = ['Penjualan', 'Merk', 'Jumlah', 'Tanggal']
    if not all(col in df.columns for col in required_cols):
        return None

    # --- 1. CLEANING SAMPAH (BARIS TOTAL/KOSONG) ---
    if 'Nama Outlet' in df.columns:
        # Hapus baris Total/Subtotal
        df = df[~df['Nama Outlet'].astype(str).str.contains(r'Total|Jumlah|Subtotal|Grand|Rekap', case=False, na=False)]
        # Hapus baris kosong atau strip
        df = df[~df['Nama Outlet'].astype(str).str.strip().isin(['', '-', 'nan', 'NaN'])]
    
    if 'Nama Barang' in df.columns:
        # Hapus baris Total di Nama Barang
        df = df[~df['Nama Barang'].astype(str).str.contains(r'Total|Jumlah', case=False, na=False)]
        # Hapus baris kosong atau strip
        df = df[~df['Nama Barang'].astype(str).str.strip().isin(['', '-', 'nan', 'NaN'])]

    # --- 2. NORMALISASI ---
    df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(SALES_MAPPING).astype('category')
    
    def normalize_brand(raw_brand):
        raw_upper = str(raw_brand).upper()
        for target_brand, keywords in BRAND_ALIASES.items():
            for keyword in keywords:
                if keyword in raw_upper: return target_brand
        return raw_brand
    df['Merk'] = df['Merk'].apply(normalize_brand).astype('category')
    
    # --- 3. NUMERIC CLEANING (LEBIH PINTAR) ---
    # Fungsi pembersih angka custom
    def clean_currency(x):
        if pd.isna(x) or str(x).strip() == '': return 0
        s = str(x)
        # Jika ada koma di akhir (desimal), ganti jadi titik
        if ',' in s[-3:]: 
            s = s.replace(',', '.')
        # Hapus semua karakter selain angka dan titik (untuk desimal)
        s = re.sub(r'[^\d.]', '', s)
        try:
            return float(s)
        except:
            return 0

    df['Jumlah'] = df['Jumlah'].apply(clean_currency)
    
    # Logic Darurat: Jika angka < 1000, kali 1000 (Asumsi salah input ribuan)
    def auto_fix_thousands(val):
        if 0 < val < 1000: return val * 1000
        return val
    df['Jumlah'] = df['Jumlah'].apply(auto_fix_thousands)

    # --- 4. DATE CLEANING & FILTER TAHUN ---
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
    
    # Hapus yang tanggalnya NaT (Not a Time)
    df = df.dropna(subset=['Tanggal', 'Penjualan', 'Merk', 'Jumlah'])

    # Filter Tahun Logis (Buffer 1 tahun ke belakang dan depan)
    current_year = datetime.datetime.now().year
    df = df[(df['Tanggal'].dt.year >= current_year - 1) & (df['Tanggal'].dt.year <= current_year + 1)]
    
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
# 4. MAIN DASHBOARD LOGIC
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

    # --- MAIN FILTER ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Filter Periode")
    
    default_start = df['Tanggal'].max().date().replace(day=1)
    default_end = df['Tanggal'].max().date()
    
    date_range = st.sidebar.date_input("Rentang Waktu", [default_start, default_end])
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_view_global = df[(df['Tanggal'].dt.date >= start_date) & (df['Tanggal'].dt.date <= end_date)]
        
        duration = (end_date - start_date).days
        prev_start = start_date - datetime.timedelta(days=duration)
        prev_end = start_date - datetime.timedelta(days=1)
        df_prev_global = df[(df['Tanggal'].dt.date >= prev_start) & (df['Tanggal'].dt.date <= prev_end)]
    else:
        df_view_global = df
        df_prev_global = pd.DataFrame()

    # --- SCOPE LOGIC ---
    role = st.session_state['role']
    my_name = st.session_state['sales_name']
    my_name_key = my_name.strip().upper()
    is_supervisor_account = my_name_key in TARGET_DATABASE

    target_sales_filter = "SEMUA"

    if role == 'manager':
        sales_list = ["SEMUA"] + sorted(list(df_view_global['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Pantau Kinerja Sales:", sales_list)
        if target_sales_filter == "SEMUA":
            df_active = df_view_global
            df_prev_active = df_prev_global
        else:
            df_active = df_view_global[df_view_global['Penjualan'] == target_sales_filter]
            df_prev_active = df_prev_global[df_prev_global['Penjualan'] == target_sales_filter] if not df_prev_global.empty else pd.DataFrame()

    elif is_supervisor_account:
        my_brands = TARGET_DATABASE[my_name_key].keys()
        df_spv_scope = df_view_global[df_view_global['Merk'].isin(my_brands)]
        df_prev_spv_scope = df_prev_global[df_prev_global['Merk'].isin(my_brands)] if not df_prev_global.empty else pd.DataFrame()
        
        team_list = sorted(list(df_spv_scope['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Filter Tim (Brand Anda):", ["SEMUA"] + team_list)
        
        if target_sales_filter == "SEMUA":
            df_active = df_spv_scope
            df_prev_active = df_prev_spv_scope
        else:
            df_active = df_spv_scope[df_spv_scope['Penjualan'] == target_sales_filter]
            df_prev_active = df_prev_spv_scope[df_prev_spv_scope['Penjualan'] == target_sales_filter] if not df_prev_spv_scope.empty else pd.DataFrame()

    else:
        # LOGIC FIX: Set target_sales_filter ke nama sales login
        target_sales_filter = my_name 
        df_active = df_view_global[df_view_global['Penjualan'] == my_name]
        df_prev_active = df_prev_global[df_prev_global['Penjualan'] == my_name] if not df_prev_global.empty else pd.DataFrame()

    # --- ADVANCED FILTER ---
    st.sidebar.subheader("🔍 Filter Lanjutan")
    if not df_active.empty:
        pilih_merk = st.sidebar.multiselect("Pilih Merk", sorted(df_active['Merk'].unique()))
        if pilih_merk: df_active = df_active[df_active['Merk'].isin(pilih_merk)]
        
        pilih_outlet = st.sidebar.multiselect("Pilih Outlet", sorted(df_active['Nama Outlet'].unique()))
        if pilih_outlet: df_active = df_active[df_active['Nama Outlet'].isin(pilih_outlet)]

    # --- HEADER ---
    st.title("🚀 Executive Dashboard")
    st.markdown("---")

    # --- KPI METRICS ---
    current_omset = df_active['Jumlah'].sum()
    prev_omset = df_prev_active['Jumlah'].sum() if not df_prev_active.empty else 0
    delta_val = current_omset - prev_omset
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total Omset", format_idr(current_omset), delta=format_idr(delta_val))
    with col2:
        st.metric("🏪 Outlet Aktif", f"{df_active['Nama Outlet'].nunique()}")
    with col3:
        st.metric("🧾 Transaksi", f"{len(df_active)}")

    # --- TARGET MONITOR (UPDATED FOR INDIVIDUAL) ---
    if role == 'manager' or is_supervisor_account or target_sales_filter in INDIVIDUAL_TARGETS:
        st.markdown("### 🎯 Target Monitor")
        
        # 1. Target Nasional / Tim
        if target_sales_filter == "SEMUA":
            realisasi_nasional = df_view_global['Jumlah'].sum() 
            render_custom_progress("🏢 Target Nasional (All Team)", realisasi_nasional, TARGET_NASIONAL_VAL)

            if is_supervisor_account:
                target_pribadi = SUPERVISOR_TOTAL_TARGETS.get(my_name_key, 0)
                my_brands_list = TARGET_DATABASE[my_name_key].keys()
                realisasi_pribadi = df_view_global[df_view_global['Merk'].isin(my_brands_list)]['Jumlah'].sum()
                
                render_custom_progress(f"👤 Target Tim {my_name}", realisasi_pribadi, target_pribadi)
        
        # 2. Target Individu Spesifik (ROZY, NOVI, WIRA, DANI, dll)
        elif target_sales_filter in INDIVIDUAL_TARGETS:
            st.info(f"📋 Target Spesifik: **{target_sales_filter}**")
            targets_map = INDIVIDUAL_TARGETS[target_sales_filter]
            
            for brand, target_val in targets_map.items():
                realisasi_brand = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                render_custom_progress(f"👤 {brand} - {target_sales_filter}", realisasi_brand, target_val)
        
        else:
            st.warning(f"Sales **{target_sales_filter}** tidak memiliki target individu spesifik.")
        
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
                    realisasi = df_view_global[df_view_global['Merk'] == brand]['Jumlah'].sum()
                    pct_val = (realisasi / target) * 100 if target > 0 else 0
                    status_text = "✅" if pct_val >= 80 else "⚠️"
                    
                    summary_data.append({
                        "Supervisor": spv, "Brand": brand,
                        "Target": format_idr(target), "Realisasi": format_idr(realisasi),
                        "Ach (%)": f"{pct_val:.0f}%", "Pencapaian": pct_val / 100,
                        "Status": status_text, "_pct_raw": pct_val
                    })
            
            df_summary = pd.DataFrame(summary_data)
            def color_row(row):
                return [f'background-color: {"#d4edda" if row["_pct_raw"] >= 80 else "#f8d7da"}; color: black'] * len(row)

            st.dataframe(
                df_summary.style.apply(color_row, axis=1).hide(axis="columns", subset=['_pct_raw']),
                use_container_width=True, hide_index=True,
                column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)}
            )
        else:
            if target_sales_filter in INDIVIDUAL_TARGETS:
                 st.info("Lihat progress bar di atas untuk detail target individu.")
            else:
                 # Fallback Table for non-specific sales
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
        
        # --- FITUR DETEKTIF DATA (Untuk Cek Selisih) ---
        with st.expander("🕵️‍♂️ DETEKTIF DATA: Cek Transaksi Terbesar (Cari Angka Aneh)"):
            st.warning("Gunakan tabel ini untuk mencari baris 'Total' yang menyusup.")
            # Tampilkan 10 transaksi terbesar yang mungkin mencurigakan
            st.dataframe(
                df_active.nlargest(10, 'Jumlah')[['Tanggal', 'Nama Outlet', 'Nama Barang', 'Jumlah']],
                use_container_width=True
            )

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
st.set_page_config(
    page_title="Dashboard Sales", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        border: 1px solid #e6e6e6; padding: 20px; border-radius: 10px;
        background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #e74c3c, #f1c40f, #2ecc71);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONFIGURASI DATABASE & TARGET (SAMA SEPERTI SEBELUMNYA)
# ==========================================
TARGET_DATABASE = {
    "MADONG": { "Somethinc": 1_200_000_000, "SYB": 150_000_000, "Sekawan": 600_000_000, "Avione": 300_000_000, "Honor": 125_000_000, "Vlagio": 75_000_000, "Ren & R & L": 20_000_000, "Mad For Make Up": 25_000_000, "Satto": 500_000_000, "Mykonos": 20_000_000 },
    "LISMAN": { "Javinci": 1_300_000_000, "Careso": 400_000_000, "Newlab": 150_000_000, "Gloow & Be": 130_000_000, "Dorskin": 20_000_000, "Whitelab": 150_000_000, "Bonavie": 50_000_000, "Goute": 50_000_000, "Mlen": 100_000_000, "Artist Inc": 130_000_000 },
    "AKBAR": { "Sociolla": 600_000_000, "Thai": 300_000_000, "Inesia": 100_000_000, "Y2000": 180_000_000, "Diosys": 520_000_000, "Masami": 40_000_000, "Cassandra": 50_000_000, "Clinelle": 80_000_000 },
    "WILLIAM": { "The Face": 600_000_000, "Yu Chun Mei": 450_000_000, "Milano": 50_000_000, "Remar": 0, "Beautica": 100_000_000, "Walnutt": 30_000_000, "Elizabeth Rose": 50_000_000, "Maskit": 30_000_000, "Claresta": 300_000_000, "Birth Beyond": 120_000_000, "OtwooO": 200_000_000, "Rose All Day": 50_000_000 }
}

INDIVIDUAL_TARGETS = {
    "WIRA": { "Somethinc": 660_000_000, "SYB": 75_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000, "Elizabeth Rose": 30_000_000, "Walnutt": 20_000_000 },
    "HAMZAH": { "Somethinc": 540_000_000, "SYB": 75_000_000, "Sekawan": 60_000_000, "Avione": 60_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000 },
    "ROZY": { "Sekawan": 100_000_000, "Avione": 100_000_000 },
    "NOVI": { "Sekawan": 90_000_000, "Avione": 90_000_000 },
    "DANI": { "Sekawan": 50_000_000, "Avione": 50_000_000 },
    "FERI": { "Honor": 50_000_000, "Thai": 200_000_000, "Vlagio": 30_000_000, "Inesia": 30_000_000 },
    "NAUFAL": { "Javinci": 550_000_000 },
    "RIZKI": { "Javinci": 450_000_000 },
    "ADE": { "Javinci": 180_000_000, "Careso": 20_000_000, "Newlab": 75_000_000, "Gloow & Be": 60_000_000, "Dorskin": 10_000_000, "Mlen": 50_000_000 },
    "FANDI": { "Javinci": 40_000_000, "Careso": 20_000_000, "Newlab": 75_000_000, "Gloow & Be": 60_000_000, "Dorskin": 10_000_000, "Whitelab": 75_000_000, "Goute": 25_000_000, "Bonavie": 25_000_000, "Mlen": 50_000_000 },
    "SYAHRUL": { "Javinci": 40_000_000, "Careso": 10_000_000, "Gloow & Be": 10_000_000 },
    "RISKA": { "Javinci": 40_000_000, "Sociolla": 190_000_000, "Thai": 30_000_000, "Inesia": 20_000_000 },
    "DWI": { "Careso": 350_000_000 },
    "SANTI": { "Whitelab": 75_000_000, "Bonavie": 25_000_000, "Goute": 25_000_000 },
    "ASWIN": { "Artist Inc": 130_000_000 },
    "DEVI": { "Sociolla": 120_000_000, "Diosys": 175_000_000, "Y2000": 65_000_000 },
    "BASTIAN": { "Sociolla": 210_000_000, "Thai": 85_000_000, "Diosys": 175_000_000, "Y2000": 65_000_000 },
    "GANI": { "Sociolla": 80_000_000, "Thai": 85_000_000, "The Face": 200_000_000, "Yu Chun Mei": 175_000_000, "Milano": 20_000_000, "Elizabeth Rose": 20_000_000, "Walnutt": 10_000_000 },
    "BAYU": { "Diosys": 170_000_000, "Y2000": 50_000_000 },
    "YOGI": { "The Face": 400_000_000, "Yu Chun Mei": 275_000_000, "Milano": 30_000_000 },
    "LYDIA": { "Birth Beyond": 120_000_000 },
    "MITHA": { "Maskit": 30_000_000, "Rose All Day": 30_000_000, "Claresta": 350_000_000, "OtwooO": 200_000_000 }
}

SUPERVISOR_TOTAL_TARGETS = {k: sum(v.values()) for k, v in TARGET_DATABASE.items()}
TARGET_NASIONAL_VAL = sum(SUPERVISOR_TOTAL_TARGETS.values())

BRAND_ALIASES = {
    "Diosys": ["DIOSYS", "DYOSIS", "DIO"], "Y2000": ["Y2000", "Y 2000", "Y-2000"],
    "Masami": ["MASAMI", "JAYA"], "Cassandra": ["CASSANDRA", "CASANDRA"],
    "Thai": ["THAI"], "Inesia": ["INESIA"], "Honor": ["HONOR"], "Vlagio": ["VLAGIO"],
    "Sociolla": ["SOCIOLLA"], "Skin1004": ["SKIN1004", "SKIN 1004"], "Oimio": ["OIMIO"],
    "Clinelle": ["CLINELLE", "CLIN"], "Ren & R & L": ["REN", "R & L", "R&L"], "Sekawan": ["SEKAWAN", "AINIE"],
    "Mad For Make Up": ["MAD FOR", "MAKE UP", "MAJU", "MADFORMAKEUP"], "Avione": ["AVIONE"],
    "SYB": ["SYB"], "Satto": ["SATTO"], "Liora": ["LIORA"], "Mykonos": ["MYKONOS"],
    "Somethinc": ["SOMETHINC"], "Gloow & Be": ["GLOOW", "GLOOWBI", "GLOW", "GLOWBE"],
    "Artist Inc": ["ARTIST", "ARTIS"], "Bonavie": ["BONAVIE"], "Whitelab": ["WHITELAB"],
    "Goute": ["GOUTE"], "Dorskin": ["DORSKIN"], "Javinci": ["JAVINCI"], "Madam G": ["MADAM", "MADAME"],
    "Careso": ["CARESO"], "Newlab": ["NEWLAB"], "Mlen": ["MLEN"], "Walnutt": ["WALNUT", "WALNUTT"],
    "Elizabeth Rose": ["ELIZABETH"], "OtwooO": ["OTWOOO", "O.TWO.O", "O TWO O"],
    "Saviosa": ["SAVIOSA"], "The Face": ["THE FACE", "THEFACE"], "Yu Chun Mei": ["YU CHUN MEI", "YCM"],
    "Milano": ["MILANO"], "Remar": ["REMAR"], "Beautica": ["BEAUTICA"], "Maskit": ["MASKIT"],
    "Claresta": ["CLARESTA"], "Birth Beyond": ["BIRTH"], "Rose All Day": ["ROSE ALL DAY"]
}

SALES_MAPPING = {
    "WIRA VG": "WIRA", "WIRA - VG": "WIRA", "WIRA VLAGIO": "WIRA", "WIRA HONOR": "WIRA", "WIRA - HONOR": "WIRA", "WIRA HR": "WIRA", "WIRA SYB": "WIRA", "WIRA - SYB": "WIRA", "WIRA SOMETHINC": "WIRA", "PMT-WIRA": "WIRA", "WIRA ELIZABETH": "WIRA", "WIRA WALNUTT": "WIRA", "WIRA ELZ": "WIRA",
    "HAMZAH VG": "HAMZAH", "HAMZAH - VG": "HAMZAH", "HAMZAH HONOR": "HAMZAH", "HAMZAH - HONOR": "HAMZAH", "HAMZAH SYB": "HAMZAH", "HAMZAH AV": "HAMZAH", "HAMZAH AINIE": "HAMZAH", "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH",
    "FERI VG": "FERI", "FERI - VG": "FERI", "FERI HONOR": "FERI", "FERI - HONOR": "FERI", "FERI THAI": "FERI", "FERI - INESIA": "FERI",
    "YOGI TF": "YOGI", "YOGI THE FACE": "YOGI", "YOGI YCM": "YOGI", "YOGI MILANO": "YOGI", "MILANO - YOGI": "YOGI", "YOGI REMAR": "YOGI",
    "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI", "GANI TF": "GANI", "GANI - YCM": "GANI", "GANI - MILANO": "GANI", "GANI - HONOR": "GANI", "GANI - VG": "GANI", "GANI - TH": "GANI", "GANI INESIA": "GANI", "GANI - KSM": "GANI", "SSL - GANI": "GANI", "GANI ELIZABETH": "GANI", "GANI WALNUTT": "GANI",
    "MITHA MASKIT": "MITHA", "MITHA RAD": "MITHA", "MITHA CLA": "MITHA", "MITHA OT": "MITHA", "MAS - MITHA": "MITHA", "SSL BABY - MITHA ": "MITHA", "SAVIOSA - MITHA": "MITHA", "MITHA ": "MITHA",
    "LYDIA KITO": "LYDIA", "LYDIA K": "LYDIA", "LYDIA BB": "LYDIA",
    "NOVI AINIE": "NOVI", "NOVI AV": "NOVI", "NOVI DAN RAFFI": "NOVI", "NOVI & RAFFI": "NOVI", "RAFFI": "NOVI", "RAFI": "NOVI", "RAPI": "NOVI",
    "ROZY AINIE": "ROZY", "ROZY AV": "ROZY",
    "DANI AINIE": "DANI", "DANI AV": "DANI", "DANI SEKAWAN": "DANI",
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG", "MADONG MYK": "MADONG",
    "RISKA AV": "RISKA", "RISKA BN": "RISKA", "RISKA CRS": "RISKA", "RISKA E-WL": "RISKA", "RISKA JV": "RISKA", "RISKA REN": "RISKA", "RISKA R&L": "RISKA", "RISKA SMT": "RISKA", "RISKA ST": "RISKA", "RISKA SYB": "RISKA", "RISKA - MILANO": "RISKA", "RISKA TF": "RISKA", "RISKA - YCM": "RISKA", "RISKA HONOR": "RISKA", "RISKA - VG": "RISKA", "RISKA TH": "RISKA", "RISKA - INESIA": "RISKA", "SSL - RISKA": "RISKA", "SKIN - RIZKA": "RISKA",
    "ADE CLA": "ADE", "ADE CRS": "ADE", "GLOOW - ADE": "ADE", "ADE JAVINCI": "ADE", "ADE JV": "ADE", "ADE SVD": "ADE", "ADE RAM PUTRA M.GIE": "ADE", "ADE - MLEN1": "ADE", "ADE NEWLAB": "ADE", "DORS - ADE": "ADE",
    "FANDI - BONAVIE": "FANDI", "DORS- FANDI": "FANDI", "FANDY CRS": "FANDI", "FANDI AFDILLAH": "FANDI", "FANDY WL": "FANDI", "GLOOW - FANDY": "FANDI", "FANDI - GOUTE": "FANDI", "FANDI MG": "FANDI", "FANDI - NEWLAB": "FANDI", "FANDY - YCM": "FANDI", "FANDY YLA": "FANDI", "FANDI JV": "FANDI", "FANDI MLEN": "FANDI",
    "NAUFAL - JAVINCI": "NAUFAL", "NAUFAL JV": "NAUFAL", "NAUFAL SVD": "NAUFAL",
    "RIZKI JV": "RIZKI", "RIZKI SVD": "RIZKI",
    "SAHRUL JAVINCI": "SAHRUL", "SAHRUL TF": "SAHRUL", "SAHRUL JV": "SAHRUL", "GLOOW - SAHRUL": "SAHRUL",
    "SANTI BONAVIE": "SANTI", "SANTI WHITELAB": "SANTI", "SANTI GOUTE": "SANTI",
    "DWI CRS": "DWI", "DWI NLAB": "DWI",
    "ASWIN ARTIS": "ASWIN", "ASWIN AI": "ASWIN",
    "BASTIAN CASANDRA": "BASTIAN", "SSL- BASTIAN": "BASTIAN", "SKIN - BASTIAN": "BASTIAN", "BASTIAN - HONOR": "BASTIAN", "BASTIAN - VG": "BASTIAN", "BASTIAN TH": "BASTIAN", "BASTIAN YL": "BASTIAN", "BASTIAN YL-DIO CAT": "BASTIAN", "BASTIAN SHMP": "BASTIAN", "BASTIAN-DIO 45": "BASTIAN",
    "SSL - DEVI": "DEVI", "SKIN - DEVI": "DEVI", "DEVI Y- DIOSYS CAT": "DEVI", "DEVI YL": "DEVI", "DEVI SHMP": "DEVI", "DEVI-DIO 45": "DEVI", "DEVI YLA": "DEVI",
    "SSL- BAYU": "BAYU", "SKIN - BAYU": "BAYU", "BAYU-DIO 45": "BAYU", "BAYU YL-DIO CAT": "BAYU", "BAYU SHMP": "BAYU", "BAYU YL": "BAYU",
    "HABIBI - FZ": "HABIBI", "HABIBI SYB": "HABIBI", "HABIBI TH": "HABIBI",
    "GLOOW - LISMAN": "LISMAN", "LISMAN - NEWLAB": "LISMAN",
    "WILLIAM BTC": "WILLIAM", "WILLI - ROS": "WILLIAM", "WILLI - WAL": "WILLIAM",
    "RINI JV": "RINI", "RINI SYB": "RINI",
    "FAUZIAH CLA": "FAUZIAH", "FAUZIAH ST": "FAUZIAH",
    "MARIANA CLIN": "MARIANA", "JAYA - MARIANA": "MARIANA"
}

# ==========================================
# 3. CORE LOGIC
# ==========================================

def get_current_time_wib():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

def format_idr(value):
    try:
        return f"Rp {value:,.0f}".replace(",", ".")
    except:
        return "Rp 0"

def check_password(plain_password, stored_password):
    if not stored_password.startswith("$2b$"):
        return plain_password == stored_password
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')
    return bcrypt.checkpw(plain_password.encode('utf-8'), stored_password)

def render_custom_progress(title, current, target):
    if target == 0: target = 1
    pct = (current / target) * 100
    visual_pct = min(pct, 100)
    
    if pct < 50: bar_color = "linear-gradient(90deg, #e74c3c, #c0392b)" 
    elif 50 <= pct < 80: bar_color = "linear-gradient(90deg, #f1c40f, #f39c12)" 
    else: bar_color = "linear-gradient(90deg, #2ecc71, #27ae60)" 
    
    st.markdown(f"""
    <div style="margin-bottom: 20px; background-color: #fcfcfc; padding: 15px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-weight: 700; font-size: 15px; color: #34495e;">{title}</span>
            <span style="font-weight: 600; color: #555; font-size: 14px;">{format_idr(current)} <span style="color:#999; font-weight:normal;">/ {format_idr(target)}</span></span>
        </div>
        <div style="width: 100%; background-color: #ecf0f1; border-radius: 20px; height: 26px; position: relative; overflow: hidden;">
            <div style="width: {visual_pct}%; background: {bar_color}; height: 100%; border-radius: 20px; transition: width 0.8s ease;"></div>
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                        display: flex; align-items: center; justify-content: center;
                        z-index: 10; font-weight: 800; font-size: 13px; color: #222;
                        text-shadow: 0px 0px 4px #fff;">
                {pct:.1f}%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    try:
        url = st.secrets["gsheet"]["url"]
    except:
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"

    try:
        url_with_ts = f"{url}&t={int(time.time())}"
        df = pd.read_csv(url_with_ts, dtype=str)
    except Exception as e:
        return None
    
    df.columns = df.columns.str.strip()
    required_cols = ['Penjualan', 'Merk', 'Jumlah', 'Tanggal']
    if not all(col in df.columns for col in required_cols):
        return None
    
    # --- AUTO DETECT KOLOM FAKTUR ---
    faktur_col = None
    for col in df.columns:
        if 'faktur' in col.lower() or 'bukti' in col.lower() or 'invoice' in col.lower():
            faktur_col = col
            break
    if faktur_col: df = df.rename(columns={faktur_col: 'No Faktur'})
    
    # --- CLEANING SAMPAH ---
    if 'Nama Outlet' in df.columns:
        df = df[~df['Nama Outlet'].astype(str).str.contains(r'Total|Jumlah|Subtotal|Grand|Rekap', case=False, regex=True, na=False)]
        df = df[df['Nama Outlet'].astype(str).str.strip() != ''] 
        df = df[df['Nama Outlet'].astype(str).str.lower() != 'nan']

    if 'Nama Barang' in df.columns:
        df = df[~df['Nama Barang'].astype(str).str.contains(r'Total|Jumlah', case=False, regex=True, na=False)]
        df = df[df['Nama Barang'].astype(str).str.strip() != ''] 

    # --- NORMALISASI SALES ---
    df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(SALES_MAPPING)
    valid_sales_names = list(INDIVIDUAL_TARGETS.keys())
    valid_sales_names.extend(["MADONG", "LISMAN", "AKBAR", "WILLIAM"]) 
    df.loc[~df['Penjualan'].isin(valid_sales_names), 'Penjualan'] = 'Non-Sales'
    df['Penjualan'] = df['Penjualan'].astype('category')

    # --- NORMALISASI BRAND ---
    def normalize_brand(raw_brand):
        raw_upper = str(raw_brand).upper()
        for target_brand, keywords in BRAND_ALIASES.items():
            for keyword in keywords:
                if keyword in raw_upper: return target_brand
        return raw_brand
    df['Merk'] = df['Merk'].apply(normalize_brand).astype('category')
    
    # --- NUMERIC CLEANING (FIX FOR SMALL DISCREPANCY) ---
    # 1. Hapus titik ribuan (misal 1.036.000 -> 1036000)
    df['Jumlah'] = df['Jumlah'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    # 2. Hapus karakter non-angka
    df['Jumlah'] = df['Jumlah'].astype(str).str.replace(r'[^0-9.-]', '', regex=True)
    # 3. Konversi ke Float
    df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    # 4. Hapus Baris dengan Jumlah 0 atau Negatif Aneh (Opsional, sesuaikan kebutuhan)
    df = df[df['Jumlah'] != 0]

    # --- DATE CLEANING ---
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

    # Filter Tahun (Hanya Tahun Ini & Kemarin)
    current_year = datetime.datetime.now().year
    df = df[(df['Tanggal'].dt.year >= current_year - 1) & (df['Tanggal'].dt.year <= current_year + 1)]
    
    cols_to_convert = ['Kota', 'Nama Outlet', 'Nama Barang', 'No Faktur']
    for col in cols_to_convert:
        if col in df.columns: df[col] = df[col].astype(str).str.strip()
            
    return df

# ==========================================
# 4. MAIN DASHBOARD LOGIC
# ==========================================

def login_page():
    st.markdown("<br><br><h1 style='text-align: center;'>🦅 Executive Command Center</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Masuk Sistem", use_container_width=True)
                
                if submitted:
                    try:
                        if username in st.secrets["users"]:
                            user_data = st.secrets["users"][username]
                            if check_password(password, user_data["password"]):
                                st.session_state['logged_in'] = True
                                st.session_state['role'] = user_data["role"]
                                st.session_state['sales_name'] = user_data["name"]
                                st.success("Login Berhasil!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Password Salah.")
                        else:
                            st.error("Username tidak ditemukan.")
                    except FileNotFoundError:
                        st.error("Konfigurasi user belum ditemukan.")

def main_dashboard():
    with st.sidebar:
        st.write("## 👤 User Profile")
        st.info(f"**{st.session_state['sales_name']}**\n\nRole: {st.session_state['role'].upper()}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
        st.markdown("---")
        st.caption(f"Last Updated: {get_current_time_wib().strftime('%H:%M:%S')} WIB")
            
    df = load_data()
    if df is None or df.empty:
        st.error("⚠️ Gagal memuat data! Periksa koneksi internet atau Link Google Sheet.")
        return

    # --- FILTER ---
    st.sidebar.subheader("📅 Filter Periode")
    col_p1, col_p2 = st.sidebar.columns(2)
    if col_p1.button("Bulan Ini", use_container_width=True):
        today = datetime.date.today()
        st.session_state['start_date'] = today.replace(day=1)
        st.session_state['end_date'] = today
    
    if 'start_date' not in st.session_state:
        st.session_state['start_date'] = df['Tanggal'].max().date().replace(day=1)
        st.session_state['end_date'] = df['Tanggal'].max().date()

    date_range = st.sidebar.date_input("Rentang Waktu", [st.session_state['start_date'], st.session_state['end_date']])

    # --- SCOPE LOGIC ---
    role = st.session_state['role']
    my_name = st.session_state['sales_name']
    my_name_key = my_name.strip().upper()
    is_supervisor_account = my_name_key in TARGET_DATABASE
    target_sales_filter = "SEMUA"

    if role in ['manager', 'direktur']:
        sales_list = ["SEMUA"] + sorted(list(df['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Pantau Kinerja Sales:", sales_list)
        df_scope_all = df if target_sales_filter == "SEMUA" else df[df['Penjualan'] == target_sales_filter]
            
    elif is_supervisor_account:
        my_brands = TARGET_DATABASE[my_name_key].keys()
        df_spv_raw = df[df['Merk'].isin(my_brands)]
        team_list = sorted(list(df_spv_raw['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Filter Tim (Brand Anda):", ["SEMUA"] + team_list)
        df_scope_all = df_spv_raw if target_sales_filter == "SEMUA" else df_spv_raw[df_spv_raw['Penjualan'] == target_sales_filter]
        
    else: # Sales Biasa
        target_sales_filter = my_name 
        df_scope_all = df[df['Penjualan'] == my_name]

    # --- APPLY FILTER ---
    with st.sidebar.expander("🔍 Filter Lanjutan", expanded=False):
        unique_brands = sorted(df_scope_all['Merk'].unique())
        pilih_merk = st.multiselect("Pilih Merk", unique_brands)
        if pilih_merk: df_scope_all = df_scope_all[df_scope_all['Merk'].isin(pilih_merk)]
        unique_outlets = sorted(df_scope_all['Nama Outlet'].unique())
        pilih_outlet = st.multiselect("Pilih Outlet", unique_outlets)
        if pilih_outlet: df_scope_all = df_scope_all[df_scope_all['Nama Outlet'].isin(pilih_outlet)]

    if len(date_range) == 2:
        start_date, end_date = date_range
        df_active = df_scope_all[(df_scope_all['Tanggal'].dt.date >= start_date) & (df_scope_all['Tanggal'].dt.date <= end_date)]
        ref_date = end_date
    else:
        df_active = df_scope_all
        ref_date = df['Tanggal'].max().date()

    # --- KPI METRICS ---
    st.title("🚀 Executive Dashboard")
    st.markdown("---")
    
    current_omset_total = df_active['Jumlah'].sum()
    
    # --- LOGIKA KENAIKAN/PENURUNAN ---
    if len(date_range) == 2 and start_date != end_date:
        delta_days = (end_date - start_date).days + 1
        prev_end = start_date - datetime.timedelta(days=1)
        prev_start = prev_end - datetime.timedelta(days=delta_days - 1)
        
        omset_prev_period = df_scope_all[(df_scope_all['Tanggal'].dt.date >= prev_start) & (df_scope_all['Tanggal'].dt.date <= prev_end)]['Jumlah'].sum()
        delta_val = current_omset_total - omset_prev_period
        delta_label = f"vs {prev_start.strftime('%d %b')} - {prev_end.strftime('%d %b')}"
    else:
        target_date = end_date if len(date_range) == 2 else df['Tanggal'].max().date()
        prev_date = target_date - datetime.timedelta(days=1)
        
        omset_prev = df_scope_all[df_scope_all['Tanggal'].dt.date == prev_date]['Jumlah'].sum()
        delta_val = current_omset_total - omset_prev
        delta_label = f"vs Kemarin ({prev_date.strftime('%d %b')})"

    c1, c2, c3 = st.columns(3)
    
    # --- LOGIKA INDIKATOR WARNA ---
    delta_str = format_idr(abs(delta_val))
    if delta_val < 0:
        delta_str = f"- {delta_str}"
        delta_color = "normal" 
    else:
        delta_str = f"+ {delta_str}"
        delta_color = "normal" 

    c1.metric(label="💰 Total Omset", value=format_idr(current_omset_total), delta=f"{delta_str} ({delta_label})", delta_color=delta_color)
    
    c2.metric("🏪 Outlet Aktif", f"{df_active['Nama Outlet'].nunique()}")
    
    if 'No Faktur' in df_active.columns:
        transaksi_count = df_active['No Faktur'].nunique()
    else:
        transaksi_count = len(df_active)
    c3.metric("🧾 Transaksi", f"{transaksi_count}")

    # --- TARGET MONITOR ---
    if role in ['manager', 'direktur'] or is_supervisor_account or target_sales_filter in INDIVIDUAL_TARGETS:
        st.markdown("### 🎯 Target Monitor")
        
        if target_sales_filter == "SEMUA":
            realisasi_nasional = df[(df['Tanggal'].dt.date >= start_date) & (df['Tanggal'].dt.date <= end_date)]['Jumlah'].sum() if len(date_range)==2 else df['Jumlah'].sum()
            render_custom_progress("🏢 Target Nasional (All Team)", realisasi_nasional, TARGET_NASIONAL_VAL)
            
            if is_supervisor_account:
                target_pribadi = SUPERVISOR_TOTAL_TARGETS.get(my_name_key, 0)
                my_brands_list = TARGET_DATABASE[my_name_key].keys()
                df_spv_only = df[df['Merk'].isin(my_brands_list)]
                if len(date_range)==2: df_spv_only = df_spv_only[(df_spv_only['Tanggal'].dt.date >= start_date) & (df_spv_only['Tanggal'].dt.date <= end_date)]
                render_custom_progress(f"👤 Target Tim {my_name}", df_spv_only['Jumlah'].sum(), target_pribadi)
        
        elif target_sales_filter in INDIVIDUAL_TARGETS:
            st.info(f"📋 Target Spesifik: **{target_sales_filter}**")
            targets_map = INDIVIDUAL_TARGETS[target_sales_filter]
            for brand, target_val in targets_map.items():
                realisasi_brand = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                render_custom_progress(f"👤 {brand} - {target_sales_filter}", realisasi_brand, target_val)
        else:
            st.warning(f"Sales **{target_sales_filter}** tidak memiliki target individu spesifik.")
        st.markdown("---")

    # --- ANALYTICS TABS ---
    t1, t2, t3, t4 = st.tabs(["📊 Target Detail", "📈 Tren Harian", "🏆 Top Performance", "📋 Data Rincian"])
    
    with t1:
        if target_sales_filter == "SEMUA":
            st.subheader("Rapor Target per Brand")
            summary_data = []
            target_loop = TARGET_DATABASE.items() if role in ['manager', 'direktur'] else {my_name_key: TARGET_DATABASE[my_name_key]}.items()
            for spv, brands_dict in target_loop:
                for brand, target in brands_dict.items():
                    realisasi = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                    pct_val = (realisasi / target) * 100 if target > 0 else 0
                    summary_data.append({
                        "Supervisor": spv, "Brand": brand, "Target": format_idr(target), 
                        "Realisasi": format_idr(realisasi), "Ach (%)": f"{pct_val:.0f}%", 
                        "Pencapaian": pct_val / 100, "Ach (Detail %)": pct_val
                    })
            df_summ = pd.DataFrame(summary_data)
            def highlight_row(row): return [f'background-color: {"#d4edda" if row["Ach (Detail %)"] >= 80 else "#f8d7da"}; color: #333'] * len(row)
            st.dataframe(df_summ.style.apply(highlight_row, axis=1).hide(axis="columns", subset=['Ach (Detail %)']), use_container_width=True, hide_index=True, column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)})
        elif target_sales_filter in INDIVIDUAL_TARGETS:
             st.info("Lihat progress bar di atas untuk detail target individu.")
        else:
            sales_brands = df_active['Merk'].unique()
            indiv_data = []
            for brand in sales_brands:
                owner, target = "-", 0
                for spv, b_dict in TARGET_DATABASE.items():
                    if brand in b_dict: owner, target = spv, b_dict[brand]; break
                if target > 0:
                    real = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                    pct = (real/target)*100
                    indiv_data.append({"Brand": brand, "Owner": owner, "Target Tim": format_idr(target), "Kontribusi": format_idr(real), "Ach (%)": f"{pct:.1f}%", "Pencapaian": pct/100})
            if indiv_data: st.dataframe(pd.DataFrame(indiv_data), use_container_width=True, hide_index=True, column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)})
            else: st.warning("Tidak ada data target brand.")

    with t2:
        st.subheader("📈 Tren Harian")
        if not df_active.empty:
            daily = df_active.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig_line = px.line(daily, x='Tanggal', y='Jumlah', markers=True)
            fig_line.update_traces(line_color='#2980b9', line_width=3)
            st.plotly_chart(fig_line, use_container_width=True)

    with t3:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📦 Top 10 Produk")
            top_prod = df_active.groupby('Nama Barang')['Jumlah'].sum().nlargest(10).reset_index()
            fig_bar = px.bar(top_prod, x='Jumlah', y='Nama Barang', orientation='h', text_auto='.2s')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            st.subheader("🏪 Top 10 Outlet")
            top_out = df_active.groupby('Nama Outlet')['Jumlah'].sum().nlargest(10).reset_index()
            fig_out = px.bar(top_out, x='Jumlah', y='Nama Outlet', orientation='h', text_auto='.2s', color_discrete_sequence=['#27ae60'])
            fig_out.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_out, use_container_width=True)

    with t4:
        st.subheader("📋 Rincian Transaksi Lengkap")
        
        with st.expander("🕵️‍♂️ DETEKTIF DATA: Cek Transaksi Terbesar (Cari Angka Aneh)"):
            st.warning("Gunakan tabel ini untuk mencari baris 'Total' yang menyusup.")
            st.dataframe(
                df_active.nlargest(10, 'Jumlah')[['Tanggal', 'Nama Outlet', 'Nama Barang', 'Jumlah']],
                use_container_width=True
            )

        cols_to_show = ['Tanggal', 'No Faktur', 'Nama Outlet', 'Merk', 'Nama Barang', 'Jumlah', 'Penjualan']
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

if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()

