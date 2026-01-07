import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import time
import re

# --- KONFIGURASI HALAMAN (WORLD CLASS SETUP) ---
st.set_page_config(
    page_title="Executive Sales Command Center", 
    layout="wide", 
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
    div[data-testid="stMetric"] {
        background-color: #f8f9fa; padding: 15px; border-radius: 10px;
        border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    @media (max-width: 768px) { .block-container { padding-left: 1rem; padding-right: 1rem; } }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. KONFIGURASI DATABASE TARGET (TIM & INDIVIDU)
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
        "Sekawan": 600_000_000, # Brand Ainie
        "Avione": 300_000_000, # UPDATED: Sum of Rozy, Novi, Hamzah, Dani
        "SYB": 150_000_000, 
        "Mad For Make Up": 25_000_000, 
        "Satto": 500_000_000,
        "Mykonos": 20_000_000, 
        "Somethinc": 1_200_000_000, 
        "Honor": 125_000_000, 
        "Vlagio": 75_000_000
    }
}

# --- DATABASE TARGET INDIVIDU (REQUEST BARU) ---
# Format: "NAMA SALES": {"Brand": Target}
# Catatan: "Sekawan" adalah nama database untuk "Ainie"
INDIVIDUAL_TARGETS = {
    "WIRA": {
        "Somethinc": 660_000_000, 
        "SYB": 75_000_000, 
        "Honor": 37_500_000, 
        "Vlagio": 22_500_000
    },
    "HAMZAH": {
        "Somethinc": 540_000_000, 
        "SYB": 75_000_000,
        "Sekawan": 60_000_000, # Ainie
        "Avione": 60_000_000,
        "Honor": 37_500_000,
        "Vlagio": 22_500_000
    },
    "ROZY": {
        "Sekawan": 100_000_000, # Ainie
        "Avione": 100_000_000
    },
    "NOVI": {
        "Sekawan": 90_000_000, # Ainie (Novi & Raffi)
        "Avione": 90_000_000
    },
    "DANI": {
        "Sekawan": 50_000_000, # Ainie
        "Avione": 50_000_000
    },
    "FERI": {
        "Honor": 50_000_000,
        "Vlagio": 30_000_000
    }
}

SUPERVISOR_TOTAL_TARGETS = {k: sum(v.values()) for k, v in TARGET_DATABASE.items()}
TARGET_NASIONAL_VAL = sum(SUPERVISOR_TOTAL_TARGETS.values())

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

SALES_MAPPING = {
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG",
    "ROZY AINIE": "ROZY", "NOVI AINIE": "NOVI", "NOVI AV": "NOVI",
    "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH", "HAMZA AV": "HAMZAH", "HAMZAH SYB": "HAMZAH",
    "RISKA AV": "RISKA", "RISKA BN": "RISKA", "RISKA CRS": "RISKA", "RISKA  E-WL": "RISKA", 
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
    "MARIANA CLIN": "MARIANA", "JAYA - MARIANA": "MARIANA",
    "DANI AINIE": "DANI", "DANI AV": "DANI" # Mapped Dani
}

# ==========================================
# 2. CORE FUNCTIONS
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
        bar_color = "linear-gradient(90deg, #e74c3c, #c0392b)" 
    elif 50 <= pct < 80:
        bar_color = "linear-gradient(90deg, #f1c40f, #f39c12)" 
    else:
        bar_color = "linear-gradient(90deg, #2ecc71, #27ae60)" 

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

