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
import concurrent.futures  # LIBRARY BARU UNTUK BOOST KECEPATAN (PARALEL)

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
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
    "SANTI": { "Goute": 25_000_000, "Bonavie": 25_000_000, "Whitelab": 75_000_000 },
    "ASWIN": { "Artist Inc": 130_000_000 },
    "DEVI": { "Sociolla": 120_000_000, "Y2000": 65_000_000, "Diosys": 175_000_000 },
    "GANI": { "The Face": 200_000_000, "Yu Chun Mei": 175_000_000, "Milano": 20_000_000, "Sociolla": 80_000_000, "Thai": 85_000_000, "Inesia": 25_000_000 },
    "BASTIAN": { "Sociolla": 210_000_000, "Thai": 85_000_000, "Inesia": 25_000_000, "Y2000": 65_000_000, "Diosys": 175_000_000 },
    "BAYU": { "Y2000": 50_000_000, "Diosys": 170_000_000 },
    "YOGI": { "The Face": 400_000_000, "Yu Chun Mei": 275_000_000, "Milano": 30_000_000 },
    "LYDIA": { "Birth Beyond": 120_000_000 },
    "MITHA": { "Maskit": 30_000_000, "Rose All Day": 30_000_000, "OtwooO": 200_000_000, "Claresta": 350_000_000 }
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
    "WIRA VG": "WIRA", "WIRA - VG": "WIRA", "WIRA VLAGIO": "WIRA", "WIRA HONOR": "WIRA", "WIRA - HONOR": "WIRA", "WIRA HR": "WIRA",
    "WIRA SYB": "WIRA", "WIRA - SYB": "WIRA", "WIRA SOMETHINC": "WIRA", "PMT-WIRA": "WIRA", "WIRA ELIZABETH": "WIRA", "WIRA WALNUTT": "WIRA", "WIRA ELZ": "WIRA",
    # 2. HAMZAH
    "HAMZAH VG": "HAMZAH", "HAMZAH - VG": "HAMZAH", "HAMZAH HONOR": "HAMZAH", "HAMZAH - HONOR": "HAMZAH",
    "HAMZAH SYB": "HAMZAH", "HAMZAH AV": "HAMZAH", "HAMZAH AINIE": "HAMZAH", "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH", "HAMZA AV": "HAMZAH",
    # 3. FERI
    "FERI VG": "FERI", "FERI - VG": "FERI", "FERI HONOR": "FERI", "FERI - HONOR": "FERI", "FERI THAI": "FERI", "FERI - INESIA": "FERI",
    # 4. YOGI
    "YOGI TF": "YOGI", "YOGI THE FACE": "YOGI", "YOGI YCM": "YOGI", "YOGI MILANO": "YOGI", "MILANO - YOGI": "YOGI", "YOGI REMAR": "YOGI",
    # 5. GANI
    "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI", "GANI TF": "GANI", "GANI - YCM": "GANI", "GANI - MILANO": "GANI", "GANI - HONOR": "GANI", "GANI - VG": "GANI", "GANI - TH": "GANI", "GANI INESIA": "GANI", "GANI - KSM": "GANI", "SSL - GANI": "GANI", "GANI ELIZABETH": "GANI", "GANI WALNUTT": "GANI",
    # 6. MITHA
    "MITHA MASKIT": "MITHA", "MITHA RAD": "MITHA", "MITHA CLA": "MITHA", "MITHA OT": "MITHA", "MAS - MITHA": "MITHA", "SSL BABY - MITHA ": "MITHA", "SAVIOSA - MITHA": "MITHA", "MITHA ": "MITHA",
    # 7. LYDIA
    "LYDIA KITO": "LYDIA", "LYDIA K": "LYDIA", "LYDIA BB": "LYDIA", "LYDIA - KITO": "LYDIA",
    # 8. NOVI
    "NOVI AINIE": "NOVI", "NOVI AV": "NOVI", "NOVI DAN RAFFI": "NOVI", "NOVI & RAFFI": "NOVI", "RAFFI": "NOVI", "RAFI": "NOVI", "RAPI": "NOVI", "RAPI AV":"NOVI",
    # 9. ROZY
    "ROZY AINIE": "ROZY", "ROZY AV": "ROZY",
    # 10. DANI
    "DANI AINIE": "DANI", "DANI AV": "DANI", "DANI SEKAWAN": "DANI",
    # 11. MADONG
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG", "MADONG MYK": "MADONG",
    # 12. RISKA
    "RISKA AV": "RISKA", "RISKA BN": "RISKA", "RISKA CRS": "RISKA", "RISKA E-WL": "RISKA", "RISKA JV": "RISKA", "RISKA REN": "RISKA", "RISKA R&L": "RISKA", "RISKA SMT": "RISKA", "RISKA ST": "RISKA", "RISKA SYB": "RISKA", "RISKA - MILANO": "RISKA", "RISKA TF": "RISKA", "RISKA - YCM": "RISKA", "RISKA HONOR": "RISKA", "RISKA - VG": "RISKA", "RISKA TH": "RISKA", "RISKA - INESIA": "RISKA", "SSL - RISKA": "RISKA", "SKIN - RIZKA": "RISKA", 
    # 13. TIM LISMAN
    "ADE CLA": "ADE", "ADE CRS": "ADE", "GLOOW - ADE": "ADE", "ADE JAVINCI": "ADE", "ADE JV": "ADE", "ADE SVD": "ADE", "ADE RAM PUTRA M.GIE": "ADE", "ADE - MLEN1": "ADE", "ADE NEWLAB": "ADE", "DORS - ADE": "ADE",
    "FANDI - BONAVIE": "FANDI", "DORS- FANDI": "FANDI", "FANDY CRS": "FANDI", "FANDI AFDILLAH": "FANDI", "FANDY WL": "FANDI", "GLOOW - FANDY": "FANDI", "FANDI - GOUTE": "FANDI", "FANDI MG": "FANDI", "FANDI - NEWLAB": "FANDI", "FANDY - YCM": "FANDI", "FANDY YLA": "FANDI", "FANDI JV": "FANDI", "FANDI MLEN": "FANDI",
    "NAUFAL - JAVINCI": "NAUFAL", "NAUFAL JV": "NAUFAL", "NAUFAL SVD": "NAUFAL", "RIZKI JV": "RIZKI", "RIZKI SVD": "RIZKI", 
    "SAHRUL JAVINCI": "SYAHRUL", "SAHRUL TF": "SYAHRUL", "SAHRUL JV": "SYAHRUL", "GLOOW - SAHRUL": "SYAHRUL",
    "SANTI BONAVIE": "SANTI", "SANTI WHITELAB": "SANTI", "SANTI GOUTE": "SANTI", "DWI CRS": "DWI", "DWI NLAB": "DWI", 
    "ASWIN ARTIS": "ASWIN", "ASWIN AI": "ASWIN", "ASWIN Inc": "ASWIN", "ASWIN INC": "ASWIN", "ASWIN - ARTIST INC": "ASWIN",
    # 14. TIM AKBAR
    "BASTIAN CASANDRA": "BASTIAN", "SSL- BASTIAN": "BASTIAN", "SKIN - BASTIAN": "BASTIAN", "BASTIAN - HONOR": "BASTIAN", "BASTIAN - VG": "BASTIAN", "BASTIAN TH": "BASTIAN", "BASTIAN YL": "BASTIAN", "BASTIAN YL-DIO CAT": "BASTIAN", "BASTIAN SHMP": "BASTIAN", "BASTIAN-DIO 45": "BASTIAN",
    "SSL - DEVI": "DEVI", "SKIN - DEVI": "DEVI", "DEVI Y- DIOSYS CAT": "DEVI", "DEVI YL": "DEVI", "DEVI SHMP": "DEVI", "DEVI-DIO 45": "DEVI", "DEVI YLA": "DEVI",
    "SSL- BAYU": "BAYU", "SKIN - BAYU": "BAYU", "BAYU-DIO 45": "BAYU", "BAYU YL-DIO CAT": "BAYU", "BAYU SHMP": "BAYU", "BAYU YL": "BAYU", 
    # 16. LAIN-LAIN
    "HABIBI - FZ": "HABIBI", "HABIBI SYB": "HABIBI", "HABIBI TH": "HABIBI", "GLOOW - LISMAN": "LISMAN", "LISMAN - NEWLAB": "LISMAN", 
    "WILLIAM BTC": "WILLIAM", "WILLI - ROS": "WILLIAM", "WILLI - WAL": "WILLIAM", "RINI JV": "RINI", "RINI SYB": "RINI", 
    "FAUZIAH CLA": "FAUZIAH", "FAUZIAH ST": "FAUZIAH", "MARIANA CLIN": "MARIANA", "JAYA - MARIANA": "MARIANA"
}

