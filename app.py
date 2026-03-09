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
import pyotp  
import qrcode 
from calendar import monthrange
from itertools import combinations
from collections import Counter
import calendar

# --- LIBRARY UNTUK TABEL EXCEL-LIKE (PILIHAN A) ---
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
    AGGRID_AVAILABLE = True
except ImportError:
    AGGRID_AVAILABLE = False

# --- ROADMAP 1: IMPORT CONFIGURATION ---
import config

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
    [data-testid="stElementToolbar"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE LOGIC
# ==========================================

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

def generate_daily_token():
    secret_salt = "RAHASIA_PERUSAHAAN_2025" 
    today_str = get_current_time_wib().strftime("%Y-%m-%d")
    raw_string = f"{today_str}-{secret_salt}"
    hash_object = hashlib.sha256(raw_string.encode())
    hex_dig = hash_object.hexdigest()
    numeric_filter = filter(str.isdigit, hex_dig)
    numeric_string = "".join(numeric_filter)
    token = numeric_string[:4].ljust(4, '0')
    return token

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
    
    faktur_col = None
    for col in df.columns:
        if 'faktur' in col.lower() or 'bukti' in col.lower() or 'invoice' in col.lower():
            faktur_col = col; break
    if faktur_col: df = df.rename(columns={faktur_col: 'No Faktur'})
    
    if 'Nama Outlet' in df.columns:
        df = df[~df['Nama Outlet'].astype(str).str.match(r'^(Total|Jumlah|Subtotal|Grand|Rekap)', case=False, na=False)]
        df = df[df['Nama Outlet'].astype(str).str.strip() != ''] 
        df = df[df['Nama Outlet'].astype(str).str.lower() != 'nan']

    if 'Nama Barang' in df.columns:
        df = df[~df['Nama Barang'].astype(str).str.match(r'^(Total|Jumlah)', case=False, na=False)]
        df = df[df['Nama Barang'].astype(str).str.strip() != ''] 

    # --- REFACTORING: USE CONFIG.PY ---
    df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(config.SALES_MAPPING)
    
    valid_sales_names = list(config.INDIVIDUAL_TARGETS.keys())
    valid_sales_names.extend(["MADONG", "LISMAN", "AKBAR", "WILLIAM"]) 
    
    df.loc[~df['Penjualan'].isin(valid_sales_names), 'Penjualan'] = 'Non-Sales'
    df['Penjualan'] = df['Penjualan'].astype('category')

    def normalize_brand(raw_brand):
        raw_upper = str(raw_brand).upper()
        # --- REFACTORING: USE CONFIG.PY ---
        for target_brand, keywords in config.BRAND_ALIASES.items():
            for keyword in keywords:
                if keyword in raw_upper: return target_brand
        return raw_brand
    df['Merk'] = df['Merk'].apply(normalize_brand).astype('category')
    
    df['Jumlah'] = df['Jumlah'].astype(str).str.replace(r'[Rp\s]', '', regex=True).str.replace('.', '').str.replace(',', '.')
    df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce', format='mixed')
    def fix_swapped_date(d):
        if pd.isnull(d): return d
        try:
            if d.day <= 12 and d.day != d.month:
                return d.replace(day=d.month, month=d.day)
        except: pass
        return d
    df['Tanggal'] = df['Tanggal'].apply(fix_swapped_date)
    df = df.dropna(subset=['Tanggal'])
    
    cols_to_convert = ['Kota', 'Nama Outlet', 'Nama Barang', 'No Faktur']
    for col in cols_to_convert:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    return df

USER_DB_FILE = 'users.csv'
def load_users():
    try:
        df = pd.read_csv(USER_DB_FILE)
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
# 4. FUNGSI ANALISIS CERDAS (Roadmap 6: Optimized)
# ==========================================

# --- ROADMAP 6: ADD CACHING FOR PERFORMANCE ---
@st.cache_data(ttl=3600, show_spinner=False)
def compute_association_rules(df):
    if 'No Faktur' not in df.columns or 'Nama Barang' not in df.columns: return None
    item_support = df.groupby('Nama Barang')['No Faktur'].nunique()
    total_transactions = df['No Faktur'].nunique()
    pair_df = df.groupby('No Faktur')['Nama Barang'].apply(lambda x: list(combinations(sorted(x.unique()), 2)) if len(x.unique()) > 1 else [])
    pairs = [p for sublist in pair_df for p in sublist]
    pair_support = Counter(pairs)
    rules = []
    for (A, B), supp_ab in pair_support.items():
        conf_ab = supp_ab / item_support[A]
        conf_ba = supp_ab / item_support[B]
        rules.append({'antecedent': A, 'consequent': B, 'support': supp_ab / total_transactions, 'confidence': conf_ab})
        rules.append({'antecedent': B, 'consequent': A, 'support': supp_ab / total_transactions, 'confidence': conf_ba})
    rules_df = pd.DataFrame(rules).drop_duplicates().sort_values('confidence', ascending=False)
    rules_df = rules_df[rules_df['confidence'] > 0.5] 
    return rules_df

# --- ROADMAP 6: ADD CACHING FOR PERFORMANCE ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_cross_sell_recommendations(df):
    rules_df = compute_association_rules(df)
    if rules_df is None or rules_df.empty: return None
    outlet_purchases = df.groupby('Nama Outlet')['Nama Barang'].apply(set).to_dict()
    recommendations = []
    for outlet, purchased in outlet_purchases.items():
        if not purchased: continue
        sales = df[df['Nama Outlet'] == outlet]['Penjualan'].unique()[0] if not df[df['Nama Outlet'] == outlet].empty else "-"
        possible_recs = {}
        for item in purchased:
            matching_rules = rules_df[rules_df['antecedent'] == item]
            for _, rule in matching_rules.iterrows():
                consequent = rule['consequent']
                if consequent not in purchased:
                    conf = rule['confidence']
                    if consequent not in possible_recs or conf > possible_recs[consequent][1]:
                        possible_recs[consequent] = (item, conf)
        if possible_recs:
            top_consequent, (antecedent, conf) = max(possible_recs.items(), key=lambda x: x[1][1])
            rec_text = f"Tawarkan {top_consequent}, karena {conf*100:.0f}% toko yang beli {antecedent} juga membelinya."
            recommendations.append({'Toko': outlet, 'Sales': sales, 'Rekomendasi': rec_text})
    if recommendations:
        return pd.DataFrame(recommendations)
    return None

# ==========================================
# 5. MAIN LOGIC (LOGIN & DASHBOARD)
# ==========================================

def login_page():
    st.markdown("<br><br><h1 style='text-align: center;'>🦅 Executive Command Center</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            st.markdown(f"<div style='text-align:center; color:#888; font-size:12px;'>Protected by Google Authenticator</div>", unsafe_allow_html=True)
            
            if 'login_step' not in st.session_state: st.session_state['login_step'] = 'credentials'
            if 'temp_user_data' not in st.session_state: st.session_state['temp_user_data'] = None
            
            if st.session_state['login_step'] == 'credentials':
                with st.form("cred_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submitted = st.form_submit_button("Verifikasi Akun", use_container_width=True)
                    
                    if submitted:
                        users = load_users()
                        if users.empty:
                            st.error("Database user tidak ditemukan.")
                        else:
                            match = users[(users['username'] == username) & (users['password'] == password)]
                            
                            if not match.empty:
                                user_row = match.iloc[0]
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

            elif st.session_state['login_step'] == '2fa_check':
                user_data = st.session_state['temp_user_data']
                secret = user_data['secret_key']
                
                if pd.isna(secret) or secret == "":
                    st.error("⛔ Akses Ditolak: 2FA Belum Aktif")
                    st.info("Silakan hubungi Direktur/Manager untuk mendapatkan QR Code Aktivasi akun Anda.")
                    if st.button("Kembali"):
                         st.session_state['login_step'] = 'credentials'
                         st.rerun()
                
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
        
        if st.session_state['role'] in ['direktur', 'manager']:
            st.markdown("---")
            st.write("### 🔐 Manajemen Akses Sales")
            with st.expander("Setup 2FA Sales"):
                users_df = load_users()
                sales_list = users_df['username'].tolist()
                selected_user_setup = st.selectbox("Pilih User:", sales_list)
                
                if st.button("Buat/Lihat QR Code"):
                    user_record = users_df[users_df['username'] == selected_user_setup].iloc[0]
                    current_secret = user_record['secret_key']
                    
                    if pd.isna(current_secret) or current_secret == "":
                        new_secret = pyotp.random_base32()
                        save_user_secret(selected_user_setup, new_secret)
                        st.success(f"Secret Key Baru Dibuat untuk {selected_user_setup}!")
                        current_secret = new_secret
                    else:
                        st.info(f"User {selected_user_setup} sudah memiliki kunci.")

                    uri = pyotp.totp.TOTP(current_secret).provisioning_uri(
                        name=user_record['sales_name'], 
                        issuer_name="Distributor App"
                    )
                    qr_img = qrcode.make(uri)
                    img_bytes = io.BytesIO()
                    qr_img.save(img_bytes, format='PNG')
                    
                    st.image(img_bytes.getvalue(), caption=f"QR Code untuk {user_record['sales_name']}")
                    st.warning(f"⚠️ **PENTING:** Foto QR ini dan kirim JAPRI ke {user_record['sales_name']}. Jangan share di grup!")
                    st.code(current_secret, language="text")

        if st.session_state['role'] == 'direktur':
            with st.expander("🛡️ Audit Log"):
                if os.path.isfile('audit_log.csv'):
                    try:
                        audit_df = pd.read_csv('audit_log.csv', names=['Waktu', 'User', 'Aksi'])
                        st.dataframe(audit_df.sort_values('Waktu', ascending=False), height=200)
                    except: st.write("Format log invalid.")
                else: st.write("Belum ada data.")

        if st.button("🚪 Logout", use_container_width=True):
            log_activity(st.session_state['sales_name'], "LOGOUT")
            st.session_state['logged_in'] = False
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        st.markdown("---")
            
    df = load_data()
    if df is None or df.empty:
        st.error("Gagal load data.")
        return

    user_role = st.session_state['role']
    role = user_role
    my_name = user_name
    
    if user_role not in ['manager', 'direktur', 'supervisor'] and user_name.lower() != 'fauziah':
        df = df[df['Penjualan'] == user_name]
    elif user_name.upper() in config.TARGET_DATABASE: 
         spv_brands = list(config.TARGET_DATABASE[user_name.upper()].keys())
         df = df[df['Merk'].isin(spv_brands)]

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
    
    if role in ['manager', 'direktur'] or my_name.lower() == 'fauziah':
        sales_list = ["SEMUA"] + sorted(list(df['Penjualan'].dropna().astype(str).unique()))
        target_sales_filter = st.sidebar.selectbox("Pantau Sales:", sales_list)
        if target_sales_filter == "SEMUA": df_active = df
        else: df_active = df[df['Penjualan'] == target_sales_filter]
    else:
        target_sales_filter = my_name
        df_active = df

    if len(date_range) == 2:
        df_active = df_active[(df_active['Tanggal'].dt.date >= date_range[0]) & (df_active['Tanggal'].dt.date <= date_range[1])]
    
    with st.sidebar.expander("🔍 Filter Lanjutan", expanded=False):
        unique_brands = sorted(df_active['Merk'].dropna().astype(str).unique())
        pilih_merk = st.multiselect("Pilih Merk", unique_brands)
        if pilih_merk: df_active = df_active[df_active['Merk'].isin(pilih_merk)]
        
        unique_outlets = sorted(df_active['Nama Outlet'].dropna().astype(str).unique())
        pilih_outlet = st.multiselect("Pilih Outlet", unique_outlets)
        if pilih_outlet: df_active = df_active[df_active['Nama Outlet'].isin(pilih_outlet)]

    # --- TABS ---
    t1, t2, t3, t4, t5 = st.tabs(["📊 Rapor", "📈 Tren", "🏆 Produk", "📋 Data Rincian", "🚀 Kejar Omset"])
    
    with t1:
        st.subheader("Rapor Kinerja")
        total_omset = df_active['Jumlah'].sum()
        st.metric("Total Omset", format_idr(total_omset))
        
        if target_sales_filter in config.INDIVIDUAL_TARGETS:
             targets = config.INDIVIDUAL_TARGETS[target_sales_filter]
             for brand, val in targets.items():
                 real = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                 render_custom_progress(f"{brand}", real, val)
        elif role in ['manager', 'direktur']:
             render_custom_progress("Nasional", total_omset, config.TARGET_NASIONAL_VAL)

    with t2:
        st.subheader("Tren Harian")
        daily = df_active.groupby('Tanggal')['Jumlah'].sum().reset_index()
        st.plotly_chart(px.line(daily, x='Tanggal', y='Jumlah'), use_container_width=True)

    with t3:
        st.subheader("Top Produk")
        top = df_active.groupby('Nama Barang')['Jumlah'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top, x='Jumlah', y='Nama Barang', orientation='h'), use_container_width=True)

    with t4:
        # ========================================================
        # PERUBAHAN UI: TABEL "DATA RINCIAN" ALA EXCEL (SUB-TABS)
        # ========================================================
        st.subheader("📋 Data Rincian & Analisis Excel")
        
        if not AGGRID_AVAILABLE:
            st.warning("Pustaka 'streamlit-aggrid' belum terinstall. Menggunakan tabel bawaan.")
            
        # 1. Filter Merk Terlebih Dahulu (Sesuai Permintaan)
        list_merk_excel = sorted(df_active['Merk'].dropna().astype(str).unique())
        selected_merk_excel = st.selectbox("🎯 Pilih Merk untuk Analisis Y VS Y dan Rekap:", ["SEMUA"] + list_merk_excel)
        
        if selected_merk_excel != "SEMUA":
            df_excel = df_active[df_active['Merk'] == selected_merk_excel].copy()
        else:
            df_excel = df_active.copy()
            
        # Tambahkan Kolom Penunjang Waktu
        df_excel['Tahun'] = df_excel['Tanggal'].dt.year
        df_excel['Bulan Angka'] = df_excel['Tanggal'].dt.month
        
        # Buat Sub-Tabs
        tab_master, tab_rekap, tab_yoy = st.tabs(["🗃️ Master Data", "📊 Rekap Pivot", "📈 Y VS Y"])
        
        # --- TAB MASTER DATA ---
        with tab_master:
            st.markdown("##### Master Data Transaksi Terperinci")
            if AGGRID_AVAILABLE:
                gb = GridOptionsBuilder.from_dataframe(df_excel[['Tanggal', 'No Faktur', 'Nama Outlet', 'Merk', 'Nama Barang', 'Penjualan', 'Jumlah']])
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_side_bar()
                gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=True)
                gridOptions = gb.build()
                AgGrid(df_excel, gridOptions=gridOptions, enable_enterprise_modules=True, height=500, theme='alpine')
            else:
                st.dataframe(df_excel[['Tanggal', 'No Faktur', 'Nama Outlet', 'Merk', 'Nama Barang', 'Penjualan', 'Jumlah']], use_container_width=True)

        # --- TAB REKAP PIVOT ---
        with tab_rekap:
            st.markdown("##### Pivot Table Rekapitulasi")
            row_dim = st.selectbox("Pilih Baris (Rows):", ["Nama Outlet", "Nama Barang", "Kota", "Penjualan", "Merk"], index=0)
            
            if not df_excel.empty:
                # Pivot Table: Rows = Pilihan, Columns = Bulan Angka, Value = Jumlah Penjualan
                pivot_df = pd.pivot_table(
                    df_excel, 
                    values='Jumlah', 
                    index=row_dim, 
                    columns='Bulan Angka', 
                    aggfunc='sum',
                    fill_value=0
                )
                
                # Ubah Angka Bulan menjadi Nama Bulan
                pivot_df.columns = [calendar.month_abbr[i] for i in pivot_df.columns]
                
                # Wajib Ada Total Penjualan (Grand Total per baris)
                pivot_df['TOTAL PENJUALAN'] = pivot_df.sum(axis=1)
                
                # Wajib Ada Total Keseluruhan (Baris paling bawah)
                pivot_df.loc['GRAND TOTAL'] = pivot_df.sum(axis=0)
                
                pivot_df = pivot_df.reset_index()
                
                if AGGRID_AVAILABLE:
                    gb_pivot = GridOptionsBuilder.from_dataframe(pivot_df)
                    for col in pivot_df.columns:
                        if col != row_dim:
                            gb_pivot.configure_column(col, type=["numericColumn","numberColumnFilter"], valueFormatter="x.toLocaleString('id-ID', {style: 'currency', currency: 'IDR', minimumFractionDigits: 0})")
                    gridOptionsPivot = gb_pivot.build()
                    AgGrid(pivot_df, gridOptions=gridOptionsPivot, height=500, theme='balham')
                else:
                    st.dataframe(pivot_df.style.format({col: "Rp {:,.0f}" for col in pivot_df.columns if col != row_dim}), use_container_width=True)
            else:
                st.info("Data Kosong untuk Merk ini.")

        # --- TAB YEAR VS YEAR (Y VS Y) ---
        with tab_yoy:
            st.markdown("##### Year VS Year (Perbandingan Omset Bulanan)")
            
            tahun_list = sorted(df_excel['Tahun'].dropna().unique())
            if len(tahun_list) >= 2:
                c_y1, c_y2 = st.columns(2)
                with c_y1:
                    thn_awal = st.selectbox("Pilih Tahun Awal:", tahun_list, index=len(tahun_list)-2)
                with c_y2:
                    thn_akhir = st.selectbox("Pilih Tahun Pembanding:", tahun_list, index=len(tahun_list)-1)
                
                df_yoy = df_excel[df_excel['Tahun'].isin([thn_awal, thn_akhir])]
                pivot_yoy = pd.pivot_table(
                    df_yoy,
                    values='Jumlah',
                    index='Bulan Angka',
                    columns='Tahun',
                    aggfunc='sum',
                    fill_value=0
                )
                
                # Pastikan ada 12 Bulan meskipun ada bulan yang belum terjadi transaksi
                all_months = pd.DataFrame(index=range(1,13))
                pivot_yoy = all_months.join(pivot_yoy).fillna(0)
                
                # Ubah angka bulan jadi nama bulan
                pivot_yoy.index = pivot_yoy.index.map(lambda x: calendar.month_abbr[x])
                pivot_yoy.index.name = 'Bulan'
                
                if thn_awal in pivot_yoy.columns and thn_akhir in pivot_yoy.columns:
                    # Rumus Growth %
                    pivot_yoy['Growth (%)'] = ((pivot_yoy[thn_akhir] - pivot_yoy[thn_awal]) / pivot_yoy[thn_awal].replace(0, np.nan)) * 100
                    pivot_yoy['Growth (%)'] = pivot_yoy['Growth (%)'].fillna(0)
                    
                    # Tambah Baris Grand Total di bawah tabel
                    total_awal = pivot_yoy[thn_awal].sum()
                    total_akhir = pivot_yoy[thn_akhir].sum()
                    total_growth = ((total_akhir - total_awal) / total_awal) * 100 if total_awal > 0 else 0
                    pivot_yoy.loc['GRAND TOTAL'] = [total_awal, total_akhir, total_growth]
                    
                    pivot_yoy = pivot_yoy.reset_index()
                    pivot_yoy.columns = ['Bulan', f'Sales {thn_awal}', f'Sales {thn_akhir}', 'Growth (%)']
                    
                    if AGGRID_AVAILABLE:
                        gb_yoy = GridOptionsBuilder.from_dataframe(pivot_yoy)
                        gb_yoy.configure_column(f'Sales {thn_awal}', valueFormatter="x.toLocaleString('id-ID', {style: 'currency', currency: 'IDR', minimumFractionDigits: 0})")
                        gb_yoy.configure_column(f'Sales {thn_akhir}', valueFormatter="x.toLocaleString('id-ID', {style: 'currency', currency: 'IDR', minimumFractionDigits: 0})")
                        
                        # Conditional Formatting Pakai JavaScript untuk Ag-Grid
                        cellstyle_jscode = JsCode("""
                        function(params) {
                            if (params.value > 0) {
                                return {'color': 'white', 'backgroundColor': '#2ecc71', 'fontWeight': 'bold'};
                            } else if (params.value < 0) {
                                return {'color': 'white', 'backgroundColor': '#e74c3c', 'fontWeight': 'bold'};
                            } else {
                                return {'color': 'black', 'backgroundColor': '#f1c40f'};
                            }
                        };
                        """)
                        gb_yoy.configure_column('Growth (%)', cellStyle=cellstyle_jscode, valueFormatter="x.toFixed(2) + '%'")
                        
                        gridOptionsYoy = gb_yoy.build()
                        AgGrid(pivot_yoy, gridOptions=gridOptionsYoy, height=450, theme='balham', allow_unsafe_jscode=True)
                    else:
                        # Conditional Formatting Bawaan Streamlit jika Ag-Grid gagal load
                        def color_growth(val):
                            if val > 0: return 'background-color: #2ecc71; color: white;'
                            elif val < 0: return 'background-color: #e74c3c; color: white;'
                            return 'background-color: #f1c40f; color: black;'

                        st.dataframe(
                            pivot_yoy.style.format({
                                f'Sales {thn_awal}': 'Rp {:,.0f}',
                                f'Sales {thn_akhir}': 'Rp {:,.0f}',
                                'Growth (%)': '{:,.2f}%'
                            }).map(color_growth, subset=['Growth (%)']),
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    # Tampilkan Grafik Perbandingan
                    fig_yoy = px.bar(pivot_yoy[pivot_yoy['Bulan'] != 'GRAND TOTAL'], x='Bulan', y=[f'Sales {thn_awal}', f'Sales {thn_akhir}'], barmode='group', title=f"Grafik Perbandingan {thn_awal} vs {thn_akhir}")
                    st.plotly_chart(fig_yoy, use_container_width=True)
                else:
                    st.warning("Data untuk tahun yang dipilih belum lengkap.")
            else:
                st.warning("Belum ada data minimal 2 Tahun. Y VS Y memerlukan komparasi 2 tahun yang berbeda.")

        # Tombol Download Excel diletakkan di luar sub-tabs (Bawah)
        if role in ['direktur', 'manager', 'supervisor']:
            st.divider()
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_excel.drop(columns=['Tahun', 'Bulan Angka'], errors='ignore').to_excel(writer, index=False, sheet_name='Master Data')
                if not df_excel.empty:
                    # Save the latest pivot generated
                    pd.pivot_table(df_excel, values='Jumlah', index=row_dim, columns='Bulan Angka', aggfunc='sum', fill_value=0).to_excel(writer, sheet_name='Rekap Pivot')
            
            st.download_button(
                label="📥 Download Excel Report Lanjutan (Semua Tab)",
                data=output.getvalue(),
                file_name=f"Laporan_Excel_Style_{selected_merk_excel}_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with t5:
        st.subheader("🚀 Kejar Omset (Smart AI)")
        st.caption("Rekomendasi berdasarkan pola belanja toko lain.")
        
        recs = get_cross_sell_recommendations(df) 
        if recs is not None and not recs.empty:
            if role == 'sales':
                recs = recs[recs['Sales'] == user_name]
            st.dataframe(recs, use_container_width=True)
        else:
            st.info("Belum ada pola belanja yang cukup kuat untuk rekomendasi.")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()
