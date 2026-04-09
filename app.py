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
import concurrent.futures
import streamlit.components.v1 as components 

# --- LIBRARY UNTUK TABEL EXCEL-LIKE ---
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, ColumnsAutoSizeMode
    AGGRID_AVAILABLE = True
except ImportError:
    AGGRID_AVAILABLE = False

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard Sales", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- INIT SESSION STATE UNTUK KEAMANAN (ANTI BRUTE-FORCE) ---
if 'failed_attempts' not in st.session_state:
    st.session_state['failed_attempts'] = {}
if 'lockout_until' not in st.session_state:
    st.session_state['lockout_until'] = {}

# --- AUTO LOGOUT (INACTIVITY TIMEOUT: 15 MENIT) ---
TIMEOUT_SECONDS = 900 
if 'last_activity' in st.session_state and st.session_state.get('logged_in', False):
    if time.time() - st.session_state['last_activity'] > TIMEOUT_SECONDS:
        st.session_state.clear()
        st.session_state['logged_out_due_to_inactivity'] = True
        st.rerun()
st.session_state['last_activity'] = time.time()

# Custom CSS & Tema Corporate Blue (Termasuk Hover Tabs & Hilangkan Logo Streamlit)
st.markdown("""
<style>
    .metric-card {
        border: 1px solid #e6e6e6; padding: 20px; border-radius: 10px;
        background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #3498db, #f1c40f, #2ecc71);
    }
    div[data-testid="stDataFrame"] div[role="gridcell"] {
        white-space: pre-wrap !important; 
    }
    
    /* MENYEMBUNYIKAN WATERMARK & TOMBOL MANAGE APP STREAMLIT SECARA PAKSA */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stAppDeployButton"] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    div[data-testid="manage-app-button"] {display: none !important;}
    
    /* PERBESAR FONT METRIC BAWAAN STREAMLIT */
    [data-testid="stMetricLabel"] p {
        font-size: 18px !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] div {
        font-size: 36px !important;
        font-weight: bold !important;
    }
    
    /* MENGUBAH WARNA TAB (ACTIVE & HOVER) KE CORPORATE BLUE */
    div[data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #2980b9 !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #2980b9 !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom-color: #2980b9 !important;
    }
    div[data-baseweb="tab-list"] button:hover {
        color: #2980b9 !important;
    }
    div[data-baseweb="tab-list"] button:hover span {
        color: #2980b9 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# MASTER KALENDER LIBUR NASIONAL 2026 (INDONESIA)
# ==========================================
HOLIDAYS_2026 = [
    '2026-01-01', '2026-02-14', '2026-02-17', '2026-03-19', '2026-03-20', 
    '2026-04-03', '2026-05-01', '2026-05-14', '2026-05-26', '2026-06-01', 
    '2026-06-16', '2026-08-17', '2026-08-25', '2026-12-25'
]

# ==========================================
# KAMUS GEOGRAFIS & PREFIX BRAND
# ==========================================
PROVINCE_MAPPING = {
    "SUMATERA UTARA": ["MEDAN", "MDN", "BINJAI", "BINJEI", "TEBING", "SIANTAR", "PEMATANG", "TANJUNG BALAI", "SIBOLGA", "SIDEMPUAN", "PADANGSIDEMPUAN", "GUNUNGSITOLI", "DELI", "SERDANG", "KARO", "LANGKAT", "ASAHAN", "SIMALUNGUN", "DAIRI", "TOBA", "MANDAILING", "NIAS", "TAPANULI", "BATUBARA", "LABUHAN", "KISARAN", "RANTAU", "TARUTUNG", "STABAT", "PAKAM", "KABANJAHE", "SAMOSIR", "HUMBANG", "PAKPAK", "BALIGE", "SIDIKALANG", "PANGURURAN", "SALAK", "PANYABUNGAN", "SUNGGAL", "PERCUT", "TEMBUNG", "TAMORA", "TANJUNG MORAWA", "BERASTAGI", "SEI RAMPAH", "PERBAUNGAN", "INDRAPURA", "LIMA PULUH", "AEK KANOPAN", "KOTA PINANG", "SIBUHUAN", "GUNUNG TUA", "SIPIROK", "PANCUR BATU"],
    "ACEH": ["ACEH", "SABANG", "LHOKSEUMAWE", "LANGSA", "SUBULUSSALAM", "BIREUEN", "BIREUN", "PIDIE", "MEULABOH", "SIGLI", "KUTACANE", "TAKENGON", "GAYO", "BENER MERIAH", "NAGAN", "SIMEULUE", "TAPAKTUAN", "SINGKIL", "BLANGPIDIE", "IDI", "PEUREULAK", "PERULAK", "LHOKSUKON", "KUALA SIMPANG", "MATANG", "PANTON", "MEUREUDU"],
    "SUMATERA BARAT": ["PADANG", "BUKITTINGGI", "PAYAKUMBUH", "PARIAMAN", "SOLOK", "SAWAHLUNTO", "AGAM", "DHARMASRAYA", "MENTAWAI", "PASAMAN", "PESISIR", "SIJUNJUNG", "TANAH DATAR", "BATUSANGKAR", "LUBUK BASUNG", "SIMPANG EMPAT", "UJUNG GADING", "LUBUK SIKAPING", "MUARA LABUH", "PULAU PUNJUNG", "SUNGAI RUMBAI"],
    "RIAU": ["PEKANBARU", "PKU", "DUMAI", "BENGKALIS", "KAMPAR", "ROKAN", "SIAK", "PELALAWAN", "INDRAGIRI", "MERANTI", "KUANTAN", "BANGKINANG", "TEMBILAHAN", "RENGAT", "UJUNGBATU", "PASIR PENGARAIAN", "BAGANSIAPIAPI", "DURI", "BAGAN BATU", "UJUNG BATU", "MINAS", "PERAWANG", "KANDIS", "PANGKALAN KERINCI", "SOREK", "BELILAS", "UKUI", "AIR MOLEK", "LIRIK", "TELUK KUANTAN"],
    "KEPULAUAN RIAU": ["BATAM", "TANJUNGPINANG", "BINTAN", "KARIMUN", "NATUNA", "LINGGA", "ANAMBAS"],
    "JAMBI": ["JAMBI", "SUNGAI PENUH", "BUNGO", "MERANGIN", "BATANGHARI", "MUARO", "SAROLANGUN", "TANJUNG JABUNG", "TEBO", "BANGKO", "MUARA BUNGO", "KUALA TUNGKAL", "RIMBO BUJANG", "SUNGAI BENGKAL"],
    "SUMATERA SELATAN": ["PALEMBANG", "LUBUKLINGGAU", "PRABUMULIH", "PAGAR ALAM", "BANYUASIN", "EMPAT LAWANG", "LAHAT", "MUARA ENIM", "MUSI", "OGAN", "OKU", "OKI", "SEKAYU", "INDRALAYA"],
    "BENGKULU": ["BENGKULU", "KAUR", "KEPAHIANG", "LEBONG", "MUKOMUKO", "REJANG LEBONG", "SELUMA", "BINTUHAN", "CURUP", "ARGA MAKMUR"],
    "LAMPUNG": ["LAMPUNG", "METRO", "PESAWARAN", "PRINGSEWU", "TANGGAMUS", "TULANG BAWANG", "WAY KANAN", "MESUJI", "KALIANDA", "KOTABUMI", "LIWA", "MENGGALA", "GUNUNG SUGIH"],
    "BANGKA BELITUNG": ["PANGKALPINANG", "BANGKA", "BELITUNG", "SUNGAILIAT", "MUNTOK", "KOBA", "TOBOALI", "TANJUNG PANDAN", "MANGGAR"],
    "DKI JAKARTA": ["JAKARTA", "JKT"],
    "JAWA BARAT": ["BANDUNG", "BEKASI", "BOGOR", "DEPOK", "CIMAHI", "CIREBON", "SUKABUMI", "TASIKMALAYA", "BANJAR", "GARUT", "CIANJUR", "CIAMIS", "KUNINGAN", "MAJALENGKA", "PANGANDARAN", "PURWAKARTA", "SUBANG", "SUMEDANG", "INDRAMAYU", "KARAWANG", "CIBINONG", "CISAAT", "SOREANG", "NGAMPRAH", "TAROGONG", "SINGAPARNA"],
    "BANTEN": ["SERANG", "CILEGON", "TANGERANG", "LEBAK", "PANDEGLANG", "RANGKASBITUNG", "TIGARAKSA"],
    "JAWA TENGAH": ["SEMARANG", "MAGELANG", "PEKALONGAN", "SALATIGA", "SURAKARTA", "SOLO", "TEGAL", "KUDUS", "PURWOKERTO", "DEMAK", "PATI", "BANJARNEGARA", "BANYUMAS", "BATANG", "BLORA", "BOYOLALI", "BREBES", "CILACAP", "GROBOGAN", "JEPARA", "KARANGANYAR", "KEBUMEN", "KENDAL", "KLATEN", "PEMALANG", "PURBALINGGA", "PURWOREJO", "REMBANG", "SRAGEN", "SUKOHARJO", "TEMANGGUNG", "WONOGIRI", "WONOSOBO", "MUNGKID", "KAJEN", "SLAWI", "PURWODADI", "UNGARAN"],
    "DI YOGYAKARTA": ["YOGYAKARTA", "JOGJA", "SLEMAN", "BANTUL", "GUNUNGKIDUL", "KULON PROGO", "WONOSARI", "WATES"],
    "JAWA TIMUR": ["SURABAYA", "KEDIRI", "MADIUN", "MALANG", "MOJOKERTO", "PASURUAN", "PROBOLINGGO", "BATU", "BLITAR", "SIDOARJO", "GRESIK", "JEMBER", "BANYUWANGI", "BOJONEGORO", "BONDOWOSO", "JOMBANG", "LAMONGAN", "LUMAJANG", "MAGETAN", "NGANJUK", "NGAWI", "PACITAN", "PAMEKASAN", "PONOROGO", "SAMPANG", "SITUBONDO", "SUMENEP", "TRENGGALEK", "TUBAN", "TULUNGAGUNG", "BANGKALAN", "KANIGORO", "NGASEM", "CARUBAN", "KEPANJEN", "MOJOSARI", "BANGIL", "KRAKSAAN"],
    "BALI": ["DENPASAR", "BADUNG", "GIANYAR", "BULELENG", "BANGLI", "JEMBRANA", "KARANGASEM", "KLUNGKUNG", "TABANAN", "MANGUPURA", "SINGARAJA", "NEGARA", "AMLAPURA", "SEMARAPURA"]
}

BRAND_PREFIXES = {
    "Javinci": ["JV"], "Careso": ["EPS", "CRS"], "Somethinc": ["SMT", "SOM"],
    "Newlab": ["NL", "NEW"], "Gloow & Be": ["GB", "GLO"], "Dorskin": ["DRS", "DOR"],
    "Whitelab": ["WL", "WHI"], "Bonavie": ["BNV", "BON"], "Goute": ["GT", "GOU"],
    "Mlen": ["MLN", "MLE"], "Artist Inc": ["ART"], "Maskit": ["MSK", "MAS"], 
    "Birth Beyond": ["BB", "BIR"], "Sociolla": ["SOC", "SCL"], "Thai": ["TH", "THA"], 
    "Inesia": ["INS", "INE"], "Y2000": ["Y2K", "Y20"], "Diosys": ["DIO", "DS"], 
    "Masami": ["MSM", "MAS"], "Cassandra": ["CAS", "CSD"], "Clinelle": ["CLN", "CLI"], 
    "Beautica": ["BTC", "BEA"], "Claresta": ["CLA", "CLR"], "Rose All Day": ["RAD", "ROS"], 
    "OtwooO": ["OTO", "OTW"], "Sekawan": ["SKW", "SEK", "AINIE", "AIN"], "Avione": ["AV"], 
    "Honor": ["HNR", "HON"], "Vlagio": ["VLG", "VLA"], "Ren & R & L": ["REN", "RRL"], 
    "Mad For Make Up": ["MFM", "MAD"], "Satto": ["STT", "SAT"], "Mykonos": ["MYK", "MYC"], 
    "The Face": ["TF", "TFC"], "Yu Chun Mei": ["YCM", "YUC"], "Milano": ["MIL", "MLN"], 
    "Walnutt": ["WAL", "WLN"], "Elizabeth Rose": ["ELZ", "ELI"], "Sombong":["SOMBONG"], "Everpure":["EVERPURE"]
}

def map_city_to_province(city_name):
    if pd.isna(city_name): return "LAIN-LAIN"
    c = str(city_name).upper().strip()
    if c in ["", "-", "NAN", "0.0", "NONE", "NULL", "0"]: return "LAIN-LAIN"
    c = re.sub(r'^(KECAMATAN|KEC\.|KEC|KABUPATEN|KAB\.|KAB|KOTA)\s+', '', c).strip()
    for province, cities in PROVINCE_MAPPING.items():
        for city in cities:
            if re.search(rf'\b{city}\b', c): return province
    return "LAIN-LAIN"

# ==========================================
# 2. KONFIGURASI DATABASE & TARGET
# ==========================================
TARGET_DATABASE = {
    "MADONG": { "Somethinc": 1_200_000_000, "SYB": 120_000_000, "Sekawan": 300_000_000, "Avione": 150_000_000, "Honor": 220_000_000, "Vlagio": 50_000_000, "Ren & R & L": 20_000_000, "Mad For Make Up": 40_000_000, "Satto": 525_000_000, "Mykonos": 20_000_000, "The Face": 600_000_000, "Yu Chun Mei": 400_000_000, "Milano": 50_000_000, "Remar": 50_000_000, "Walnutt": 30_000_000, "Elizabeth Rose": 80_000_000, "Sombong": 50_000_000},
    "LISMAN": { "Javinci": 1_300_000_000, "Careso": 400_000_000, "Newlab": 120_000_000, "Gloow & Be": 170_000_000, "Dorskin": 30_000_000, "Whitelab": 100_000_000, "Bonavie": 50_000_000, "Goute": 70_000_000, "Mlen": 225_000_000, "Artist Inc": 150_000_000, "Maskit": 50_000_000, "Birth Beyond": 120_000_000, "Everpure": 0},
    "AKBAR": { "Sociolla": 600_000_000, "Thai": 400_000_000, "Inesia": 80_000_000, "Y2000": 250_000_000, "Diosys": 600_000_000, "Masami": 50_000_000, "Cassandra": 20_000_000, "Clinelle": 80_000_000,"Beautica": 100_000_000, "Claresta": 350_000_000, "Rose All Day": 30_000_000, "OtwooO": 180_000_000}
}

ESTIMASI_TARGET_BULANAN = {
    "Bonavie": 5_000_000, "Whitelab": 5_000_000, "Dorskin": 3_000_000, "Gloow & Be": 10_000_000,
    "Javinci": 90_000_000, "Careso": 30_000_000, "Artist Inc": 8_000_000, "Newlab": 7_000_000,
    "Mlen": 8_000_000, "COSLINE": 1_000_000, "Thai": 50_000_000, "Diosys": 55_000_000,
    "Sociolla": 40_000_000, "Skin1004": 30_000_000, "Beautica": 10_000_000, "Claresta": 20_000_000,
    "Masami": 10_000_000, "Cassandra": 4_000_000, "Clinelle": 15_000_000, "Honor": 10_000_000,
    "The Face": 80_000_000, "Elizabeth Rose": 3_000_000, "Mad For Make Up": 4_000_000,
    "Satto": 20_000_000, "Somethinc": 80_000_000, "SYB": 10_000_000
}

INDIVIDUAL_TARGETS = {
    "WIRA": { "Somethinc": 660_000_000, "SYB": 75_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000, "Elizabeth Rose": 30_000_000, "Walnutt": 20_000_000 },
    "HAMZAH": { "Somethinc": 540_000_000, "SYB": 75_000_000, "Sekawan": 60_000_000, "Avione": 60_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000 },
    "ROZY": { "Sekawan": 100_000_000, "Avione": 100_000_000 },
    "RAPI": { "Sekawan": 90_000_000, "Avione": 90_000_000 },
    "SRI RAMADHANI": { "Sekawan": 50_000_000, "Avione": 50_000_000 },
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
    "Thai": ["THAI", "JINSU"], "Inesia": ["INESIA"], "Honor": ["HONOR"], "Vlagio": ["VLAGIO"],
    "Sociolla": ["SOCIOLLA"], "Skin1004": ["SKIN1004", "SKIN 1004"], "Oimio": ["OIMIO"],
    "Clinelle": ["CLINELLE", "CLIN"], "Ren & R & L": ["REN", "R & L", "R&L"], "Sekawan": ["SEKAWAN", "AINIE"],
    "Mad For Make Up": ["MAD FOR", "MAKE UP", "MAJU", "MADFORMAKEUP"], "Avione": ["AVIONE"],
    "SYB": ["SYB"], "Satto": ["SATTO"], "Liora": ["LIORA"], "Mykonos": ["MYKONOS"],
    "Somethinc": ["SOMETHINC"], "Gloow & Be": ["GLOOW", "GLOOWBI", "GLOW", "GLOWBE"],
    "Artist Inc": ["ARTIST", "ARTIS"], "Bonavie": ["BONAVIE"], "Whitelab": ["WHITELAB"],
    "Goute": ["GOUTE"], "Dorskin": ["DORSKIN"], "Javinci": ["JAVINCI"], "Madame G": ["MADAM", "MADAME"],
    "Careso": ["CARESO"], "Newlab": ["NEWLAB"], "Mlen": ["MLEN"], "Walnutt": ["WALNUT", "WALNUTT"],
    "Elizabeth Rose": ["ELIZABETH"], "OtwooO": ["OTWOOO", "O.TWO.O", "O TWO O"],
    "Saviosa": ["SAVIOSA"], "The Face": ["THE FACE", "THEFACE"], "Yu Chun Mei": ["YU CHUN MEI", "YCM"],
    "Milano": ["MILANO"], "Remar": ["REMAR"], "Beautica": ["BEAUTICA"], "Maskit": ["MASKIT"],
    "Claresta": ["CLARESTA"], "Birth Beyond": ["BIRTH"], "Rose All Day": ["ROSE ALL DAY"],
    "Everpure": ["EVERPURE"], "COSLINE": ["COSLINE"], "NAMA": ["NAMA"], "Rosanna": ["ROSANNA"], "Summer": ["SUMMER"], "Sombong":["SOMBONG"]
}

SALES_MAPPING = {
    "WIRA VG": "WIRA", "WIRA - VG": "WIRA", "WIRA VLAGIO": "WIRA", "WIRA HONOR": "WIRA", "WIRA - HONOR": "WIRA", "WIRA HR": "WIRA", "WIRA SYB": "WIRA", "WIRA - SYB": "WIRA", "WIRA SOMETHINC": "WIRA", "PMT-WIRA": "WIRA", "WIRA ELIZABETH": "WIRA", "WIRA WALNUTT": "WIRA", "WIRA ELZ": "WIRA", "WIRA SBG": "WIRA", 
    "HAMZAH VG": "HAMZAH", "HAMZAH - VG": "HAMZAH", "HAMZAH HONOR": "HAMZAH", "HAMZAH - HONOR": "HAMZAH", "HAMZAH SYB": "HAMZAH", "HAMZAH AV": "HAMZAH", "HAMZAH AINIE": "HAMZAH", "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH", "HAMZA AV": "HAMZAH", "HAMZA SBG": "HAMZAH",
    "FERI VG": "FERI", "FERI - VG": "FERI", "FERI HONOR": "FERI", "FERI - HONOR": "FERI", "FERI THAI": "FERI", "FERI - INESIA": "FERI",
    "YOGI TF": "YOGI", "YOGI THE FACE": "YOGI", "YOGI YCM": "YOGI", "YOGI MILANO": "YOGI", "MILANO - YOGI": "YOGI", "YOGI REMAR": "YOGI",
    "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI", "GANI TF": "GANI", "GANI - YCM": "GANI", "GANI - MILANO": "GANI", "GANI - HONOR": "GANI", "GANI - VG": "GANI", "GANI - TH": "GANI", "GANI INESIA": "GANI", "GANI - KSM": "GANI", "SSL - GANI": "GANI", "GANI ELIZABETH": "GANI", "GANI WALNUTT": "GANI",
    "MITHA MASKIT": "MITHA", "MITHA RAD": "MITHA", "MITHA CLA": "MITHA", "MITHA OT": "MITHA", "MAS - MITHA": "MITHA", "SSL BABY - MITHA ": "MITHA", "SAVIOSA - MITHA": "MITHA", "MITHA ": "MITHA",
    "LYDIA KITO": "LYDIA", "LYDIA K": "LYDIA", "LYDIA BB": "LYDIA", "LYDIA - KITO": "LYDIA",
    "RAPI": "RAPI", "RAPI AV": "RAPI", "NOVI DAN RAFFI": "NOVI", "NOVI & RAFFI": "NOVI", "RAPI AV":"RAPI", "RAPI SBG": "RAPI", 
    "ROZY AINIE": "ROZY", "ROZY AV": "ROZY",
    "SRI RAMADHANI": "SRI RAMADHANI", "SRI RAMADHANI": "SRI RAMADHANI", "SRI RAMADHANI SEKAWAN": "SRI RAMADHANI", "SRI RAMADHANI SBG": "SRI RAMADHANI",
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG", "MADONG MYK": "MADONG",
    "RISKA AV": "RISKA", "RISKA BN": "RISKA", "RISKA CRS": "RISKA", "RISKA E-WL": "RISKA", "RISKA JV": "RISKA", "RISKA REN": "RISKA", "RISKA R&L": "RISKA", "RISKA SMT": "RISKA", "RISKA ST": "RISKA", "RISKA SYB": "RISKA", "RISKA - MILANO": "RISKA", "RISKA TF": "RISKA", "RISKA - YCM": "RISKA", "RISKA HONOR": "RISKA", "RISKA - VG": "RISKA", "RISKA TH": "RISKA", "RISKA - INESIA": "RISKA", "SSL - RISKA": "RISKA", "SKIN - RIZKA": "RISKA", 
    "ADE CLA": "ADE", "ADE CRS": "ADE", "GLOOW - ADE": "ADE", "ADE JAVINCI": "ADE", "ADE JV": "ADE", "ADE SVD": "ADE", "ADE RAM PUTRA M.GIE": "ADE", "ADE - MLEN1": "ADE", "ADE NEWLAB": "ADE", "DORS - ADE": "ADE",
    "FANDI - BONAVIE": "FANDI", "DORS- FANDI": "FANDI", "FANDY CRS": "FANDI", "FANDI AFDILLAH": "FANDI", "FANDY WL": "FANDI", "GLOOW - FANDY": "FANDI", "FANDI - GOUTE": "FANDI", "FANDI MG": "FANDI", "FANDI - NEWLAB": "FANDI", "FANDY - YCM": "FANDI", "FANDY YLA": "FANDI", "FANDI JV": "FANDI", "FANDI MLEN": "FANDI",
    "NAUFAL - JAVINCI": "NAUFAL", "NAUFAL JV": "NAUFAL", "NAUFAL SVD": "NAUFAL", "RIZKI JV": "RIZKI", "RIZKI SVD": "RIZKI", 
    "SAHRUL JAVINCI": "SYAHRUL", "SAHRUL TF": "SYAHRUL", "SAHRUL JV": "SYAHRUL", "GLOOW - SAHRUL": "SYAHRUL",
    "SANTI BONAVIE": "SANTI", "SANTI WHITELAB": "SANTI", "SANTI GOUTE": "SANTI", "DWI CRS": "DWI", "DWI NLAB": "DWI", 
    "ASWIN ARTIS": "ASWIN", "ASWIN AI": "ASWIN", "ASWIN Inc": "ASWIN", "ASWIN INC": "ASWIN", "ASWIN - ARTIST INC": "ASWIN",
    "BASTIAN CASANDRA": "BASTIAN", "SSL- BASTIAN": "BASTIAN", "SKIN - BASTIAN": "BASTIAN", "BASTIAN - HONOR": "BASTIAN", "BASTIAN - VG": "BASTIAN", "BASTIAN TH": "BASTIAN", "BASTIAN YL": "BASTIAN", "BASTIAN YL-DIO CAT": "BASTIAN", "BASTIAN SHMP": "BASTIAN", "BASTIAN-DIO 45": "BASTIAN",
    "SSL - DEVI": "DEVI", "SKIN - DEVI": "DEVI", "DEVI Y- DIOSYS CAT": "DEVI", "DEVI YL": "DEVI", "DEVI SHMP": "DEVI", "DEVI-DIO 45": "DEVI", "DEVI YLA": "DEVI",
    "SSL- BAYU": "BAYU", "SKIN - BAYU": "BAYU", "BAYU-DIO 45": "BAYU", "BAYU YL-DIO CAT": "BAYU", "BAYU SHMP": "BAYU", "BAYU YL": "BAYU", 
    "HABIBI - FZ": "HABIBI", "HABIBI SYB": "HABIBI", "HABIBI TH": "HABIBI", "GLOOW - LISMAN": "LISMAN", "LISMAN - NEWLAB": "LISMAN", 
    "WILLIAM BTC": "WILLIAM", "WILLI - ROS": "WILLIAM", "WILLI - WAL": "WILLIAM", "RINI JV": "RINI", "RINI SYB": "RINI", 
    "FAUZIAH CLA": "FAUZIAH", "FAUZIAH ST": "FAUZIAH", "MARIANA CLIN": "MARIANA", "JAYA - MARIANA": "MARIANA", "NOVITA":"NOVITA"
}

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
    try: secret_salt = st.secrets["APP_SALT"]
    except: secret_salt = "RAHASIA_PERUSAHAAN_2025" 
    now_wib = get_current_time_wib()
    time_key = now_wib.strftime("%Y-%m-%d-%p")
    raw_string = f"{time_key}-{secret_salt}"
    hash_object = hashlib.sha256(raw_string.encode())
    hex_dig = hash_object.hexdigest()
    numeric_filter = filter(str.isdigit, hex_dig)
    numeric_string = "".join(numeric_filter)
    return numeric_string[:4].ljust(4, '0')

def render_custom_progress(title, current, target):
    if target == 0: target = 1
    pct = (current / target) * 100
    visual_pct = min(pct, 100)
    
    if pct < 50: bar_color = "linear-gradient(90deg, #ff4b4b, #e74c3c)" 
    elif 50 <= pct < 85: bar_color = "linear-gradient(90deg, #f1c40f, #f39c12)" 
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

# =========================================================================
# CACHE & DATA LOADER (SUPER CACHE: 12 JAM)
# =========================================================================
@st.cache_data(ttl=43200) 
def load_data_from_url():
    urls = [
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vSaGwT-qw0iz6kKhkwep4R5b-TWlegy8rHdBU3HcY_veP8KEsiLmKpCemC-D1VA2STstlCjA2VLUM-Q/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vT6KbuunLLoGQRSanRK_A8e5jgXcJ-FCZCEb8dr611HdJQi40dFr_HNMItnodJEwD7dKk7woC7Ud-DG/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vQyEgQMxR75QW7HYKbJov4WtNuZmghPAhMHeH-cI5Wem_NwIMuC95sqa8QzXh2p1DX-HxQSJGptz_xy/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBTn4hKKl-e9BFITUW2dYBsKfMbTBc-zrdn3qweQxzL_tiTr3FMi4cGE-17IrixYwg9T-4YugLcQdq/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vTVyv41klRlykXzW5wYo01y5a4HtplUEXVMpt05DzEO-ijxJ9T2Xk5Yiruv4uZW--QM0NIU3fnww_xX/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vT_5jmQOnxI-9BwKolYKVhtdmlgQg4QNJ4SfqcB8evLvHFCdD-s6Gs73gW4uJoKJtapngxwJ4WVMXPs/pub?output=csv"  
    ]
    
    def fetch_url(url):
        if url.strip() != "" and url.startswith("http") and "LINK_SHEET" not in url:
            try:
                url_with_ts = f"{url}&t={int(time.time())}"
                return pd.read_csv(url_with_ts, dtype=str, engine='pyarrow')
            except Exception as e:
                return None
        return None

    all_dfs = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(fetch_url, urls)
        for res in results:
            if res is not None and not res.empty:
                all_dfs.append(res)
                
    if not all_dfs: return None
        
    df = pd.concat(all_dfs, ignore_index=True)
    df.columns = df.columns.str.strip()
    
    for alt_col in ['Sales', 'Salesman', 'Nama Sales']:
        if alt_col in df.columns:
            if 'Penjualan' in df.columns:
                df['Penjualan'] = df['Penjualan'].fillna(df[alt_col])
            else:
                df['Penjualan'] = df[alt_col]
                
    for col_name in ['Kode Customer', 'Kode Costumer', 'Kode Outlet']:
        if col_name in df.columns:
            if 'Kode_Global' not in df.columns:
                df['Kode_Global'] = df[col_name]
            else:
                df['Kode_Global'] = df['Kode_Global'].fillna(df[col_name])
    if 'Kode_Global' not in df.columns: df['Kode_Global'] = "-"

    faktur_col = None
    for col in df.columns:
        if 'faktur' in col.lower() or 'bukti' in col.lower() or 'invoice' in col.lower():
            faktur_col = col; break
    if faktur_col: df = df.rename(columns={faktur_col: 'No Faktur'})
    
    if 'Nama Barang' in df.columns:
        df = df[~df['Nama Barang'].astype(str).str.match(r'^(Total|Jumlah)', case=False, na=False)]
        df['Nama Barang'] = df['Nama Barang'].fillna("-")

    if 'Nama Outlet' in df.columns:
        df = df[~df['Nama Outlet'].astype(str).str.match(r'^(Total|Jumlah|Subtotal|Grand|Rekap)', case=False, na=False)]
        df = df[df['Nama Outlet'].astype(str).str.strip() != ''] 
        df = df[df['Nama Outlet'].astype(str).str.lower() != 'nan']

    def clean_rupiah(x):
        x = str(x).upper().replace('RP', '').strip()
        x = re.sub(r'\s+', '', x) 
        x = re.sub(r'[,.]\d{2}$', '', x) 
        x = x.replace(',', '').replace('.', '') 
        x = re.sub(r'[^\d-]', '', x) 
        try: return float(x)
        except: return 0.0

    if 'Jumlah' in df.columns:
        df['Jumlah'] = df['Jumlah'].apply(clean_rupiah)
    else:
        df['Jumlah'] = 0.0

    if 'Tanggal' in df.columns:
        tanggal_raw = df['Tanggal'].astype(str).str.strip()
        d1 = pd.to_datetime(tanggal_raw, format='%d/%m/%Y', errors='coerce')
        d2 = pd.to_datetime(tanggal_raw, format='%d-%m-%Y', errors='coerce')
        d3 = pd.to_datetime(tanggal_raw, dayfirst=True, errors='coerce', format='mixed')
        df['Tanggal'] = d1.fillna(d2).fillna(d3).fillna(pd.to_datetime('2000-01-01'))
    else:
        df['Tanggal'] = pd.to_datetime('2000-01-01')

    if 'Penjualan' in df.columns:
        df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(SALES_MAPPING)
        valid_sales_names = list(INDIVIDUAL_TARGETS.keys())
        valid_sales_names.extend(["MADONG", "LISMAN", "AKBAR"]) 
        df.loc[~df['Penjualan'].isin(valid_sales_names), 'Penjualan'] = 'Non-Sales'
        df_valid = df[df['Penjualan'] != 'Non-Sales']
        outlet_to_sales = df_valid.groupby('Nama Outlet')['Penjualan'].first().to_dict()
        mask_non = df['Penjualan'] == 'Non-Sales'
        df.loc[mask_non, 'Penjualan'] = df.loc[mask_non, 'Nama Outlet'].map(outlet_to_sales).fillna('Non-Sales')
        df['Penjualan'] = df['Penjualan'].astype('category')
    else:
        df['Penjualan'] = 'Non-Sales'

    def normalize_brand(raw_brand):
        raw_upper = str(raw_brand).upper()
        for target_brand, keywords in BRAND_ALIASES.items(): 
            for keyword in keywords:
                if keyword in raw_upper: return target_brand
        return raw_brand
        
    if 'Merk' in df.columns:
        df['Merk'] = df['Merk'].fillna("-").apply(normalize_brand).astype('category')
    else:
        df['Merk'] = "-"
    
    cols_to_convert = ['Kota', 'Nama Outlet', 'No Faktur', 'Kode_Global']
    for col in cols_to_convert:
        if col in df.columns: 
            df[col] = df[col].fillna("-").astype(str).str.strip()
            df[col] = df[col].replace({'nan': '-', 'NaN': '-', '0.0': '-', 'None': '-', '': '-'})
    
    if 'Kota' in df.columns:
        df['Provinsi'] = df['Kota'].apply(map_city_to_province)
    else:
        df['Provinsi'] = "-"
    
    try: df.to_parquet("master_database_penjualan.parquet", index=False)
    except: pass 
            
    return df

def load_data(fast_mode=False):
    if fast_mode and os.path.exists("master_database_penjualan.parquet"):
        try:
            return pd.read_parquet("master_database_penjualan.parquet")
        except Exception:
            pass
    return load_data_from_url()

# =========================================================================
# PIVOT FAST ENGINE (DIHAPUS CACHE-NYA AGAR TIDAK STUCK)
# =========================================================================
def generate_pivot_fast(df_pivot_source, selected_merk_excel, selected_tahun_excel_tuple, group_cols_tuple, brand_prefixes_dict):
    group_cols = list(group_cols_tuple)
    
    invalid_codes = ['-', '', 'NAN', 'NONE', '0.0']
    nama_col = 'Nama Outlet' if 'Nama Outlet' in df_pivot_source.columns else 'Nama Customer'
    
    df_pivot_source['ID_Patokan'] = np.where(
        df_pivot_source['Kode_Global'].astype(str).str.strip().str.upper().isin(invalid_codes),
        df_pivot_source[nama_col].astype(str).str.strip(),
        df_pivot_source['Kode_Global'].astype(str).str.strip()
    )

    if not df_pivot_source.empty:
        if selected_merk_excel != "SEMUA":
            prefixes = brand_prefixes_dict.get(selected_merk_excel, [selected_merk_excel[:3].upper()])
            prefix_tuple = tuple(prefixes)
            
            mask_history = df_pivot_source['Merk'] == selected_merk_excel
            kd_col = 'Kode_Global'
            mask_prefix = df_pivot_source[kd_col].astype(str).str.strip().str.upper().apply(lambda x: any(x.startswith(p) for p in prefix_tuple))
            final_mask = mask_history | mask_prefix
        else:
            final_mask = pd.Series(True, index=df_pivot_source.index)
            
        df_filtered = df_pivot_source[final_mask].copy()
        
        if df_filtered.empty: return pd.DataFrame()

        df_filtered = df_filtered.sort_values('Tanggal', ascending=False)
        base_customers = df_filtered.drop_duplicates(subset=['ID_Patokan'], keep='first')[['ID_Patokan'] + group_cols]
        
        df_excel = df_filtered[df_filtered['Tanggal'].dt.year.isin(selected_tahun_excel_tuple)].copy()
        
        if not df_excel.empty:
            df_excel['Bulan Angka'] = df_excel['Tanggal'].dt.month
            pivot_sales = pd.pivot_table(df_excel, values='Jumlah', index='ID_Patokan', columns='Bulan Angka', aggfunc='sum', fill_value=0).reset_index()
            master_pivot = pd.merge(base_customers, pivot_sales, on='ID_Patokan', how='left').fillna(0)
        else:
            master_pivot = base_customers.copy()
            for i in range(1, 13): master_pivot[i] = 0
            
        master_pivot = master_pivot.drop(columns=['ID_Patokan'])
        return master_pivot
        
    return pd.DataFrame()

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
    pair_df = df.groupby('No Faktur')['Nama Barang'].apply(lambda x: list(combinations(sorted(x.dropna().unique()), 2)) if len(x.dropna().unique()) > 1 else [])
    pairs = [p for sublist in pair_df for p in sublist]
    pair_support = Counter(pairs)
    
    rules = []
    for (A, B), supp_ab in pair_support.items():
        conf_ab = supp_ab / item_support[A]
        conf_ba = supp_ab / item_support[B]
        rules.append({'antecedent': A, 'consequent': B, 'support': supp_ab / total_transactions, 'confidence': conf_ab})
        rules.append({'antecedent': B, 'consequent': A, 'support': supp_ab / total_transactions, 'confidence': conf_ba})
    if not rules: return None
    rules_df = pd.DataFrame(rules).drop_duplicates().sort_values('confidence', ascending=False)
    rules_df = rules_df[rules_df['confidence'] > 0.5]  
    return rules_df

@st.cache_data(ttl=3600, show_spinner=False)
def get_cross_sell_recommendations(df):
    rules_df = compute_association_rules(df)
    if rules_df is None or rules_df.empty: return None
    
    outlet_purchases = df.groupby('Nama Outlet')['Nama Barang'].apply(lambda x: set(x.dropna())).to_dict()
    recommendations = []
    for outlet, purchased in outlet_purchases.items():
        if not purchased: continue
        sales_arr = df[df['Nama Outlet'] == outlet]['Penjualan'].unique()
        sales = sales_arr[0] if len(sales_arr) > 0 else "-"
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

@st.fragment
def render_pivot_fragment(df_scope_all, role):
    list_merk_excel = sorted(df_scope_all['Merk'].dropna().astype(str).unique())
    list_tahun = sorted(df_scope_all['Tanggal'].dt.year.dropna().unique(), reverse=True)
    
    grp_cols = []
    if 'Kode_Global' in df_scope_all.columns: 
        grp_cols.append('Kode_Global'); kd_asal = 'Kode_Global'
    else:
        df_scope_all['Kode_Global'] = "-"; grp_cols.append('Kode_Global'); kd_asal = 'Kode_Global'
        
    # --- Murni Menggunakan Nama Outlet ---
    if 'Nama Outlet' in df_scope_all.columns: 
        grp_cols.append('Nama Outlet')
    else: 
        df_scope_all['Nama Outlet'] = "-"; grp_cols.append('Nama Outlet')
    
    if 'Provinsi' in df_scope_all.columns: grp_cols.append('Provinsi')
    else: df_scope_all['Provinsi'] = "-"; grp_cols.append('Provinsi')
    
    if 'Kota' in df_scope_all.columns: grp_cols.append('Kota')
    else: df_scope_all['Kota'] = "-"; grp_cols.append('Kota')

    with st.form(key='pivot_filter_form'):
        col_piv1, col_piv2 = st.columns(2)
        with col_piv1:
            selected_merk_excel = st.selectbox("🎯 Pilih Merk:", ["SEMUA"] + list_merk_excel)
        with col_piv2:
            selected_tahun_excel = st.multiselect("🗓️ Pilih Tahun:", list_tahun, default=list_tahun)
            
        st.markdown("#### 🔎 Filter Spesifik (Batch Processing)")
        
        list_kode_all = sorted(df_scope_all[kd_asal].astype(str).unique())
        list_nama_all = sorted(df_scope_all['Nama Outlet'].astype(str).unique())
        list_provinsi_all = sorted(df_scope_all['Provinsi'].astype(str).unique())
        list_kota_all = sorted(df_scope_all['Kota'].astype(str).unique())

        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1: filter_kode = st.multiselect("Kode Customer:", list_kode_all, placeholder="Pilih Kode...")
        with col_f2: filter_nama = st.multiselect("Nama Outlet:", list_nama_all, placeholder="Pilih Outlet...")
        with col_f3: filter_provinsi = st.multiselect("Provinsi:", list_provinsi_all, placeholder="Pilih Provinsi...")
        with col_f4: filter_kota = st.multiselect("Kota:", list_kota_all, placeholder="Pilih Kota...")

        maximize_toggle = st.toggle("🗖 Mode Layar Penuh (Tabel Super Lebar)")
        
        submit_button = st.form_submit_button(label='🚀 Terapkan Filter (Super Cepat)', use_container_width=True)

    master_pivot = generate_pivot_fast(df_scope_all, selected_merk_excel, tuple(selected_tahun_excel), tuple(grp_cols), BRAND_PREFIXES)

    if not master_pivot.empty:
        bulan_indo_map = {1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'}
        for i in range(1, 13):
            if i not in master_pivot.columns: master_pivot[i] = 0
        
        cols_to_keep = []
        for c in grp_cols:
            if c in master_pivot.columns: cols_to_keep.append(c)
        cols_to_keep.extend(list(range(1, 13)))
        
        master_pivot = master_pivot[cols_to_keep]
        
        new_cols = []
        for c in cols_to_keep:
            if isinstance(c, int): new_cols.append(bulan_indo_map[c])
            else: new_cols.append(c)
        master_pivot.columns = new_cols
        
        master_pivot['Total Penjualan'] = master_pivot[list(bulan_indo_map.values())].sum(axis=1)
        
        ren_dict = {'Kode_Global': 'Kode Customer'}
        master_pivot = master_pivot.rename(columns=ren_dict)
        
        if 'Kode Customer' not in master_pivot.columns: master_pivot['Kode Customer'] = "-"
        if 'Nama Outlet' not in master_pivot.columns: master_pivot['Nama Outlet'] = "-"
        if 'Provinsi' not in master_pivot.columns: master_pivot['Provinsi'] = "-"
        if 'Kota' not in master_pivot.columns: master_pivot['Kota'] = "-"

        df_filtered = master_pivot.copy()
        if filter_kode: df_filtered = df_filtered[df_filtered['Kode Customer'].astype(str).isin(filter_kode)]
        if filter_nama: df_filtered = df_filtered[df_filtered['Nama Outlet'].astype(str).isin(filter_nama)]
        if filter_provinsi: df_filtered = df_filtered[df_filtered['Provinsi'].astype(str).isin(filter_provinsi)]
        if filter_kota: df_filtered = df_filtered[df_filtered['Kota'].astype(str).isin(filter_kota)]

        st.caption(f"Menampilkan {len(df_filtered)} data customer.")

        if maximize_toggle:
            st.markdown("""
            <style>
                header {display: none !important;}
                [data-testid="stSidebar"] {display: none !important;}
                .block-container {
                    max-width: 100% !important;
                    padding-top: 1rem !important;
                    padding-right: 1rem !important;
                    padding-left: 1rem !important;
                    padding-bottom: 1rem !important;
                }
            </style>
            """, unsafe_allow_html=True)
            st.info("ℹ️ Mode Layar Penuh aktif. Hilangkan centang pada toggle 'Mode Layar Penuh' di atas untuk kembali.")

        if not df_filtered.empty:

            bulan_indo_list = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
            num_cols = bulan_indo_list + ['Total Penjualan']
            
            # --- 1. REORDER KOLOM (Kode Customer lalu Nama Outlet) ---
            cols_reordered = ['Kode Customer', 'Nama Outlet', 'Provinsi', 'Kota'] + num_cols
            df_display = df_filtered[cols_reordered].copy()
            df_display = df_display.loc[:, ~df_display.columns.duplicated()]
            
            # --- 2. PENYESUAIAN GRAND TOTAL (PINNED BOTTOM ROW - NO MERGE) ---
            total_dict = {col: "" for col in df_display.columns}
            
            # Posisi Teks Grand Total HANYA di Kode Customer (Kolom 1)
            total_dict['Kode Customer'] = "GRAND TOTAL" 
                
            for col in num_cols:
                if col in df_display.columns:
                    # Enforce Python float to avoid Numpy JSON serialization crash
                    total_dict[col] = float(df_display[col].sum())
                    # Explicitly cast column to float to avoid PyArrow mixed-type crash
                    df_display[col] = df_display[col].astype(float)
            
            df_display.columns.name = None # Remove hidden index name
            
            df_display_export = pd.concat([df_display, pd.DataFrame([total_dict])], ignore_index=True)
            
            # ================= AG-GRID PIVOT TABLE RENDERER (SMART FILTER) =================
            if AGGRID_AVAILABLE:
                gb = GridOptionsBuilder.from_dataframe(df_display)
                
                currency_formatter = JsCode("""
                function(params) {
                    if (params.value === null || params.value === undefined || params.value === "") return '-';
                    var val = Number(params.value);
                    if (isNaN(val)) return params.value; 
                    return 'Rp ' + val.toLocaleString('id-ID');
                }
                """)
                
                for col in df_display.columns:
                    if col in num_cols:
                        gb.configure_column(col, type=["numericColumn"], headerClass="right-aligned-header", filter='agNumberColumnFilter', floatingFilter=True, valueFormatter=currency_formatter)
                    elif col in ['Kode Customer', 'Nama Outlet']:
                        # KUNCI KEDUA KOLOM KE KIRI
                        gb.configure_column(col, pinned='left', filter='agSetColumnFilter', floatingFilter=True)
                    else:
                        # PROVINSI DAN KOTA TIDAK DIKUNCI
                        gb.configure_column(col, filter='agSetColumnFilter', floatingFilter=True)
                
                gb.configure_default_column(resizable=True, sortable=True)
                
                # --- KONFIGURASI ROW HEIGHT (DINAMIS UNTUK GRAND TOTAL) ---
                getRowHeight = JsCode("""
                function(params) {
                    if (params.node.rowPinned === 'bottom') {
                        return 40; // Tinggi Baris Grand Total (Lebih Besar)
                    }
                    return 35;     // Tinggi Baris Standar
                }
                """)
                
                gb.configure_grid_options(
                    getRowHeight=getRowHeight,
                    headerHeight=40, 
                    floatingFiltersHeight=40,
                    pinnedBottomRowData=[total_dict]
                )
                
                # Warnai SELURUH baris Grand Total dengan Kuning Stabilo
                getRowStyle = JsCode("""
                function(params) {
                    if (params.node.rowPinned === 'bottom') {
                        return { 'background-color': '#FFFF00 !important', 'font-weight': 'bold !important', 'color': 'black !important', 'border-top': '3px solid #333 !important' };
                    }
                    return null;
                }
                """)
                gb.configure_grid_options(getRowStyle=getRowStyle)
                
                gridOptions = gb.build()
                
                # --- CUSTOM CSS: BOLD YELLOW PINNED ROW ---
                custom_css = {
                    ".ag-header-cell-label": {"color": "white !important", "font-weight": "bold !important"},
                    ".ag-header-cell": {"background-color": "#2980b9 !important", "border-right": "1px solid #555555 !important"},
                    ".ag-header": {"background-color": "#2980b9 !important", "border-bottom": "1px solid #555555 !important"},
                    ".ag-cell": {"color": "black !important", "background-color": "white !important", "border-right": "1px solid #555555 !important", "border-bottom": "1px solid #555555 !important", "display": "flex", "align-items": "center"},
                    ".ag-row-hover .ag-cell": {"background-color": "#e3f2fd !important"},
                    ".ag-root-wrapper": {"border": "1px solid #555555 !important"},
                    ".ag-floating-filter-input input": {"background-color": "white !important", "color": "black !important", "border-radius": "3px !important", "padding": "2px 5px !important", "border": "1px solid #ccc !important"},
                    ".right-aligned-header .ag-header-cell-label": {"justify-content": "flex-end !important"},
                    
                    # Target KEDUA container (pinned left & scrolling body) agar seutuhnya kuning stabilo
                    ".ag-floating-bottom-container .ag-row, .ag-pinned-left-floating-bottom .ag-row": {
                        "border-top": "3px solid #333 !important"
                    },
                    ".ag-floating-bottom-container .ag-cell, .ag-pinned-left-floating-bottom .ag-cell": {
                        "background-color": "#FFFF00 !important", 
                        "color": "black !important", 
                        "font-weight": "bold !important"
                    }
                }
                
                AgGrid(df_display, gridOptions=gridOptions, allow_unsafe_jscode=True, theme='balham', height=600, fit_columns_on_grid_load=False, custom_css=custom_css)
            else:
                st.error("Library st_aggrid belum terpasang.")
            
        else:
            st.info("Data Kosong setelah difilter.")
            
        # ================= KEMBALIKAN TOMBOL DOWNLOAD EXCEL (TANPA MERGE) =================
        user_role_lower = role.lower()
        if user_role_lower in ['direktur', 'manager', 'supervisor']:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                if 'df_display_export' in locals() and not df_display_export.empty:
                    df_display_export.to_excel(writer, index=False, sheet_name='Master Data')
                
                workbook = writer.book
                worksheet = writer.sheets['Master Data']
                
                user_identity = f"{st.session_state.get('sales_name', 'Unknown')} ({st.session_state.get('role', 'Unknown').upper()})"
                time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                watermark_text = f"CONFIDENTIAL DOCUMENT | TRACKED USER: {user_identity} | DOWNLOADED: {time_stamp} | DO NOT DISTRIBUTE"
                
                worksheet.set_header(f'&C&10{watermark_text}')
                worksheet.set_footer(f'&RPage &P of &N')
                
                format1 = workbook.add_format({'num_format': '#,##0'})
                worksheet.set_column('E:Q', None, format1) 
                
                if 'df_display_export' in locals() and not df_display_export.empty:
                    last_row_idx = len(df_display_export) 
                    
                    # Format Kuning untuk Keseluruhan Baris Terakhir (Tidak di-merge)
                    bold_yellow_format = workbook.add_format({
                        'bold': True,
                        'bg_color': '#FFFF00',
                        'border': 1,
                        'num_format': '#,##0',
                        'font_color': 'black'
                    })
                    
                    # Terapkan format tinggi baris & warna ke baris akhir
                    worksheet.set_row(last_row_idx, 30, bold_yellow_format)
            
            st.download_button(
                label="📥 Download Laporan Excel (XLSX) - DRM Protected",
                data=output.getvalue(),
                file_name=f"Laporan_Master_{selected_merk_excel}_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("Data Kosong.")

        with tab_sku:
            st.markdown("### 🛒 Detail SKU per Toko")
            df_sku_base = df_scope_all.copy()
            
            list_merk_sku = sorted(df_sku_base['Merk'].dropna().astype(str).unique())
            list_merk_sku = [m for m in list_merk_sku if m != "-"]
            list_tahun_sku = sorted(df_sku_base['Tanggal'].dt.year.dropna().unique(), reverse=True)
            kd_asal = 'Kode_Global' if 'Kode_Global' in df_sku_base.columns else 'Kode Customer'
            
            # --- CASCADING DROPDOWN (Pilih Merk di Luar Form agar bisa auto-update) ---
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                selected_merk_sku = st.selectbox("🎯 Pilih Merk:", ["SEMUA"] + list_merk_sku, key='merk_sku')
            with col_s2:
                selected_tahun_sku = st.multiselect("🗓️ Pilih Tahun:", list_tahun_sku, default=list_tahun_sku, key='tahun_sku')
                
            # Pra-Filter df_sku_base untuk mendapatkan daftar opsi dropdown yang dinamis (Cascading)
            df_sku_for_options = df_sku_base.copy()
            if selected_merk_sku != "SEMUA":
                prefixes = BRAND_PREFIXES.get(selected_merk_sku, [selected_merk_sku[:3].upper()])
                prefix_tuple = tuple(prefixes)
                mask_history = df_sku_for_options['Merk'] == selected_merk_sku
                mask_prefix = df_sku_for_options[kd_asal].astype(str).str.strip().str.upper().apply(lambda x: any(x.startswith(p) for p in prefix_tuple))
                df_sku_for_options = df_sku_for_options[mask_history | mask_prefix]
                
            list_sku_cascading = sorted(df_sku_for_options['Nama Barang'].dropna().astype(str).unique())
            list_kode_all_sku = sorted(df_sku_for_options[kd_asal].astype(str).unique())
            list_nama_all_sku = sorted(df_sku_for_options['Nama Outlet'].astype(str).unique())
            list_provinsi_all_sku = sorted(df_sku_for_options['Provinsi'].astype(str).unique())
            list_kota_all_sku = sorted(df_sku_for_options['Kota'].astype(str).unique())

            with st.form(key='sku_filter_form'):
                st.markdown("#### 🔎 Filter Spesifik (Batch Processing)")
                
                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                with col_f1: filter_kode_sku = st.multiselect("Kode Customer:", list_kode_all_sku, placeholder="Pilih Kode...")
                with col_f2: filter_nama_sku = st.multiselect("Nama Outlet:", list_nama_all_sku, placeholder="Pilih Outlet...")
                with col_f3: filter_provinsi_sku = st.multiselect("Provinsi:", list_provinsi_all_sku, placeholder="Pilih Provinsi...")
                with col_f4: filter_kota_sku = st.multiselect("Kota:", list_kota_all_sku, placeholder="Pilih Kota...")
                
                filter_sku_spesifik = st.multiselect("📦 Nama Barang (SKU):", list_sku_cascading, placeholder="Pilih SKU spesifik (Kosongkan untuk melihat semua)...")

                maximize_toggle_sku = st.toggle("🗖 Mode Layar Penuh (Tabel Super Lebar)", key='fs_sku')
                submit_button_sku = st.form_submit_button(label='🚀 Terapkan Filter (Super Cepat)', use_container_width=True)

            # Filtering Execution
            df_sku_filtered = df_sku_for_options.copy() 

            if selected_tahun_sku:
                df_sku_filtered = df_sku_filtered[df_sku_filtered['Tanggal'].dt.year.isin(selected_tahun_sku)]

            if filter_kode_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered[kd_asal].astype(str).isin(filter_kode_sku)]
            if filter_nama_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered['Nama Outlet'].astype(str).isin(filter_nama_sku)]
            if filter_provinsi_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered['Provinsi'].astype(str).isin(filter_provinsi_sku)]
            if filter_kota_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered['Kota'].astype(str).isin(filter_kota_sku)]
            if filter_sku_spesifik: df_sku_filtered = df_sku_filtered[df_sku_filtered['Nama Barang'].astype(str).isin(filter_sku_spesifik)]

            if not filter_nama_sku and not filter_sku_spesifik:
                st.info("👈 Silakan pilih minimal 1 'Nama Outlet' ATAU 'Nama Barang (SKU)' di kotak pencarian atas lalu klik 'Terapkan Filter' untuk melihat detail transaksi.")
            else:
                st.caption(f"Menampilkan transaksi dari {df_sku_filtered['Nama Outlet'].nunique()} toko.")

                if maximize_toggle_sku:
                    st.markdown("""
                    <style>
                        header {display: none !important;}
                        [data-testid="stSidebar"] {display: none !important;}
                        .block-container {
                            max-width: 100% !important;
                            padding-top: 1rem !important;
                            padding-right: 1rem !important;
                            padding-left: 1rem !important;
                            padding-bottom: 1rem !important;
                        }
                    </style>
                    """, unsafe_allow_html=True)
                    st.info("ℹ️ Mode Layar Penuh aktif. Hilangkan centang pada toggle 'Mode Layar Penuh' di atas untuk kembali.")

                if not df_sku_filtered.empty:
                    df_sku_filtered['Bulan Angka'] = df_sku_filtered['Tanggal'].dt.month
                    
                    if filter_sku_spesifik:
                        index_col = 'Nama Outlet'
                        display_col = 'Nama Toko'
                    else:
                        index_col = 'Nama Barang'
                        display_col = 'Nama Barang'
                        
                    pivot_sku = pd.pivot_table(df_sku_filtered, values='Jumlah', index=index_col, columns='Bulan Angka', aggfunc='sum', fill_value=0).reset_index()
                    pivot_sku = pivot_sku.rename(columns={index_col: display_col})
                    
                    bulan_indo_map = {1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'}
                    for i in range(1, 13):
                        if i not in pivot_sku.columns: pivot_sku[i] = 0.0 # Use 0.0 float instead of 0 int
                        
                    cols_sku = [display_col] + list(range(1, 13))
                    pivot_sku = pivot_sku[cols_sku]
                    pivot_sku.columns = [display_col] + [bulan_indo_map[i] for i in range(1, 13)]
                    
                    pivot_sku['Total Penjualan'] = pivot_sku[list(bulan_indo_map.values())].sum(axis=1)
                    
                    # --- Grand Total Row (PINNED BOTTOM ROW) ---
                    total_dict_sku = {col: "" for col in pivot_sku.columns}
                    total_dict_sku[display_col] = "GRAND TOTAL"
                    for col in [bulan_indo_map[i] for i in range(1, 13)] + ['Total Penjualan']:
                        # Enforce native float
                        total_dict_sku[col] = float(pivot_sku[col].sum())
                    
                    df_display_sku = pivot_sku.copy()
                    df_display_sku = df_display_sku.loc[:, ~df_display_sku.columns.duplicated()]
                    
                    # Cast all numeric columns to float explicitly
                    for col in [bulan_indo_map[i] for i in range(1, 13)] + ['Total Penjualan']:
                        df_display_sku[col] = df_display_sku[col].astype(float)
                        
                    df_display_sku.columns.name = None # Remove hidden index name
                    
                    df_display_sku_export = pd.concat([df_display_sku, pd.DataFrame([total_dict_sku])], ignore_index=True)
                    
                    # ================= AG-GRID SKU TABLE RENDERER (SMART FILTER) =================
                    if AGGRID_AVAILABLE:
                        gb_sku = GridOptionsBuilder.from_dataframe(df_display_sku)
                        
                        currency_formatter = JsCode("""
                        function(params) {
                            if (params.value === null || params.value === undefined || params.value === "") return '-';
                            var val = Number(params.value);
                            if (isNaN(val)) return params.value; 
                            return 'Rp ' + val.toLocaleString('id-ID');
                        }
                        """)
                        
                        num_cols_sku = [bulan_indo_map[i] for i in range(1, 13)] + ['Total Penjualan']
                        
                        for col in df_display_sku.columns:
                            if col in num_cols_sku:
                                gb_sku.configure_column(col, type=["numericColumn"], headerClass="right-aligned-header", filter='agNumberColumnFilter', floatingFilter=True, valueFormatter=currency_formatter)
                            elif col == display_col:
                                gb_sku.configure_column(col, filter='agSetColumnFilter', floatingFilter=True, pinned='left')
                            else:
                                gb_sku.configure_column(col, filter='agSetColumnFilter', floatingFilter=True)
                        
                        gb_sku.configure_default_column(resizable=True, sortable=True)
                        
                        # --- KONFIGURASI ROW HEIGHT ---
                        getRowHeightSKU = JsCode("""
                        function(params) {
                            if (params.node.rowPinned === 'bottom') {
                                return 40;
                            }
                            return 35;
                        }
                        """)
                        
                        gb_sku.configure_grid_options(
                            getRowHeight=getRowHeightSKU,
                            headerHeight=40,
                            floatingFiltersHeight=40,
                            pinnedBottomRowData=[total_dict_sku]
                        )
                        
                        gridOptions_sku = gb_sku.build()
                        
                        custom_css_sku = {
                            ".ag-header-cell-label": {"color": "white !important", "font-weight": "bold !important"},
                            ".ag-header-cell": {"background-color": "#2980b9 !important", "border-right": "1px solid #555555 !important"},
                            ".ag-header": {"background-color": "#2980b9 !important", "border-bottom": "1px solid #555555 !important"},
                            ".ag-cell": {"color": "black !important", "background-color": "white !important", "border-right": "1px solid #555555 !important", "border-bottom": "1px solid #555555 !important", "display": "flex", "align-items": "center"},
                            ".ag-row-hover .ag-cell": {"background-color": "#e3f2fd !important"},
                            ".ag-root-wrapper": {"border": "1px solid #555555 !important"},
                            ".ag-floating-filter-input input": {"background-color": "white !important", "color": "black !important", "border-radius": "3px !important", "padding": "2px 5px !important", "border": "1px solid #ccc !important"},
                            ".right-aligned-header .ag-header-cell-label": {"justify-content": "flex-end !important"},
                            
                            # MEMAKSA BARIS PINNED BAWAH MENJADI KUNING & BOLD SEPENUHNYA
                            ".ag-floating-bottom-container .ag-row, .ag-pinned-left-floating-bottom .ag-row": {"border-top": "3px solid #333 !important"},
                            ".ag-floating-bottom-container .ag-cell, .ag-pinned-left-floating-bottom .ag-cell": {
                                "background-color": "#FFFF00 !important", 
                                "color": "black !important", 
                                "font-weight": "bold !important"
                            }
                        }
                        
                        AgGrid(
                            df_display_sku,
                            gridOptions=gridOptions_sku,
                            allow_unsafe_jscode=True,
                            theme='balham', 
                            height=600,
                            fit_columns_on_grid_load=False,
                            custom_css=custom_css_sku
                        )
                    else:
                        st.error("Library st_aggrid belum terpasang. Fitur Smart Filter tidak bisa ditampilkan.")
                    
                    user_role_lower = role.lower()
                    if user_role_lower in ['direktur', 'manager', 'supervisor']:
                        output_sku = io.BytesIO()
                        with pd.ExcelWriter(output_sku, engine='xlsxwriter') as writer:
                            if 'df_display_sku_export' in locals() and not df_display_sku_export.empty:
                                df_display_sku_export.to_excel(writer, index=False, sheet_name='Detail SKU')
                                
                            workbook = writer.book
                            worksheet = writer.sheets['Detail SKU']
                            
                            user_identity = f"{st.session_state.get('sales_name', 'Unknown')} ({st.session_state.get('role', 'Unknown').upper()})"
                            time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            watermark_text = f"CONFIDENTIAL DOCUMENT | TRACKED USER: {user_identity} | DOWNLOADED: {time_stamp} | DO NOT DISTRIBUTE"
                            worksheet.set_header(f'&C&10{watermark_text}')
                            
                            format1 = workbook.add_format({'num_format': '#,##0'})
                            worksheet.set_column('B:N', None, format1)
                            
                            if 'df_display_sku_export' in locals() and not df_display_sku_export.empty:
                                last_row_idx_sku = len(df_display_sku_export)
                                
                                bold_yellow_format_sku = workbook.add_format({
                                    'bold': True,
                                    'bg_color': '#FFFF00',
                                    'border': 1,
                                    'num_format': '#,##0',
                                    'font_color': 'black'
                                })
                                worksheet.set_row(last_row_idx_sku, 30, bold_yellow_format_sku)
                            
                        st.download_button(
                            label="📥 Download Detail SKU (Excel)",
                            data=output_sku.getvalue(),
                            file_name=f"Detail_SKU_{datetime.date.today()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.warning("Tidak ada transaksi untuk filter tersebut.")

        with tab_growth:
            st.markdown("### 📈 Rekap Growth Brand")
            list_merk_growth = sorted(df['Merk'].dropna().astype(str).unique())
            list_merk_growth = [m for m in list_merk_growth if m != "-"]
            
            if list_merk_growth:
                brand_growth = st.selectbox("Pilih Brand untuk Analisis Growth:", list_merk_growth)
                
                # --- PIPA DATA RAW KHUSUS GROWTH ---
                df_team_all = df.copy()
                
                if target_sales_filter != "SEMUA":
                    if target_sales_filter.upper() in TARGET_DATABASE:
                        tim_sales_list = list(TARGET_DATABASE[target_sales_filter.upper()].keys())
                        df_team_all = df_team_all[df_team_all['Penjualan'].isin(tim_sales_list)]
                    else:
                        df_team_all = df_team_all[df_team_all['Penjualan'] == target_sales_filter]

                invalid_codes = ['-', '', 'NAN', 'NONE', '0.0']
                df_team_all['ID_Patokan'] = np.where(
                    df_team_all['Kode_Global'].str.strip().str.upper().isin(invalid_codes),
                    df_team_all['Nama Outlet'].str.strip(),
                    df_team_all['Kode_Global'].str.strip()
                )
                
                prefixes = BRAND_PREFIXES.get(brand_growth, [brand_growth[:3].upper()])
                prefix_tuple = tuple(prefixes)
                
                # === WATERTIGHT ALGORITMA RO (Murni dari Hulu) ===
                is_target_brand = df_team_all['Merk'] == brand_growth
                is_target_prefix = df_team_all['Kode_Global'].astype(str).str.strip().str.upper().apply(lambda x: any(x.startswith(p) for p in prefix_tuple))
                is_valid_ro = is_target_brand | is_target_prefix

                if st.checkbox("🔍 Buka Radar Detektif (Cek Toko Double)"):
                    df_cek = df_team_all[is_valid_ro].copy()
                    kd_col_cek = 'Kode_Global' if 'Kode_Global' in df_cek.columns else 'Kode Customer'
                    
                    if kd_col_cek in df_cek.columns:
                        duplikat = df_cek.groupby('Nama Outlet')[kd_col_cek].nunique().reset_index()
                        toko_double = duplikat[duplikat[kd_col_cek] > 1]['Nama Outlet'].tolist()
                        
                        if toko_double:
                            st.error(f"🚨 Ditemukan {len(toko_double)} Toko yang tercatat ganda (karena beda Kode)!")
                            df_tampil = df_cek[df_cek['Nama Outlet'].isin(toko_double)][['Nama Outlet', kd_col_cek, 'Provinsi', 'Kota']].drop_duplicates()
                            st.dataframe(df_tampil.sort_values('Nama Outlet'), use_container_width=True)
                        else:
                            st.success("✅ Tidak ada nama toko yang kodenya ganda.")
                    else:
                        st.warning("Kolom Kode tidak ditemukan untuk pengecekan.")

                if not df_team_all.empty:
                    df_team_all['Tahun'] = df_team_all['Tanggal'].dt.year
                    df_team_all['Bulan'] = df_team_all['Tanggal'].dt.month
                    df_team_all['Bulan-Tahun'] = df_team_all['Tanggal'].dt.to_period('M')
                    
                    min_period_2026 = pd.Period('2026-01', freq='M')
                    df_base = df_team_all[(df_team_all['Bulan-Tahun'] < min_period_2026) & is_valid_ro]
                    
                    ro_accumulated = set(df_base['ID_Patokan'].dropna().unique())
                    growth_data = []
                    
                    for m in range(1, 13):
                        period_str = f"2026-{m:02d}"
                        period = pd.Period(period_str, freq='M')
                        
                        df_ao_current = df_team_all[(df_team_all['Bulan-Tahun'] == period) & is_target_brand]
                        current_ao = set(df_ao_current['ID_Patokan'].dropna().unique())
                        sales = df_ao_current['Jumlah'].sum()
                        
                        noo = len(current_ao - ro_accumulated)
                        
                        df_ro_current = df_team_all[(df_team_all['Bulan-Tahun'] == period) & is_valid_ro]
                        ro_accumulated.update(df_ro_current['ID_Patokan'].dropna().unique())
                        
                        ro = len(ro_accumulated)
                        ao = len(current_ao)
                        ao_vs_ro = (ao / ro) if ro > 0 else 0
                        
                        growth_data.append({
                            'Year': 2026,
                            'Month': m,
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
                        
                        df_2025 = df_team_all[df_team_all['Tahun'] == 2025] 
                        df_2026_sales = df_growth_all[df_growth_all['Year'] == 2026]
                        
                        def get_sales_2025(df_yr, m, brand_name):
                            res = df_yr[(df_yr['Bulan'] == m) & (df_yr['Merk'] == brand_name)]['Jumlah']
                            return res.sum() if not res.empty else 0
                            
                        def get_sales_2026(df_yr, m):
                            res = df_yr[df_yr['Month'] == m]['SALES']
                            return res.sum() if not res.empty else 0

                        tot_2025 = 0
                        tot_2026 = 0
                        
                        with col_g1:
                            st.write(f"#### **Tabel 2: {brand_growth} 2025 vs 2026 Sales Growth**")
                            yoy_data = []
                            for m in range(1, 13):
                                s25 = get_sales_2025(df_2025, m, brand_growth)
                                s26 = get_sales_2026(df_2026_sales, m)
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
                                q_2025 = sum(get_sales_2025(df_2025, m, brand_growth) for m in range(m_start, m_end + 1))
                                q_2026 = sum(get_sales_2026(df_2026_sales, m) for m in range(m_start, m_end + 1))
                                
                                q_growth = ((q_2026 - q_2025) / q_2025) if q_2025 > 0 else (1 if q_2026 > 0 else 0)
                                q_data.append({
                                    'MONTH': f"Total {q}", 'SALES 2025': q_2025, 'SALES 2026': q_2026, 'Growth MTM': q_growth
                                })
                            
                            df_q = pd.DataFrame(q_data)
                            df_q_display = pd.concat([df_q, df_t2_total], ignore_index=True)
                            
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

        with tab_ai:
            st.markdown("### 🤖 Asisten AI Gemini (Enterprise Secure Mode)")
            st.info("🔒 **Keamanan Aktif:** Sistem HANYA mengirimkan ringkasan angka statistik ke AI. Data mentah dan nama toko rahasia Anda tetap berada di dalam server ini.")
            
            try:
                import google.generativeai as genai
                GENAI_AVAILABLE = True
            except ImportError:
                GENAI_AVAILABLE = False
                
            if not GENAI_AVAILABLE:
                st.error("⚠️ Library AI belum terinstal di Server. Pastikan Anda telah menambahkan 'google-generativeai' ke dalam file requirements.txt di Github Anda.")
            else:
                api_key_input = st.text_input("🔑 Masukkan API Key Gemini Anda:", type="password", help="Dapatkan API Key gratis di aistudio.google.com")
                
                if api_key_input:
                    try:
                        genai.configure(api_key=api_key_input)
                        user_question = st.text_area("Tanya AI tentang performa data yang sedang Anda filter:", placeholder="Contoh: Berdasarkan data ini, apa evaluasi untuk tim sales?")
                        
                        if st.button("💡 Analisis Sekarang"):
                            with st.spinner("AI sedang membaca ringkasan data Anda..."):
                                
                                # Merangkum Data
                                summary_brand = df_active.groupby('Merk')['Jumlah'].sum().nlargest(5).reset_index()
                                summary_sales = df_active.groupby('Penjualan')['Jumlah'].sum().nlargest(5).reset_index()
                                top_produk = df_active.groupby('Nama Barang')['Jumlah'].sum().nlargest(3).reset_index()
                                
                                context = f"""
                                TOTAL OMSET SAAT INI: Rp {current_omset_total:,.0f}
                                JUMLAH TRANSAKSI: {transaksi_count}
                                
                                TOP 5 BRAND:
                                {summary_brand.to_string()}
                                
                                TOP 5 SALESMAN:
                                {summary_sales.to_string()}
                                
                                TOP 3 PRODUK PALING LAKU:
                                {top_produk.to_string()}
                                """
                                
                                final_prompt = f"Anda adalah Konsultan Bisnis Ahli. Berikut adalah ringkasan data penjualan perusahaan bulan ini:\n{context}\n\nPertanyaan User: {user_question}\nBerikan jawaban yang taktis, cerdas, profesional, dan berbahasa Indonesia."
                                
                                models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-pro']
                                response = None
                                success_model = ""
                                
                                for m_name in models_to_try:
                                    try:
                                        model = genai.GenerativeModel(m_name)
                                        response = model.generate_content(final_prompt)
                                        success_model = m_name
                                        break
                                    except Exception:
                                        continue 
                                
                                if response:
                                    st.success(f"Analisis Selesai! (Powered by {success_model})")
                                    st.write(response.text)
                                else:
                                    st.error("Gagal! API Key Anda tidak memiliki akses ke versi Gemini apa pun. Silakan buat API Key baru di aistudio.google.com")
                                        
                    except Exception as e:
                        st.error(f"Koneksi gagal. Detail: {e}")

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if st.session_state['logged_in']: main_dashboard()
else: login_page()