# ==========================================
# 3. CORE LOGIC
# ==========================================

def log_activity(user, action):
    log_file = 'audit_log.csv'
    timestamp = get_current_time_wib().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([[timestamp, user, action]], columns=['Timestamp', 'User', 'Action'])
    
    if not os.path.isfile(log_file): new_log.to_csv(log_file, index=False)
    else: new_log.to_csv(log_file, mode='a', header=False, index=False)

def get_current_time_wib():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

def format_idr(value):
    try: return f"Rp {value:,.0f}".replace(",", ".")
    except: return "Rp 0"

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

# --- FUNGSI DOWNLOAD PARALEL YANG DIPERBARUI ---
@st.cache_data(ttl=300) # Memperpanjang memori menjadi 5 menit agar aplikasi tidak berat
def load_data():
    urls = [
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vSaGwT-qw0iz6kKhkwep4R5b-TWlegy8rHdBU3HcY_veP8KEsiLmKpCemC-D1VA2STstlCjA2VLUM-Q/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vT6KbuunLLoGQRSanRK_A8e5jgXcJ-FCZCEb8dr611HdJQi40dFr_HNMItnodJEwD7dKk7woC7Ud-DG/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vQyEgQMxR75QW7HYKbJov4WtNuZmghPAhMHeH-cI5Wem_NwIMuC95sqa8QzXh2p1DX-HxQSJGptz_xy/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBTn4hKKl-e9BFITUW2dYBsKfMbTBc-zrdn3qweQxzL_tiTr3FMi4cGE-17IrixYwg9T-4YugLcQdq/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vTVyv41klRlykXzW5wYo01y5a4HtplUEXVMpt05DzEO-ijxJ9T2Xk5Yiruv4uZW--QM0NIU3fnww_xX/pub?output=csv" 
    ]
    
    # Fungsi kecil khusus untuk menangkap 1 link
    def fetch_url(url):
        if url.strip() != "" and url.startswith("http"):
            try:
                url_with_ts = f"{url}&t={int(time.time())}"
                return pd.read_csv(url_with_ts, dtype=str)
            except Exception as e:
                return None
        return None

    all_dfs = []
    
    # MENGGUNAKAN MULTITHREADING (5 KURIR SEKALIGUS)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(fetch_url, urls)
        for res in results:
            if res is not None:
                all_dfs.append(res)
                
    if not all_dfs:
        return None
        
    df = pd.concat(all_dfs, ignore_index=True)
    
    df.columns = df.columns.str.strip()
    required_cols = ['Penjualan', 'Merk', 'Jumlah', 'Tanggal']
    if not all(col in df.columns for col in required_cols): return None
    
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
    
    def clean_rupiah(x):
        x = str(x).upper().replace('RP', '').strip()
        x = re.sub(r'\s+', '', x) 
        x = re.sub(r'[,.]\d{2}$', '', x) 
        x = x.replace(',', '').replace('.', '') 
        x = re.sub(r'[^\d-]', '', x) 
        try:
            return float(x)
        except:
            return 0.0

    df['Jumlah'] = df['Jumlah'].apply(clean_rupiah)
    
    tanggal_raw = df['Tanggal'].astype(str).str.strip()
    d1 = pd.to_datetime(tanggal_raw, format='%d/%m/%Y', errors='coerce')
    d2 = pd.to_datetime(tanggal_raw, format='%d-%m-%Y', errors='coerce')
    d3 = pd.to_datetime(tanggal_raw, dayfirst=True, errors='coerce', format='mixed')
    
    df['Tanggal'] = d1.fillna(d2).fillna(d3)
    df = df.dropna(subset=['Tanggal'])
    
    cols_to_convert = ['Kota', 'Nama Outlet', 'Nama Barang', 'No Faktur']
    for col in cols_to_convert:
        if col in df.columns: df[col] = df[col].astype(str).str.strip()
            
    return df

def load_users():
    try: return pd.read_csv('users.csv')
    except: return pd.DataFrame()

def save_user_secret(username, secret_key):
    df = load_users()
    if 'secret_key' not in df.columns: df['secret_key'] = None
    df.loc[df['username'] == username, 'secret_key'] = secret_key
    df.to_csv('users.csv', index=False)

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
    if recommendations: return pd.DataFrame(recommendations)
    return None

