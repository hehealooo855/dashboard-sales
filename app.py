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
import hashlib # Library untuk enkripsi token
import numpy as np
from calendar import monthrange
from itertools import combinations
from collections import Counter

# --- IMPORT KONFIGURASI DARI FILE LAIN (CLEAN CODE) ---
from config import TARGET_DATABASE, INDIVIDUAL_TARGETS, SUPERVISOR_TOTAL_TARGETS, TARGET_NASIONAL_VAL, BRAND_ALIASES, SALES_MAPPING

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
    timestamp = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([[timestamp, user, action]], columns=['Timestamp', 'User', 'Action'])
    
    if not os.path.isfile(log_file):
        new_log.to_csv(log_file, index=False)
    else:
        new_log.to_csv(log_file, mode='a', header=False, index=False)
# ---------------------------------------

def get_current_time_wib():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

def format_idr(value):
    try:
        return f"Rp {value:,.0f}".replace(",", ".")
    except:
        return "Rp 0"

# --- SECURITY: DAILY TOKEN GENERATOR ---
def generate_daily_token():
    """
    Membuat token 4 digit unik berdasarkan tanggal hari ini.
    Rumus: Hash(Tanggal + Secret Salt) -> Ambil 4 digit angka
    """
    secret_salt = "RAHASIA_PERUSAHAAN_2025" # Ganti string ini agar unik untuk perusahaan Anda
    today_str = get_current_time_wib().strftime("%Y-%m-%d")
    raw_string = f"{today_str}-{secret_salt}"
    
    # Buat hash SHA256
    hash_object = hashlib.sha256(raw_string.encode())
    hex_dig = hash_object.hexdigest()
    
    # Ambil hanya karakter angka dari hash
    numeric_filter = filter(str.isdigit, hex_dig)
    numeric_string = "".join(numeric_filter)
    
    # Ambil 4 digit pertama (jika kurang, padding dengan 0)
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
    
    if faktur_col:
        df = df.rename(columns={faktur_col: 'No Faktur'})
    
    # --- CLEANING SAMPAH YANG LEBIH CERDAS ---
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
    
    # --- NUMERIC CLEANING (FIX SELISIH RP 300rb) ---
    # 1. Pastikan string
    df['Jumlah'] = df['Jumlah'].astype(str)
    # 2. Hapus simbol mata uang dan spasi
    df['Jumlah'] = df['Jumlah'].str.replace(r'[Rp\s]', '', regex=True)
    # 3. Hapus TITIK sebagai pemisah ribuan
    df['Jumlah'] = df['Jumlah'].str.replace('.', '', regex=False)
    # 4. Ganti KOMA dengan TITIK (untuk desimal, jika ada)
    df['Jumlah'] = df['Jumlah'].str.replace(',', '.', regex=False)
    # 5. Konversi ke angka
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
            
    return df

def load_users():
    try:
        return pd.read_csv('users.csv')
    except:
        return pd.DataFrame()

# ==========================================
# Fungsi Tambahan untuk Market Basket Analysis
# ==========================================
def compute_association_rules(df):
    if 'No Faktur' not in df.columns or 'Nama Barang' not in df.columns:
        return None
    
    # Hitung support item (jumlah transaksi unik yang mengandung item)
    item_support = df.groupby('Nama Barang')['No Faktur'].nunique()
    
    # Total transaksi unik
    total_transactions = df['No Faktur'].nunique()
    
    # Dapatkan pairs dari setiap basket (transaksi)
    pair_df = df.groupby('No Faktur')['Nama Barang'].apply(lambda x: list(combinations(sorted(x.unique()), 2)) if len(x.unique()) > 1 else [])
    pairs = [p for sublist in pair_df for p in sublist]
    
    # Hitung support pair
    pair_support = Counter(pairs)
    
    # Buat rules A -> B dengan confidence
    rules = []
    for (A, B), supp_ab in pair_support.items():
        conf_ab = supp_ab / item_support[A]
        conf_ba = supp_ab / item_support[B]
        rules.append({'antecedent': A, 'consequent': B, 'support': supp_ab / total_transactions, 'confidence': conf_ab})
        rules.append({'antecedent': B, 'consequent': A, 'support': supp_ab / total_transactions, 'confidence': conf_ba})
    
    rules_df = pd.DataFrame(rules).drop_duplicates().sort_values('confidence', ascending=False)
    rules_df = rules_df[rules_df['confidence'] > 0.5]  # Threshold confidence minimal 50%
    
    return rules_df

