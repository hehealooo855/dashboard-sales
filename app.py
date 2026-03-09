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
    
    /* BARIS DI BAWAH INI ADALAH PENYEBABNYA - HAPUS ATAU KOMENTARI */
    /* header {visibility: hidden;} */ 
    
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
        "Claresta": 350_000_000, 
        "Birth Beyond": 120_000_000, 
        "OtwooO": 200_000_000, 
        "Rose All Day": 50_000_000
    }
}

INDIVIDUAL_TARGETS = {
    # 1. WIRA 
    "WIRA": { 
        "Somethinc": 660_000_000, "SYB": 75_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000,
        "Elizabeth Rose": 30_000_000, "Walnutt": 20_000_000
    },
    # 2. HAMZAH
    "HAMZAH": { 
        "Somethinc": 540_000_000, "SYB": 75_000_000, "Sekawan": 60_000_000, 
        "Avione": 60_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000 
    },
    # 3. ROZY
    "ROZY": { "Sekawan": 100_000_000, "Avione": 100_000_000 },
    
    # 4. NOVI
    "NOVI": { "Sekawan": 90_000_000, "Avione": 90_000_000 },
    
    # 5. DANI
    "DANI": { "Sekawan": 50_000_000, "Avione": 50_000_000 },
    
    # 6. FERI
    "FERI": { "Honor": 50_000_000, "Thai": 200_000_000, "Vlagio": 30_000_000, "Inesia": 30_000_000 },
    
    # 7. NAUFAL
    "NAUFAL": { "Javinci": 550_000_000 },
    
    # 8. RIZKI
    "RIZKI": { "Javinci": 450_000_000 },
    
    # 9. ADE
    "ADE": { 
        "Javinci": 180_000_000, "Careso": 20_000_000, "Newlab": 75_000_000, 
        "Gloow & Be": 60_000_000, "Dorskin": 10_000_000, "Mlen": 50_000_000 
    },
    # 10. FANDI
    "FANDI": { 
        "Javinci": 40_000_000, "Careso": 20_000_000, "Newlab": 75_000_000, 
        "Gloow & Be": 60_000_000, "Dorskin": 10_000_000, "Whitelab": 75_000_000,
        "Goute": 25_000_000, "Bonavie": 25_000_000, "Mlen": 50_000_000
    },
    # 11. SYAHRUL
    "SYAHRUL": { "Javinci": 40_000_000, "Careso": 10_000_000, "Gloow & Be": 10_000_000 },
    
    # 12. RISKA
    "RISKA": { 
        "Javinci": 40_000_000, "Sociolla": 190_000_000, "Thai": 30_000_000, "Inesia": 20_000_000 
    },
    # 13. DWI
    "DWI": { "Careso": 350_000_000 },
    
    # 14. SANTI
    "SANTI": { "Goute": 25_000_000, "Bonavie": 25_000_000, "Whitelab": 75_000_000 },
    
    # 15. ASWIN
    "ASWIN": { "Artist Inc": 130_000_000 },
    
    # 16. DEVI
    "DEVI": { "Sociolla": 120_000_000, "Y2000": 65_000_000, "Diosys": 175_000_000 },
    
    # 17. GANI
    "GANI": { 
        "The Face": 200_000_000, "Yu Chun Mei": 175_000_000, "Milano": 20_000_000,
        "Sociolla": 80_000_000, "Thai": 85_000_000, "Inesia": 25_000_000
    },
    # 18. BASTIAN
    "BASTIAN": { 
        "Sociolla": 210_000_000, "Thai": 85_000_000, "Inesia": 25_000_000,
        "Y2000": 65_000_000, "Diosys": 175_000_000
    },
    # 19. BAYU
    "BAYU": { "Y2000": 50_000_000, "Diosys": 170_000_000 },
    
    # 20. YOGI
    "YOGI": { "The Face": 400_000_000, "Yu Chun Mei": 275_000_000, "Milano": 30_000_000 },
    
    # 21. LYDIA
    "LYDIA": { "Birth Beyond": 120_000_000 },
    
    # 22. MITHA
    "MITHA": { 
        "Maskit": 30_000_000, "Rose All Day": 30_000_000, 
        "OtwooO": 200_000_000, "Claresta": 350_000_000 
    }
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
    # 1. WIRA 
    "WIRA VG": "WIRA", "WIRA - VG": "WIRA", "WIRA VLAGIO": "WIRA",
    "WIRA HONOR": "WIRA", "WIRA - HONOR": "WIRA", "WIRA HR": "WIRA",
    "WIRA SYB": "WIRA", "WIRA - SYB": "WIRA",
    "WIRA SOMETHINC": "WIRA", "PMT-WIRA": "WIRA", 
    "WIRA ELIZABETH": "WIRA", "WIRA WALNUTT": "WIRA", "WIRA ELZ": "WIRA",

    # 2. HAMZAH
    "HAMZAH VG": "HAMZAH", "HAMZAH - VG": "HAMZAH",
    "HAMZAH HONOR": "HAMZAH", "HAMZAH - HONOR": "HAMZAH",
    "HAMZAH SYB": "HAMZAH", "HAMZAH AV": "HAMZAH", "HAMZAH AINIE": "HAMZAH",
    "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH", "HAMZA AV": "HAMZAH",

    # 3. FERI
    "FERI VG": "FERI", "FERI - VG": "FERI",
    "FERI HONOR": "FERI", "FERI - HONOR": "FERI",
    "FERI THAI": "FERI", "FERI - INESIA": "FERI",

    # 4. YOGI
    "YOGI TF": "YOGI", "YOGI THE FACE": "YOGI", 
    "YOGI YCM": "YOGI", "YOGI MILANO": "YOGI", "MILANO - YOGI": "YOGI", "YOGI REMAR": "YOGI",

    # 5. GANI
    "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI", "GANI TF": "GANI", 
    "GANI - YCM": "GANI", "GANI - MILANO": "GANI", "GANI - HONOR": "GANI", "GANI - VG": "GANI", 
    "GANI - TH": "GANI", "GANI INESIA": "GANI", "GANI - KSM": "GANI", "SSL - GANI": "GANI",
    "GANI ELIZABETH": "GANI", "GANI WALNUTT": "GANI",

    # 6. MITHA
    "MITHA MASKIT": "MITHA", "MITHA RAD": "MITHA", "MITHA CLA": "MITHA", "MITHA OT": "MITHA",
    "MAS - MITHA": "MITHA", "SSL BABY - MITHA ": "MITHA", "SAVIOSA - MITHA": "MITHA", "MITHA ": "MITHA",

    # 7. LYDIA
    "LYDIA KITO": "LYDIA", "LYDIA K": "LYDIA", "LYDIA BB": "LYDIA", "LYDIA - KITO": "LYDIA",

    # 8. NOVI (MERGE DENGAN RAFI/RAPI)
    "NOVI AINIE": "NOVI", "NOVI AV": "NOVI", "NOVI DAN RAFFI": "NOVI", "NOVI & RAFFI": "NOVI", 
    "RAFFI": "NOVI", "RAFI": "NOVI", "RAPI": "NOVI", "RAPI AV":"NOVI",

    # 9. ROZY
    "ROZY AINIE": "ROZY", "ROZY AV": "ROZY",

    # 10. DANI
    "DANI AINIE": "DANI", "DANI AV": "DANI", "DANI SEKAWAN": "DANI",

    # 11. MADONG
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG", "MADONG MYK": "MADONG",

    # 12. RISKA
    "RISKA AV": "RISKA", "RISKA BN": "RISKA", "RISKA CRS": "RISKA", "RISKA E-WL": "RISKA", 
    "RISKA JV": "RISKA", "RISKA REN": "RISKA", "RISKA R&L": "RISKA", "RISKA SMT": "RISKA", 
    "RISKA ST": "RISKA", "RISKA SYB": "RISKA", "RISKA - MILANO": "RISKA", "RISKA TF": "RISKA",
    "RISKA - YCM": "RISKA", "RISKA HONOR": "RISKA", "RISKA - VG": "RISKA", "RISKA TH": "RISKA", 
    "RISKA - INESIA": "RISKA", "SSL - RISKA": "RISKA", "SKIN - RIZKA": "RISKA", 

    # 13. TIM LISMAN (ADE, FANDI, DLL)
    "ADE CLA": "ADE", "ADE CRS": "ADE", "GLOOW - ADE": "ADE", "ADE JAVINCI": "ADE", "ADE JV": "ADE",
    "ADE SVD": "ADE", "ADE RAM PUTRA M.GIE": "ADE", "ADE - MLEN1": "ADE", "ADE NEWLAB": "ADE", "DORS - ADE": "ADE",
    "FANDI - BONAVIE": "FANDI", "DORS- FANDI": "FANDI", "FANDY CRS": "FANDI", "FANDI AFDILLAH": "FANDI", 
    "FANDY WL": "FANDI", "GLOOW - FANDY": "FANDI", "FANDI - GOUTE": "FANDI", "FANDI MG": "FANDI", 
    "FANDI - NEWLAB": "FANDI", "FANDY - YCM": "FANDI", "FANDY YLA": "FANDI", "FANDI JV": "FANDI", "FANDI MLEN": "FANDI",
    "NAUFAL - JAVINCI": "NAUFAL", "NAUFAL JV": "NAUFAL", "NAUFAL SVD": "NAUFAL", 
    "RIZKI JV": "RIZKI", "RIZKI SVD": "RIZKI", 
    "SAHRUL JAVINCI": "SYAHRUL", "SAHRUL TF": "SYAHRUL", "SAHRUL JV": "SYAHRUL", "GLOOW - SAHRUL": "SYAHRUL",
    "SANTI BONAVIE": "SANTI", "SANTI WHITELAB": "SANTI", "SANTI GOUTE": "SANTI",
    "DWI CRS": "DWI", "DWI NLAB": "DWI", 
    "ASWIN ARTIS": "ASWIN", "ASWIN AI": "ASWIN", "ASWIN Inc": "ASWIN", "ASWIN INC": "ASWIN", "ASWIN - ARTIST INC": "ASWIN",

    # 14. TIM AKBAR (DEVI, BASTIAN, BAYU)
    "BASTIAN CASANDRA": "BASTIAN", "SSL- BASTIAN": "BASTIAN", "SKIN - BASTIAN": "BASTIAN", 
    "BASTIAN - HONOR": "BASTIAN", "BASTIAN - VG": "BASTIAN", "BASTIAN TH": "BASTIAN", 
    "BASTIAN YL": "BASTIAN", "BASTIAN YL-DIO CAT": "BASTIAN", "BASTIAN SHMP": "BASTIAN", "BASTIAN-DIO 45": "BASTIAN",
    "SSL - DEVI": "DEVI", "SKIN - DEVI": "DEVI", "DEVI Y- DIOSYS CAT": "DEVI",
    "DEVI YL": "DEVI", "DEVI SHMP": "DEVI", "DEVI-DIO 45": "DEVI", "DEVI YLA": "DEVI",
    "SSL- BAYU": "BAYU", "SKIN - BAYU": "BAYU", "BAYU-DIO 45": "BAYU", "BAYU YL-DIO CAT": "BAYU", 
    "BAYU SHMP": "BAYU", "BAYU YL": "BAYU", 

    # 16. LAIN-LAIN
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

# --- SECURITY FEATURE: AUDIT LOGGING ---
def log_activity(user, action):
    log_file = 'audit_log.csv'
    # Menggunakan WIB untuk Log
    timestamp = get_current_time_wib().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([[timestamp, user, action]], columns=['Timestamp', 'User', 'Action'])
    
    if not os.path.isfile(log_file):
        new_log.to_csv(log_file, index=False)
    else:
        new_log.to_csv(log_file, mode='a', header=False, index=False)
# ---------------------------------------

# --- FITUR: HARDCODED TIMEZONE WIB (GMT+7) ---
def get_current_time_wib():
    # Memaksa program menggunakan zona waktu Asia/Jakarta (WIB)
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

def format_idr(value):
    try:
        return f"Rp {value:,.0f}".replace(",", ".")
    except:
        return "Rp 0"

# --- SECURITY: DAILY TOKEN GENERATOR (12-HOUR ROTATION) ---
def generate_daily_token():
    """
    Membuat token 4 digit unik yang berubah setiap 12 jam (AM/PM) mengikuti waktu WIB.
    Rumus: Hash(Tanggal + AM/PM + Secret Salt) -> Ambil 4 digit angka
    """
    secret_salt = "RAHASIA_PERUSAHAAN_2025" 
    
    # Ambil waktu WIB saat ini
    now_wib = get_current_time_wib()
    
    # Format string kunci: YYYY-MM-DD-AM atau YYYY-MM-DD-PM
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
            faktur_col = col
            break
    
    if faktur_col:
        df = df.rename(columns={faktur_col: 'No Faktur'})
    
    if 'Nama Outlet' in df.columns:
        df = df[~df['Nama Outlet'].astype(str).str.match(r'^(Total|Jumlah|Subtotal|Grand|Rekap)', case=False, na=False)]
        df = df[df['Nama Outlet'].astype(str).str.strip() != ''] 
        df = df[df['Nama Outlet'].astype(str).str.lower() != 'nan']

    if 'Nama Barang' in df.columns:
        df = df[~df['Nama Barang'].astype(str).str.match(r'^(Total|Jumlah)', case=False, na=False)]
        df = df[df['Nama Barang'].astype(str).str.strip() != ''] 

    df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(SALES_MAPPING)
    
    valid_sales_names = list(INDIVIDUAL_TARGETS.keys())
    valid_sales_names.extend(["MADONG", "LISMAN", "AKBAR", "WILLIAM"]) 
    
    df.loc[~df['Penjualan'].isin(valid_sales_names), 'Penjualan'] = 'Non-Sales'
    df['Penjualan'] = df['Penjualan'].astype('category')

    def normalize_brand(raw_brand):
        raw_upper = str(raw_brand).upper()
        for target_brand, keywords in BRAND_ALIASES.items():
            for keyword in keywords:
                if keyword in raw_upper: return target_brand
        return raw_brand
    df['Merk'] = df['Merk'].apply(normalize_brand).astype('category')
    
    df['Jumlah'] = df['Jumlah'].astype(str).str.replace(r'[Rp\s]', '', regex=True).str.replace('.', '', regex=False)
    df['Jumlah'] = df['Jumlah'].str.replace(',', '.', regex=False)
    df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
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

def save_user_secret(username, secret_key):
    df = load_users()
    if 'secret_key' not in df.columns:
        df['secret_key'] = None
    df.loc[df['username'] == username, 'secret_key'] = secret_key
    df.to_csv('users.csv', index=False)

# ==========================================
# Fungsi Tambahan untuk Market Basket Analysis
# ==========================================

@st.cache_data(ttl=3600, show_spinner=False)
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
    rules_df = rules_df[rules_df['confidence'] > 0.5]  
    return rules_df

@st.cache_data(ttl=3600, show_spinner=False)
def get_cross_sell_recommendations(df):
    rules_df = compute_association_rules(df)
    if rules_df is None or rules_df.empty:
        return None
    
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
    if recommendations: return pd.DataFrame(recommendations)
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
            
            if 'login_step' not in st.session_state: st.session_state['login_step'] = 'credentials'
            if 'temp_user_data' not in st.session_state: st.session_state['temp_user_data'] = None
            
            if st.session_state['login_step'] == 'credentials':
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submitted = st.form_submit_button("Verifikasi Akun", use_container_width=True)
                    
                    if submitted:
                        users = load_users()
                        if users.empty: st.error("Database user (users.csv) tidak ditemukan.")
                        else:
                            match = users[(users['username'] == username) & (users['password'] == password)]
                            if match.empty:
                                st.error("Username atau Password salah.")
                                log_activity(username, "FAILED LOGIN - WRONG PASS")
                            else:
                                user_row = match.iloc[0]
                                user_role = user_row['role']
                                user_sales_name = user_row['sales_name']
                                
                                if user_role in ['direktur', 'manager']:
                                    st.session_state['logged_in'] = True
                                    st.session_state['role'] = user_role
                                    st.session_state['sales_name'] = user_sales_name
                                    log_activity(user_sales_name, "LOGIN SUCCESS")
                                    st.rerun()
                                else:
                                    st.session_state['temp_user_data'] = user_row
                                    st.session_state['login_step'] = '2fa_check'
                                    st.rerun()
                                    
            elif st.session_state['login_step'] == '2fa_check':
                user_data = st.session_state['temp_user_data']
                secret = user_data.get('secret_key', None)
                
                if pd.isna(secret) or secret == "" or secret is None:
                    st.error("⛔ Akun Anda belum diaktivasi 2FA.")
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
    def add_aggressive_watermark():
        user_name = st.session_state.get('sales_name', 'User')
        role_name = st.session_state.get('role', 'staff')
        
        if role_name != 'direktur':
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
                margin: 20px; user-select: none;
            }}
            </style>
            <div class="watermark-container">
                {''.join([f'<div class="watermark-text">{user_name} • CONFIDENTIAL • {get_current_time_wib().strftime("%H:%M")}</div>' for _ in range(300)])}
            </div>
            <script>
            window.addEventListener('blur', () => {{ document.body.style.filter = 'blur(20px) brightness(0.4)'; document.body.style.backgroundColor = '#000'; }});
            window.addEventListener('focus', () => {{ document.body.style.filter = 'none'; document.body.style.backgroundColor = '#fff'; }});
            document.addEventListener('keydown', (e) => {{
                if ((e.ctrlKey || e.metaKey) && (e.key === 'p' || e.key === 's')) {{
                    e.preventDefault(); alert('⚠️ Action Disabled for Security Reasons!');
                }}
            }});
            </script>
            """, unsafe_allow_html=True)
    
    add_aggressive_watermark()

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
            st.caption("Ketik nama sales untuk membuatkan akses khusus.")
            
            target_sales = st.text_input("Nama Sales", placeholder="Ketik nama (mis: Wira)...")
            if target_sales:
                users_df = load_users()
                if target_sales in users_df['username'].values:
                    user_record = users_df[users_df['username'] == target_sales].iloc[0]
                    current_secret = user_record.get('secret_key', None)
                    
                    if pd.isna(current_secret) or current_secret == "" or current_secret is None:
                        current_secret = pyotp.random_base32()
                        save_user_secret(target_sales, current_secret)
                        st.success(f"Secret Key Baru Dibuat untuk {target_sales}!")
                    
                    uri = pyotp.totp.TOTP(current_secret).provisioning_uri(name=user_record['sales_name'], issuer_name="Distributor App")
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={uri}"
                    
                    st.image(qr_url, caption=f"QR Akses untuk {target_sales.upper()}", width=150)
                    st.warning(f"⚠️ **PENTING:** Foto QR ini dan kirim JAPRI ke {target_sales}. Jangan share di grup!")
                else: st.error("Username tidak ditemukan di database.")
            else: st.info("Input nama sales diatas untuk memunculkan QR Code.")
        
        if st.session_state['role'] == 'direktur':
            with st.expander("🛡️ Audit Log (Director Only)"):
                if os.path.isfile('audit_log.csv'):
                    try:
                        audit_df = pd.read_csv('audit_log.csv', names=['Timestamp', 'User', 'Action'])
                        st.dataframe(audit_df.sort_values('Timestamp', ascending=False), height=200)
                    except: st.write("Format log invalid.")
                else: st.write("Belum ada data.")
        
        if st.button("🚪 Logout", use_container_width=True):
            log_activity(st.session_state['sales_name'], "LOGOUT")
            st.session_state['logged_in'] = False
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        st.markdown("---")
        st.caption(f"Waktu Server (WIB): {get_current_time_wib().strftime('%d-%b-%Y %H:%M:%S')}")
            
    df = load_data()
    if df is None or df.empty:
        st.error("⚠️ Gagal memuat data! Periksa koneksi internet atau Link Google Sheet.")
        return

    user_role = st.session_state['role']
    user_name = st.session_state['sales_name']
    role = user_role
    my_name = user_name
    my_name_key = my_name.strip().upper()
    
    if user_role not in ['manager', 'direktur', 'supervisor'] and user_name.lower() != 'fauziah':
        df = df[df['Penjualan'] == user_name]
    elif user_name.upper() in TARGET_DATABASE: 
         spv_brands = list(TARGET_DATABASE[user_name.upper()].keys())
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
    
    is_supervisor_account = my_name_key in TARGET_DATABASE
    target_sales_filter = "SEMUA"

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

    t1, t2, t3, t4, t5 = st.tabs(["📊 Rapor", "📈 Tren", "🏆 Produk", "📋 Data Rincian", "🚀 Kejar Omset"])
    
    with t1:
        st.subheader("Rapor Kinerja")
        total_omset = df_active['Jumlah'].sum()
        st.metric("Total Omset", format_idr(total_omset))
        
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

    with t4:
        st.subheader("📋 Data Rincian Bulanan per Customer")
        
        if not AGGRID_AVAILABLE:
            st.warning("Pustaka 'streamlit-aggrid' belum terinstall. Menggunakan tabel bawaan.")
            
        list_merk_excel = sorted(df_active['Merk'].dropna().astype(str).unique())
        selected_merk_excel = st.selectbox("🎯 Pilih Merk untuk dilihat rinciannya:", ["SEMUA"] + list_merk_excel)
        
        if selected_merk_excel != "SEMUA":
            df_excel = df_active[df_active['Merk'] == selected_merk_excel].copy()
        else:
            df_excel = df_active.copy()

        if not df_excel.empty:
            df_excel['Bulan Angka'] = df_excel['Tanggal'].dt.month
            
            group_cols = []
            
            if 'Kode Customer' in df_excel.columns: group_cols.append('Kode Customer')
            elif 'Kode Costumer' in df_excel.columns: group_cols.append('Kode Costumer')
            elif 'Kode Outlet' in df_excel.columns: group_cols.append('Kode Outlet')
            else:
                df_excel['Kode Customer'] = "-"
                group_cols.append('Kode Customer')
                
            group_cols.append('Nama Outlet') 
            
            if 'Kota' in df_excel.columns: group_cols.append('Kota')
            else:
                df_excel['Kota'] = "-"
                group_cols.append('Kota')

            master_pivot = pd.pivot_table(
                df_excel, 
                values='Jumlah', 
                index=group_cols, 
                columns='Bulan Angka', 
                aggfunc='sum', 
                fill_value=0
            )

            bulan_indo = {
                1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
                5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
                9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
            }

            for i in range(1, 13):
                if i not in master_pivot.columns:
                    master_pivot[i] = 0

            master_pivot = master_pivot[list(range(1, 13))]
            master_pivot.columns = [bulan_indo[i] for i in master_pivot.columns]
            
            master_pivot['Total Penjualan'] = master_pivot.sum(axis=1)
            master_pivot = master_pivot.reset_index()
            master_pivot = master_pivot.rename(columns={'Nama Outlet': 'Nama Customer'})

            # --- MENGAKTIFKAN FILTER KOLOM GLOBAL (AGGRID & STREAMLIT NATIVE) ---
            if AGGRID_AVAILABLE:
                # Modifikasi mulai di sini
                gb = GridOptionsBuilder.from_dataframe(master_pivot)
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_side_bar()
                
                # MENGAKTIFKAN FILTER EXCEL-LIKE UNTUK SEMUA KOLOM
                gb.configure_default_column(
                    filter='agSetColumnFilter', 
                    sortable=True, 
                    resizable=True, 
                    floatingFilter=True,
                    menuTabs=['filterMenuTab', 'generalMenuTab', 'columnsMenuTab'] # Menampilkan tombol hamburger menu
                )
                
                # Menerapkan format mata uang Rupiah untuk kolom numerik (Bulan + Total)
                num_cols = list(bulan_indo.values()) + ['Total Penjualan']
                for col in num_cols:
                    gb.configure_column(col, type=["numericColumn","numberColumnFilter"], valueFormatter="x.toLocaleString('id-ID', {style: 'currency', currency: 'IDR', minimumFractionDigits: 0})")
                
                gridOptions = gb.build()
                # Menampilkan tabel AgGrid yang interaktif
                AgGrid(master_pivot, gridOptions=gridOptions, enable_enterprise_modules=True, height=500, theme='alpine')
            else:
                # Fallback untuk native Streamlit dataframe
                format_dict = {col: "Rp {:,.0f}" for col in list(bulan_indo.values()) + ['Total Penjualan']}
                st.dataframe(master_pivot.style.format(format_dict), use_container_width=True, hide_index=True)
        else:
            st.info("Data Kosong.")

        # --- EXCEL EXPORT (TIDAK ADA PERUBAHAN) ---
        user_role_lower = role.lower()
        if user_role_lower in ['direktur', 'manager', 'supervisor']:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                if 'master_pivot' in locals() and not master_pivot.empty:
                    master_pivot.to_excel(writer, index=False, sheet_name='Master Data')
                else:
                    df_active.to_excel(writer, index=False, sheet_name='Sales Data')
                
                workbook = writer.book
                worksheet = writer.sheets['Master Data' if 'master_pivot' in locals() else 'Sales Data']
                
                user_identity = f"{st.session_state['sales_name']} ({st.session_state['role'].upper()})"
                time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                watermark_text = f"CONFIDENTIAL DOCUMENT | TRACKED USER: {user_identity} | DOWNLOADED: {time_stamp} | DO NOT DISTRIBUTE"
                
                worksheet.set_header(f'&C&10{watermark_text}')
                worksheet.set_footer(f'&RPage &P of &N')
                
                format1 = workbook.add_format({'num_format': '#,##0'})
                worksheet.set_column('D:P', None, format1) 
            
            st.download_button(
                label="📥 Download Laporan Excel (XLSX) - DRM Protected",
                data=output.getvalue(),
                file_name=f"Laporan_Master_{selected_merk_excel}_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        elif role in ['direktur']: 
             csv = master_pivot.to_csv(index=False).encode('utf-8')
             file_name = f"Laporan_Sales_{datetime.date.today()}.csv"
             st.download_button("📥 Download Data CSV", data=csv, file_name=file_name, mime="text/csv")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()