# ==========================================
# 4. MAIN DASHBOARD LOGIC
# ==========================================
def login_page():
    st.markdown("<br><br><h1 style='text-align: center;'>🦅 Executive Command Center</h1>", unsafe_allow_html=True)
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
            .watermark-container {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 99999; pointer-events: none; overflow: hidden; display: flex; flex-wrap: wrap; opacity: 0.15; }}
            .watermark-text {{ font-family: 'Arial', sans-serif; font-size: 16px; color: #555; font-weight: 700; transform: rotate(-30deg); white-space: nowrap; margin: 20px; user-select: none; }}
            </style>
            <div class="watermark-container">{''.join([f'<div class="watermark-text">{user_name} • CONFIDENTIAL • {get_current_time_wib().strftime("%H:%M")}</div>' for _ in range(300)])}</div>
            <script>
            window.addEventListener('blur', () => {{ document.body.style.filter = 'blur(20px) brightness(0.4)'; document.body.style.backgroundColor = '#000'; }});
            window.addEventListener('focus', () => {{ document.body.style.filter = 'none'; document.body.style.backgroundColor = '#fff'; }});
            document.addEventListener('keydown', (e) => {{ if ((e.ctrlKey || e.metaKey) && (e.key === 'p' || e.key === 's')) {{ e.preventDefault(); alert('⚠️ Action Disabled for Security Reasons!'); }} }});
            </script>
            """, unsafe_allow_html=True)
    
    add_aggressive_watermark()

    if st.session_state['role'] != 'direktur':
        st.markdown("<style>@media print { body { display: none !important; } } body { -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none; } img { pointer-events: none; }</style>", unsafe_allow_html=True)

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
        target_sales_filter = st.sidebar.selectbox("Pantau Kinerja Sales:", sales_list)
        if target_sales_filter.upper() in TARGET_DATABASE:
            selected_spv_key = target_sales_filter.upper()
            spv_brands = TARGET_DATABASE[selected_spv_key].keys()
            df_spv_raw = df[df['Merk'].isin(spv_brands)]
            team_list = sorted(list(df_spv_raw['Penjualan'].dropna().astype(str).unique()))
            sub_filter = st.sidebar.selectbox(f"Filter Tim ({target_sales_filter}):", ["SEMUA"] + team_list)
            if sub_filter == "SEMUA": df_scope_all = df_spv_raw
            else: df_scope_all = df_spv_raw[df_spv_raw['Penjualan'] == sub_filter]
        else: df_scope_all = df if target_sales_filter == "SEMUA" else df[df['Penjualan'] == target_sales_filter]
    elif is_supervisor_account:
        my_brands = TARGET_DATABASE[my_name_key].keys()
        df_spv_raw = df[df['Merk'].isin(my_brands)]
        team_list = sorted(list(df_spv_raw['Penjualan'].dropna().astype(str).unique()))
        target_sales_filter = st.sidebar.selectbox("Filter Tim (Brand Anda):", ["SEMUA"] + team_list)
        df_scope_all = df_spv_raw if target_sales_filter == "SEMUA" else df_spv_raw[df_spv_raw['Penjualan'] == target_sales_filter]
    else: 
        target_sales_filter = my_name 
        df_scope_all = df[df['Penjualan'] == my_name]

    with st.sidebar.expander("🔍 Filter Lanjutan", expanded=False):
        unique_brands = sorted(df_scope_all['Merk'].dropna().astype(str).unique())
        pilih_merk = st.multiselect("Pilih Merk", unique_brands)
        if pilih_merk: df_scope_all = df_scope_all[df_scope_all['Merk'].isin(pilih_merk)]
        
        unique_outlets = sorted(df_scope_all['Nama Outlet'].dropna().astype(str).unique())
        pilih_outlet = st.multiselect("Pilih Outlet", unique_outlets)
        if pilih_outlet: df_scope_all = df_scope_all[df_scope_all['Nama Outlet'].isin(pilih_outlet)]

    if len(date_range) == 2:
        start_date, end_date = date_range
        df_active = df_scope_all[(df_scope_all['Tanggal'].dt.date >= start_date) & (df_scope_all['Tanggal'].dt.date <= end_date)]
        ref_date = end_date
    else:
        df_active = df_scope_all
        ref_date = df['Tanggal'].max().date()

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
    if delta_val < 0: delta_str = delta_str.replace("Rp -", "- Rp ")
    elif delta_val > 0: delta_str = f"+ {delta_str}"

    c1.metric(label="💰 Total Omset (Periode)", value=format_idr(current_omset_total), delta=f"{delta_str} ({delta_label})")
    c2.metric("🏪 Outlet Aktif", f"{df_active['Nama Outlet'].nunique()}")
    
    if 'No Faktur' in df_active.columns:
        valid_faktur = df_active['No Faktur'].astype(str)
        valid_faktur = valid_faktur[~valid_faktur.isin(['nan', 'None', '', '-', '0', 'None', '.'])]
        valid_faktur = valid_faktur[valid_faktur.str.len() > 2]
        transaksi_count = valid_faktur.nunique()
    else: transaksi_count = len(df_active)
        
    c3.metric("🧾 Transaksi", f"{transaksi_count}")

    try:
        if len(date_range) == 2 and (date_range[1].month == today.month and date_range[1].year == today.year):
            days_in_month = monthrange(today.year, today.month)[1]
            day_current = today.day
            if day_current > 0:
                run_rate = (current_omset_total / day_current) * days_in_month
                st.info(f"📈 **Proyeksi Akhir Bulan (Run Rate):** {format_idr(run_rate)} (Estimasi berdasarkan kinerja harian rata-rata saat ini)")
    except Exception as e: pass

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
        else: st.warning(f"Sales **{target_sales_filter}** tidak memiliki target individu spesifik.")
        st.markdown("---")

    t1, t2, t_detail_sales, t3, t5, t_forecast, t4 = st.tabs(["📊 Rapor Brand", "📈 Tren Harian", "👥 Detail Tim", "🏆 Top Produk", "🚀 Kejar Omset", "🔮 Prediksi Omset", "📋 Data Rincian"])
    
    with t1:
        if role in ['manager', 'direktur'] or my_name.lower() == 'fauziah': loop_source = TARGET_DATABASE.items()
        elif is_supervisor_account: loop_source = {my_name_key: TARGET_DATABASE[my_name_key]}.items()
        else: loop_source = None

        if loop_source and (target_sales_filter == "SEMUA" or target_sales_filter.upper() in TARGET_DATABASE):
            st.subheader("🏆 Ranking Brand & Detail Sales")
            temp_grouped_data = [] 
            for spv, brands_dict in loop_source:
                for brand, target in brands_dict.items():
                    realisasi_brand = df_active[df_active['Merk'] == brand]['Jumlah'].sum()
                    pct_brand = (realisasi_brand / target * 100) if target > 0 else 0
                    brand_row = {
                        "Rank": 0, "Item": brand, "Supervisor": spv, "Target": format_idr(target),
                        "Realisasi": format_idr(realisasi_brand), "Ach (%)": f"{pct_brand:.0f}%",
                        "Bar": pct_brand / 100, "Progress (Detail %)": pct_brand 
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
                                "Ach (%)": f"{pct_indiv:.0f}%", "Bar": pct_indiv / 100,
                                "Progress (Detail %)": pct_brand 
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
                    if row["Supervisor"]: return [f'background-color: {bg_color}; color: black; font-weight: bold; border-top: 2px solid white'] * len(row)
                    else: return ['background-color: white; color: #555'] * len(row)
                st.dataframe(
                    df_summ.style.apply(style_rows, axis=1).hide(axis="columns", subset=['Progress (Detail %)']),
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Rank": st.column_config.TextColumn("🏆 Rank", width="small"),
                        "Item": st.column_config.TextColumn("Brand / Salesman", width="medium"),
                        "Bar": st.column_config.ProgressColumn("Progress", format=" ", min_value=0, max_value=1)
                    }
                )
            else: st.warning("Tidak ada data untuk ditampilkan.")
        elif target_sales_filter in INDIVIDUAL_TARGETS: st.info("Lihat progress bar di atas untuk detail target individu.")
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
            for spv_brands in TARGET_DATABASE.values(): allowed_brands.extend(spv_brands.keys())
        elif is_supervisor_account: allowed_brands = list(TARGET_DATABASE[my_name_key].keys())
        
        if allowed_brands:
            selected_brand_detail = st.selectbox("Pilih Brand untuk Detail Sales:", sorted(set(allowed_brands)))
            if selected_brand_detail:
                sales_stats = []
                total_brand_sales = 0
                total_brand_target = 0
                today = datetime.date.today()
                
                holidays_id = [
                    '2024-01-01', '2024-02-08', '2024-02-10', '2024-03-11', '2024-03-29', '2024-04-10', '2024-04-11', '2024-05-01', '2024-05-09', '2024-05-23', '2024-06-01', '2024-06-17', '2024-07-07', '2024-08-17', '2024-09-16', '2024-12-25', 
                    '2025-01-01', '2025-01-27', '2025-03-29', '2025-03-31', '2025-04-18', '2025-04-20', '2025-05-01', '2025-05-12', '2025-05-29', '2025-06-01', '2025-06-06', '2025-06-27', '2025-08-17', '2025-09-05', '2025-10-20', '2025-12-25',
                    '2026-01-01', '2026-02-17', '2026-03-19', '2026-03-20', '2026-04-03', '2026-04-05', '2026-05-01', '2026-05-14', '2026-05-24', '2026-06-01', '2026-06-16', '2026-07-07', '2026-08-17', '2026-08-25', '2026-12-25' 
                ]
                next_month = today.replace(day=28) + datetime.timedelta(days=4)
                last_day_month = next_month - datetime.timedelta(days=next_month.day)
                date_range_rest = pd.date_range(start=today, end=last_day_month)
                remaining_workdays = sum(1 for d in date_range_rest if d.weekday() != 6 and d.strftime('%Y-%m-%d') not in holidays_id)
                
                if len(date_range) == 2:
                    start_d, end_d = date_range
                    total_days = (end_d - start_d).days + 1
                    if end_d < today: days_gone = total_days
                    elif start_d > today: days_gone = 0
                    else: 
                        days_gone = (today - start_d).days + 1
                        if days_gone > total_days: days_gone = total_days
                        if days_gone < 0: days_gone = 0
                else: total_days = 1; days_gone = 1
                
                for sales_name, targets in INDIVIDUAL_TARGETS.items():
                    if selected_brand_detail in targets:
                        t_pribadi = targets[selected_brand_detail]
                        real_sales = df_active[(df_active['Penjualan'] == sales_name) & (df_active['Merk'] == selected_brand_detail)]['Jumlah'].sum()
                        
                        if total_days > 0:
                            target_harian = t_pribadi / total_days
                            expected_ach = target_harian * days_gone
                            gap = real_sales - expected_ach
                            target_remaining = t_pribadi - real_sales
                            if target_remaining > 0 and remaining_workdays > 0: catch_up_needed = target_remaining / remaining_workdays
                            else: catch_up_needed = 0 
                        else:
                            expected_ach = 0; gap = 0; catch_up_needed = 0

                        sales_stats.append({
                            "Nama Sales": sales_name, "Target Pribadi": format_idr(t_pribadi), "Realisasi": format_idr(real_sales),
                            "Ach %": f"{(real_sales/t_pribadi)*100:.1f}%", "Expected (Time Gone)": format_idr(expected_ach),
                            "Gap (Defisit/Surplus)": format_idr(gap), "Catch-up (Per Hari)": format_idr(catch_up_needed),
                            "_real": real_sales, "_target": t_pribadi
                        })
                        total_brand_sales += real_sales; total_brand_target += t_pribadi
                
                if sales_stats:
                    st.dataframe(pd.DataFrame(sales_stats).drop(columns=["_real", "_target"]), use_container_width=True)
                    m1, m2, m3 = st.columns(3)
                    m1.metric(f"Total Target {selected_brand_detail}", format_idr(total_brand_target))
                    m2.metric(f"Total Omset {selected_brand_detail}", format_idr(total_brand_sales))
                    ach_total = (total_brand_sales/total_brand_target)*100 if total_brand_target > 0 else 0
                    m3.metric("Total Ach %", f"{ach_total:.1f}%")
                else: st.info(f"Belum ada data target sales individu untuk brand {selected_brand_detail}")
        else: st.info("Menu ini khusus untuk melihat detail tim sales per brand.")

    with t3:
        st.subheader("📊 Pareto Analysis (80/20 Rule)")
        st.caption("Produk yang berkontribusi terhadap 80% dari total omset.")
        
        pareto_df = df_active.groupby('Nama Barang')['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=False)
        total_omset_pareto = pareto_df['Jumlah'].sum()
        
        if total_omset_pareto > 0:
            pareto_df['Kontribusi %'] = (pareto_df['Jumlah'] / total_omset_pareto) * 100
            pareto_df['Cumulative %'] = pareto_df['Kontribusi %'].cumsum()
            top_performers = pareto_df[pareto_df['Cumulative %'] <= 80]
            
            col_pareto1, col_pareto2 = st.columns(2)
            col_pareto1.metric("Total Produk Unik", len(pareto_df))
            col_pareto2.metric("Produk Kontributor Utama (80%)", len(top_performers))
            
            st.dataframe(
                top_performers[['Nama Barang', 'Jumlah', 'Kontribusi %']].style.format({'Jumlah': 'Rp {:,.0f}', 'Kontribusi %': '{:.2f}%'}),
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
        st.write("#### 🚨 Toko Tidur (Potensi Hilang)")
        st.caption("Toko yang bertransaksi di masa lalu tetapi TIDAK bertransaksi di periode yang dipilih.")
        
        all_outlets = df_scope_all['Nama Outlet'].unique()
        active_outlets = df_active['Nama Outlet'].unique()
        sleeping_outlets = list(set(all_outlets) - set(active_outlets))
        
        if sleeping_outlets:
            st.warning(f"Ada {len(sleeping_outlets)} toko yang belum order di periode ini.")
            with st.expander("Lihat Daftar Toko Tidur"):
                last_trx = []
                for outlet in sleeping_outlets:
                    outlet_df = df_scope_all[df_scope_all['Nama Outlet'] == outlet]
                    last_date = outlet_df['Tanggal'].max()
                    sales_handler = outlet_df['Penjualan'].iloc[0] if not outlet_df.empty else "-"
                    last_trx.append({"Nama Toko": outlet, "Sales": sales_handler, "Terakhir Order": last_date.strftime('%d %b %Y'), "Hari Sejak Order Terakhir": (datetime.date.today() - last_date.date()).days})
                st.dataframe(pd.DataFrame(last_trx).sort_values("Hari Sejak Order Terakhir"), use_container_width=True)
        else: st.success("Semua toko langganan sudah order di periode ini.")

        st.divider()
        st.write("#### 💎 Peluang Cross-Selling (White Space Analysis)")
        
        # PERBAIKAN TYPERROR PADA CROSS SELLING BRAND
        relevant_brands = df_active['Merk'].dropna().astype(str).unique()
        
        if len(relevant_brands) > 1:
            col_cs1, col_cs2 = st.columns(2)
            with col_cs1: brand_acuan = st.selectbox("Jika Toko sudah beli Brand:", sorted(relevant_brands), index=0)
            with col_cs2:
                target_options = [b for b in relevant_brands if b != brand_acuan]
                brand_target = st.selectbox("Tapi BELUM beli Brand:", sorted(target_options), index=0 if target_options else None)
            if brand_target:
                outlets_buy_acuan = df_active[df_active['Merk'] == brand_acuan]['Nama Outlet'].unique()
                opportunities = []
                for outlet in outlets_buy_acuan:
                    check = df_active[(df_active['Nama Outlet'] == outlet) & (df_active['Merk'] == brand_target)]
                    if check.empty:
                        sales_name = df_active[df_active['Nama Outlet'] == outlet]['Penjualan'].iloc[0]
                        opportunities.append({"Nama Toko": outlet, "Salesman": sales_name, "Potensi": f"Tawarkan {brand_target}"})
                if opportunities:
                    st.info(f"Ditemukan **{len(opportunities)} Toko** yang beli {brand_acuan} tapi belum beli {brand_target}.")
                    st.dataframe(pd.DataFrame(opportunities), use_container_width=True)
                else: st.success(f"Semua toko yang beli {brand_acuan} juga sudah membeli {brand_target}.")
        else: st.info("Data tidak cukup untuk analisa cross-selling (perlu minimal 2 brand aktif).")
        
        st.divider()
        st.write("#### 🧠 Rekomendasi Cross-Selling Cerdas (Berdasarkan Pola Transaksi)")
        st.caption("AI menganalisa pola pembelian dari ribuan transaksi untuk menemukan rekomendasi tersembunyi.")
        recs_df = get_cross_sell_recommendations(df_scope_all)
        if recs_df is not None and not recs_df.empty:
            st.success(f"Ditemukan {len(recs_df)} rekomendasi cerdas berdasarkan pola pembelian.")
            st.dataframe(recs_df, use_container_width=True)
        elif recs_df is None: st.warning("Kolom 'No Faktur' atau 'Nama Barang' tidak ditemukan. Tidak bisa menghitung pola.")
        else: st.info("Tidak ada rekomendasi cerdas yang memenuhi threshold (confidence > 50%). Perlu lebih banyak data transaksi.")
            
    with t_forecast:
        st.subheader("🔮 Prediksi Omset (Forecasting)")
        st.info("Prediksi tren omset 30 hari ke depan berdasarkan data historis harian.")
        df_forecast = df_scope_all.groupby('Tanggal')['Jumlah'].sum().reset_index().sort_values('Tanggal')
        if len(df_forecast) > 10:
            df_forecast['Date_Ordinal'] = df_forecast['Tanggal'].apply(lambda x: x.toordinal())
            x = df_forecast['Date_Ordinal'].values; y = df_forecast['Jumlah'].values
            z = np.polyfit(x, y, 1); p = np.poly1d(z)
            last_date = df_forecast['Tanggal'].max()
            future_days = 30
            future_dates = [last_date + datetime.timedelta(days=i) for i in range(1, future_days + 1)]
            future_ordinals = [d.toordinal() for d in future_dates]
            future_values = p(future_ordinals)
            
            df_history = df_forecast[['Tanggal', 'Jumlah']].copy()
            df_history['Type'] = 'Historis'
            df_future = pd.DataFrame({'Tanggal': future_dates, 'Jumlah': future_values})
            df_future['Type'] = 'Prediksi'
            df_combined = pd.concat([df_history, df_future])
            
            fig_forecast = px.line(df_combined, x='Tanggal', y='Jumlah', color='Type', line_dash='Type', color_discrete_map={'Historis': '#2980b9', 'Prediksi': '#e74c3c'})
            fig_forecast.update_layout(title="Proyeksi Omset 30 Hari Kedepan", xaxis_title="Tanggal", yaxis_title="Omset")
            st.plotly_chart(fig_forecast, use_container_width=True)
            trend = "NAIK 📈" if z[0] > 0 else "TURUN 📉"
            st.write(f"**Analisa Tren:** Berdasarkan data historis, tren penjualan terlihat **{trend}**.")
        else: st.warning("Data belum cukup untuk melakukan prediksi (minimal 10 hari transaksi).")

    with t4:
        st.subheader("📋 Data Rincian & Analisis Spesifik")
        
        # --- FUNGSI WARNA SMART CONDITIONAL FORMATTING ---
        def get_color_achv(val):
            try:
                if val < 0.50: return '#ffcccc' # Merah (Di bawah 50%)
                elif val < 0.85: return '#ffffcc' # Kuning (50% sampai 84.9%)
                else: return '#ccffcc' # Hijau (85% ke atas)
            except:
                return ''
        # --------------------------------------------------

        # --- UI: 3 SUB-TAB BARU ---
        tab_pivot, tab_growth, tab_ba = st.tabs(["📊 Pivot Data Customer", "📈 Rekap Growth Brand", "🎯 Pencapaian Target BA"])
        
        # =========================================================================
        # SUB-TAB 1: PIVOT DATA CUSTOMER
        # =========================================================================
        with tab_pivot:
            list_merk_excel = sorted(df_active['Merk'].dropna().astype(str).unique())
            selected_merk_excel = st.selectbox("🎯 Pilih Merk untuk dilihat rinciannya:", ["SEMUA"] + list_merk_excel)
            
            if selected_merk_excel != "SEMUA":
                df_excel = df_active[df_active['Merk'] == selected_merk_excel].copy()
            else:
                df_excel = df_active.copy()

            if not df_excel.empty:
                df_excel['Bulan Angka'] = df_excel['Tanggal'].dt.month
                
                group_cols = []
                kode_asal = 'Kode Customer'
                
                if 'Kode Customer' in df_excel.columns: 
                    group_cols.append('Kode Customer')
                    kode_asal = 'Kode Customer'
                elif 'Kode Costumer' in df_excel.columns: 
                    group_cols.append('Kode Costumer')
                    kode_asal = 'Kode Costumer'
                elif 'Kode Outlet' in df_excel.columns: 
                    group_cols.append('Kode Outlet')
                    kode_asal = 'Kode Outlet'
                else:
                    df_excel['Kode Customer'] = "-"
                    group_cols.append('Kode Customer')
                    kode_asal = 'Kode Customer'
                    
                group_cols.append('Nama Outlet') 
                
                if 'Kota' in df_excel.columns: group_cols.append('Kota')
                else:
                    df_excel['Kota'] = "-"
                    group_cols.append('Kota')

                master_pivot = pd.pivot_table(
                    df_excel, values='Jumlah', index=group_cols, columns='Bulan Angka', aggfunc='sum', fill_value=0
                )

                bulan_indo = {
                    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
                    5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
                    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
                }

                for i in range(1, 13):
                    if i not in master_pivot.columns: master_pivot[i] = 0

                master_pivot = master_pivot[list(range(1, 13))]
                master_pivot.columns = [bulan_indo[i] for i in master_pivot.columns]
                master_pivot['Total Penjualan'] = master_pivot.sum(axis=1)

                master_pivot = master_pivot.reset_index()
                
                master_pivot = master_pivot.rename(columns={'Nama Outlet': 'Nama Customer', kode_asal: 'Kode Customer'})

                st.markdown("#### 🔎 Filter Spesifik")
                col_f1, col_f2, col_f3 = st.columns(3)
                
                with col_f1:
                    list_kode = sorted([str(x) for x in master_pivot['Kode Customer'].unique() if str(x) != 'nan'])
                    filter_kode = st.multiselect("Kode Customer:", list_kode, placeholder="Pilih Kode...")
                    
                with col_f2:
                    list_nama = sorted([str(x) for x in master_pivot['Nama Customer'].unique() if str(x) != 'nan'])
                    filter_nama = st.multiselect("Nama Customer:", list_nama, placeholder="Pilih Customer...")
                    
                with col_f3:
                    list_kota = sorted([str(x) for x in master_pivot['Kota'].unique() if str(x) != 'nan'])
                    filter_kota = st.multiselect("Kota:", list_kota, placeholder="Pilih Kota...")

                df_filtered = master_pivot.copy()
                if filter_kode: df_filtered = df_filtered[df_filtered['Kode Customer'].astype(str).isin(filter_kode)]
                if filter_nama: df_filtered = df_filtered[df_filtered['Nama Customer'].astype(str).isin(filter_nama)]
                if filter_kota: df_filtered = df_filtered[df_filtered['Kota'].astype(str).isin(filter_kota)]
                
                st.caption(f"Menampilkan {len(df_filtered)} data customer.")

                if not df_filtered.empty:
                    num_cols = list(bulan_indo.values()) + ['Total Penjualan']
                    
                    total_dict = {col: "" for col in df_filtered.columns}
                    total_dict['Nama Customer'] = "GRAND TOTAL" 
                    
                    for col in num_cols:
                        total_dict[col] = df_filtered[col].sum()
                    
                    df_display = pd.concat([df_filtered, pd.DataFrame([total_dict])], ignore_index=True)
                else:
                    df_display = df_filtered.copy()

                if AGGRID_AVAILABLE:
                    gb = GridOptionsBuilder.from_dataframe(df_display)
                    gb.configure_pagination(paginationAutoPageSize=True)
                    gb.configure_side_bar()
                    gb.configure_default_column(filter='agSetColumnFilter', sortable=True, resizable=True, floatingFilter=True, menuTabs=['filterMenuTab', 'generalMenuTab', 'columnsMenuTab'])
                    
                    for col in num_cols:
                        gb.configure_column(col, type=["numericColumn","numberColumnFilter"], valueFormatter="x.toLocaleString('id-ID', {style: 'currency', currency: 'IDR', minimumFractionDigits: 0})")
                    
                    jscode = JsCode("""
                    function(params) {
                        if (params.data['Nama Customer'] === 'GRAND TOTAL') {
                            return {
                                'font-weight': 'bold',
                                'background-color': '#eef2f5',
                                'border-top': '2px solid #2980b9'
                            }
                        }
                    }
                    """)
                    gb.configure_grid_options(getRowStyle=jscode)
                    
                    gridOptions = gb.build()
                    AgGrid(df_display, gridOptions=gridOptions, enable_enterprise_modules=True, height=550, theme='alpine', allow_unsafe_jscode=True)
                else:
                    format_dict = {col: "Rp {:,.0f}" for col in num_cols}
                    st.dataframe(df_display.style.format(format_dict), use_container_width=True, hide_index=True)
            else:
                st.info("Data Kosong.")

            user_role_lower = role.lower()
            if user_role_lower in ['direktur', 'manager', 'supervisor']:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    if 'df_display' in locals() and not df_display.empty:
                        df_display.to_excel(writer, index=False, sheet_name='Master Data')
                    else:
                        df_active.to_excel(writer, index=False, sheet_name='Sales Data')
                    
                    workbook = writer.book
                    worksheet = writer.sheets['Master Data' if 'df_display' in locals() else 'Sales Data']
                    
                    user_identity = f"{st.session_state['sales_name']} ({st.session_state['role'].upper()})"
                    time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    watermark_text = f"CONFIDENTIAL DOCUMENT | TRACKED USER: {user_identity} | DOWNLOADED: {time_stamp} | DO NOT DISTRIBUTE"
                    
                    worksheet.set_header(f'&C&10{watermark_text}')
                    worksheet.set_footer(f'&RPage &P of &N')
                    
                    format1 = workbook.add_format({'num_format': '#,##0'})
                    worksheet.set_column('D:P', None, format1) 
                    
                    if 'df_display' in locals() and not df_display.empty:
                        bold_format = workbook.add_format({'bold': True, 'bg_color': '#f2f2f2', 'border': 1, 'num_format': '#,##0'})
                        last_row_idx = len(df_display) 
                        worksheet.set_row(last_row_idx, None, bold_format)
                
                st.download_button(
                    label="📥 Download Laporan Excel (XLSX) - DRM Protected",
                    data=output.getvalue(),
                    file_name=f"Laporan_Master_{selected_merk_excel}_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            elif role in ['direktur']: 
                 csv = df_display.to_csv(index=False).encode('utf-8') if 'df_display' in locals() else df_active.to_csv(index=False).encode('utf-8')
                 file_name = f"Laporan_Sales_{datetime.date.today()}.csv"
                 st.download_button("📥 Download Data CSV", data=csv, file_name=file_name, mime="text/csv")

        # =========================================================================
        # SUB-TAB 2: REKAP GROWTH BRAND (RO, AO, NOO & YoY)
        # =========================================================================
        with tab_growth:
            st.markdown("### 📈 Rekap Growth Brand (2025 vs 2026)")
            list_merk_growth = sorted(df_scope_all['Merk'].dropna().astype(str).unique())
            
            if list_merk_growth:
                brand_growth = st.selectbox("Pilih Brand untuk Analisis Growth:", list_merk_growth)
                
                df_brand_all = df[df['Merk'] == brand_growth].copy()
                
                if target_sales_filter != "SEMUA":
                    if target_sales_filter.upper() in TARGET_DATABASE:
                        tim_sales_list = list(TARGET_DATABASE[target_sales_filter.upper()].keys())
                        df_brand_all = df_brand_all[df_brand_all['Penjualan'].isin(tim_sales_list)]
                    else:
                        df_brand_all = df_brand_all[df_brand_all['Penjualan'] == target_sales_filter]
                elif role not in ['manager', 'direktur', 'supervisor'] and my_name.lower() != 'fauziah':
                    df_brand_all = df_brand_all[df_brand_all['Penjualan'] == my_name]

                if not df_brand_all.empty:
                    df_brand_all['Tahun'] = df_brand_all['Tanggal'].dt.year
                    df_brand_all['Bulan'] = df_brand_all['Tanggal'].dt.month
                    df_brand_all['Bulan-Tahun'] = df_brand_all['Tanggal'].dt.to_period('M')
                    
                    all_months = sorted(df_brand_all['Bulan-Tahun'].dropna().unique())
                    
                    growth_data = []
                    seen_outlets = set()
                    
                    for period in all_months:
                        df_period = df_brand_all[df_brand_all['Bulan-Tahun'] == period]
                        current_outlets = set(df_period['Nama Outlet'].dropna().unique())
                        
                        sales = df_period['Jumlah'].sum()
                        ao = len(current_outlets)
                        noo = len(current_outlets - seen_outlets)
                        
                        seen_outlets.update(current_outlets)
                        ro = len(seen_outlets)
                        
                        ao_vs_ro = (ao / ro) if ro > 0 else 0
                        
                        growth_data.append({
                            'Year': period.year,
                            'Month': period.month,
                            'SALES': sales,
                            'RO': ro,
                            'AO': ao,
                            'AO VS RO %': ao_vs_ro,
                            'NOO': noo
                        })
                    
                    df_growth_all = pd.DataFrame(growth_data)
                    
                    if not df_growth_all.empty:
                        bulan_dict_short = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
                        
                        st.divider()
                        st.write(f"#### **Tabel 1: Aktivitas Outlet {brand_growth} (Tahun 2026)**")
                        df_2026 = df_growth_all[df_growth_all['Year'] == 2026].copy()
                        
                        display_2026 = []
                        for m in range(1, 13):
                            row = df_2026[df_2026['Month'] == m]
                            if not row.empty:
                                r = row.iloc[0]
                                display_2026.append({
                                    'MONTH': f"{bulan_dict_short[m]}-26",
                                    'SALES': r['SALES'],
                                    'RO': int(r['RO']), 'AO': int(r['AO']),
                                    'AO VS RO %': r['AO VS RO %'],
                                    'NOO': int(r['NOO'])
                                })
                            else:
                                display_2026.append({'MONTH': f"{bulan_dict_short[m]}-26", 'SALES': 0, 'RO': 0, 'AO': 0, 'AO VS RO %': 0, 'NOO': 0})
                        
                        # Apply style with borders for Table 1
                        def style_tab1(row):
                            styles = []
                            for col in row.index:
                                base_style = 'border: 1px solid #dcdcdc; '
                                if col == 'AO VS RO %':
                                    bg = get_color_achv(row[col])
                                    styles.append(base_style + f'background-color: {bg}; color: black;')
                                else:
                                    styles.append(base_style)
                            return styles

                        st.dataframe(pd.DataFrame(display_2026).style.format({
                            'SALES': 'Rp {:,.0f}', 'AO VS RO %': '{:.0%}'
                        }).apply(style_tab1, axis=1), use_container_width=True)
                        
                        st.divider()
                        col_g1, col_g2 = st.columns(2)
                        
                        df_2025 = df_growth_all[df_growth_all['Year'] == 2025]
                        df_2026_sales = df_growth_all[df_growth_all['Year'] == 2026]
                        
                        def get_sales(df_yr, m):
                            res = df_yr[df_yr['Month'] == m]['SALES']
                            return res.sum() if not res.empty else 0

                        tot_2025 = 0
                        tot_2026 = 0
                        
                        with col_g1:
                            st.write(f"#### **Tabel 2: {brand_growth} 2025 vs 2026 Sales Growth**")
                            yoy_data = []
                            for m in range(1, 13):
                                s25 = get_sales(df_2025, m)
                                s26 = get_sales(df_2026_sales, m)
                                tot_2025 += s25
                                tot_2026 += s26
                                growth = ((s26 - s25) / s25) if s25 > 0 else (1 if s26 > 0 else 0)
                                yoy_data.append({
                                    'MONTH': bulan_dict_short[m], 'SALES 2025': s25, 'SALES 2026': s26, 'Growth MTM': growth
                                })
                            
                            df_t2 = pd.DataFrame(yoy_data)
                            tot_growth = ((tot_2026 - tot_2025) / tot_2025) if tot_2025 > 0 else (1 if tot_2026 > 0 else 0)
                            df_t2_total = pd.DataFrame([{'MONTH': 'Total Sales', 'SALES 2025': tot_2025, 'SALES 2026': tot_2026, 'Growth MTM': tot_growth}])
                            df_t2_display = pd.concat([df_t2, df_t2_total], ignore_index=True)
                            
                            # Apply style with borders for Table 2
                            def style_tab2(row):
                                styles = []
                                for col in row.index:
                                    base_style = 'border: 1px solid #dcdcdc; '
                                    if row['MONTH'] == 'Total Sales':
                                        if col == 'Growth MTM':
                                            bg = get_color_achv(row[col])
                                            styles.append(base_style + f'background-color: {bg}; color: black; font-weight: bold;')
                                        else:
                                            styles.append(base_style + 'background-color: lightblue; font-weight: bold; color: black;')
                                    else:
                                        if col == 'Growth MTM':
                                            bg = get_color_achv(row[col])
                                            styles.append(base_style + f'background-color: {bg}; color: black;')
                                        else:
                                            styles.append(base_style)
                                return styles

                            st.dataframe(df_t2_display.style.format({
                                'SALES 2025': 'Rp {:,.0f}', 'SALES 2026': 'Rp {:,.0f}', 'Growth MTM': '{:.0%}'
                            }).apply(style_tab2, axis=1), use_container_width=True)
                        
                        with col_g2:
                            st.write(f"#### **Tabel 3: Quarterly Growth**")
                            q_data = []
                            for q, m_start in [('Q1', 1), ('Q2', 4), ('Q3', 7), ('Q4', 10)]:
                                m_end = m_start + 2
                                q_2025 = sum(get_sales(df_2025, m) for m in range(m_start, m_end + 1))
                                q_2026 = sum(get_sales(df_2026_sales, m) for m in range(m_start, m_end + 1))
                                
                                q_growth = ((q_2026 - q_2025) / q_2025) if q_2025 > 0 else (1 if q_2026 > 0 else 0)
                                q_data.append({
                                    'MONTH': f"Total {q}", 'SALES 2025': q_2025, 'SALES 2026': q_2026, 'Growth MTM': q_growth
                                })
                            
                            df_q = pd.DataFrame(q_data)
                            df_q_display = pd.concat([df_q, df_t2_total], ignore_index=True)
                            
                            # Apply style with borders for Table 3
                            def style_tab3(row):
                                styles = []
                                for col in row.index:
                                    base_style = 'border: 1px solid #dcdcdc; '
                                    if row['MONTH'] == 'Total Sales':
                                        if col == 'Growth MTM':
                                            bg = get_color_achv(row[col])
                                            styles.append(base_style + f'background-color: {bg}; color: black; font-weight: bold;')
                                        else:
                                            styles.append(base_style + 'background-color: lightblue; font-weight: bold; color: black;')
                                    else:
                                        if col == 'Growth MTM':
                                            bg = get_color_achv(row[col])
                                            styles.append(base_style + f'background-color: {bg}; color: black;')
                                        else:
                                            styles.append(base_style)
                                return styles

                            st.dataframe(df_q_display.style.format({
                                'SALES 2025': 'Rp {:,.0f}', 'SALES 2026': 'Rp {:,.0f}', 'Growth MTM': '{:.0%}'
                            }).apply(style_tab3, axis=1), use_container_width=True)
                else:
                    st.info(f"Belum ada data untuk brand {brand_growth}.")
            else:
                st.info("Tidak ada data.")

        # =========================================================================
        # SUB-TAB 3: PENCAPAIAN TARGET BA (DIBAGI PER BRAND)
        # =========================================================================
        with tab_ba:
            st.markdown("### 🎯 Pencapaian Target BA per Brand (Tahun 2026)")
            
            TARGET_BA_PER_BRAND = {
                "Careso": {
                    "PT. PESONA ASIA GROUP ( GM STORE )": 30_000_000,
                    "TOKO DUTA COSMETIK ( BIREUEN )": 50_000_000,
                    "HIJRAH STORE COSMETIK": 50_000_000,
                    "TOKO UNDERPRICE SKIN CARE": 50_000_000,
                    "PT.RADYSA DHARMA ABADI": 50_000_000,
                    "TOKO BEAUTY ART": 30_000_000,
                    "PT.PINMOOD INDONESIA SEJAHTERA": 30_000_000
                },
                "Somethinc": {
                    "PT. PESONA ASIA GROUP ( GM STORE )": 40_000_000,
                    "TOKO DUTA COSMETIK ( BIREUEN )": 25_000_000,
                    "TOKO BEAUTY ART": 35_000_000
                },
                "Javinci": {
                    "HIJRAH STORE COSMETIK": 20_000_000,
                    "TOKO UNDERPRICE SKIN CARE": 25_000_000,
                    "PT.PINMOOD INDONESIA SEJAHTERA": 15_000_000
                }
            }
            
            available_ba_brands = list(TARGET_BA_PER_BRAND.keys())
            selected_ba_brand = st.selectbox("Pilih Brand untuk melihat Target BA:", available_ba_brands)
            
            if selected_ba_brand:
                current_target_dict = TARGET_BA_PER_BRAND[selected_ba_brand]
                
                df_ba_all = df_scope_all[
                    (df_scope_all['Merk'] == selected_ba_brand) & 
                    (df_scope_all['Nama Outlet'].isin(current_target_dict.keys())) & 
                    (df_scope_all['Tanggal'].dt.year == 2026)
                ].copy()
                
                bulan_dict_ba = {1:'Januari', 2:'Februari', 3:'Maret', 4:'April', 5:'Mei', 6:'Juni', 7:'Juli', 8:'Agustus', 9:'September', 10:'Oktober', 11:'November', 12:'Desember'}
                
                ba_df = pd.DataFrame(list(current_target_dict.items()), columns=['Costumer', 'Target BA'])
                
                if not df_ba_all.empty:
                    df_ba_all['Bulan Angka'] = df_ba_all['Tanggal'].dt.month
                    pivot_ba = pd.pivot_table(df_ba_all, values='Jumlah', index='Nama Outlet', columns='Bulan Angka', aggfunc='sum', fill_value=0)
                    
                    for m in range(1, 13):
                        if m not in pivot_ba.columns:
                            pivot_ba[m] = 0
                            
                    pivot_ba = pivot_ba[list(range(1, 13))]
                    pivot_ba.columns = [bulan_dict_ba[m] for m in pivot_ba.columns]
                    pivot_ba = pivot_ba.reset_index().rename(columns={'Nama Outlet': 'Costumer'})
                    
                    merged_ba = pd.merge(ba_df, pivot_ba, on='Costumer', how='left').fillna(0)
                else:
                    merged_ba = ba_df.copy()
                    for m in range(1, 13):
                        merged_ba[bulan_dict_ba[m]] = 0
                
                st.write(f"**Rekap Keseluruhan Toko BA untuk Brand `{selected_ba_brand}` (2026)**")
                format_ba = {col: 'Rp {:,.0f}' for col in list(bulan_dict_ba.values()) + ['Target BA']}
                st.dataframe(merged_ba.style.format(format_ba), use_container_width=True, hide_index=True)
                
                st.divider()
                
                selected_month_ba = st.selectbox(f"Pilih Bulan untuk Detail Achievement ({selected_ba_brand}):", list(bulan_dict_ba.values()))
                
                achv_data = []
                total_target = 0
                total_achv = 0
                
                for idx, row in merged_ba.iterrows():
                    costumer = row['Costumer']
                    target = row['Target BA']
                    pencapaian = row[selected_month_ba]
                    achv_pct = (pencapaian / target) if target > 0 else 0
                    
                    total_target += target
                    total_achv += pencapaian
                    
                    achv_data.append({
                        'Costumer': costumer,
                        'Target BA': target,
                        f'Pencapaian {selected_month_ba}': pencapaian,
                        'ACHV': achv_pct
                    })
                
                df_achv = pd.DataFrame(achv_data)
                
                df_achv_total = pd.DataFrame([{
                    'Costumer': 'Total Achievement',
                    'Target BA': total_target,
                    f'Pencapaian {selected_month_ba}': total_achv,
                    'ACHV': (total_achv/total_target) if total_target > 0 else 0
                }])
                
                df_achv_display = pd.concat([df_achv, df_achv_total], ignore_index=True)
                
                st.write(f"**Tabel Pencapaian Target BA `{selected_ba_brand}` - {selected_month_ba} 2026**")
                
                # Apply style with borders for Table Target BA
                def style_ba(row):
                    styles = []
                    for col in row.index:
                        base_style = 'border: 1px solid #dcdcdc; '
                        if row['Costumer'] == 'Total Achievement':
                            if col == 'ACHV':
                                bg = get_color_achv(row[col])
                                styles.append(base_style + f'background-color: {bg}; color: black; font-weight: bold;')
                            else:
                                styles.append(base_style + 'background-color: lightblue; font-weight: bold; color: black;')
                        else:
                            if col == 'ACHV':
                                bg = get_color_achv(row[col])
                                styles.append(base_style + f'background-color: {bg}; color: black;')
                            else:
                                styles.append(base_style)
                    return styles
                
                st.dataframe(df_achv_display.style.format({
                    'Target BA': 'Rp {:,.0f}',
                    f'Pencapaian {selected_month_ba}': 'Rp {:,.0f}',
                    'ACHV': '{:.0%}'
                }).apply(style_ba, axis=1), use_container_width=True)

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if st.session_state['logged_in']: main_dashboard()
else: login_page()