@st.cache_data(ttl=60, show_spinner=False)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    try:
        url_with_ts = f"{url}&t={datetime.datetime.now().timestamp()}"
        df = pd.read_csv(url_with_ts, dtype=str)
    except Exception as e:
        return None

    df.columns = df.columns.str.strip()
    required_cols = ['Penjualan', 'Merk', 'Jumlah', 'Tanggal']
    if not all(col in df.columns for col in required_cols):
        return None

    if 'Nama Outlet' in df.columns:
        df = df[~df['Nama Outlet'].astype(str).str.contains('Total|Jumlah|Subtotal|Grand|Rekap', case=False, na=False)]
        df = df[df['Nama Outlet'].astype(str).str.strip() != ''] 
    
    if 'Nama Barang' in df.columns:
        df = df[~df['Nama Barang'].astype(str).str.contains('Total|Jumlah', case=False, na=False)]
        df = df[df['Nama Barang'].astype(str).str.strip() != ''] 

    df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(SALES_MAPPING).astype('category')
    
    def normalize_brand(raw_brand):
        raw_upper = str(raw_brand).upper()
        for target_brand, keywords in BRAND_ALIASES.items():
            for keyword in keywords:
                if keyword in raw_upper: return target_brand
        return raw_brand
    
    df['Merk'] = df['Merk'].apply(normalize_brand).astype('category')
    
    df['Jumlah'] = df['Jumlah'].astype(str).replace(r'[^\d]', '', regex=True)
    df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    def auto_fix_thousands(val):
        if 0 < val < 1000: return val * 1000
        return val
    df['Jumlah'] = df['Jumlah'].apply(auto_fix_thousands)

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
    df = df.dropna(subset=['Tanggal'])

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
# 3. MAIN DASHBOARD LOGIC
# ==========================================

def login_page():
    st.markdown("<br><br><h1 style='text-align: center;'>🔒 Sales Command Center</h1>", unsafe_allow_html=True)
    
    users = load_users()
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Masuk Sistem", use_container_width=True)
            if submitted:
                if users.empty:
                    st.error("⚠️ Database user tidak ditemukan (users.csv hilang).")
                else:
                    match = users[(users['username'] == username) & (users['password'] == password)]
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['role'] = match.iloc[0]['role']
                        st.session_state['sales_name'] = match.iloc[0]['sales_name']
                        st.rerun()
                    else:
                        st.error("⛔ Akses Ditolak: Username atau Password salah.")