def get_cross_sell_recommendations(df):
    rules_df = compute_association_rules(df)
    if rules_df is None or rules_df.empty:
        return None
    
    # Dapatkan pembelian per outlet (set unik produk)
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
        
        # Pilih rekomendasi terbaik (confidence tertinggi)
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
    
    # --- GET DAILY TOKEN ---
    daily_token = generate_daily_token()
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            st.markdown(f"<div style='text-align:center; color:#888; font-size:12px;'>Sistem Terproteksi</div>", unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                # --- FITUR: OTP INPUT (BERSIH, TANPA SETUP GOOGLE AUTH) ---
                otp_input = st.text_input("Kode Akses Harian (OTP)", placeholder="Masukkan Kode 4 Digit", max_chars=4)
                
                submitted = st.form_submit_button("Masuk Sistem", use_container_width=True)
                
                if submitted:
                    users = load_users()
                    if users.empty:
                        st.error("Database user (users.csv) tidak ditemukan.")
                    else:
                        # 1. Cek User & Password Terlebih Dahulu
                        match = users[(users['username'] == username) & (users['password'] == password)]
                        
                        if match.empty:
                            st.error("Username atau Password salah.")
                            log_activity(username, "FAILED LOGIN - WRONG PASS")
                        else:
                            # 2. Cek Role & Validasi OTP
                            user_role = match.iloc[0]['role']
                            user_sales_name = match.iloc[0]['sales_name']
                            
                            is_authorized = False
                            
                            # BYPASS OTP untuk Direktur & Manager
                            if user_role in ['direktur', 'manager']:
                                is_authorized = True
                            # WAJIB OTP untuk Sales & Supervisor
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
                                
                                # Log Activity
                                log_activity(user_sales_name, "LOGIN SUCCESS")
                                
                                st.success("Login Berhasil! Mengalihkan...")
                                time.sleep(1)
                                st.rerun()

def main_dashboard():
    # --- SECURITY SECTION (POINT 1 - AGGRESSIVE TILED WATERMARK & BLACKOUT) ---
    def add_aggressive_watermark():
        user_name = st.session_state.get('sales_name', 'User')
        role_name = st.session_state.get('role', 'staff')
        
        # Jika bukan direktur, tampilkan watermark agresif & fitur blackout
        if role_name != 'direktur':
            # Buat teks watermark berulang
            
            st.markdown(f"""
            <style>
            .watermark-container {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                z-index: 99999; /* Paling atas */
                pointer-events: none; /* Klik tembus ke bawah */
                overflow: hidden;
                display: flex;
                flex-wrap: wrap;
                opacity: 0.15; /* Transparansi cukup mengganggu screenshot tapi bisa dibaca */
            }}
            
            .watermark-text {{
                font-family: 'Arial', sans-serif;
                font-size: 16px;
                color: #555;
                font-weight: 700;
                transform: rotate(-30deg);
                white-space: nowrap;
                margin: 20px;
                user-select: none;
            }}
            </style>
            
            <div class="watermark-container">
                {''.join([f'<div class="watermark-text">{user_name} • CONFIDENTIAL • {datetime.datetime.now().strftime("%H:%M")}</div>' for _ in range(300)])}
            </div>
            
            <script>
            // --- FITUR AUTO-BLACKOUT & BLUR SAAT KEHILANGAN FOKUS (Anti-Snipping Tool) ---
            window.addEventListener('blur', () => {{
                // Saat user pindah ke aplikasi lain (misal Snipping Tool), layar jadi hitam & blur
                document.body.style.filter = 'blur(20px) brightness(0.4)'; 
                document.body.style.backgroundColor = '#000';
            }});
            
            window.addEventListener('focus', () => {{
                // Saat user kembali ke browser, layar normal kembali
                document.body.style.filter = 'none';
                document.body.style.backgroundColor = '#fff';
            }});
            
            // --- ANTI PRINT SHORTCUT ---
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

    # --- FITUR DRM: ANTI-COPY (Kecuali Direktur) ---
    if st.session_state['role'] != 'direktur':
        st.markdown("""
            <style>
            /* Sembunyikan konten saat dicetak (Print/Save to PDF) */
            @media print {
                body { display: none !important; }
            }
            /* Mencegah seleksi teks (Copy-Paste) */
            body {
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                user-select: none;
            }
            img { pointer-events: none; }
            </style>
            """, unsafe_allow_html=True)
    # -----------------------------------------------------------------

    with st.sidebar:
        st.write("## 👤 User Profile")
        st.info(f"**{st.session_state['sales_name']}**\n\nRole: {st.session_state['role'].upper()}")
        
        # --- MENU KHUSUS DIREKTUR/MANAGER: CENTRALIZED PROVISIONING ---
        if st.session_state['role'] in ['manager', 'direktur']:
            st.markdown("---")
            st.write("### 🔐 Admin Zone")
            token_hari_ini = generate_daily_token()
            
            # 1. Tampilan Master Token (Untuk Direktur sendiri)
            st.write(f"**Token Master:** `{token_hari_ini}`")
            
            # 2. Centralized Provisioning (Generate QR for specific user)
            st.markdown("#### 📱 Generate QR Sales")
            st.caption("Ketik nama sales untuk membuatkan akses khusus.")
            
            target_sales = st.text_input("Nama Sales", placeholder="Ketik nama (mis: Wira)...")
            
            if target_sales:
                # Menggunakan API QR Server untuk generate gambar
                # QR Code berisi Token Harian, tapi disajikan secara personal
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={token_hari_ini}"
                
                st.image(qr_url, caption=f"QR Akses untuk {target_sales.upper()}", width=150)
                st.warning(f"⚠️ **PENTING:** Foto QR ini dan kirim JAPRI ke {target_sales}. Jangan share di grup!")
            else:
                st.info("Input nama sales diatas untuk memunculkan QR Code.")
        
        # --- AUDIT LOG VIEWER FOR DIRECTOR (POINT 5) ---
        if st.session_state['role'] == 'direktur':
            with st.expander("🛡️ Audit Log (Director Only)"):
                if os.path.isfile('audit_log.csv'):
                    audit_df = pd.read_csv('audit_log.csv', names=['Timestamp', 'User', 'Action'])
                    st.dataframe(audit_df.sort_values('Timestamp', ascending=False), height=200)
                else:
                    st.write("Belum ada log.")
        # ---------------------------------------------
        
        if st.button("🚪 Logout", use_container_width=True):
            log_activity(st.session_state['sales_name'], "LOGOUT")
            st.session_state['logged_in'] = False
            st.rerun()
        st.markdown("---")
        st.caption(f"Last Updated: {get_current_time_wib().strftime('%H:%M:%S')} WIB")
            
    df = load_data()
    if df is None or df.empty:
        st.error("⚠️ Gagal memuat data! Periksa koneksi internet atau Link Google Sheet.")
        return

    # --- SECURITY: STRICT SCOPING (POINT 3 - ISOLASI DATA) ---
    user_role = st.session_state['role']
    user_name = st.session_state['sales_name']
    
    # Jika bukan Direktur/Manager/Fauziah, potong data df agar hanya berisi data mereka sendiri
    if user_role not in ['manager', 'direktur', 'supervisor'] and user_name.lower() != 'fauziah':
        # 1. Isolasi Dataframe Transaksi
        df = df[df['Penjualan'] == user_name]
    
    # 2. SUPERVISOR: Lihat data berdasarkan Brand yang dipegang
    elif user_name.upper() in TARGET_DATABASE: 
         # Ambil list brand yang dipegang Supervisor ini
         spv_brands = list(TARGET_DATABASE[user_name.upper()].keys())
         # Filter DataFrame hanya untuk brand tersebut
         df = df[df['Merk'].isin(spv_brands)]
    # ---------------------------------------------------------

    # --- FILTER ---
    st.sidebar.subheader("📅 Filter Periode")

    # -- DATE PICKER PRESET (ADDED FEATURE) --
    today = datetime.date.today()
    
    if 'start_date' not in st.session_state:
        st.session_state['start_date'] = df['Tanggal'].max().date().replace(day=1)
        st.session_state['end_date'] = df['Tanggal'].max().date()

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

    # --- FORECASTING / RUN RATE ---
    try:
        from calendar import monthrange
        today = datetime.date.today()
        if len(date_range) == 2 and (date_range[1].month == today.month and date_range[1].year == today.year):
            days_in_month = monthrange(today.year, today.month)[1]
            day_current = today.day
            if day_current > 0:
                run_rate = (current_omset_total / day_current) * days_in_month
                st.info(f"📈 **Proyeksi Akhir Bulan (Run Rate):** {format_idr(run_rate)} (Estimasi berdasarkan kinerja harian rata-rata saat ini)")
    except Exception as e:
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

    # --- ANALYTICS TABS ---
    t1, t2, t_detail_sales, t3, t5, t_forecast, t4 = st.tabs(["📊 Rapor Brand", "📈 Tren Harian", "👥 Detail Tim", "🏆 Top Produk", "🚀 Kejar Omset", "🔮 Prediksi Omset", "📋 Data Rincian"])
    
    with t1:
        # Determine the loop based on the user's role
        # Supervisors see only their own brands; Managers/Directors/Fauziah see all
        if role in ['manager', 'direktur'] or my_name.lower() == 'fauziah':
             loop_source = TARGET_DATABASE.items()
        elif is_supervisor_account:
             loop_source = {my_name_key: TARGET_DATABASE[my_name_key]}.items()
        else:
             loop_source = None

        if loop_source and (target_sales_filter == "SEMUA" or target_sales_filter.upper() in TARGET_DATABASE):
            st.subheader("🏆 Ranking Brand & Detail Sales")
            
            # 1. TAHAP PENGUMPULAN DATA (GROUPING)
            temp_grouped_data = [] # List untuk menyimpan paket [Brand + Anak-anaknya]
            
            for spv, brands_dict in loop_source:
                for brand, target in brands_dict.items():
                    # Hitung Total Realisasi Brand (Global)
                    realisasi_brand = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                    pct_brand = (realisasi_brand / target * 100) if target > 0 else 0
                    
                    # Siapkan Baris PARENT (Brand)
                    brand_row = {
                        "Rank": 0, # Placeholder, akan diisi nanti setelah sort
                        "Item": brand,
                        "Supervisor": spv,
                        "Target": format_idr(target),
                        "Realisasi": format_idr(realisasi_brand),
                        "Ach (%)": f"{pct_brand:.0f}%",
                        "Bar": pct_brand / 100, 
                        "Progress (Detail %)": pct_brand 
                    }
                    
                    # Siapkan Baris CHILDREN (Sales)
                    sales_rows_list = []
                    for s_name, s_targets in INDIVIDUAL_TARGETS.items():
                        if brand in s_targets:
                            t_indiv = s_targets[brand]
                            r_indiv = df_active[(df_active['Penjualan'] == s_name) & (df_active['Merk'] == brand)]['Jumlah'].sum()
                            pct_indiv = (r_indiv / t_indiv * 100) if t_indiv > 0 else 0
                            
                            sales_rows_list.append({
                                "Rank": "", # Kosongkan rank untuk sales
                                "Item": f"   └─ {s_name}", 
                                "Supervisor": "", 
                                "Target": format_idr(t_indiv),
                                "Realisasi": format_idr(r_indiv),
                                "Ach (%)": f"{pct_indiv:.0f}%",
                                "Bar": pct_indiv / 100,
                                "Progress (Detail %)": pct_brand 
                            })
                    
                    # Simpan paket data brand ini beserta sorting key-nya (realisasi_brand)
                    temp_grouped_data.append({
                        "parent": brand_row,
                        "children": sales_rows_list,
                        "sort_val": realisasi_brand # Key untuk sorting
                    })

            # 2. TAHAP SORTING & RANKING
            # Sort berdasarkan omset (sort_val) tertinggi ke terendah
            temp_grouped_data.sort(key=lambda x: x['sort_val'], reverse=True)
            
            # 3. TAHAP FLATTENING (Menyusun kembali jadi flat list untuk DataFrame)
            final_summary_data = []
            for idx, group in enumerate(temp_grouped_data, 1):
                # Update Rank pada Parent
                group['parent']['Rank'] = idx 
                
                # Masukkan Parent
                final_summary_data.append(group['parent'])
                
                # Masukkan Children (Sales) tepat dibawahnya
                final_summary_data.extend(group['children'])

            # Buat DataFrame Akhir
            df_summ = pd.DataFrame(final_summary_data)
            
            if not df_summ.empty:
                # Pindahkan kolom Rank ke paling depan (opsional, tapi good practice)
                cols = ['Rank'] + [c for c in df_summ.columns if c != 'Rank']
                df_summ = df_summ[cols]

                # --- FLEXIBLE TRAFFIC LIGHT COLORING ---
                def style_rows(row):
                    pct = row['Progress (Detail %)']
                    
                    if pct >= 80: bg_color = '#d1e7dd' 
                    elif pct >= 50: bg_color = '#fff3cd' 
                    else: bg_color = '#f8d7da'

                    # Styling: Brand (ada Supervisor) vs Sales (Kosong)
                    if row["Supervisor"]: 
                        return [f'background-color: {bg_color}; color: black; font-weight: bold; border-top: 2px solid white'] * len(row)
                    else:
                        return ['background-color: white; color: #555'] * len(row)

                # Render Dataframe
                st.dataframe(
                    df_summ.style.apply(style_rows, axis=1).hide(axis="columns", subset=['Progress (Detail %)']),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Rank": st.column_config.TextColumn("🏆 Rank", width="small"),
                        "Item": st.column_config.TextColumn("Brand / Salesman", width="medium"),
                        "Bar": st.column_config.ProgressColumn(
                            "Progress",
                            format=" ",
                            min_value=0,
                            max_value=1,
                        )
                    }
                )
            else:
                st.warning("Tidak ada data untuk ditampilkan.")

        elif target_sales_filter in INDIVIDUAL_TARGETS:
             st.info("Lihat progress bar di atas untuk detail target individu.")
        else:
            # Fallback (Existing code logic for non-grouped view)
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
        # Logic to enable dropdown based on user role and context
        allowed_brands = []
        if role in ['manager', 'direktur']:
            # All brands
            for spv_brands in TARGET_DATABASE.values():
                allowed_brands.extend(spv_brands.keys())
        elif is_supervisor_account:
            allowed_brands = list(TARGET_DATABASE[my_name_key].keys())
        
        # If accessing specific sales view, usually no detail team needed, but allowed if they manage brands
        if allowed_brands:
            selected_brand_detail = st.selectbox("Pilih Brand untuk Detail Sales:", sorted(set(allowed_brands)))
            
            if selected_brand_detail:
                # Find all sales with individual targets for this brand
                sales_stats = []
                total_brand_sales = 0
                total_brand_target = 0
                
                # Calendar logic for "Time Gone" calculation
                today = datetime.date.today()
                
                # Holidays Indonesia (Example - Update per year)
                holidays_id = [
                    '2024-01-01', '2024-02-08', '2024-02-10', '2024-03-11', '2024-03-29',
                    '2024-04-10', '2024-04-11', '2024-05-01', '2024-05-09', '2024-05-23',
                    '2024-06-01', '2024-06-17', '2024-07-07', '2024-08-17', '2024-09-16',
                    '2024-12-25', 
                    '2025-01-01', '2025-01-27', '2025-03-29', '2025-03-31',
                    '2025-04-18', '2025-04-20', '2025-05-01', '2025-05-12', '2025-05-29',
                    '2025-06-01', '2025-06-06', '2025-06-27', '2025-08-17', '2025-09-05',
                    '2025-10-20', '2025-12-25',
                    '2026-01-01', '2026-02-17', '2026-03-19', '2026-03-20', '2026-04-03',
                    '2026-04-05', '2026-05-01', '2026-05-14', '2026-05-24', '2026-06-01',
                    '2026-06-16', '2026-07-07', '2026-08-17', '2026-08-25', '2026-12-25' 
                ]

                # Calculate Month End
                next_month = today.replace(day=28) + datetime.timedelta(days=4)
                last_day_month = next_month - datetime.timedelta(days=next_month.day)
                
                # Calculate Remaining Working Days (From Today until End of Month)
                # Filter: Not Sunday (6) AND Not in Holiday List
                date_range_rest = pd.date_range(start=today, end=last_day_month)
                remaining_workdays = sum(1 for d in date_range_rest if d.weekday() != 6 and d.strftime('%Y-%m-%d') not in holidays_id)
                
                # Check if selected date range includes current month to apply current month logic
                if len(date_range) == 2:
                    start_d, end_d = date_range
                    # Calculate total days in the period
                    total_days = (end_d - start_d).days + 1
                    # Calculate days elapsed (Time Gone) relative to the period and today
                    # If period is in past, days gone = total days. If future, 0. If current, today - start.
                    
                    if end_d < today: # Past period
                        days_gone = total_days
                    elif start_d > today: # Future period
                        days_gone = 0
                    else: # Current period
                        days_gone = (today - start_d).days + 1
                        # Clamp days_gone to total_days (e.g. if today > end_d)
                        if days_gone > total_days: days_gone = total_days
                        if days_gone < 0: days_gone = 0
                else:
                    # Single date
                    total_days = 1
                    days_gone = 1
                
                
                for sales_name, targets in INDIVIDUAL_TARGETS.items():
                    if selected_brand_detail in targets:
                        t_pribadi = targets[selected_brand_detail]
                        
                        # Filter dataframe for this sales and brand within selected date range
                        real_sales = df_active[(df_active['Penjualan'] == sales_name) & (df_active['Merk'] == selected_brand_detail)]['Jumlah'].sum()
                        
                        # Time Gone Logic: 
                        # Expected Achievement = (Target / Total Days) * Days Gone
                        if total_days > 0:
                            target_harian = t_pribadi / total_days
                            expected_ach = target_harian * days_gone
                            gap = real_sales - expected_ach
                            
                            # Catch-up logic (Required Run Rate for remaining days)
                            # Gap / Remaining Workdays
                            target_remaining = t_pribadi - real_sales
                            if target_remaining > 0 and remaining_workdays > 0:
                                catch_up_needed = target_remaining / remaining_workdays
                            else:
                                catch_up_needed = 0 # Target met or no days left
                        else:
                            expected_ach = 0
                            gap = 0
                            catch_up_needed = 0

                        sales_stats.append({
                            "Nama Sales": sales_name,
                            "Target Pribadi": format_idr(t_pribadi),
                            "Realisasi": format_idr(real_sales),
                            "Ach %": f"{(real_sales/t_pribadi)*100:.1f}%",
                            "Expected (Time Gone)": format_idr(expected_ach),
                            "Gap (Defisit/Surplus)": format_idr(gap),
                            "Catch-up (Per Hari)": format_idr(catch_up_needed),
                            "_real": real_sales,
                            "_target": t_pribadi
                        })
                        total_brand_sales += real_sales
                        total_brand_target += t_pribadi
                
                if sales_stats:
                    st.dataframe(pd.DataFrame(sales_stats).drop(columns=["_real", "_target"]), use_container_width=True)
                    
                    # Summary metrics for the brand
                    m1, m2, m3 = st.columns(3)
                    m1.metric(f"Total Target {selected_brand_detail}", format_idr(total_brand_target))
                    m2.metric(f"Total Omset {selected_brand_detail}", format_idr(total_brand_sales))
                    ach_total = (total_brand_sales/total_brand_target)*100 if total_brand_target > 0 else 0
                    m3.metric("Total Ach %", f"{ach_total:.1f}%")
                else:
                    st.info(f"Belum ada data target sales individu untuk brand {selected_brand_detail}")
        else:
            st.info("Menu ini khusus untuk melihat detail tim sales per brand.")

    with t3:
        # --- PARETO ANALYSIS (UPDATED: Contribution %) ---
        st.subheader("📊 Pareto Analysis (80/20 Rule)")
        st.caption("Produk yang berkontribusi terhadap 80% dari total omset.")
        
        pareto_df = df_active.groupby('Nama Barang')['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=False)
        total_omset_pareto = pareto_df['Jumlah'].sum()
        
        # Calculate Contribution % (Item Sales / Total Sales)
        pareto_df['Kontribusi %'] = (pareto_df['Jumlah'] / total_omset_pareto) * 100
        
        # Calculate Cumulative % for 80/20 cut-off
        pareto_df['Cumulative %'] = pareto_df['Kontribusi %'].cumsum()
        
        # Filter top 80% contributors
        top_performers = pareto_df[pareto_df['Cumulative %'] <= 80]
        
        # Display summary metric
        col_pareto1, col_pareto2 = st.columns(2)
        col_pareto1.metric("Total Produk Unik", len(pareto_df))
        col_pareto2.metric("Produk Kontributor Utama (80%)", len(top_performers))
        
        st.dataframe(
            # Select only specific columns to display, excluding Cumulative %
            top_performers[['Nama Barang', 'Jumlah', 'Kontribusi %']].style.format({
                'Jumlah': 'Rp {:,.0f}',
                'Kontribusi %': '{:.2f}%'
            }),
            use_container_width=True
        )
        
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
        
        # 1. Analisa Toko Tidur (Churn Risk)
        # Toko yang pernah beli, tapi tidak beli dalam periode ini
        # ATAU (Lebih canggih) Toko yang beli bulan lalu, tapi bulan ini 0
        
        st.write("#### 🚨 Toko Tidur (Potensi Hilang)")
        st.caption("Toko yang bertransaksi di masa lalu (sebelum periode ini) tetapi TIDAK bertransaksi di periode yang dipilih.")
        
        all_outlets = df_scope_all['Nama Outlet'].unique()
        active_outlets = df_active['Nama Outlet'].unique()
        sleeping_outlets = list(set(all_outlets) - set(active_outlets))
        
        if sleeping_outlets:
            st.warning(f"Ada {len(sleeping_outlets)} toko yang belum order di periode ini.")
            with st.expander("Lihat Daftar Toko Tidur"):
                # Cari last transaction date untuk toko tidur
                last_trx = []
                for outlet in sleeping_outlets:
                    outlet_df = df_scope_all[df_scope_all['Nama Outlet'] == outlet]
                    last_date = outlet_df['Tanggal'].max()
                    sales_handler = outlet_df['Penjualan'].iloc[0] if not outlet_df.empty else "-"
                    last_trx.append({
                        "Nama Toko": outlet,
                        "Sales": sales_handler,
                        "Terakhir Order": last_date.strftime('%d %b %Y'),
                        "Hari Sejak Order Terakhir": (datetime.date.today() - last_date.date()).days
                    })
                
                df_sleep = pd.DataFrame(last_trx).sort_values("Hari Sejak Order Terakhir")
                st.dataframe(df_sleep, use_container_width=True)
        else:
            st.success("Luar biasa! Semua toko langganan sudah order di periode ini.")

        st.divider()

        # 2. Analisa Cross-Selling (Peluang)
        # Toko yang beli Brand A, tapi belum beli Brand B (dalam portofolio sales/SPV yang sama)
        st.write("#### 💎 Peluang Cross-Selling (White Space Analysis)")
        
        # Ambil daftar brand yang relevan dalam scope saat ini
        relevant_brands = df_active['Merk'].unique()
        
        if len(relevant_brands) > 1:
            col_cs1, col_cs2 = st.columns(2)
            with col_cs1:
                brand_acuan = st.selectbox("Jika Toko sudah beli Brand:", sorted(relevant_brands), index=0)
            with col_cs2:
                # Remove brand_acuan from options to avoid same-same comparison
                target_options = [b for b in relevant_brands if b != brand_acuan]
                brand_target = st.selectbox("Tapi BELUM beli Brand:", sorted(target_options), index=0 if target_options else None)
            
            if brand_target:
                # Logic: Find outlets that bought Brand A but sum(Sales Brand B) == 0
                outlets_buy_acuan = df_active[df_active['Merk'] == brand_acuan]['Nama Outlet'].unique()
                
                # Dari outlet tersebut, mana yang tidak punya transaksi di brand target?
                opportunities = []
                for outlet in outlets_buy_acuan:
                    # Cek apakah outlet ini beli brand target
                    check = df_active[(df_active['Nama Outlet'] == outlet) & (df_active['Merk'] == brand_target)]
                    if check.empty:
                        # Get Salesman name for this outlet
                        sales_name = df_active[df_active['Nama Outlet'] == outlet]['Penjualan'].iloc[0]
                        opportunities.append({
                            "Nama Toko": outlet,
                            "Salesman": sales_name,
                            "Potensi": f"Tawarkan {brand_target}"
                        })
                
                if opportunities:
                    st.info(f"Ditemukan **{len(opportunities)} Toko** yang beli {brand_acuan} tapi belum beli {brand_target}.")
                    st.dataframe(pd.DataFrame(opportunities), use_container_width=True)
                else:
                    st.success(f"Hebat! Semua toko yang beli {brand_acuan} juga sudah membeli {brand_target}.")
        else:
            st.info("Data tidak cukup untuk analisa cross-selling (perlu minimal 2 brand aktif).")
        
        st.divider()

        # 3. Rekomendasi Cross-Selling Cerdas (AI-Powered dengan Association Rules)
        st.write("#### 🧠 Rekomendasi Cross-Selling Cerdas (Berdasarkan Pola Transaksi)")
        st.caption("AI menganalisa pola pembelian dari ribuan transaksi untuk menemukan rekomendasi tersembunyi.")
        
        recs_df = get_cross_sell_recommendations(df_scope_all)
        if recs_df is not None and not recs_df.empty:
            st.success(f"Ditemukan {len(recs_df)} rekomendasi cerdas berdasarkan pola pembelian.")
            st.dataframe(recs_df, use_container_width=True)
        elif recs_df is None:
            st.warning("Kolom 'No Faktur' atau 'Nama Barang' tidak ditemukan. Tidak bisa menghitung pola.")
        else:
            st.info("Tidak ada rekomendasi cerdas yang memenuhi threshold (confidence > 50%). Perlu lebih banyak data transaksi.")
            
    with t_forecast:
        # --- FEATURE 3: FORECASTING (PREDIKSI OMSET) ---
        st.subheader("🔮 Prediksi Omset (Forecasting)")
        st.info("Prediksi tren omset 30 hari ke depan berdasarkan data historis harian.")
        
        # 1. Prepare Data
        # Group by Date
        df_forecast = df_scope_all.groupby('Tanggal')['Jumlah'].sum().reset_index()
        df_forecast = df_forecast.sort_values('Tanggal')
        
        if len(df_forecast) > 10: # Need minimal data points
            # 2. Linear Regression (Simple) using Numpy
            # Convert date to ordinal for regression
            df_forecast['Date_Ordinal'] = df_forecast['Tanggal'].apply(lambda x: x.toordinal())
            
            x = df_forecast['Date_Ordinal'].values
            y = df_forecast['Jumlah'].values
            
            # Fit Polynomial (Degree 1 = Linear)
            # slope (m), intercept (c) = np.polyfit(x, y, 1)
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            
            # 3. Create Future Dates
            last_date = df_forecast['Tanggal'].max()
            future_days = 30
            future_dates = [last_date + datetime.timedelta(days=i) for i in range(1, future_days + 1)]
            future_ordinals = [d.toordinal() for d in future_dates]
            
            # Predict
            future_values = p(future_ordinals)
            
            # Combine for Visualization
            df_history = df_forecast[['Tanggal', 'Jumlah']].copy()
            df_history['Type'] = 'Historis'
            
            df_future = pd.DataFrame({'Tanggal': future_dates, 'Jumlah': future_values})
            df_future['Type'] = 'Prediksi'
            
            df_combined = pd.concat([df_history, df_future])
            
            # 4. Visualize
            fig_forecast = px.line(df_combined, x='Tanggal', y='Jumlah', color='Type', 
                                   line_dash='Type', 
                                   color_discrete_map={'Historis': '#2980b9', 'Prediksi': '#e74c3c'})
            
            fig_forecast.update_layout(title="Proyeksi Omset 30 Hari Kedepan", xaxis_title="Tanggal", yaxis_title="Omset")
            st.plotly_chart(fig_forecast, use_container_width=True)
            
            # 5. Insight Text
            trend = "NAIK 📈" if z[0] > 0 else "TURUN 📉"
            st.write(f"**Analisa Tren:** Berdasarkan data historis, tren penjualan terlihat **{trend}**.")
            
        else:
            st.warning("Data belum cukup untuk melakukan prediksi (minimal 10 hari transaksi).")

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
        
        # --- EXCEL EXPORT (NEW FEATURE: Only for Manager, Direktur, Supervisor) ---
        user_role_lower = role.lower()
        # user_name_lower = my_name.lower() # No longer needed for specific exclusion logic if we just rely on role, but keeping it is fine if logic changes later.

        if user_role_lower in ['direktur', 'manager', 'supervisor']:
            # Create an in-memory Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_active[final_cols].to_excel(writer, index=False, sheet_name='Sales Data')
                workbook = writer.book
                worksheet = writer.sheets['Sales Data']
                format1 = workbook.add_format({'num_format': '#,##0'})
                worksheet.set_column('F:F', None, format1) # Assuming 'Jumlah' is column F (index 5)
            
            st.download_button(
                label="📥 Download Laporan Excel (XLSX)",
                data=output.getvalue(),
                file_name=f"Laporan_Sales_Profesional_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        # Keep CSV for others or as fallback if needed (Optional, removing as requested focus is upgrade)
        elif role in ['direktur']: # Legacy condition kept just in case
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
