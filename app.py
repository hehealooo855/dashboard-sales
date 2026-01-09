import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import time
import re
import pytz 

# ==========================================
# 1. KONFIGURASI LINK GOOGLE SHEET (ISI DISINI!)
# ==========================================
# Ganti string di dalam tanda kutip "" dengan Link CSV Publish to Web Anda.

URL_DATA_TRANSAKSI = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pubhtml?gid=0&single=true"

# LINK DARI TAB: Master_Target
URL_MASTER_TARGET  = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=2102937723&single=true&output=csv" 

# LINK DARI TAB: Master_Mapping
URL_MASTER_MAPPING = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=518733046&single=true&output=csv" 

# LINK DARI TAB: Master_User
URL_MASTER_USER    = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=1629420292&single=true&output=csv" 


# --- 2. SETUP HALAMAN & CSS ---
st.set_page_config(
    page_title="Executive Sales Command Center", 
    layout="wide", 
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

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
# 3. CORE LOGIC (DYNAMIC CONFIG LOADER)
# ==========================================

# Database Typo Brand (Static Knowledge Base) - Jarang berubah, aman di hardcode
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

def format_idr(value):
    try: return f"Rp {value:,.0f}".replace(",", ".")
    except: return "Rp 0"

def get_current_time_wib():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

# --- FUNGSI LOAD KONFIGURASI DINAMIS ---
@st.cache_data(ttl=300) # Cache 5 menit agar tidak lemot
def load_configurations():
    # Default values jika load gagal
    empty_users = pd.DataFrame(columns=['Username', 'Password', 'Role', 'Sales_Name'])
    
    try:
        # 1. Load User Database
        if "MASUKKAN_LINK" in URL_MASTER_USER:
             st.warning("⚠️ Link Master User belum diisi di kode!")
             return empty_users, {}, {}, {}, {}, 0, []
        df_users = pd.read_csv(URL_MASTER_USER, dtype=str)
        
        # 2. Load Mapping Sales
        df_map = pd.read_csv(URL_MASTER_MAPPING, dtype=str)
        # Convert ke Dictionary {Input: Output}
        sales_mapping = dict(zip(df_map.iloc[:, 0].str.upper().str.strip(), df_map.iloc[:, 1].str.upper().str.strip()))
        
        # 3. Load Target & Build Databases
        df_target = pd.read_csv(URL_MASTER_TARGET)
        # Bersihkan data target (hapus Rp, titik, koma)
        df_target['Target'] = pd.to_numeric(df_target['Target'].astype(str).replace(r'[^\d]', '', regex=True), errors='coerce').fillna(0)
        df_target['Nama Sales'] = df_target['Nama Sales'].str.upper().str.strip()
        df_target['Supervisor'] = df_target['Supervisor'].str.upper().str.strip()
        
        # A. Bangun INDIVIDUAL_TARGETS {Sales: {Brand: Target}}
        individual_targets = {}
        for _, row in df_target.iterrows():
            sales = row['Nama Sales']
            brand = row['Brand']
            target = row['Target']
            if sales not in individual_targets: individual_targets[sales] = {}
            individual_targets[sales][brand] = target
            
        # B. Bangun TARGET_DATABASE (Supervisor View)
        # Group by Supervisor & Brand -> Sum Target
        df_spv = df_target.groupby(['Supervisor', 'Brand'])['Target'].sum().reset_index()
        target_database = {}
        for _, row in df_spv.iterrows():
            spv = row['Supervisor']
            brand = row['Brand']
            target = row['Target']
            if spv not in target_database: target_database[spv] = {}
            target_database[spv][brand] = target

        # C. Hitung Total Target Supervisor
        supervisor_total_targets = {spv: sum(brands.values()) for spv, brands in target_database.items()}
        target_nasional_val = sum(supervisor_total_targets.values())
        
        valid_sales_list = list(individual_targets.keys())

        return df_users, sales_mapping, individual_targets, target_database, supervisor_total_targets, target_nasional_val, valid_sales_list

    except Exception as e:
        # Fallback agar program tidak crash total saat setting awal
        st.error(f"Gagal memuat konfigurasi. Error: {e}")
        return empty_users, {}, {}, {}, {}, 0, []

# Load Config saat startup
CFG_USERS, CFG_MAPPING, CFG_INDIV_TARGETS, CFG_TARGET_DB, CFG_SPV_TOTAL, CFG_NASIONAL, CFG_VALID_SALES = load_configurations()

# --- FUNGSI LOAD DATA TRANSAKSI ---
@st.cache_data(ttl=60)
def load_data():
    try:
        url_with_ts = f"{URL_DATA_TRANSAKSI}&t={int(time.time())}"
        df = pd.read_csv(url_with_ts, dtype=str)
    except: return None
    
    df.columns = df.columns.str.strip()
    required = ['Penjualan', 'Merk', 'Jumlah', 'Tanggal']
    if not all(c in df.columns for c in required): return None

    # Hapus Baris Sampah (Aggressive Cleaning)
    if 'Nama Outlet' in df.columns:
        df = df[~df['Nama Outlet'].astype(str).str.contains(r'Total|Jumlah|Subtotal|Grand|Rekap', case=False, regex=True, na=False)]
        df = df[df['Nama Outlet'].astype(str).str.strip() != '']
        df = df[df['Nama Outlet'].astype(str).str.lower() != 'nan']

    if 'Nama Barang' in df.columns:
        df = df[~df['Nama Barang'].astype(str).str.contains(r'Total|Jumlah', case=False, regex=True, na=False)]
        df = df[df['Nama Barang'].astype(str).str.strip() != '']

    # Normalisasi Sales (Pakai Mapping dari Sheet)
    df['Penjualan'] = df['Penjualan'].astype(str).str.strip().upper().replace(CFG_MAPPING)
    
    # Logic Non-Sales (Hanya Sales yang ada di Master Target/Mapping yang dianggap Valid)
    # Kita gabungkan sales valid + supervisor name agar tidak hilang
    all_valid_names = set(CFG_VALID_SALES) | set(CFG_TARGET_DB.keys())
    # Optional: Jika ingin strict, uncomment baris bawah. 
    # df.loc[~df['Penjualan'].isin(all_valid_names), 'Penjualan'] = 'Non-Sales'
    
    df['Penjualan'] = df['Penjualan'].astype('category')

    # Normalisasi Brand
    def normalize_brand(raw):
        raw_upper = str(raw).upper()
        for target, keywords in BRAND_ALIASES.items():
            for k in keywords:
                if k in raw_upper: return target
        return raw
    df['Merk'] = df['Merk'].apply(normalize_brand).astype('category')

    # Numeric Cleaning (Smart)
    def clean_currency(x):
        if pd.isna(x) or str(x).strip() == '': return 0
        s = str(x)
        if ',' in s[-3:]: s = s.replace(',', '.') # Handle desimal koma
        s = re.sub(r'[^\d.]', '', s) # Hapus non angka
        try: return float(s)
        except: return 0
        
    df['Jumlah'] = df['Jumlah'].apply(clean_currency)
    
    # Logic Darurat 1000
    def fix_thou(v): return v * 1000 if 0 < v < 1000 else v
    df['Jumlah'] = df['Jumlah'].apply(fix_thou)

    # Date Cleaning
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce', format='mixed')
    def fix_date(d):
        if pd.isnull(d): return d
        try:
            if d.day <= 12 and d.day != d.month: return d.replace(day=d.month, month=d.day)
        except: pass
        return d
    df['Tanggal'] = df['Tanggal'].apply(fix_date)
    df = df.dropna(subset=['Tanggal', 'Penjualan', 'Merk', 'Jumlah'])
    
    # Filter Tahun
    cy = datetime.datetime.now().year
    df = df[(df['Tanggal'].dt.year >= cy - 1) & (df['Tanggal'].dt.year <= cy + 1)]

    for c in ['Kota', 'Nama Outlet', 'Nama Barang']:
        if c in df.columns: df[c] = df[c].astype(str)
        
    return df

def render_custom_progress(title, current, target):
    if target == 0: target = 1
    pct = (current / target) * 100
    visual_pct = min(pct, 100)
    if pct < 50: bar_color = "linear-gradient(90deg, #e74c3c, #c0392b)" 
    elif 50 <= pct < 80: bar_color = "linear-gradient(90deg, #f1c40f, #f39c12)" 
    else: bar_color = "linear-gradient(90deg, #2ecc71, #27ae60)" 
    
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
                {pct:.1f}%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. PAGES
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
                    # Validasi User dari Config
                    if CFG_USERS is None or CFG_USERS.empty:
                        st.error("Gagal terhubung ke Database User (Google Sheet).")
                    else:
                        match = CFG_USERS[(CFG_USERS['Username'] == username) & (CFG_USERS['Password'] == password)]
                        if not match.empty:
                            st.session_state['logged_in'] = True
                            st.session_state['role'] = match.iloc[0]['Role']
                            st.session_state['sales_name'] = match.iloc[0]['Sales_Name']
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
            st.session_state['logged_in'] = False; st.rerun()
        st.markdown("---")
        st.caption(f"Last Updated: {get_current_time_wib().strftime('%H:%M:%S')} WIB")
            
    df = load_data()
    if df is None or df.empty:
        st.error("⚠️ Gagal memuat data transaksi! Periksa Link Google Sheet Data Transaksi.")
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
        s, e = date_range
        df_active = df[(df['Tanggal'].dt.date >= s) & (df['Tanggal'].dt.date <= e)]
        df_full_period = df[(df['Tanggal'].dt.date >= s) & (df['Tanggal'].dt.date <= e)] 
    else:
        df_active = df
        df_full_period = df

    # SCOPE LOGIC (MENGGUNAKAN CONFIG DARI SHEET)
    role = st.session_state['role']
    my_name = st.session_state['sales_name'].upper()
    
    is_supervisor = my_name in CFG_TARGET_DB
    
    target_filter = "SEMUA"

    if role in ['manager', 'direktur']:
        sales_list = ["SEMUA"] + sorted(list(df['Penjualan'].unique()))
        target_filter = st.sidebar.selectbox("Pantau Sales:", sales_list)
        if target_filter != "SEMUA": df_active = df_active[df_active['Penjualan'] == target_filter]
            
    elif is_supervisor:
        # Ambil Brand milik Supervisor ini dari Config
        my_brands = CFG_TARGET_DB[my_name].keys()
        # Filter data hanya brand miliknya
        df_active = df_active[df_active['Merk'].isin(my_brands)]
        # List tim sales yang menjual brand miliknya (dari data transaksi)
        team_list = sorted(list(df_active['Penjualan'].unique()))
        target_filter = st.sidebar.selectbox("Filter Tim Anda:", ["SEMUA"] + team_list)
        if target_filter != "SEMUA": df_active = df_active[df_active['Penjualan'] == target_filter]
        
    else: # Sales Biasa
        target_filter = my_name
        df_active = df_active[df_active['Penjualan'] == my_name]

    # Filter Lanjutan
    with st.sidebar.expander("🔍 Filter Lanjutan", expanded=False):
        brands = sorted(df_active['Merk'].unique())
        sel_brand = st.multiselect("Pilih Merk", brands)
        if sel_brand: df_active = df_active[df_active['Merk'].isin(sel_brand)]
        
        outlets = sorted(df_active['Nama Outlet'].unique())
        sel_outlet = st.multiselect("Pilih Outlet", outlets)
        if sel_outlet: df_active = df_active[df_active['Nama Outlet'].isin(sel_outlet)]

    # KPI
    st.title("🚀 Executive Dashboard")
    st.markdown("---")
    
    curr_omset = df_active['Jumlah'].sum()
    ref_date = df['Tanggal'].max().date()
    omset_today = df[(df['Tanggal'].dt.date == ref_date) & df['Penjualan'].isin(df_active['Penjualan'])]['Jumlah'].sum()
    omset_yesterday = df[(df['Tanggal'].dt.date == ref_date - datetime.timedelta(days=1)) & df['Penjualan'].isin(df_active['Penjualan'])]['Jumlah'].sum()
    delta = omset_today - omset_yesterday
    
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Omset", format_idr(curr_omset), delta=format_idr(delta))
    c2.metric("🏪 Outlet Aktif", f"{df_active['Nama Outlet'].nunique()}")
    transaksi_count = df_active['No Faktur'].nunique() if 'No Faktur' in df_active.columns else len(df_active)
    c3.metric("🧾 Transaksi", f"{transaksi_count}")

    # TARGET MONITORING
    if role in ['manager', 'direktur'] or is_supervisor or target_filter in CFG_INDIV_TARGETS:
        st.markdown("### 🎯 Target Monitor")
        
        if target_filter == "SEMUA":
            if is_supervisor:
                target_val = CFG_SPV_TOTAL.get(my_name, 0)
                my_brands = CFG_TARGET_DB.get(my_name, {}).keys()
                realisasi = df_full_period[df_full_period['Merk'].isin(my_brands)]['Jumlah'].sum()
                render_custom_progress(f"👤 Target Tim {my_name}", realisasi, target_val)
            else:
                realisasi = df_full_period['Jumlah'].sum()
                render_custom_progress("🏢 Target Nasional", realisasi, CFG_NASIONAL)
        
        elif target_filter in CFG_INDIV_TARGETS:
            st.info(f"📋 Target Individu: **{target_filter}**")
            targets = CFG_INDIV_TARGETS[target_filter]
            for brand, tgt in targets.items():
                real = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                render_custom_progress(f"{brand} - {target_filter}", real, tgt)
        else:
            st.warning("Sales ini tidak memiliki target individu di database.")
            
        st.markdown("---")

    # TABS
    t1, t2, t3, t4 = st.tabs(["📊 Rapor Brand", "📈 Tren", "🏆 Top Produk", "📋 Data"])
    
    with t1:
        if target_filter == "SEMUA":
            st.subheader("Rapor Target per Brand")
            target_source = CFG_TARGET_DB if role in ['manager','direktur'] else {my_name: CFG_TARGET_DB.get(my_name, {})}
            
            summary = []
            for spv, brands in target_source.items():
                for brand, tgt in brands.items():
                    real = df_full_period[df_full_period['Merk'] == brand]['Jumlah'].sum()
                    pct = (real/tgt)*100 if tgt > 0 else 0
                    summary.append({"Supervisor": spv, "Brand": brand, "Target": format_idr(tgt), "Realisasi": format_idr(real), "Ach (%)": f"{pct:.0f}%", "Val": pct})
            
            df_sum = pd.DataFrame(summary)
            if not df_sum.empty:
                st.dataframe(df_sum.style.background_gradient(subset=['Val'], cmap='RdYlGn', vmin=0, vmax=100).hide(axis="columns", subset=['Val']), use_container_width=True)
        
        elif target_filter in CFG_INDIV_TARGETS:
            st.info("Lihat progress bar di atas.")
        else:
            st.info("Kontribusi Penjualan per Brand:")
            brand_perf = df_active.groupby('Merk')['Jumlah'].sum().reset_index()
            brand_perf['Jumlah'] = brand_perf['Jumlah'].apply(format_idr)
            st.dataframe(brand_perf, use_container_width=True)

    with t2:
        if not df_active.empty:
            daily = df_active.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig = px.line(daily, x='Tanggal', y='Jumlah', markers=True)
            st.plotly_chart(fig, use_container_width=True)

    with t3:
        if not df_active.empty:
            top = df_active.groupby('Nama Barang')['Jumlah'].sum().nlargest(10).reset_index()
            fig = px.bar(top, x='Jumlah', y='Nama Barang', orientation='h')
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

    with t4:
        st.subheader("Data Rincian")
        with st.expander("🕵️‍♂️ Detektif Data (Cek Angka Aneh)"):
            st.dataframe(df_active.nlargest(10, 'Jumlah'), use_container_width=True)
            
        cols = ['Tanggal', 'Nama Outlet', 'Merk', 'Nama Barang', 'Jumlah', 'Penjualan']
        final_cols = [c for c in cols if c in df_active.columns]
        st.dataframe(df_active[final_cols].sort_values('Tanggal', ascending=False), use_container_width=True)

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if st.session_state['logged_in']: main_dashboard()
else: login_page()