def main_dashboard():
    with st.sidebar:
        st.write(f"### 👋 Welcome, {st.session_state['sales_name']}")
        st.caption(f"Role: **{st.session_state['role'].upper()}**")
        st.divider()
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

    df = load_data()
    if df is None or df.empty:
        st.error("⚠️ Gagal memuat data! Periksa koneksi internet atau Link Google Sheet.")
        return

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
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_view_global = df[(df['Tanggal'].dt.date >= start_date) & (df['Tanggal'].dt.date <= end_date)]
        duration = (end_date - start_date).days
        prev_start = start_date - datetime.timedelta(days=duration)
        prev_end = start_date - datetime.timedelta(days=1)
        df_prev_global = df[(df['Tanggal'].dt.date >= prev_start) & (df['Tanggal'].dt.date <= prev_end)]
    else:
        df_view_global = df; df_prev_global = pd.DataFrame()

    role = st.session_state['role']
    my_name = st.session_state['sales_name']
    my_name_key = my_name.strip().upper()
    is_supervisor_account = my_name_key in TARGET_DATABASE

    target_sales_filter = "SEMUA"

    if role == 'manager':
        sales_list = ["SEMUA"] + sorted(list(df_view_global['Penjualan'].unique()))
        target_sales_filter = st.sidebar.selectbox("Pantau Kinerja Sales:", sales_list)
        if target_sales_filter == "SEMUA":
            df_active = df_view_global; df_prev_active = df_prev_global
        else:
            df_active = df_view_global[df_view_global['Penjualan'] == target_sales_filter]
            df_prev_active = df_prev_global[df_prev_global['Penjualan'] == target_sales_filter] if not df_prev_global.empty else pd.DataFrame()

    elif is_supervisor_account:
        my_brands = TARGET_DATABASE[my_name_key].keys()
        df_spv_scope = df_view_global[df_view_global['Merk'].isin(my_brands)]
        df_prev_spv_scope = df_prev_global[df_prev_global['Merk'].isin(my_brands)] if not df_prev_global.empty else pd.DataFrame()
        
        team_list = sorted(list(df_spv_scope['Penjualan'].unique()))
        target_sales_filter = st.sidebar.selectbox("Filter Tim (Brand Anda):", ["SEMUA"] + team_list)
        
        if target_sales_filter == "SEMUA":
            df_active = df_spv_scope; df_prev_active = df_prev_spv_scope
        else:
            df_active = df_spv_scope[df_spv_scope['Penjualan'] == target_sales_filter]
            df_prev_active = df_prev_spv_scope[df_prev_spv_scope['Penjualan'] == target_sales_filter] if not df_prev_spv_scope.empty else pd.DataFrame()
    else:
        df_active = df_view_global[df_view_global['Penjualan'] == my_name]
        df_prev_active = df_prev_global[df_prev_global['Penjualan'] == my_name] if not df_prev_global.empty else pd.DataFrame()

    st.sidebar.subheader("🔍 Filter Lanjutan")
    if not df_active.empty:
        pilih_merk = st.sidebar.multiselect("Pilih Merk", sorted(df_active['Merk'].unique()))
        if pilih_merk: df_active = df_active[df_active['Merk'].isin(pilih_merk)]
        pilih_outlet = st.sidebar.multiselect("Pilih Outlet", sorted(df_active['Nama Outlet'].unique()))
        if pilih_outlet: df_active = df_active[df_active['Nama Outlet'].isin(pilih_outlet)]

    st.title("🚀 Executive Dashboard")
    st.markdown("---")

    current_omset = df_active['Jumlah'].sum()
    prev_omset = df_prev_active['Jumlah'].sum() if not df_prev_active.empty else 0
    delta_val = current_omset - prev_omset
    
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Omset", format_idr(current_omset), delta=format_idr(delta_val))
    c2.metric("🏪 Outlet Aktif", f"{df_active['Nama Outlet'].nunique()}")
    c3.metric("🧾 Transaksi", f"{len(df_active)}")

    if role == 'manager' or is_supervisor_account:
        st.markdown("### 🎯 Target Monitor")
        
        # 1. Target Nasional
        if target_sales_filter == "SEMUA":
            if is_supervisor_account:
                target_tim = SUPERVISOR_TOTAL_TARGETS.get(my_name_key, 0)
                my_brands_list = TARGET_DATABASE[my_name_key].keys()
                realisasi_tim = df_view_global[df_view_global['Merk'].isin(my_brands_list)]['Jumlah'].sum()
                render_custom_progress(f"🏢 Total Target Tim {my_name}", realisasi_tim, target_tim)
            else:
                realisasi_nasional = df_view_global['Jumlah'].sum() 
                render_custom_progress("🏢 Target Nasional (All Team)", realisasi_nasional, TARGET_NASIONAL_VAL)
        
        # 2. Target Individu Spesifik (Jika Filter != SEMUA dan ada di Database Individu)
        elif target_sales_filter in INDIVIDUAL_TARGETS:
            st.info(f"Menampilkan Target Spesifik untuk: **{target_sales_filter}**")
            individual_targets = INDIVIDUAL_TARGETS[target_sales_filter]
            
            for brand, target in individual_targets.items():
                realisasi_brand = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                render_custom_progress(f"👤 {brand} - {target_sales_filter}", realisasi_brand, target)
        
        else:
            st.warning(f"Sales **{target_sales_filter}** tidak memiliki target individu spesifik yang terdaftar.")

        st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Target Detail", "📈 Tren Harian", "🏆 Top Performance", "📋 Data Rincian"])

    with tab1:
        if target_sales_filter == "SEMUA":
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
            def color_row(row): return [f'background-color: {"#d4edda" if row["_pct_raw"] >= 80 else "#f8d7da"}; color: black'] * len(row)
            st.dataframe(df_summary.style.apply(color_row, axis=1).hide(axis="columns", subset=['_pct_raw']), use_container_width=True, hide_index=True, column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)})
        else:
            st.info("Lihat progress bar di atas untuk detail target individu.")

    with tab2:
        st.subheader("Grafik Tren Penjualan Harian")
        if not df_active.empty:
            daily_trend = df_active.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig = px.line(daily_trend, x='Tanggal', y='Jumlah', markers=True, title="Pergerakan Omset Harian")
            fig.update_layout(xaxis_title="", yaxis_title="Omset (Rp)", hovermode="x unified")
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
        st.dataframe(df_active[final_cols].sort_values('Tanggal', ascending=False), use_container_width=True, hide_index=True, column_config={"Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"), "Jumlah": st.column_config.NumberColumn("Omset", format="Rp %d")})
        csv = df_active[final_cols].to_csv(index=False).encode('utf-8')
        file_name = f"Laporan_Sales_{datetime.date.today()}.csv"
        st.download_button("📥 Download Data CSV", data=csv, file_name=file_name, mime="text/csv")

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']: login_page()
else: main_dashboard()
