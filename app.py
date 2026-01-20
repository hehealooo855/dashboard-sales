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
from calendar import monthrange
from itertools import combinations
from collections import Counter

# --- IMPORT KONFIGURASI DARI FILE LAIN ---
# Pastikan file config.py ada di folder yang sama
try:
    from config import TARGET_DATABASE, INDIVIDUAL_TARGETS, SUPERVISOR_TOTAL_TARGETS, TARGET_NASIONAL_VAL, BRAND_ALIASES, SALES_MAPPING
except ImportError:
    st.error("File config.py tidak ditemukan. Pastikan file tersebut ada di folder yang sama.")
    st.stop()

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
    /* Memastikan text dalam dataframe wrap dengan baik */
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
# 3. CORE LOGIC
# ==========================================

# --- SECURITY FEATURE: AUDIT LOGGING ---
def log_activity(user, action):
    log_file = 'audit_log.csv'
    timestamp = get_current_time_wib().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([[timestamp, user, action]], columns=['Timestamp', 'User', 'Action'])
    
    if not os.path.isfile(log_file):
        new_log.to_csv(log_file, index=False)
    else:
        new_log.to_csv(log_file, mode='a', header=False, index=False)

# --- FITUR: HARDCODED TIMEZONE WIB (GMT+7) ---
def get_current_time_wib():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

def format_idr(value):
    try:
        return f"Rp {value:,.0f}".replace(",", ".")
    except:
        return "Rp 0"

# --- SECURITY: DAILY TOKEN GENERATOR ---
def generate_daily_token():
    secret_salt = "RAHASIA_PERUSAHAAN_2025" 
    now_wib = get_current_time_wib()
    time_key = now_wib.strftime("%Y-%m-%d-%p")
    raw_string = f"{time_key}-{secret_salt}"
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
    print("--- [DEBUG] Sedang mendownload data dari Google Sheet... ---")
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    try:
        url_with_ts = f"{url}&t={int(time.time())}"
        df = pd.read_csv(url_with_ts, dtype=str)
        print("--- [DEBUG] Download selesai. Memulai cleaning data... ---")
    except Exception as e:
        print(f"--- [ERROR] Gagal download: {e} ---")
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
    
    if faktur_col:
        df = df.rename(columns={faktur_col: 'No Faktur'})
    
    # --- CLEANING SAMPAH ---
    if 'Nama Outlet' in df.columns:
        df = df[~df['Nama Outlet'].astype(str).str.match(r'^(Total|Jumlah|Subtotal|Grand|Rekap)', case=False, na=False)]
        df = df[df['Nama Outlet'].astype(str).str.strip() != ''] 
        df = df[df['Nama Outlet'].astype(str).str.lower() != 'nan']

    if 'Nama Barang' in df.columns:
        df = df[~df['Nama Barang'].astype(str).str.match(r'^(Total|Jumlah)', case=False, na=False)]
        df = df[df['Nama Barang'].astype(str).str.strip() != ''] 

    # --- NORMALISASI SALES ---
    df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(SALES_MAPPING)
    
    # --- LOGIKA NON-SALES ---
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
    
    # --- NUMERIC CLEANING ---
    df['Jumlah'] = df['Jumlah'].astype(str)
    df['Jumlah'] = df['Jumlah'].str.replace(r'[Rp\s]', '', regex=True)
    df['Jumlah'] = df['Jumlah'].str.replace('.', '', regex=False)
    df['Jumlah'] = df['Jumlah'].str.replace(',', '.', regex=False)
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
    df = df.dropna(subset=['Tanggal'])
    
    # --- CONVERT STRING FOR METADATA ---
    cols_to_convert = ['Kota', 'Nama Outlet', 'Nama Barang', 'No Faktur']
    for col in cols_to_convert:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    print("--- [DEBUG] Selesai cleaning data. Siap ditampilkan. ---")
    return df

def load_users():
    try:
        if not os.path.exists('users.csv'):
            print("--- [WARNING] File users.csv tidak ditemukan! Login mungkin gagal. ---")
            return pd.DataFrame()
        return pd.read_csv('users.csv')
    except:
        return pd.DataFrame()

# ==========================================
# FUNGSI TAMBAHAN (MBA)
# ==========================================
def compute_association_rules(df):
    if 'No Faktur' not in df.columns or 'Nama Barang' not in df.columns:
        return None
    
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
    if not rules_df.empty:
        rules_df = rules_df[rules_df['confidence'] > 0.5]
    
    return rules_df

