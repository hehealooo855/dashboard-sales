import streamlit as st
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
        "Ren & R & L": 20_000_000, 
        "Sekawan": 600_000_000, 
        "Avione": 300_000_000, 
        "SYB": 150_000_000, 
        "Mad For Make Up": 25_000_000, 
        "Satto": 500_000_000,
        "Mykonos": 20_000_000, 
        "Somethinc": 1_200_000_000, 
        "Honor": 125_000_000, 
        "Vlagio": 75_000_000
    }
}

INDIVIDUAL_TARGETS = {
    # --- TIM WIRA DLL ---
    "WIRA": { "Somethinc": 660_000_000, "SYB": 75_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000 },
    "HAMZAH": { "Somethinc": 540_000_000, "SYB": 75_000_000, "Sekawan": 60_000_000, "Avione": 60_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000 },
    "ROZY": { "Sekawan": 100_000_000, "Avione": 100_000_000 },
    "NOVI": { "Sekawan": 90_000_000, "Avione": 90_000_000 },
    "DANI": { "Sekawan": 50_000_000, "Avione": 50_000_000 },

    # --- TIM LISMAN ---
    "NAUFAL": { "Javinci": 550_000_000 },
    "RIZKI": { "Javinci": 450_000_000 },
    "ADE": { 
        "Javinci": 180_000_000, "Careso": 20_000_000, "Newlab": 75_000_000, 
        "Gloow & Be": 60_000_000, "Dorskin": 10_000_000, "Mlen": 50_000_000 
    },
    "FANDI": { 
        "Javinci": 40_000_000, "Careso": 20_000_000, "Newlab": 75_000_000, 
        "Gloow & Be": 60_000_000, "Dorskin": 10_000_000, "Whitelab": 75_000_000,
        "Bonavie": 25_000_000, "Goute": 25_000_000, "Mlen": 50_000_000
    },
    "SYAHRUL": { "Javinci": 40_000_000, "Careso": 10_000_000, "Gloow & Be": 10_000_000 },
    "RISKA": { 
        "Javinci": 40_000_000, 
        "Sociolla": 190_000_000, "Thai": 30_000_000 
    },
    "DWI": { "Careso": 350_000_000 },
    "SANTI": { "Whitelab": 75_000_000, "Bonavie": 25_000_000, "Goute": 25_000_000 },
    "ASWIN": { "Artist Inc": 130_000_000 },

    # --- TIM AKBAR ---
    "DEVI": { "Sociolla": 120_000_000, "Diosys": 175_000_000, "Y2000": 65_000_000 },
    "BASTIAN": { "Sociolla": 210_000_000, "Thai": 85_000_000, "Diosys": 175_000_000, "Y2000": 65_000_000 },
    "GANI": { "Sociolla": 80_000_000, "Thai": 85_000_000 },
    "FERI": { "Thai": 200_000_000, "Honor": 50_000_000, "Vlagio": 30_000_000 },
    "BAYU": { "Diosys": 170_000_000, "Y2000": 50_000_000 }
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
    # EXISTING
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG", "ROZY AINIE": "ROZY", 
    "NOVI AINIE": "NOVI", "NOVI AV": "NOVI", "NOVI DAN RAFFI": "NOVI", "NOVI & RAFFI": "NOVI", "RAFFI": "NOVI",
    "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH", "HAMZA AV": "HAMZAH", "HAMZAH SYB": "HAMZAH",
    "DANI AINIE": "DANI", "DANI AV": "DANI", "DANI SEKAWAN": "DANI",
    
    # RISKA (Mixed)
    "RISKA AV": "RISKA", "RISKA BN": "RISKA", "RISKA CRS": "RISKA", "RISKA E-WL": "RISKA", 
    "RISKA JV": "RISKA", "RISKA REN": "RISKA", "RISKA R&L": "RISKA", "RISKA SMT": "RISKA", 
    "RISKA ST": "RISKA", "RISKA SYB": "RISKA", "RISKA - MILANO": "RISKA", "RISKA TF": "RISKA",
    "RISKA - YCM": "RISKA", "RISKA HONOR": "RISKA", "RISKA - VG": "RISKA", "RISKA TH": "RISKA", 
    "RISKA - INESIA": "RISKA", "SSL - RISKA": "RISKA", "SKIN - RIZKA": "RISKA", 

    # ADE
    "ADE CLA": "ADE", "ADE CRS": "ADE", "GLOOW - ADE": "ADE", "ADE JAVINCI": "ADE", "ADE JV": "ADE",
    "ADE SVD": "ADE", "ADE RAM PUTRA M.GIE": "ADE", "ADE - MLEN1": "ADE", "ADE NEWLAB": "ADE", "DORS - ADE": "ADE",

    # FANDI
    "FANDI - BONAVIE": "FANDI", "DORS- FANDI": "FANDI", "FANDY CRS": "FANDI", "FANDI AFDILLAH": "FANDI", 
    "FANDY WL": "FANDI", "GLOOW - FANDY": "FANDI", "FANDI - GOUTE": "FANDI", "FANDI MG": "FANDI", 
    "FANDI - NEWLAB": "FANDI", "FANDY - YCM": "FANDI", "FANDY YLA": "FANDI", "FANDI JV": "FANDI", "FANDI MLEN": "FANDI",
    
    # GANI
    "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI", "GANI TF": "GANI", 
    "GANI - YCM": "GANI", "GANI - MILANO": "GANI", "GANI - HONOR": "GANI", "GANI - VG": "GANI", 
    "GANI - TH": "GANI", "GANI INESIA": "GANI", "GANI - KSM": "GANI", "SSL - GANI": "GANI",

    # BASTIAN
    "BASTIAN CASANDRA": "BASTIAN", "SSL- BASTIAN": "BASTIAN", "SKIN - BASTIAN": "BASTIAN", 
    "BASTIAN - HONOR": "BASTIAN", "BASTIAN - VG": "BASTIAN", "BASTIAN TH": "BASTIAN", 
    "BASTIAN YL": "BASTIAN", "BASTIAN YL-DIO CAT": "BASTIAN", "BASTIAN SHMP": "BASTIAN",
    "BASTIAN-DIO 45": "BASTIAN",

    # YOGI & FERI
    "YOGI REMAR": "YOGI", "YOGI THE FACE": "YOGI", "YOGI YCM": "YOGI", "MILANO - YOGI": "YOGI",
    "FERI - HONOR": "FERI", "FERI - VG": "FERI", "FERI THAI": "FERI", "FERI - INESIA": "FERI",

    # DEVI & BAYU
    "SSL - DEVI": "DEVI", "SKIN - DEVI": "DEVI", "DEVI Y- DIOSYS CAT": "DEVI",
    "DEVI YL": "DEVI", "DEVI SHMP": "DEVI", "DEVI-DIO 45": "DEVI", "DEVI YLA": "DEVI",
    "SSL- BAYU": "BAYU", "SKIN - BAYU": "BAYU", "BAYU-DIO 45": "BAYU", "BAYU YL-DIO CAT": "BAYU", 
    "BAYU SHMP": "BAYU", "BAYU YL": "BAYU", 

    # OTHERS
    "PMT-WIRA": "WIRA", "WIRA SOMETHINC": "WIRA", "WIRA SYB": "WIRA", 
    "SANTI BONAVIE": "SANTI", "SANTI WHITELAB": "SANTI", "SANTI GOUTE": "SANTI",
    "HABIBI - FZ": "HABIBI", "HABIBI SYB": "HABIBI", "HABIBI TH": "HABIBI", "MAS - MITHA": "MITHA",
    "MITHA ": "MITHA", "SSL BABY - MITHA ": "MITHA", "SAVIOSA - MITHA": "MITHA",
    "GLOOW - LISMAN": "LISMAN", "LISMAN - NEWLAB": "LISMAN", "WILLIAM BTC": "WILLIAM",
    "WILLI - ROS": "WILLIAM", "WILLI - WAL": "WILLIAM", "NAUFAL - JAVINCI": "NAUFAL", "NAUFAL JV": "NAUFAL",
    "NAUFAL SVD": "NAUFAL", "RIZKI JV": "RIZKI", "RIZKI SVD": "RIZKI", "RINI JV": "RINI",
    "RINI SYB": "RINI", "SAHRUL JAVINCI": "SAHRUL", "SAHRUL TF": "SAHRUL", "SAHRUL JV": "SAHRUL", "GLOOW - SAHRUL": "SAHRUL",
    "DWI CRS": "DWI", "DWI NLAB": "DWI", 
    "FAUZIAH CLA": "FAUZIAH", "FAUZIAH ST": "FAUZIAH", "MARIANA CLIN": "MARIANA",
    "JAYA - MARIANA": "MARIANA", "ASWIN ARTIS": "ASWIN", "ASWIN AI": "ASWIN"
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
    # Mencari kolom yang mengandung kata 'faktur' atau 'bukti' dan mengubahnya jadi 'No Faktur'
    faktur_col = None
    for col in df.columns:
        if 'faktur' in col.lower() or 'bukti' in col.lower() or 'invoice' in col.lower():
            faktur_col = col
            break
    
    if faktur_col:
        df = df.rename(columns={faktur_col: 'No Faktur'})
    
    # --- CLEANING SAMPAH ---
    if 'Nama Outlet' in df.columns:
        df = df[~df['Nama Outlet'].astype(str).str.contains(r'Total|Jumlah|Subtotal|Grand|Rekap', case=False, regex=True, na=False)]
        df = df[df['Nama Outlet'].astype(str).str.strip() != ''] 
        df = df[df['Nama Outlet'].astype(str).str.lower() != 'nan']

    if 'Nama Barang' in df.columns:
        df = df[~df['Nama Barang'].astype(str).str.contains(r'Total|Jumlah', case=False, regex=True, na=False)]
        df = df[df['Nama Barang'].astype(str).str.strip() != ''] 

    # --- NORMALISASI ---
    df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(SALES_MAPPING).astype('category')
    
    def normalize_brand(raw_brand):
        raw_upper = str(raw_brand).upper()
        for target_brand, keywords in BRAND_ALIASES.items():
            for keyword in keywords:
                if keyword in raw_upper: return target_brand
        return raw_brand
    df['Merk'] = df['Merk'].apply(normalize_brand).astype('category')
    
    # --- NUMERIC CLEANING ---
    df['Jumlah'] = df['Jumlah'].astype(str).str.replace(r'[^-\d.]', '', regex=True)
    df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
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

    current_year = datetime.datetime.now().year
    df = df[(df['Tanggal'].dt.year >= current_year - 1) & (df['Tanggal'].dt.year <= current_year + 1)]
    
    # --- CONVERT STRING FOR METADATA ---
    cols_to_convert = ['Kota', 'Nama Outlet', 'Nama Barang', 'No Faktur']
    for col in cols_to_convert:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
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
    st.markdown("<br><br><h1 style='text-align: center;'>🦅 Executive Command Center</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Masuk Sistem", use_container_width=True)
                
                if submitted:
                    users = load_users()
                    if users.empty:
                        st.error("Database user (users.csv) tidak ditemukan.")
                    else:
                        match = users[(users['username'] == username) & (users['password'] == password)]
                        if not match.empty:
                            st.session_state['logged_in'] = True
                            st.session_state['role'] = match.iloc[0]['role']
                            st.session_state['sales_name'] = match.iloc[0]['sales_name']
                            st.success("Login Berhasil! Mengalihkan...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Username atau Password salah.")

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
    omset_hari_ini = df_scope_all[df_scope_all['Tanggal'].dt.date == ref_date]['Jumlah'].sum()
    prev_date = ref_date - datetime.timedelta(days=1)
    omset_kemarin = df_scope_all[df_scope_all['Tanggal'].dt.date == prev_date]['Jumlah'].sum()
    delta_val = omset_hari_ini - omset_kemarin
    
    c1, c2, c3 = st.columns(3)
    
    # --- LOGIKA INDIKATOR WARNA (PERBAIKAN) ---
    delta_str = format_idr(delta_val)
    if delta_val < 0:
        # Pindahkan tanda minus ke depan agar terbaca Streamlit sebagai penurunan (Merah)
        # format_idr menghasilkan "Rp -100.000", kita ubah jadi "- Rp 100.000"
        delta_str = delta_str.replace("Rp -", "- Rp ")
    elif delta_val > 0:
        # Tambahkan plus agar terbaca sebagai kenaikan (Hijau)
        delta_str = f"+ {delta_str}"

    c1.metric(label="💰 Total Omset (Periode)", value=format_idr(current_omset_total), delta=f"{delta_str} (vs {prev_date.strftime('%d %b')})")
    
    c2.metric("🏪 Outlet Aktif", f"{df_active['Nama Outlet'].nunique()}")
    
    # --- HITUNG TRANSAKSI (UNIQUE FAKTUR) ---
    if 'No Faktur' in df_active.columns:
        valid_faktur = df_active['No Faktur'].astype(str)
        valid_faktur = valid_faktur[~valid_faktur.isin(['nan', 'None', '', '-', '0', 'None', '.'])]
        valid_faktur = valid_faktur[valid_faktur.str.len() > 2]
        transaksi_count = valid_faktur.nunique()
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
