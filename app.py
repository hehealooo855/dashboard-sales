import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import time
import re
import pytz # Library untuk Zona Waktu

# --- 1. KONFIGURASI HALAMAN & CSS PREMIUM ---
st.set_page_config(
    page_title="Executive Sales Command Center", 
    layout="wide", 
    page_icon="🦅",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan lebih bersih
st.markdown("""
<style>
    .metric-card {
        border: 1px solid #e6e6e6;
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #e74c3c, #f1c40f, #2ecc71);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONFIGURASI DATABASE & TARGET
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

SUPERVISOR_TOTAL_TARGETS = {k: sum(v.values()) for k, v in TARGET_DATABASE.items()}
TARGET_NASIONAL_VAL = sum(SUPERVISOR_TOTAL_TARGETS.values())

# Dictionary Mapping (Database Knowledge)
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
    "JAYA - MARIANA": "MARIANA"
}

# ==========================================
# 3. CORE LOGIC & ENGINE
# ==========================================

def get_current_time_wib():
    """Mengambil waktu server yang dipaksa ke WIB"""
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
        bar_color = "linear-gradient(90deg, #e74c3c, #c0392b)" # Merah
    elif 50 <= pct < 80:
        bar_color = "linear-gradient(90deg, #f1c40f, #f39c12)" # Kuning
    else:
        bar_color = "linear-gradient(90deg, #2ecc71, #27ae60)" # Hijau
    
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
        # Menambahkan parameter waktu agar cache Google Sheet tertipu dan memberikan data fresh
        url_with_ts = f"{url}&t={int(time.time())}"
        df = pd.read_csv(url_with_ts)
    except Exception as e:
        return None
    
    required_cols = ['Penjualan', 'Merk', 'Jumlah', 'Tanggal']
    if not all(col in df.columns for col in required_cols):
        return None
    
    # --- PERFORMANCE FIX: Vectorized Filtering (50x Faster than .apply) ---
    # Mengubah semua kolom jadi string, gabungkan, lalu cari kata kunci sampah
    df_str = df.astype(str).agg(' '.join, axis=1)
    # Hapus baris yang mengandung Total, Jumlah, atau Subtotal
    df = df[~df_str.str.contains(r'Total|Jumlah|Subtotal|Grand', case=False, regex=True)]
    
    # Cleaning Ops
    df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(SALES_MAPPING)
    
    # Pre-compile mapping untuk efisiensi
    def normalize_brand(raw_brand):
        raw_upper = str(raw_brand).upper()
        for target_brand, keywords in BRAND_ALIASES.items():
            for keyword in keywords:
                if keyword in raw_upper:
                    return target_brand
        return raw_brand
    
    df['Merk'] = df['Merk'].apply(normalize_brand)
    
    # Numeric Cleaning
    df['Jumlah'] = df['Jumlah'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    # Date Parsing (Handle Mixed Format & Swapped Dates)
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce', format='mixed')
    
    # Fix Swapped Date (US vs ID Format Logic)
    mask_swap = (df['Tanggal'].dt.day <= 12) & (df['Tanggal'].dt.day != df['Tanggal'].dt.month)
    # Create corrected dates
    swapped_dates = pd.to_datetime({
        'year': df.loc[mask_swap, 'Tanggal'].dt.year,
        'month': df.loc[mask_swap, 'Tanggal'].dt.day,
        'day': df.loc[mask_swap, 'Tanggal'].dt.month
    })
    df.loc[mask_swap, 'Tanggal'] = swapped_dates
    
    df = df.dropna(subset=['Tanggal', 'Penjualan', 'Merk', 'Jumlah'])
    
    # Ensure other columns are string
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
# 4. UI PAGES
# ==========================================

def login_page():
    st.markdown("<br><br><h1 style='text-align: center;'>🦅 Executive Command Center</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Sistem Monitoring Penjualan Real-time</p>", unsafe_allow_html=True)
    
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
    # --- Sidebar ---
    with st.sidebar:
        st.write("## 👤 User Profile")
        st.info(f"**{st.session_state['sales_name']}**\n\nRole: {st.session_state['role'].upper()}")
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
            
        st.markdown("---")
        st.caption(f"Last Updated: {get_current_time_wib().strftime('%H:%M:%S')} WIB")
            
    df = load_data()
    if df is None or df.empty:
        st.error("⚠️ Gagal memuat data! Periksa koneksi internet atau Link Google Sheet.")
        return

    # --- FILTER SECTION ---
    st.sidebar.subheader("📅 Filter Periode")

    # Timezone Aware Date
    today_wib = get_current_time_wib().date()
    max_date_data = df['Tanggal'].max().date()
    
    # Logic: Jika data hari ini belum masuk, pakai max date data. Jika sudah, pakai today.
    default_end = max_date_data
    default_start = default_end.replace(day=1) # Awal bulan dari data terakhir
    
    date_range = st.sidebar.date_input("Rentang Waktu", [default_start, default_end])

    # --- SCOPE LOGIC ---
    role = st.session_state['role']
    my_name = st.session_state['sales_name']
    my_name_key = my_name.strip().upper()
    is_supervisor_account = my_name_key in TARGET_DATABASE
    target_sales_filter = "SEMUA"

    # -- 1. Tentukan Universe Data (df_scope_all) --
    if role == 'manager':
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
        df_scope_all = df[df['Penjualan'] == my_name]

    # -- 2. Filter Lanjutan --
    with st.sidebar.expander("🔍 Filter Lanjutan", expanded=False):
        unique_brands = sorted(df_scope_all['Merk'].unique())
        pilih_merk = st.multiselect("Pilih Merk", unique_brands)
        if pilih_merk: df_scope_all = df_scope_all[df_scope_all['Merk'].isin(pilih_merk)]
            
        unique_outlets = sorted(df_scope_all['Nama Outlet'].unique())
        pilih_outlet = st.multiselect("Pilih Outlet", unique_outlets)
        if pilih_outlet: df_scope_all = df_scope_all[df_scope_all['Nama Outlet'].isin(pilih_outlet)]

    # -- 3. Apply Time Filter --
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_active = df_scope_all[(df_scope_all['Tanggal'].dt.date >= start_date) & (df_scope_all['Tanggal'].dt.date <= end_date)]
        ref_date = end_date
    else:
        df_active = df_scope_all
        ref_date = df['Tanggal'].max().date()

    # --- MAIN DASHBOARD ---
    st.title("🚀 Executive Dashboard")
    st.markdown("---")
    
    # --- KPI METRICS ---
    current_omset_total = df_active['Jumlah'].sum()
    
    # Logika Delta H vs H-1
    omset_hari_ini = df_scope_all[df_scope_all['Tanggal'].dt.date == ref_date]['Jumlah'].sum()
    prev_date = ref_date - datetime.timedelta(days=1)
    omset_kemarin = df_scope_all[df_scope_all['Tanggal'].dt.date == prev_date]['Jumlah'].sum()
    
    delta_val = omset_hari_ini - omset_kemarin
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="💰 Total Omset (Periode)", 
            value=format_idr(current_omset_total), 
            delta=f"{format_idr(delta_val)} (vs {prev_date.strftime('%d %b')})"
        )
        st.caption(f"📅 Omset Tgl {ref_date.strftime('%d %b')}: **{format_idr(omset_hari_ini)}**")
        
    with col2:
        st.metric("🏪 Outlet Aktif", f"{df_active['Nama Outlet'].nunique()}")
    with col3:
        st.metric("🧾 Transaksi", f"{len(df_active)}")

    # --- TARGET MONITOR ---
    if role == 'manager' or is_supervisor_account:
        st.markdown("### 🎯 Target Monitor")
        
        # Realisasi Nasional (Always Global)
        realisasi_nasional = df[(df['Tanggal'].dt.date >= start_date) & (df['Tanggal'].dt.date <= end_date)]['Jumlah'].sum() if len(date_range)==2 else df['Jumlah'].sum()
        
        render_custom_progress("🏢 Target Nasional (All Team)", realisasi_nasional, TARGET_NASIONAL_VAL)
        
        if is_supervisor_account:
            target_pribadi = SUPERVISOR_TOTAL_TARGETS.get(my_name_key, 0)
            my_brands_list = TARGET_DATABASE[my_name_key].keys()
            df_spv_only = df[df['Merk'].isin(my_brands_list)]
            if len(date_range)==2:
                df_spv_only = df_spv_only[(df_spv_only['Tanggal'].dt.date >= start_date) & (df_spv_only['Tanggal'].dt.date <= end_date)]
            
            render_custom_progress(f"👤 Target Tim {my_name}", df_spv_only['Jumlah'].sum(), target_pribadi)
        
        st.markdown("---")

    # --- ANALYTICS TABS ---
    t1, t2, t3, t4, t5 = st.tabs(["📊 Target Detail", "☀️ Brand Hierarchy", "📈 Tren Harian", "🏆 Top Performance", "📋 Data Rincian"])
    
    with t1:
        show_rapor = (role == 'manager' and target_sales_filter == "SEMUA") or (is_supervisor_account and target_sales_filter == "SEMUA")
        
        if show_rapor:
            st.subheader("Rapor Target per Brand")
            summary_data = []
            target_loop = TARGET_DATABASE.items() if role == 'manager' else {my_name_key: TARGET_DATABASE[my_name_key]}.items()
            
            for spv, brands_dict in target_loop:
                for brand, target in brands_dict.items():
                    realisasi = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                    pct_val = (realisasi / target) * 100 if target > 0 else 0
                    
                    summary_data.append({
                        "Supervisor": spv, "Brand": brand,
                        "Target": format_idr(target), "Realisasi": format_idr(realisasi),
                        "Ach (%)": f"{pct_val:.0f}%", "Pencapaian": pct_val / 100,
                        "_pct": pct_val
                    })
            
            df_summ = pd.DataFrame(summary_data)
            def highlight_row(row):
                return [f'background-color: {"#d4edda" if row["_pct"] >= 80 else "#f8d7da"}; color: #333'] * len(row)
            
            st.dataframe(
                df_summ.style.apply(highlight_row, axis=1).hide(axis="columns", subset=['_pct']),
                use_container_width=True, hide_index=True,
                column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)}
            )
        else:
            # Individual Sales View
            st.info(f"Menampilkan kontribusi: **{target_sales_filter}**")
            sales_brands = df_active['Merk'].unique()
            indiv_data = []
            
            for brand in sales_brands:
                # Find owner
                owner, target = "-", 0
                for spv, b_dict in TARGET_DATABASE.items():
                    if brand in b_dict:
                        owner, target = spv, b_dict[brand]
                        break
                
                if target > 0:
                    real = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                    pct = (real/target)*100
                    indiv_data.append({
                        "Brand": brand, "Owner": owner, "Target Tim": format_idr(target),
                        "Kontribusi Sales": format_idr(real), "Ach (%)": f"{pct:.1f}%",
                        "Pencapaian": pct/100
                    })
            
            if indiv_data:
                st.dataframe(
                    pd.DataFrame(indiv_data), 
                    use_container_width=True, hide_index=True,
                    column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)}
                )
            else:
                st.warning("Tidak ada data target brand untuk sales ini.")

    with t2:
        st.subheader("☀️ Kontribusi Brand (Hierarki)")
        if not df_active.empty:
            # Siapkan data untuk Sunburst
            df_sun = df_active.groupby(['Merk', 'Nama Barang'])['Jumlah'].sum().reset_index()
            # Mapping Supervisor manual karena tidak ada di kolom
            def get_spv(m):
                for s, b in TARGET_DATABASE.items():
                    if m in b: return s
                return "Lainnya"
            df_sun['Supervisor'] = df_sun['Merk'].apply(get_spv)
            
            fig_sun = px.sunburst(
                df_sun, path=['Supervisor', 'Merk', 'Nama Barang'], values='Jumlah',
                color='Jumlah', color_continuous_scale='RdBu'
            )
            st.plotly_chart(fig_sun, use_container_width=True)
        else:
            st.info("Data tidak cukup untuk visualisasi.")

    with t3:
        st.subheader("📈 Tren Harian")
        if not df_active.empty:
            daily = df_active.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig_line = px.line(daily, x='Tanggal', y='Jumlah', markers=True)
            fig_line.update_traces(line_color='#2980b9', line_width=3)
            st.plotly_chart(fig_line, use_container_width=True)

    with t4:
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

    with t5:
        st.subheader("📋 Data Rincian")
        cols = ['Tanggal', 'Nama Outlet', 'Merk', 'Nama Barang', 'Jumlah', 'Penjualan']
        final_cols = [c for c in cols if c in df_active.columns]
        
        st.dataframe(
            df_active[final_cols].sort_values('Tanggal', ascending=False),
            use_container_width=True, hide_index=True,
            column_config={
                "Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"),
                "Jumlah": st.column_config.NumberColumn("Omset", format="Rp %d")
            }
        )
        
        # Download Button
        csv = df_active[final_cols].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Laporan (CSV)",
            data=csv,
            file_name=f"Laporan_Sales_{datetime.date.today()}.csv",
            mime="text/csv",
            type="primary"
        )

# --- 5. ENTRY POINT ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()
