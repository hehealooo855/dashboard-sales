import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import time
import re
import pytz
import io 
import os
import hashlib
import numpy as np
import pyotp  # Library WAJIB untuk Google Authenticator
import qrcode # Library WAJIB untuk QR Code
from calendar import monthrange
from itertools import combinations
from collections import Counter

# --- 1. KONFIGURASI HALAMAN & CSS PREMIUM ---
st.set_page_config(
    page_title="Dashboard Sales Pro", 
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
    div[data-testid="stDataFrame"] div[role="gridcell"] {
        white-space: pre-wrap !important; 
    }
    /* Security: Hide Menu & Footer */
    [data-testid="stElementToolbar"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONFIGURASI DATABASE & TARGET
# ==========================================
TARGET_DATABASE = {
    "MADONG": {"Somethinc": 1200000000, "SYB": 150000000, "Sekawan": 600000000, "Avione": 300000000, "Honor": 125000000, "Vlagio": 75000000, "Ren & R & L": 20000000, "Mad For Make Up": 25000000, "Satto": 500000000, "Mykonos": 20000000},
    "LISMAN": {"Javinci": 1300000000, "Careso": 400000000, "Newlab": 150000000, "Gloow & Be": 130000000, "Dorskin": 20000000, "Whitelab": 150000000, "Bonavie": 50000000, "Goute": 50000000, "Mlen": 100000000, "Artist Inc": 130000000},
    "AKBAR": {"Sociolla": 600000000, "Thai": 300000000, "Inesia": 100000000, "Y2000": 180000000, "Diosys": 520000000, "Masami": 40000000, "Cassandra": 50000000, "Clinelle": 80000000},
    "WILLIAM": {"The Face": 600000000, "Yu Chun Mei": 450000000, "Milano": 50000000, "Remar": 0, "Beautica": 100000000, "Walnutt": 30000000, "Elizabeth Rose": 50000000, "Maskit": 30000000, "Claresta": 350000000, "Birth Beyond": 120000000, "OtwooO": 200000000, "Rose All Day": 50000000}
}

INDIVIDUAL_TARGETS = {
    "WIRA": { "Somethinc": 660000000, "SYB": 75000000, "Honor": 37500000, "Vlagio": 22500000, "Elizabeth Rose": 30000000, "Walnutt": 20000000 },
    "HAMZAH": { "Somethinc": 540000000, "SYB": 75000000, "Sekawan": 60000000, "Avione": 60000000, "Honor": 37500000, "Vlagio": 22500000 },
    "ROZY": { "Sekawan": 100000000, "Avione": 100000000 },
    "NOVI": { "Sekawan": 90000000, "Avione": 90000000 },
    "DANI": { "Sekawan": 50000000, "Avione": 50000000 },
    "FERI": { "Honor": 50000000, "Thai": 200000000, "Vlagio": 30000000, "Inesia": 30000000 },
    "NAUFAL": { "Javinci": 550000000 },
    "RIZKI": { "Javinci": 450000000 },
    "ADE": { "Javinci": 180000000, "Careso": 20000000, "Newlab": 75000000, "Gloow & Be": 60000000, "Dorskin": 10000000, "Mlen": 50000000 },
    "FANDI": { "Javinci": 40000000, "Careso": 20000000, "Newlab": 75000000, "Gloow & Be": 60000000, "Dorskin": 10000000, "Whitelab": 75000000, "Goute": 25000000, "Bonavie": 25000000, "Mlen": 50000000 },
    "SYAHRUL": { "Javinci": 40000000, "Careso": 10000000, "Gloow & Be": 10000000 },
    "RISKA": { "Javinci": 40000000, "Sociolla": 190000000, "Thai": 30000000, "Inesia": 20000000 },
    "DWI": { "Careso": 350000000 },
    "SANTI": { "Goute": 25000000, "Bonavie": 25000000, "Whitelab": 75000000 },
    "ASWIN": { "Artist Inc": 130000000 },
    "DEVI": { "Sociolla": 120000000, "Y2000": 65000000, "Diosys": 175000000 },
    "GANI": { "The Face": 200000000, "Yu Chun Mei": 175000000, "Milano": 20000000, "Sociolla": 80000000, "Thai": 85000000, "Inesia": 25000000 },
    "BASTIAN": { "Sociolla": 210000000, "Thai": 85000000, "Inesia": 25000000, "Y2000": 65000000, "Diosys": 175000000 },
    "BAYU": { "Y2000": 50000000, "Diosys": 170000000 },
    "YOGI": { "The Face": 400000000, "Yu Chun Mei": 275000000, "Milano": 30000000 },
    "LYDIA": { "Birth Beyond": 120000000 },
    "MITHA": { "Maskit": 30000000, "Rose All Day": 30000000, "OtwooO": 200000000, "Claresta": 350000000 }
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
    "Claresta": ["CLARESTA"], "Birth Beyond": ["BIRTH"], "Rose All Day": ["ROSE ALL DAY"],
}

SALES_MAPPING = {
    # (Mapping Sales Anda yang lengkap ada di sini - saya persingkat agar muat)
    "WIRA VG": "WIRA", "WIRA SOMETHINC": "WIRA", "PMT-WIRA": "WIRA",
    "HAMZAH VG": "HAMZAH", "FERI VG": "FERI", "YOGI TF": "YOGI", 
    "GANI TF": "GANI", "MITHA MASKIT": "MITHA", "LYDIA KITO": "LYDIA",
    "NOVI AINIE": "NOVI", "ROZY AINIE": "ROZY", "DANI AINIE": "DANI",
    "MADONG - MYKONOS": "MADONG", "RISKA AV": "RISKA", "ADE CLA": "ADE",
    "FANDI - BONAVIE": "FANDI", "SAHRUL JAVINCI": "SYAHRUL", "SANTI BONAVIE": "SANTI",
    "DWI CRS": "DWI", "ASWIN ARTIS": "ASWIN", "BASTIAN CASANDRA": "BASTIAN",
    "SSL - DEVI": "DEVI", "SSL- BAYU": "BAYU", "HABIBI - FZ": "HABIBI",
    "GLOOW - LISMAN": "LISMAN", "WILLIAM BTC": "WILLIAM"
}

# ==========================================
# 3. CORE LOGIC
# ==========================================

# --- SECURITY FEATURE: AUDIT LOGGING ---
def log_activity(user, action):
    log_file = 'audit_log.csv'
    timestamp = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([[timestamp, user, action]], columns=['Timestamp', 'User', 'Action'])
    
    if not os.path.isfile(log_file):
        new_log.to_csv(log_file, index=False)
    else:
        new_log.to_csv(log_file, mode='a', header=False, index=False)

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
    if pct < 50: bar_color = "linear-gradient(90deg, #e74c3c, #c0392b)" 
    elif 50 <= pct < 80: bar_color = "linear-gradient(90deg, #f1c40f, #f39c12)" 
    else: bar_color = "linear-gradient(90deg, #2ecc71, #27ae60)" 
    
    st.markdown(f"""
    <div style="margin-bottom: 20px; background-color: #fcfcfc; padding: 15px; border-radius: 12px; border: 1px solid #eee;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-weight: 700; color: #34495e;">{title}</span>
            <span style="font-weight: 600; color: #555;">{format_idr(current)} / {format_idr(target)}</span>
        </div>
        <div style="width: 100%; background-color: #ecf0f1; border-radius: 20px; height: 26px;">
            <div style="width: {visual_pct}%; background: {bar_color}; height: 100%; border-radius: 20px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    try:
        url_with_ts = f"{url}&t={int(time.time())}"
        df = pd.read_csv(url_with_ts, dtype=str)
    except: return None
    
    df.columns = df.columns.str.strip()
    
    faktur_col = None
    for col in df.columns:
        if 'faktur' in col.lower() or 'bukti' in col.lower() or 'invoice' in col.lower():
            faktur_col = col; break
    if faktur_col: df = df.rename(columns={faktur_col: 'No Faktur'})
    
    if 'Nama Outlet' in df.columns:
        df = df[~df['Nama Outlet'].astype(str).str.match(r'^(Total|Jumlah|Subtotal)', case=False, na=False)]
        df = df[df['Nama Outlet'].astype(str).str.strip() != ''] 

    df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(SALES_MAPPING)
    valid_sales = list(INDIVIDUAL_TARGETS.keys()) + ["MADONG", "LISMAN", "AKBAR", "WILLIAM"]
    df.loc[~df['Penjualan'].isin(valid_sales), 'Penjualan'] = 'Non-Sales'
    
    def normalize_brand(raw):
        raw_u = str(raw).upper()
        for k, v in BRAND_ALIASES.items():
            for kw in v: 
                if kw in raw_u: return k
        return raw
    df['Merk'] = df['Merk'].apply(normalize_brand)

    df['Jumlah'] = pd.to_numeric(df['Jumlah'].astype(str).str.replace(r'[Rp\s.]', '', regex=True).str.replace(',','.'), errors='coerce').fillna(0)
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Tanggal'])
    
    return df

# --- DATABASE USER & SECRET KEY MANAGER ---
USER_DB_FILE = 'users.csv'

def load_users():
    try:
        df = pd.read_csv(USER_DB_FILE)
        # AUTO UPGRADE: Tambahkan kolom secret_key jika belum ada
        if 'secret_key' not in df.columns:
            df['secret_key'] = None
            df.to_csv(USER_DB_FILE, index=False)
        return df
    except:
        return pd.DataFrame(columns=['username', 'password', 'role', 'sales_name', 'secret_key'])

def save_user_secret(username, secret_key):
    df = load_users()
    df.loc[df['username'] == username, 'secret_key'] = secret_key
    df.to_csv(USER_DB_FILE, index=False)

# ==========================================
# 4. FUNGSI ANALISIS CERDAS
# ==========================================
def compute_association_rules(df):
    if 'No Faktur' not in df.columns or 'Nama Barang' not in df.columns: return None
    item_support = df.groupby('Nama Barang')['No Faktur'].nunique()
    total_transactions = df['No Faktur'].nunique()
    
    # Simple Association Rules (A -> B)
    pair_counts = Counter()
    for _, group in df.groupby('No Faktur'):
        items = sorted(group['Nama Barang'].unique())
        if len(items) > 1:
            pair_counts.update(combinations(items, 2))
            
    rules = []
    for (A, B), count in pair_counts.items():
        conf_a = count / item_support[A]
        conf_b = count / item_support[B]
        if conf_a > 0.4: # Threshold 40%
            rules.append({'antecedent': A, 'consequent': B, 'confidence': conf_a})
        if conf_b > 0.4:
            rules.append({'antecedent': B, 'consequent': A, 'confidence': conf_b})
            
    return pd.DataFrame(rules).sort_values('confidence', ascending=False) if rules else None

def get_cross_sell_recommendations(df):
    rules = compute_association_rules(df)
    if rules is None or rules.empty: return None
    
    recommendations = []
    # Cek histori toko terakhir
    latest_tx = df.sort_values('Tanggal', ascending=False).groupby('Nama Outlet').head(30) # Ambil 30 transaksi terakhir per toko
    
    outlet_items = latest_tx.groupby('Nama Outlet')['Nama Barang'].apply(set).to_dict()
    
    for outlet, items in outlet_items.items():
        salesman = df[df['Nama Outlet'] == outlet]['Penjualan'].iloc[0]
        for item in items:
            matches = rules[rules['antecedent'] == item]
            for _, r in matches.iterrows():
                if r['consequent'] not in items:
                    rec_text = f"Toko beli **{r['antecedent']}**, tawarkan **{r['consequent']}** (Peluang: {r['confidence']:.0%})"
                    recommendations.append({'Sales': salesman, 'Toko': outlet, 'Rekomendasi': rec_text})
                    break # Ambil 1 rekomendasi terbaik per item source
    
    return pd.DataFrame(recommendations)

# ==========================================
# 5. MAIN LOGIC (LOGIN & DASHBOARD)
# ==========================================

def login_page():
    st.markdown("<br><br><h1 style='text-align: center;'>🦅 Executive Command Center</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            st.markdown(f"<div style='text-align:center; color:#888; font-size:12px;'>Protected by Google Authenticator</div>", unsafe_allow_html=True)
            
            # --- SESSION STATE INITIALIZATION ---
            if 'login_step' not in st.session_state: st.session_state['login_step'] = 'credentials'
            if 'temp_user_data' not in st.session_state: st.session_state['temp_user_data'] = None
            
            # --- STEP 1: USERNAME & PASSWORD ---
            if st.session_state['login_step'] == 'credentials':
                with st.form("cred_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submitted = st.form_submit_button("Verifikasi Akun", use_container_width=True)
                    
                    if submitted:
                        users = load_users()
                        match = users[(users['username'] == username) & (users['password'] == password)]
                        
                        if not match.empty:
                            user_row = match.iloc[0]
                            # BYPASS UNTUK DIREKTUR / MANAGER (Optional)
                            if user_row['role'] in ['direktur', 'manager']:
                                st.session_state['logged_in'] = True
                                st.session_state['role'] = user_row['role']
                                st.session_state['sales_name'] = user_row['sales_name']
                                log_activity(user_row['sales_name'], "LOGIN (BYPASS OTP)")
                                st.rerun()
                            else:
                                st.session_state['temp_user_data'] = user_row
                                st.session_state['login_step'] = '2fa_check'
                                st.rerun()
                        else:
                            st.error("Username/Password Salah")
                            log_activity(username, "FAILED LOGIN - CREDENTIALS")

            # --- STEP 2: 2FA CHECK ---
            elif st.session_state['login_step'] == '2fa_check':
                user_data = st.session_state['temp_user_data']
                secret = user_data['secret_key']
                
                # JIKA BELUM PUNYA SECRET KEY -> SETUP AWAL
                if pd.isna(secret) or secret == "":
                    st.warning("⚠️ Setup Keamanan Pertama Kali")
                    st.info("Akun Anda wajib menggunakan Google Authenticator.")
                    
                    # Generate New Secret
                    if 'new_secret' not in st.session_state:
                        st.session_state['new_secret'] = pyotp.random_base32()
                    
                    new_secret = st.session_state['new_secret']
                    
                    # Generate QR Code
                    uri = pyotp.totp.TOTP(new_secret).provisioning_uri(name=user_data['sales_name'], issuer_name="Distributor App")
                    qr_img = qrcode.make(uri)
                    img_bytes = io.BytesIO()
                    qr_img.save(img_bytes, format='PNG')
                    
                    st.image(img_bytes.getvalue(), caption="Scan QR ini di Google Authenticator HP Anda")
                    st.code(new_secret, language="text")
                    st.caption("Jika kamera rusak, masukkan kode di atas manual ke aplikasi.")
                    
                    code_input = st.text_input("Masukkan 6 Angka dari Aplikasi:")
                    if st.button("Simpan & Login"):
                        totp = pyotp.TOTP(new_secret)
                        if totp.verify(code_input):
                            save_user_secret(user_data['username'], new_secret)
                            st.session_state['logged_in'] = True
                            st.session_state['role'] = user_data['role']
                            st.session_state['sales_name'] = user_data['sales_name']
                            log_activity(user_data['sales_name'], "LOGIN SUCCESS (NEW 2FA)")
                            st.rerun()
                        else:
                            st.error("Kode Salah. Coba lagi.")
                
                # JIKA SUDAH PUNYA SECRET KEY -> VERIFIKASI BIASA
                else:
                    st.write(f"Halo, **{user_data['sales_name']}** 👋")
                    st.caption("Buka Google Authenticator di HP Anda.")
                    code_input = st.text_input("Masukkan Kode 6 Digit:", max_chars=6)
                    
                    if st.button("Masuk"):
                        totp = pyotp.TOTP(secret)
                        if totp.verify(code_input):
                            st.session_state['logged_in'] = True
                            st.session_state['role'] = user_data['role']
                            st.session_state['sales_name'] = user_data['sales_name']
                            log_activity(user_data['sales_name'], "LOGIN SUCCESS (2FA)")
                            st.rerun()
                        else:
                            st.error("Kode OTP Salah!")
                            log_activity(user_data['sales_name'], "FAILED LOGIN - WRONG OTP")
                    
                    if st.button("Kembali"):
                        st.session_state['login_step'] = 'credentials'
                        st.rerun()

def main_dashboard():
    # --- SECURITY: WATERMARK ---
    user_name = st.session_state.get('sales_name', 'User')
    st.markdown(f"""
    <style>
    .watermark {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        z-index: 9999; pointer-events: none;
        display: flex; flex-wrap: wrap; justify-content: space-around; align-content: space-around;
        opacity: 0.04;
    }}
    .watermark-text {{
        transform: rotate(-45deg); font-size: 24px; color: #000; font-weight: bold; margin: 50px;
    }}
    </style>
    <div class="watermark">
        {''.join([f'<div class="watermark-text">{user_name} - CONFIDENTIAL</div>' for _ in range(20)])}
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.write("## 👤 User Profile")
        st.info(f"**{st.session_state['sales_name']}**\n\nRole: {st.session_state['role'].upper()}")
        
        # --- AUDIT LOG (DIREKTUR) ---
        if st.session_state['role'] == 'direktur':
            with st.expander("🛡️ Audit Log"):
                if os.path.isfile('audit_log.csv'):
                    audit_df = pd.read_csv('audit_log.csv', names=['Waktu', 'User', 'Aksi'])
                    st.dataframe(audit_df.sort_values('Waktu', ascending=False), height=200)
                else:
                    st.write("Belum ada data.")

        if st.button("🚪 Logout", use_container_width=True):
            log_activity(st.session_state['sales_name'], "LOGOUT")
            st.session_state['logged_in'] = False
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.markdown("---")
            
    df = load_data()
    if df is None or df.empty:
        st.error("Gagal load data.")
        return

    # --- SECURITY: STRICT SCOPING ---
    user_role = st.session_state['role']
    if user_role not in ['manager', 'direktur', 'supervisor'] and user_name.lower() != 'fauziah':
        df = df[df['Penjualan'] == user_name]
    elif user_name.upper() in TARGET_DATABASE: 
         spv_brands = list(TARGET_DATABASE[user_name.upper()].keys())
         df = df[df['Merk'].isin(spv_brands)]

    # --- MAIN CONTENT ---
    st.sidebar.subheader("📅 Filter Periode")
    today = datetime.date.today()
    if 'start_date' not in st.session_state:
        st.session_state['start_date'] = df['Tanggal'].max().date().replace(day=1)
        st.session_state['end_date'] = df['Tanggal'].max().date()
        
    c_p1, c_p2 = st.sidebar.columns(2)
    with c_p1:
        if st.button("Bulan Ini"):
            st.session_state['start_date'] = today.replace(day=1)
            st.session_state['end_date'] = today
    with c_p2:
        if st.button("Kemarin"):
            st.session_state['start_date'] = today - datetime.timedelta(days=1)
            st.session_state['end_date'] = today - datetime.timedelta(days=1)
            
    date_range = st.sidebar.date_input("Rentang Waktu", [st.session_state['start_date'], st.session_state['end_date']])
    
    # --- SCOPE FILTER ---
    if role in ['manager', 'direktur'] or my_name.lower() == 'fauziah':
        sales_list = ["SEMUA"] + sorted(list(df['Penjualan'].unique()))
        target_sales_filter = st.sidebar.selectbox("Pantau Sales:", sales_list)
        if target_sales_filter == "SEMUA": df_active = df
        else: df_active = df[df['Penjualan'] == target_sales_filter]
    else:
        target_sales_filter = my_name
        df_active = df

    # Date Filtering
    if len(date_range) == 2:
        df_active = df_active[(df_active['Tanggal'].dt.date >= date_range[0]) & (df_active['Tanggal'].dt.date <= date_range[1])]

    # --- TABS ---
    t1, t2, t3, t4, t5 = st.tabs(["📊 Rapor", "📈 Tren", "🏆 Produk", "🚀 Kejar Omset", "📋 Data"])
    
    with t1:
        st.subheader("Rapor Kinerja")
        total_omset = df_active['Jumlah'].sum()
        st.metric("Total Omset", format_idr(total_omset))
        
        # Target Logic Simple
        if target_sales_filter in INDIVIDUAL_TARGETS:
             targets = INDIVIDUAL_TARGETS[target_sales_filter]
             for brand, val in targets.items():
                 real = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                 render_custom_progress(f"{brand}", real, val)
        elif role in ['manager', 'direktur']:
             render_custom_progress("Nasional", total_omset, TARGET_NASIONAL_VAL)

    with t2:
        st.subheader("Tren Harian")
        daily = df_active.groupby('Tanggal')['Jumlah'].sum().reset_index()
        st.plotly_chart(px.line(daily, x='Tanggal', y='Jumlah'), use_container_width=True)

    with t3:
        st.subheader("Top Produk")
        top = df_active.groupby('Nama Barang')['Jumlah'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top, x='Jumlah', y='Nama Barang', orientation='h'), use_container_width=True)

    with t4:
        st.subheader("🚀 Kejar Omset (Smart AI)")
        st.caption("Rekomendasi berdasarkan pola belanja toko lain.")
        
        recs = get_cross_sell_recommendations(df) # Use global df for better pattern
        if recs is not None and not recs.empty:
            # Filter recs by user scope
            if role == 'sales':
                recs = recs[recs['Sales'] == user_name]
            
            st.dataframe(recs, use_container_width=True)
        else:
            st.info("Belum ada pola belanja yang cukup kuat untuk rekomendasi.")

    with t5:
        st.subheader("Data Rincian")
        st.dataframe(df_active)
        
        if role in ['direktur', 'manager']:
             csv = df_active.to_csv(index=False).encode('utf-8')
             st.download_button("Download CSV", data=csv, file_name="sales_data.csv", mime="text/csv")

# --- 5. EXECUTION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()