def get_cross_sell_recommendations(df):
    rules_df = compute_association_rules(df)
    if rules_df is None or rules_df.empty:
        return None
    
    outlet_purchases = df.groupby('Nama Outlet')['Nama Barang'].apply(set).to_dict()
    
    recommendations = []
    for outlet, purchased in outlet_purchases.items():
        if not purchased:
            continue
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
# 4. MAIN DASHBOARD LOGIC
# ==========================================
def login_page():
    st.markdown("<br><br><h1 style='text-align: center;'>🦅 Executive Command Center</h1>", unsafe_allow_html=True)
    
    daily_token = generate_daily_token()
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            st.markdown(f"<div style='text-align:center; color:#888; font-size:12px;'>Sistem Terproteksi</div>", unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                otp_input = st.text_input("Kode Akses Harian (OTP)", placeholder="Masukkan Kode 4 Digit", max_chars=4)
                
                submitted = st.form_submit_button("Masuk Sistem", use_container_width=True)
                
                if submitted:
                    users = load_users()
                    if users.empty:
                        st.error("Database user (users.csv) tidak ditemukan. Hubungi Admin.")
                    else:
                        match = users[(users['username'] == username) & (users['password'] == password)]
                        
                        if match.empty:
                            st.error("Username atau Password salah.")
                            log_activity(username, "FAILED LOGIN - WRONG PASS")
                        else:
                            user_role = match.iloc[0]['role']
                            user_sales_name = match.iloc[0]['sales_name']
                            is_authorized = False
                            
                            if user_role in ['direktur', 'manager']:
                                is_authorized = True
                            else:
                                if otp_input == daily_token:
                                    is_authorized = True
                                else:
                                    st.error("⛔ Kode Akses Harian Salah! Hubungi Admin.")
                                    log_activity(user_sales_name, f"FAILED LOGIN - WRONG OTP ({otp_input})")
                            
                            if is_authorized:
                                st.session_state['logged_in'] = True
                                st.session_state['role'] = user_role
                                st.session_state['sales_name'] = user_sales_name
                                log_activity(user_sales_name, "LOGIN SUCCESS")
                                st.success("Login Berhasil! Mengalihkan...")
                                time.sleep(1)
                                st.rerun()

def main_dashboard():
    # --- SECURITY SECTION ---
    def add_aggressive_watermark():
        user_name = st.session_state.get('sales_name', 'User')
        role_name = st.session_state.get('role', 'staff')
        
        if role_name != 'direktur':
            # --- PERBAIKAN: JUMLAH DIKURANGI DARI 300 KE 50 AGAR TIDAK HANG ---
            # Tetap ada watermark, tapi lebih ringan untuk browser
            limit_loop = 50 
            
            st.markdown(f"""
            <style>
            .watermark-container {{
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                z-index: 99999; pointer-events: none; overflow: hidden;
                display: flex; flex-wrap: wrap; opacity: 0.15;
            }}
            .watermark-text {{
                font-family: 'Arial', sans-serif; font-size: 16px; color: #555;
                font-weight: 700; transform: rotate(-30deg); white-space: nowrap;
                margin: 40px; user-select: none;
            }}
            </style>
            <div class="watermark-container">
                {''.join([f'<div class="watermark-text">{user_name} • CONFIDENTIAL • {get_current_time_wib().strftime("%H:%M")}</div>' for _ in range(limit_loop)])}
            </div>
            <script>
            window.addEventListener('blur', () => {{
                document.body.style.filter = 'blur(20px) brightness(0.4)'; 
                document.body.style.backgroundColor = '#000';
            }});
            window.addEventListener('focus', () => {{
                document.body.style.filter = 'none';
                document.body.style.backgroundColor = '#fff';
            }});
            document.addEventListener('keydown', (e) => {{
                if ((e.ctrlKey || e.metaKey) && (e.key === 'p' || e.key === 's')) {{
                    e.preventDefault();
                    alert('⚠️ Action Disabled for Security Reasons!');
                }}
            }});
            </script>
            """, unsafe_allow_html=True)
    
    add_aggressive_watermark()
    # -----------------------------------------------

    if st.session_state['role'] != 'direktur':
        st.markdown("""
            <style>
            @media print { body { display: none !important; } }
            body { -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none; }
            img { pointer-events: none; }
            </style>
            """, unsafe_allow_html=True)

    with st.sidebar:
        st.write("## 👤 User Profile")
        st.info(f"**{st.session_state['sales_name']}**\n\nRole: {st.session_state['role'].upper()}")
        
        if st.session_state['role'] in ['manager', 'direktur']:
            st.markdown("---")
            st.write("### 🔐 Admin Zone")
            token_hari_ini = generate_daily_token()
            st.write(f"**Token Master (Refresh per 12 Jam):** `{token_hari_ini}`")
            st.markdown("#### 📱 Generate QR Sales")
            target_sales = st.text_input("Nama Sales", placeholder="Ketik nama (mis: Wira)...")
            
            if target_sales:
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={token_hari_ini}"
                st.image(qr_url, caption=f"QR Akses untuk {target_sales.upper()}", width=150)
                st.warning(f"⚠️ **PENTING:** Foto QR ini dan kirim JAPRI ke {target_sales}. Jangan share di grup!")
        
        if st.session_state['role'] == 'direktur':
            with st.expander("🛡️ Audit Log (Director Only)"):
                if os.path.isfile('audit_log.csv'):
                    audit_df = pd.read_csv('audit_log.csv', names=['Timestamp', 'User', 'Action'])
                    st.dataframe(audit_df.sort_values('Timestamp', ascending=False), height=200)
                else:
                    st.write("Belum ada log.")
        
        if st.button("🚪 Logout", use_container_width=True):
            log_activity(st.session_state['sales_name'], "LOGOUT")
            st.session_state['logged_in'] = False
            st.rerun()
        st.markdown("---")
        st.caption(f"Waktu Server (WIB): {get_current_time_wib().strftime('%d-%b-%Y %H:%M:%S')}")
            
    df = load_data()
    if df is None or df.empty:
        st.error("⚠️ Gagal memuat data! Periksa koneksi internet atau Link Google Sheet.")
        return

    # --- SECURITY: STRICT SCOPING ---
    user_role = st.session_state['role']
    user_name = st.session_state['sales_name']
    
    if user_role not in ['manager', 'direktur', 'supervisor'] and user_name.lower() != 'fauziah':
        df = df[df['Penjualan'] == user_name]
    elif user_name.upper() in TARGET_DATABASE: 
         spv_brands = list(TARGET_DATABASE[user_name.upper()].keys())
         df = df[df['Merk'].isin(spv_brands)]

    # --- FILTER ---
    st.sidebar.subheader("📅 Filter Periode")
    today = datetime.date.today()
    if 'start_date' not in st.session_state:
        # Default start date logic adjusted
        try:
            st.session_state['start_date'] = df['Tanggal'].max().date().replace(day=1)
            st.session_state['end_date'] = df['Tanggal'].max().date()
        except:
             st.session_state['start_date'] = today
             st.session_state['end_date'] = today

    col_preset1, col_preset2 = st.sidebar.columns(2)
    with col_preset1:
        if st.button("Kemarin", use_container_width=True):
            st.session_state['start_date'] = today - datetime.timedelta(days=1)
            st.session_state['end_date'] = today - datetime.timedelta(days=1)
        if st.button("Bulan Ini", use_container_width=True):
            st.session_state['start_date'] = today.replace(day=1)
            st.session_state['end_date'] = today
    with col_preset2:
        if st.button("7 Hari Terakhir", use_container_width=True):
            st.session_state['start_date'] = today - datetime.timedelta(days=7)
            st.session_state['end_date'] = today
        if st.button("Bulan Lalu", use_container_width=True):
            first_day_current_month = today.replace(day=1)
            last_day_prev_month = first_day_current_month - datetime.timedelta(days=1)
            first_day_prev_month = last_day_prev_month.replace(day=1)
            st.session_state['start_date'] = first_day_prev_month
            st.session_state['end_date'] = last_day_prev_month

    date_range = st.sidebar.date_input("Rentang Waktu Manual", [st.session_state['start_date'], st.session_state['end_date']])

    # --- SCOPE LOGIC ---
    role = st.session_state['role']
    my_name = st.session_state['sales_name']
    my_name_key = my_name.strip().upper()
    is_supervisor_account = my_name_key in TARGET_DATABASE
    target_sales_filter = "SEMUA"

    if role in ['manager', 'direktur'] or my_name.lower() == 'fauziah':
        sales_list = ["SEMUA"] + sorted(list(df['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Pantau Kinerja Sales:", sales_list)
        
        if target_sales_filter.upper() in TARGET_DATABASE:
            selected_spv_key = target_sales_filter.upper()
            spv_brands = TARGET_DATABASE[selected_spv_key].keys()
            df_spv_raw = df[df['Merk'].isin(spv_brands)]
            team_list = sorted(list(df_spv_raw['Penjualan'].dropna().unique()))
            sub_filter = st.sidebar.selectbox(f"Filter Tim ({target_sales_filter}):", ["SEMUA"] + team_list)
            
            if sub_filter == "SEMUA":
                df_scope_all = df_spv_raw
            else:
                df_scope_all = df_spv_raw[df_spv_raw['Penjualan'] == sub_filter]
        else:
            df_scope_all = df if target_sales_filter == "SEMUA" else df[df['Penjualan'] == target_sales_filter]
            
    elif is_supervisor_account:
        my_brands = TARGET_DATABASE[my_name_key].keys()
        df_spv_raw = df[df['Merk'].isin(my_brands)]
        team_list = sorted(list(df_spv_raw['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Filter Tim (Brand Anda):", ["SEMUA"] + team_list)
        df_scope_all = df_spv_raw if target_sales_filter == "SEMUA" else df_spv_raw[df_spv_raw['Penjualan'] == target_sales_filter]
        
    else: 
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
    
    if len(date_range) == 2:
        start, end = date_range
        delta_days = (end - start).days + 1
        prev_end = start - datetime.timedelta(days=1)
        prev_start = prev_end - datetime.timedelta(days=delta_days - 1)
        omset_prev_period = df_scope_all[(df_scope_all['Tanggal'].dt.date >= prev_start) & (df_scope_all['Tanggal'].dt.date <= prev_end)]['Jumlah'].sum()
        delta_val = current_omset_total - omset_prev_period
        delta_label = f"vs {prev_start.strftime('%d %b')} - {prev_end.strftime('%d %b')}"
    else:
        prev_date = ref_date - datetime.timedelta(days=1)
        omset_prev_period = df_scope_all[df_scope_all['Tanggal'].dt.date == prev_date]['Jumlah'].sum()
        delta_val = current_omset_total - omset_prev_period
        delta_label = f"vs {prev_date.strftime('%d %b')}"

    c1, c2, c3 = st.columns(3)
    
    delta_str = format_idr(delta_val)
    if delta_val < 0:
        delta_str = delta_str.replace("Rp -", "- Rp ")
    elif delta_val > 0:
        delta_str = f"+ {delta_str}"

    c1.metric(label="💰 Total Omset (Periode)", value=format_idr(current_omset_total), delta=f"{delta_str} ({delta_label})")
    c2.metric("🏪 Outlet Aktif", f"{df_active['Nama Outlet'].nunique()}")
    
    if 'No Faktur' in df_active.columns:
        valid_faktur = df_active['No Faktur'].astype(str)
        valid_faktur = valid_faktur[~valid_faktur.isin(['nan', 'None', '', '-', '0', 'None', '.'])]
        valid_faktur = valid_faktur[valid_faktur.str.len() > 2]
        transaksi_count = valid_faktur.nunique()
    else:
        transaksi_count = len(df_active)
        
    c3.metric("🧾 Transaksi", f"{transaksi_count}")

    # --- RUN RATE ---
    try:
        if len(date_range) == 2 and (date_range[1].month == today.month and date_range[1].year == today.year):
            days_in_month = monthrange(today.year, today.month)[1]
            day_current = today.day
            if day_current > 0:
                run_rate = (current_omset_total / day_current) * days_in_month
                st.info(f"📈 **Proyeksi Akhir Bulan (Run Rate):** {format_idr(run_rate)}")
    except:
        pass

    # --- TARGET MONITOR ---
    if role in ['manager', 'direktur'] or is_supervisor_account or target_sales_filter in INDIVIDUAL_TARGETS or target_sales_filter.upper() in TARGET_DATABASE:
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
                
        elif target_sales_filter.upper() in TARGET_DATABASE:
             spv_name = target_sales_filter.upper()
             target_pribadi = SUPERVISOR_TOTAL_TARGETS.get(spv_name, 0)
             render_custom_progress(f"👤 Target Tim {spv_name}", df_active['Jumlah'].sum(), target_pribadi)
             
        else:
            st.warning(f"Sales **{target_sales_filter}** tidak memiliki target individu spesifik.")
        st.markdown("---")

    # --- TABS ---
    t1, t2, t_detail_sales, t3, t5, t_forecast, t4 = st.tabs(["📊 Rapor Brand", "📈 Tren Harian", "👥 Detail Tim", "🏆 Top Produk", "🚀 Kejar Omset", "🔮 Prediksi Omset", "📋 Data Rincian"])
    
    with t1:
        if role in ['manager', 'direktur'] or my_name.lower() == 'fauziah':
             loop_source = TARGET_DATABASE.items()
        elif is_supervisor_account:
             loop_source = {my_name_key: TARGET_DATABASE[my_name_key]}.items()
        else:
             loop_source = None

        if loop_source and (target_sales_filter == "SEMUA" or target_sales_filter.upper() in TARGET_DATABASE):
            st.subheader("🏆 Ranking Brand & Detail Sales")
            temp_grouped_data = []
            
            for spv, brands_dict in loop_source:
                for brand, target in brands_dict.items():
                    realisasi_brand = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                    pct_brand = (realisasi_brand / target * 100) if target > 0 else 0
                    
                    brand_row = {
                        "Rank": 0, "Item": brand, "Supervisor": spv,
                        "Target": format_idr(target), "Realisasi": format_idr(realisasi_brand),
                        "Ach (%)": f"{pct_brand:.0f}%", "Bar": pct_brand / 100, "Progress (Detail %)": pct_brand 
                    }
                    
                    sales_rows_list = []
                    for s_name, s_targets in INDIVIDUAL_TARGETS.items():
                        if brand in s_targets:
                            t_indiv = s_targets[brand]
                            r_indiv = df_active[(df_active['Penjualan'] == s_name) & (df_active['Merk'] == brand)]['Jumlah'].sum()
                            pct_indiv = (r_indiv / t_indiv * 100) if t_indiv > 0 else 0
                            sales_rows_list.append({
                                "Rank": "", "Item": f"   └─ {s_name}", "Supervisor": "", 
                                "Target": format_idr(t_indiv), "Realisasi": format_idr(r_indiv),
                                "Ach (%)": f"{pct_indiv:.0f}%", "Bar": pct_indiv / 100, "Progress (Detail %)": pct_brand 
                            })
                    
                    temp_grouped_data.append({"parent": brand_row, "children": sales_rows_list, "sort_val": realisasi_brand})

            temp_grouped_data.sort(key=lambda x: x['sort_val'], reverse=True)
            
            final_summary_data = []
            for idx, group in enumerate(temp_grouped_data, 1):
                group['parent']['Rank'] = idx 
                final_summary_data.append(group['parent'])
                final_summary_data.extend(group['children'])

            df_summ = pd.DataFrame(final_summary_data)
            
            if not df_summ.empty:
                cols = ['Rank'] + [c for c in df_summ.columns if c != 'Rank']
                df_summ = df_summ[cols]
                def style_rows(row):
                    pct = row['Progress (Detail %)']
                    if pct >= 80: bg_color = '#d1e7dd' 
                    elif pct >= 50: bg_color = '#fff3cd' 
                    else: bg_color = '#f8d7da'
                    if row["Supervisor"]: 
                        return [f'background-color: {bg_color}; color: black; font-weight: bold; border-top: 2px solid white'] * len(row)
                    else:
                        return ['background-color: white; color: #555'] * len(row)

                st.dataframe(
                    df_summ.style.apply(style_rows, axis=1).hide(axis="columns", subset=['Progress (Detail %)']),
                    use_container_width=True, hide_index=True,
                    column_config={"Bar": st.column_config.ProgressColumn("Progress", format=" ", min_value=0, max_value=1)}
                )
            else:
                st.warning("Tidak ada data untuk ditampilkan.")

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
            if indiv_data: st.dataframe(pd.DataFrame(indiv_data).sort_values("Kontribusi", ascending=False), use_container_width=True, hide_index=True, column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)})
            else: st.warning("Tidak ada data target brand.")

    with t2:
        st.subheader("📈 Tren Harian")
        if not df_active.empty:
            daily = df_active.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig_line = px.line(daily, x='Tanggal', y='Jumlah', markers=True)
            fig_line.update_traces(line_color='#2980b9', line_width=3)
            st.plotly_chart(fig_line, use_container_width=True)

    with t_detail_sales:
        st.subheader("👥 Detail Sales Team per Brand")
        allowed_brands = []
        if role in ['manager', 'direktur']:
            for spv_brands in TARGET_DATABASE.values():
                allowed_brands.extend(spv_brands.keys())
        elif is_supervisor_account:
            allowed_brands = list(TARGET_DATABASE[my_name_key].keys())
        
        if allowed_brands:
            selected_brand_detail = st.selectbox("Pilih Brand untuk Detail Sales:", sorted(set(allowed_brands)))
            if selected_brand_detail:
                sales_stats = []
                total_brand_sales, total_brand_target = 0, 0
                
                # Simple Time Gone Logic
                if len(date_range) == 2:
                    total_days = (date_range[1] - date_range[0]).days + 1
                    days_gone = (today - date_range[0]).days + 1
                    if days_gone > total_days: days_gone = total_days
                    if days_gone < 0: days_gone = 0
                else:
                    total_days, days_gone = 1, 1
                
                for sales_name, targets in INDIVIDUAL_TARGETS.items():
                    if selected_brand_detail in targets:
                        t_pribadi = targets[selected_brand_detail]
                        real_sales = df_active[(df_active['Penjualan'] == sales_name) & (df_active['Merk'] == selected_brand_detail)]['Jumlah'].sum()
                        
                        expected_ach = (t_pribadi / total_days * days_gone) if total_days > 0 else 0
                        gap = real_sales - expected_ach

                        sales_stats.append({
                            "Nama Sales": sales_name, "Target Pribadi": format_idr(t_pribadi),
                            "Realisasi": format_idr(real_sales), "Ach %": f"{(real_sales/t_pribadi)*100:.1f}%",
                            "Expected (Time Gone)": format_idr(expected_ach), "Gap (Defisit/Surplus)": format_idr(gap)
                        })
                        total_brand_sales += real_sales
                        total_brand_target += t_pribadi
                
                if sales_stats:
                    st.dataframe(pd.DataFrame(sales_stats), use_container_width=True)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Target", format_idr(total_brand_target))
                    m2.metric("Total Omset", format_idr(total_brand_sales))
                    ach_total = (total_brand_sales/total_brand_target)*100 if total_brand_target > 0 else 0
                    m3.metric("Total Ach %", f"{ach_total:.1f}%")
                else:
                    st.info(f"Belum ada data target sales individu untuk brand {selected_brand_detail}")

    with t3:
        st.subheader("📊 Pareto Analysis (80/20 Rule)")
        pareto_df = df_active.groupby('Nama Barang')['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=False)
        if not pareto_df.empty:
            total_omset_pareto = pareto_df['Jumlah'].sum()
            pareto_df['Kontribusi %'] = (pareto_df['Jumlah'] / total_omset_pareto) * 100
            pareto_df['Cumulative %'] = pareto_df['Kontribusi %'].cumsum()
            top_performers = pareto_df[pareto_df['Cumulative %'] <= 80]
            
            c1, c2 = st.columns(2)
            c1.metric("Total Produk Unik", len(pareto_df))
            c2.metric("Produk Kontributor Utama (80%)", len(top_performers))
            st.dataframe(top_performers[['Nama Barang', 'Jumlah', 'Kontribusi %']].style.format({'Jumlah': 'Rp {:,.0f}','Kontribusi %': '{:.2f}%'}), use_container_width=True)
        st.divider()
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
        st.subheader("🚀 Kejar Omset (Actionable Insights)")
        st.write("#### 🚨 Toko Tidur (Potensi Hilang)")
        all_outlets = df_scope_all['Nama Outlet'].unique()
        active_outlets = df_active['Nama Outlet'].unique()
        sleeping_outlets = list(set(all_outlets) - set(active_outlets))
        
        if sleeping_outlets:
            st.warning(f"Ada {len(sleeping_outlets)} toko yang belum order di periode ini.")
            with st.expander("Lihat Daftar Toko Tidur"):
                last_trx = []
                for outlet in sleeping_outlets:
                    outlet_df = df_scope_all[df_scope_all['Nama Outlet'] == outlet]
                    if not outlet_df.empty:
                        last_date = outlet_df['Tanggal'].max()
                        sales_handler = outlet_df['Penjualan'].iloc[0]
                        last_trx.append({"Nama Toko": outlet, "Sales": sales_handler, "Terakhir Order": last_date.strftime('%d %b %Y'), "Hari Sejak": (datetime.date.today() - last_date.date()).days})
                if last_trx: st.dataframe(pd.DataFrame(last_trx).sort_values("Hari Sejak"), use_container_width=True)
        else:
            st.success("Semua toko langganan sudah order di periode ini.")

        st.divider()
        st.write("#### 💎 Peluang Cross-Selling")
        relevant_brands = df_active['Merk'].unique()
        if len(relevant_brands) > 1:
            c1, c2 = st.columns(2)
            b1 = c1.selectbox("Beli Brand A:", sorted(relevant_brands), index=0)
            opts_b2 = [b for b in relevant_brands if b != b1]
            b2 = c2.selectbox("Tapi BELUM beli Brand B:", sorted(opts_b2), index=0 if opts_b2 else None)
            
            if b2:
                outlets_a = df_active[df_active['Merk'] == b1]['Nama Outlet'].unique()
                opps = []
                for o in outlets_a:
                    if df_active[(df_active['Nama Outlet'] == o) & (df_active['Merk'] == b2)].empty:
                         s_name = df_active[df_active['Nama Outlet'] == o]['Penjualan'].iloc[0]
                         opps.append({"Nama Toko": o, "Salesman": s_name, "Potensi": f"Tawarkan {b2}"})
                if opps: st.dataframe(pd.DataFrame(opps), use_container_width=True)
                else: st.success("Semua toko sudah beli kedua brand tersebut.")
        
        st.divider()
        st.write("#### 🧠 Rekomendasi Cerdas (AI)")
        recs_df = get_cross_sell_recommendations(df_scope_all)
        if recs_df is not None and not recs_df.empty:
            st.dataframe(recs_df, use_container_width=True)
        else:
            st.info("Data belum cukup untuk rekomendasi AI.")
            
    with t_forecast:
        st.subheader("🔮 Prediksi Omset")
        df_forecast = df_scope_all.groupby('Tanggal')['Jumlah'].sum().reset_index().sort_values('Tanggal')
        if len(df_forecast) > 10:
            df_forecast['Ordinal'] = df_forecast['Tanggal'].apply(lambda x: x.toordinal())
            x, y = df_forecast['Ordinal'].values, df_forecast['Jumlah'].values
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            
            future_dates = [df_forecast['Tanggal'].max() + datetime.timedelta(days=i) for i in range(1, 31)]
            future_vals = p([d.toordinal() for d in future_dates])
            
            df_combined = pd.concat([
                df_forecast[['Tanggal', 'Jumlah']].assign(Type='Historis'),
                pd.DataFrame({'Tanggal': future_dates, 'Jumlah': future_vals, 'Type': 'Prediksi'})
            ])
            
            fig = px.line(df_combined, x='Tanggal', y='Jumlah', color='Type', line_dash='Type', color_discrete_map={'Historis': '#2980b9', 'Prediksi': '#e74c3c'})
            st.plotly_chart(fig, use_container_width=True)
            st.write(f"**Analisa Tren:** {'NAIK 📈' if z[0] > 0 else 'TURUN 📉'}")
        else:
            st.warning("Data belum cukup untuk prediksi (min 10 hari).")

    with t4:
        st.subheader("📋 Rincian Transaksi")
        cols = ['Tanggal', 'No Faktur', 'Nama Outlet', 'Merk', 'Nama Barang', 'Jumlah', 'Penjualan']
        final_cols = [c for c in cols if c in df_active.columns]
        
        st.dataframe(df_active[final_cols].sort_values('Tanggal', ascending=False), use_container_width=True, hide_index=True, column_config={"Jumlah": st.column_config.NumberColumn("Omset", format="Rp %d")})
        
        if role == 'direktur':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_active[final_cols].to_excel(writer, index=False, sheet_name='Sales Data')
            st.download_button("📥 Download Excel (Protected)", data=output.getvalue(), file_name="Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- 5. EXECUTION BLOCK (BEST PRACTICE) ---
if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        main_dashboard()
    else:
        login_page()
