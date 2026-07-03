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
import difflib
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
    # LINK MASTER ANDA
    MASTER_SALES_URL ="https://docs.google.com/spreadsheets/d/e/2PACX-1vSJ-xqNCgSOSjOle60U1UQZX7101O0sBluq84Ge5ifnQVeZgv17j8Jc5ZYaqYhdfRRvJ8WCNYs4bujk/pub?output=csv" 
    MASTER_OPS_URL ="https://docs.google.com/spreadsheets/d/e/2PACX-1vQj-OjZqccPb57iVJtIXtyrEXgXfev3tnDZC0zhmPR7cCdVVC6Pifl_p7cgd2wmJ4MFfux_hbs_Ou7t/pub?output=csv" 
    
    # Fungsi pembantu untuk ambil list dari master dan membersihkannya
    def get_urls_from_master(master_url):
        df_index = pd.read_csv(master_url)
        # 1. Hapus baris yang kosong / NaN agar tidak menjadi error
        df_index = df_index.dropna(subset=['Link_Sheets']) 
        # 2. Bersihkan spasi tersembunyi di awal/akhir teks URL
        return [str(url).strip() for url in df_index['Link_Sheets'].tolist() if str(url).strip() != '']

    # Ambil semua link
    sales_urls = get_urls_from_master(MASTER_SALES_URL)
    ops_urls = get_urls_from_master(MASTER_OPS_URL)
    
    # --- PENGUNDUHAN DATA SALES DENGAN PENGAMAN (TRY-EXCEPT) ---
    sales_dfs = []
    for u in sales_urls:
        try:
            # Mencoba membaca data secara normal sebagai teks
            temp_df = pd.read_csv(u, dtype=str)
        except pd.errors.ParserError:
            # Jika ada baris tidak rata, paksa baca dengan template 150 kolom
            temp_df = pd.read_csv(u, header=None, names=range(150), dtype=str)
            # Hapus sisa kolom yang benar-benar kosong semua
            temp_df = temp_df.dropna(axis=1, how='all')
            # Jadikan baris pertama sebagai judul kolom yang sah
            if not temp_df.empty:
                temp_df.columns = temp_df.iloc[0]
                temp_df = temp_df[1:]
                temp_df = temp_df.reset_index(drop=True)
        except Exception:
            st.warning(f"Gagal membaca link Sales (Periksa link): {u}")
            continue

        if not temp_df.empty:
            sales_dfs.append(temp_df)

    if sales_dfs:
        df_sales = pd.concat(sales_dfs, ignore_index=True)
        df_sales['Tipe_Data'] = 'SALES'
    else:
        df_sales = pd.DataFrame()
        
    # --- PENGUNDUHAN DATA OPERASIONAL ---
    ops_dfs = []
    for u in ops_urls:
        try:
            temp_df = pd.read_csv(u, dtype=str)
        except pd.errors.ParserError:
            temp_df = pd.read_csv(u, header=None, names=range(150), dtype=str)
            temp_df = temp_df.dropna(axis=1, how='all')
            if not temp_df.empty:
                temp_df.columns = temp_df.iloc[0]
                temp_df = temp_df[1:]
                temp_df = temp_df.reset_index(drop=True)
        except Exception:
            st.warning(f"Gagal membaca link Ops (Periksa link): {u}")
            continue

        if not temp_df.empty:
            ops_dfs.append(temp_df)
            
    if ops_dfs:
        df_ops = pd.concat(ops_dfs, ignore_index=True)
        df_ops['Tipe_Data'] = 'OPERASIONAL'
    else:
        df_ops = pd.DataFrame()

    # Gabungkan seluruh hasil
    df = pd.concat([df_sales, df_ops], ignore_index=True)
    df.columns = df.columns.str.strip()
    
    # Penambahan kolom operasional
    if 'Status Faktur' not in df.columns:
        df['Status Faktur'] = "Baru"
    if 'Tahun' in df.columns:
        df['Tahun'] = df['Tahun'].fillna('2024')
    if 'Tanggal' in df.columns:
        df['Tanggal'] = df['Tanggal'].fillna('2024-01-01')

    # 2. Mencegah tabel pivot membuang toko tanpa riwayat transaksi
    # Pastikan Anda menyesuaikan nama 'Total' atau 'Nilai' sesuai dengan nama kolom di sheet Anda
    kolom_transaksi = ['Total', 'Nilai', 'Qty', 'Nominal'] 
    for col in kolom_transaksi:
        if col in df.columns:
            # Ubah menjadi numerik jika memungkinkan, lalu isi dengan 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 3. Bersihkan sisa data kosong lainnya agar tampilan UI tetap rapi
    df = df.fillna('')
        
    # -------------------------------------------------------------------------
    # 1. PENYATUAN NAMA KOLOM BRUTAL (MENGGABUNGKAN SEMUA SHEET)
    # -------------------------------------------------------------------------
    def gabungkan_kolom(df, target_name, aliases):
        if target_name not in df.columns:
            df[target_name] = np.nan
        for alias in aliases:
            matched_cols = [c for c in df.columns if c.upper() == alias.upper() and c != target_name]
            for match in matched_cols:
                df[target_name] = df[target_name].fillna(df[match])
        return df

    df = gabungkan_kolom(df, 'Nama Outlet', ['NAMA CUSTOMER', 'CUSTOMER', 'NAMA TOKO', 'TOKO', 'PELANGGAN', 'OUTLET', 'NAMA OUTLET'])
    df = gabungkan_kolom(df, 'Kode_Global', ['KODE CUSTOMER', 'KODE COSTUMER', 'KODE OUTLET', 'KODE TOKO', 'KODE GLOBAL', 'KODE_GLOBAL'])
    df = gabungkan_kolom(df, 'Penjualan', ['SALES', 'SALESMAN', 'NAMA SALES', 'PENJUALAN'])
    df = gabungkan_kolom(df, 'Merk', ['BRAND', 'PRODUK', 'MERK'])
    
    faktur_cols = [c for c in df.columns if 'faktur' in c.lower() or 'bukti' in c.lower() or 'invoice' in c.lower()]
    if faktur_cols:
        df = gabungkan_kolom(df, 'No Faktur', faktur_cols)

    # -------------------------------------------------------------------------
    # 2. PEMBERSIHAN DATA DASAR
    # -------------------------------------------------------------------------
    if 'Kode_Global' not in df.columns: df['Kode_Global'] = "-"
    
    if 'Nama Barang' in df.columns:
        df = df[~df['Nama Barang'].astype(str).str.match(r'^(Total|Jumlah)', case=False, na=False)]
        df['Nama Barang'] = df['Nama Barang'].fillna("-")

    if 'Nama Outlet' in df.columns:
        df = df[~df['Nama Outlet'].astype(str).str.match(r'^(Total|Jumlah|Subtotal|Grand|Rekap)', case=False, na=False)]
        df['Nama Outlet'] = df['Nama Outlet'].fillna("-")
        df = df[df['Nama Outlet'].astype(str).str.strip() != ''] 
        df = df[df['Nama Outlet'].astype(str).str.lower() != 'nan']
    else:
        df['Nama Outlet'] = "-" 

    def clean_rupiah(x):
        x = str(x).upper().replace('RP', '').strip()
        x = re.sub(r'\s+', '', x) 
        x = re.sub(r'[,.]\d{2}$', '', x) 
        x = x.replace(',', '').replace('.', '') 
        x = re.sub(r'[^\d Grama-z-]', '', x, flags=re.IGNORECASE) 
        try: return float(x)
        except: return 0.0

    if 'Jumlah' in df.columns: df['Jumlah'] = df['Jumlah'].apply(clean_rupiah)
    else: df['Jumlah'] = 0.0

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

    # -------------------------------------------------------------------------
    # 3. RADAR DETEKTIF PROVINSI
    # -------------------------------------------------------------------------
    df = gabungkan_kolom(df, 'Provinsi', ['PROPINSI', 'PROVINCE', 'PROV', 'WILAYAH'])
    df = gabungkan_kolom(df, 'Kota', ['CITY', 'KABUPATEN', 'KAB', 'DAERAH', 'LOKASI'])

    def determine_province(row):
        valid_provinces = {
            "ACEH", "SUMATERA UTARA", "SUMATERA BARAT", "RIAU", "KEPULAUAN RIAU", 
            "JAMBI", "SUMATERA SELATAN", "BANGKA BELITUNG", "BENGKULU", "LAMPUNG", 
            "DKI JAKARTA", "JAWA BARAT", "BANTEN", "JAWA TENGAH", "DI YOGYAKARTA", 
            "JAWA TIMUR", "BALI", "NUSA TENGGARA BARAT", "NUSA TENGGARA TIMUR", 
            "KALIMANTAN BARAT", "KALIMANTAN TENGAH", "KALIMANTAN SELATAN", "KALIMANTAN TIMUR", 
            "KALIMANTAN UTARA", "SULAWESI UTARA", "SULAWESI TENGAH", "SULAWESI SELATAN", 
            "SULAWESI TENGGARA", "SULAWESI BARAT", "GORONTALO", "MALUKU", "MALUKU UTARA", 
            "PAPUA BARAT", "PAPUA", "PAPUA SELATAN", "PAPUA TENGAH", "PAPUA PEGUNUNGAN", "PAPUA BARAT DAYA"
        }
        abbreviations = {
            "SUMUT": "SUMATERA UTARA", "SUMBAR": "SUMATERA BARAT", "KEPRI": "KEPULAUAN RIAU",
            "SUMSEL": "SUMATERA SELATAN", "BABEL": "BANGKA BELITUNG", "DKI": "DKI JAKARTA",
            "JAKARTA": "DKI JAKARTA", "JABAR": "JAWA BARAT", "JATENG": "JAWA TENGAH",
            "DIY": "DI YOGYAKARTA", "JOGJA": "DI YOGYAKARTA", "YOGYAKARTA": "DI YOGYAKARTA",
            "JATIM": "JAWA TIMUR", "NTB": "NUSA TENGGARA BARAT", "NTT": "NUSA TENGGARA TIMUR",
            "KALBAR": "KALIMANTAN BARAT", "KALTENG": "KALIMANTAN TENGAH", "KALSEL": "KALIMANTAN SELATAN",
            "KALTIM": "KALIMANTAN TIMUR", "KALUT": "KALIMANTAN UTARA", "SULUT": "SULAWESI UTARA",
            "SULTENG": "SULAWESI TENGAH", "SULSEL": "SULAWESI SELATAN", "SULTRA": "SULAWESI TENGGARA",
            "SULBAR": "SULAWESI BARAT", "MALUT": "MALUKU UTARA", "NAD": "ACEH"
        }
        
        p_raw = str(row.get('Provinsi', '')).strip().upper()
        c_raw = str(row.get('Kota', '')).strip().upper()
        o_raw = str(row.get('Nama Outlet', '')).strip().upper()
        
        if p_raw in ['NAN', '-', 'NONE', '0']: p_raw = ""
        if c_raw in ['NAN', '-', 'NONE', '0']: c_raw = ""
        if o_raw in ['NAN', '-', 'NONE', '0']: o_raw = ""
        
        if p_raw:
            if p_raw in valid_provinces: return p_raw
            if p_raw in abbreviations: return abbreviations[p_raw]
            matches = difflib.get_close_matches(p_raw, valid_provinces, n=1, cutoff=0.8)
            if matches: return matches[0]

        teks_lokasi = f"{p_raw} {c_raw}".strip()
        if teks_lokasi:
            for prov_name, cities in PROVINCE_MAPPING.items():
                for city in cities:
                    if city == teks_lokasi or f" {city} " in f" {teks_lokasi} ": return prov_name
            semua_kota = [ct for cities in PROVINCE_MAPPING.values() for ct in cities]
            map_kota_prov = {ct: p_name for p_name, cities in PROVINCE_MAPPING.items() for ct in cities}
            matches_kota = difflib.get_close_matches(teks_lokasi, semua_kota, n=1, cutoff=0.85)
            if matches_kota: return map_kota_prov[matches_kota[0]]

        if o_raw:
            for prov_name, cities in PROVINCE_MAPPING.items():
                for city in cities:
                    if len(city) >= 4: 
                        if f" {city} " in f" {o_raw} " or o_raw.endswith(f" {city}") or o_raw.startswith(f"{city} "):
                            return prov_name
        return "LAIN-LAIN"

    df['Provinsi'] = df.apply(determine_province, axis=1)

    # -------------------------------------------------------------------------
    # 4. AUTO-HEALING CERDAS (Kode Spesifik per Brand)
    # -------------------------------------------------------------------------
    df['Nama_Pencocokan'] = df['Nama Outlet'].astype(str).str.strip().str.upper()
    
    # KUNCI UTAMA: Kita pasangkan Toko DENGAN Brand-nya (Merk)
    df['Kunci_Kode'] = list(zip(df['Nama_Pencocokan'], df['Merk']))
    
    # Healing 1: Kode Customer WAJIB di-group berdasarkan Toko + Brand
    valid_kodes = df[~df['Kode_Global'].isin(['-', '', 'NAN', 'NONE', '0.0', '0'])].groupby('Kunci_Kode')['Kode_Global'].first()
    df['Kode_Global'] = df['Kunci_Kode'].map(valid_kodes).fillna(df['Kode_Global'])
    
    # Healing 2: Provinsi & Kota di-group murni berdasarkan Toko (karena lokasi fisik sama)
    valid_provs = df[~df['Provinsi'].isin(['-', '', 'LAIN-LAIN', 'NAN', 'NONE'])].groupby('Nama_Pencocokan')['Provinsi'].first()
    valid_kotas = df[~df['Kota'].isin(['-', '', 'NAN', 'NONE'])].groupby('Nama_Pencocokan')['Kota'].first()
    df['Provinsi'] = df['Nama_Pencocokan'].map(valid_provs).fillna(df['Provinsi'])
    df['Kota'] = df['Nama_Pencocokan'].map(valid_kotas).fillna(df['Kota'])
    
    df = df.drop(columns=['Nama_Pencocokan', 'Kunci_Kode'])
    
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
# PIVOT FAST ENGINE 
# =========================================================================
def generate_pivot_fast(df_pivot_source, selected_merk_excel, selected_tahun_excel_tuple, group_cols_tuple, brand_prefixes_dict):
    group_cols = list(group_cols_tuple)

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

        cols_to_keep = group_cols.copy()
        if 'Nama Outlet' not in cols_to_keep:
            cols_to_keep.append('Nama Outlet')
            
        # --- KUNCI UTAMA: Pastikan Kolom Merk Dipertahankan ---
        if 'Merk' not in cols_to_keep:
            cols_to_keep.append('Merk')

        df_excel = df_filtered[df_filtered['Tanggal'].dt.year.isin(selected_tahun_excel_tuple)].copy()
        
        if not df_excel.empty:
            df_excel['Bulan Angka'] = df_excel['Tanggal'].dt.month
            
            # KUNCI UTAMA: Pivot dipisah berdasarkan Nama Outlet DAN Merk
            pivot_sales = pd.pivot_table(df_excel, values='Jumlah', index=['Nama Outlet', 'Merk'], columns='Bulan Angka', aggfunc='sum', fill_value=0).reset_index()
            
            df_sorted = df_filtered.sort_values(by=['Nama Outlet', 'Kode_Global'], ascending=[True, False])
            
            base_customers = df_sorted.drop_duplicates(subset=['Nama Outlet', 'Merk'], keep='first')[cols_to_keep]
            
            master_pivot = pd.merge(base_customers, pivot_sales, on=['Nama Outlet', 'Merk'], how='left').fillna(0)
            
            for i in range(1, 13):
                if i not in master_pivot.columns: master_pivot[i] = 0
        else:
            df_sorted = df_filtered.sort_values(by=['Nama Outlet', 'Kode_Global'], ascending=[True, False])
            master_pivot = df_sorted.drop_duplicates(subset=['Nama Outlet', 'Merk'], keep='first')[cols_to_keep]
            for i in range(1, 13): master_pivot[i] = 0
            
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
        
    if 'Nama Customer' in df_scope_all.columns: grp_cols.append('Nama Customer')
    elif 'Nama Outlet' in df_scope_all.columns: 
        grp_cols.append('Nama Outlet')
        df_scope_all['Nama Customer'] = df_scope_all['Nama Outlet']
    else: df_scope_all['Nama Customer'] = "-"; grp_cols.append('Nama Customer')
    
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
        list_nama_all = sorted(df_scope_all['Nama Outlet'].astype(str).unique()) if 'Nama Outlet' in df_scope_all.columns else sorted(df_scope_all['Nama Customer'].astype(str).unique())
        list_provinsi_all = sorted(df_scope_all['Provinsi'].astype(str).unique())
        list_kota_all = sorted(df_scope_all['Kota'].astype(str).unique())

        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1: filter_kode = st.multiselect("Kode Customer:", list_kode_all, placeholder="Pilih Kode...")
        with col_f2: filter_nama = st.multiselect("Nama Customer:", list_nama_all, placeholder="Pilih Customer...")
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
        
        ren_dict = {'Kode_Global': 'Kode Customer', 'Nama Outlet': 'Nama Customer'}
        master_pivot = master_pivot.rename(columns=ren_dict)
        
        if 'Kode Customer' not in master_pivot.columns: master_pivot['Kode Customer'] = "-"
        if 'Nama Customer' not in master_pivot.columns: master_pivot['Nama Customer'] = "-"
        if 'Provinsi' not in master_pivot.columns: master_pivot['Provinsi'] = "-"
        if 'Kota' not in master_pivot.columns: master_pivot['Kota'] = "-"

        df_filtered = master_pivot.copy()
        if filter_kode: df_filtered = df_filtered[df_filtered['Kode Customer'].astype(str).isin(filter_kode)]
        if filter_nama: df_filtered = df_filtered[df_filtered['Nama Customer'].astype(str).isin(filter_nama)]
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
            # (Baris yang membuang Nama Customer SUDAH DIHAPUS DARI SINI)

            bulan_indo_list = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
            num_cols = bulan_indo_list + ['Total Penjualan']
            
            # Tambahkan 'Nama Customer' dan 'Merk' kembali ke urutan kolom
            cols_reordered = ['Kode Customer', 'Nama Customer', 'Merk', 'Provinsi', 'Kota'] + num_cols
            
            # Antisipasi agar tidak error jika kolom ada yang kurang
            cols_reordered = [c for c in cols_reordered if c in df_filtered.columns]
            
            df_display = df_filtered[cols_reordered].copy()
            
            total_dict = {col: "" for col in df_display.columns}
            if 'Kode Customer' in total_dict:
                total_dict['Kode Customer'] = "GRAND TOTAL"
            elif len(df_display.columns) > 0:
                total_dict[df_display.columns[0]] = "GRAND TOTAL"
                
            for col in num_cols:
                if col in df_display.columns:
                    total_dict[col] = df_display[col].sum()
                    
            df_display_export = pd.concat([df_display, pd.DataFrame([total_dict])], ignore_index=True)
            df_display_export = df_display_export.loc[:, ~df_display_export.columns.duplicated()]
            
            # --- AGGRID IMPLEMENTATION FOR MAIN PIVOT ---
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
                    elif col in ['Kode Customer', 'Nama Customer']:
                        gb.configure_column(col, pinned='left', filter='agSetColumnFilter', floatingFilter=True)
                    else:
                        gb.configure_column(col, filter='agSetColumnFilter', floatingFilter=True)
                
                gb.configure_default_column(resizable=True, sortable=True)
                
                getRowHeight = JsCode("""
                function(params) {
                    if (params.node.rowPinned === 'bottom') return 45;
                    return 40;
                }
                """)
                
                gb.configure_grid_options(
                    getRowHeight=getRowHeight,
                    headerHeight=45, 
                    floatingFiltersHeight=40,
                    pinnedBottomRowData=[total_dict]
                )
                
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
                
                custom_css = {
                    ".ag-root-wrapper": {"font-family": "sans-serif !important"},
                    ".ag-header-cell-label": {"font-size": "14px !important", "color": "white !important", "font-weight": "bold !important"},
                    ".ag-header-cell": {"background-color": "#2980b9 !important", "border-right": "1px solid #555555 !important"},
                    ".ag-header": {"background-color": "#2980b9 !important", "border-bottom": "1px solid #555555 !important"},
                    ".ag-header-row-column-filter": {"background-color": "#2980b9 !important"},
                    ".ag-header .ag-icon": {"color": "white !important", "fill": "white !important"},
                    ".ag-cell": {"font-size": "14px !important", "font-weight": "500 !important", "color": "black !important", "background-color": "white !important", "border-right": "1px solid #555555 !important", "border-bottom": "1px solid #555555 !important", "display": "flex", "align-items": "center"},
                    ".ag-row-hover .ag-cell": {"background-color": "#e3f2fd !important"},
                    ".ag-floating-filter-input input": {"font-size": "13px !important", "background-color": "white !important", "color": "black !important", "border-radius": "3px !important", "padding": "2px 5px !important", "border": "1px solid #ccc !important"},
                    ".right-aligned-header .ag-header-cell-label": {"justify-content": "flex-end !important"},
                    ".ag-floating-bottom-container .ag-row, .ag-pinned-left-floating-bottom .ag-row": {"border-top": "3px solid #333 !important"},
                    ".ag-floating-bottom-container .ag-cell, .ag-pinned-left-floating-bottom .ag-cell": {
                        "font-size": "14px !important", "background-color": "#FFFF00 !important", "color": "black !important", "font-weight": "bold !important", "border-right": "none !important"
                    }
                }
                
                try:
                    AgGrid(df_display, gridOptions=gridOptions, allow_unsafe_jscode=True, theme='balham', height=600, fit_columns_on_grid_load=False, custom_css=custom_css, enable_enterprise_modules=True)
                except Exception:
                    st.dataframe(df_display_export, use_container_width=True)
            else:
                st.dataframe(df_display_export, use_container_width=True)
            
        else:
            st.info("Data Kosong setelah difilter.")
            
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
                worksheet.set_column('D:P', None, format1) 
                
                if 'df_display_export' in locals() and not df_display_export.empty:
                    bold_format = workbook.add_format({'bold': True, 'bg_color': '#f2f2f2', 'border': 1, 'num_format': '#,##0'})
                    last_row_idx = len(df_display_export) 
                    worksheet.set_row(last_row_idx, None, bold_format)
            
            st.download_button(
                label="📥 Download Laporan Excel (XLSX) - DRM Protected",
                data=output.getvalue(),
                file_name=f"Laporan_Master_{selected_merk_excel}_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("Data Kosong.")

def login_page():
    st.markdown("<br><br><h1 style='text-align: center;'>🦅 Executive Command Center</h1>", unsafe_allow_html=True)
    
    if st.session_state.get('logged_out_due_to_inactivity', False):
        st.warning("⏱️ Sesi Anda telah berakhir karena tidak ada aktivitas selama 15 menit. Silakan login kembali demi keamanan.")
        st.session_state['logged_out_due_to_inactivity'] = False

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
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    captcha_val = st.slider("Geser slider ke ujung kanan (100) untuk verifikasi manusia 🤖", 0, 100, 0)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    submitted = st.form_submit_button("Verifikasi Akun", use_container_width=True)
                    
                    if submitted:
                        if username in st.session_state.get('lockout_until', {}):
                            if time.time() < st.session_state['lockout_until'][username]:
                                remaining = int((st.session_state['lockout_until'][username] - time.time()) / 60)
                                st.error(f"🔒 Akses ditolak! Akun terkunci karena percobaan gagal beruntun. Coba lagi dalam {remaining + 1} menit.")
                                return
                            else:
                                st.session_state['failed_attempts'][username] = 0
                                del st.session_state['lockout_until'][username]

                        if captcha_val != 100:
                            st.error("🚨 Verifikasi Captcha gagal! Geser slider hingga angka 100.")
                        else:
                            users = load_users()
                            if users.empty: st.error("Database user (users.csv) tidak ditemukan.")
                            else:
                                match = users[(users['username'] == username) & (users['password'] == password)]
                                if match.empty:
                                    st.error("Username atau Password salah.")
                                    log_activity(username, "FAILED LOGIN - WRONG PASS")
                                    st.session_state['failed_attempts'][username] = st.session_state['failed_attempts'].get(username, 0) + 1
                                    if st.session_state['failed_attempts'][username] >= 3:
                                        st.session_state['lockout_until'][username] = time.time() + 600 
                                        st.error("🔒 Akun dikunci selama 10 menit karena 3x percobaan gagal.")
                                else:
                                    st.session_state['failed_attempts'][username] = 0
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
                username_2fa = user_data['username']
                
                if username_2fa in st.session_state.get('lockout_until', {}):
                    if time.time() < st.session_state['lockout_until'][username_2fa]:
                        remaining = int((st.session_state['lockout_until'][username_2fa] - time.time()) / 60)
                        st.error(f"🔒 Akses ditolak! Akun terkunci. Coba lagi dalam {remaining + 1} menit.")
                        if st.button("Kembali ke Awal"):
                            st.session_state['login_step'] = 'credentials'
                            st.rerun()
                        return
                
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
                            st.session_state['failed_attempts'][username_2fa] = 0
                            st.session_state['logged_in'] = True
                            st.session_state['role'] = user_data['role']
                            st.session_state['sales_name'] = user_data['sales_name']
                            log_activity(user_data['sales_name'], "LOGIN SUCCESS (2FA)")
                            st.rerun()
                        else:
                            st.error("Kode OTP Salah!")
                            log_activity(user_data['sales_name'], "FAILED LOGIN - WRONG OTP")
                            st.session_state['failed_attempts'][username_2fa] = st.session_state['failed_attempts'].get(username_2fa, 0) + 1
                            if st.session_state['failed_attempts'][username_2fa] >= 3:
                                st.session_state['lockout_until'][username_2fa] = time.time() + 600
                                st.error("🔒 Akun dikunci selama 10 menit karena 3x percobaan gagal.")
                    if st.button("Kembali"):
                        st.session_state['login_step'] = 'credentials'
                        st.rerun()

# =========================================================================
# MOCKUP UI OPERASIONAL (MANAGER, GUDANG, DRIVER) - VERSI 2.0 (ENHANCED)
# =========================================================================
def ui_operasional_manager():
    st.markdown("### 📦 Dashboard Operasional & Logistik")

    # --- 1. TOP BADGES / TOMBOL PERINGATAN (Bisa diklik, Data Kosong) ---
    col_badge1, col_badge2, _ = st.columns([2, 3, 5])
    with col_badge1:
        if st.button("🕒 0 dok titip", use_container_width=True):
            st.toast("Menampilkan filter dokumen titip...")
    with col_badge2:
        if st.button("📸 0 kirim tanpa foto · hari ini", use_container_width=True):
            st.toast("Menampilkan filter kiriman tanpa foto...")

    st.write("") # Spacer

    # --- 2. MAIN METRICS CARDS (Data 0, Tooltip Logika Ditambahkan) ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True):
            # Tooltip help menjelaskan logika "In-flight"
            st.markdown("**In-flight**", help="Faktur telah diterima Gudang")
            st.markdown("## 0")
            
    with col2:
        with st.container(border=True):
            # Tooltip help menjelaskan logika "Batas SLA"
            st.markdown("**> batas SLA**", help="Faktur telat diantar lebih dari ketentuan yang berlaku")
            # Menggunakan warna merah (Red) untuk menandakan SLA
            st.markdown("<h2 style='color: #e74c3c;'>0</h2>", unsafe_allow_html=True)

    with col3:
        with st.container(border=True):
            # Tooltip help menjelaskan logika "Stuck antar"
            st.markdown("**Stuck antar**", help="Faktur ditahan gudang dengan alasan apapun")
            st.markdown("## 0")
            
    with col4:
        with st.container(border=True):
            st.markdown("**Selesai**", help="Faktur telah kembali ke Gudang setelah barang diantar")
            st.markdown("## 0")
            
            # Indikator Visual 4 Garis Hijau & Teks "Selesai" sesuai gambar image_cfe404.png
            st.markdown("""
            <div style="display: flex; gap: 4px; align-items: center; margin-top: 8px;">
                <div style="width: 22px; height: 7px; background-color: #7bb88f; border-radius: 10px;"></div>
                <div style="width: 22px; height: 7px; background-color: #7bb88f; border-radius: 10px;"></div>
                <div style="width: 22px; height: 7px; background-color: #7bb88f; border-radius: 10px;"></div>
                <div style="width: 22px; height: 7px; background-color: #7bb88f; border-radius: 10px;"></div>
            </div>
            <div style="color: #7bb88f; font-weight: 600; font-size: 15px; margin-top: 4px; font-family: sans-serif;">Selesai</div>
            """, unsafe_allow_html=True)

    st.write("") # Spacer

    # --- 3. FILTER BUTTONS ROW (Flow, Office, Gudang, dll) ---
    # Dibuat menggunakan kolom agar tersusun rapi secara horizontal seperti di desain
    btn_col1, btn_col2, btn_col3, btn_col4, btn_col5, btn_col6, _ = st.columns([1, 1, 1, 1, 1, 1, 4])

    with btn_col1:
        st.button("Flow", type="primary", use_container_width=True) # Dibuat primary agar lebih menonjol (aktif)
    with btn_col2:
        st.button("Office", use_container_width=True)
    with btn_col3:
        st.button("Gudang", use_container_width=True)
    with btn_col4:
        st.button("Checker", use_container_width=True)
    with btn_col5:
        st.button("Delivery", use_container_width=True)
    with btn_col6:
        st.button("Fakturis", use_container_width=True)

    # --- 4. PLACEHOLDER UNTUK DATA TABEL NANTINYA ---
    st.divider()
    st.caption("Menunggu sinkronisasi data operasional...")
    
    st.markdown("### Laporan")
    t_ringkasan, t_harian, t_detail, t_kurir, t_efektif, t_sla = st.tabs([
        "Ringkasan", "Rangkuman Harian", "Detail Harian", "Kinerja Kurir", "Peta Pengiriman (Live)", "Kepatuhan SLA"
    ])
    
    with t_ringkasan:
        st.markdown("### 📊 Ringkasan Eksekutif Operasional")
        st.caption("Menampilkan data operasional hari ini. (Data saat ini masih kosong/menunggu integrasi)")
        
        # --- 1. ACTION CENTER (PERLU TINDAKAN CEPAT) ---
        st.markdown("#### 🚨 Action Center")
        col_rt1, col_rt2, col_rt3 = st.columns(3)
        with col_rt1:
            st.warning("⏱️ > Batas SLA (0 Faktur)")
        with col_rt2:
            st.error("⚠️ Stuck Antar > 20 Jam (0 Faktur)")
            # Tombol dinonaktifkan sementara karena data kosong
            st.button("🚨 Senggol Tim Gudang/Kurir (via WA)", disabled=True, use_container_width=True)
        with col_rt3:
            st.info("📦 Menunggu Checker / Packing (0 Faktur)")

        st.divider()

        # --- 2. KPI METRICS ---
        st.markdown("#### 📈 Indikator Kinerja Utama (KPI)")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.metric(label="Total Surat Jalan Keluar", value="0", delta="0% vs Kemarin")
        with kpi2:
            st.metric(label="Berhasil Terkirim", value="0", delta="0% vs Kemarin")
        with kpi3:
            st.metric(label="Total Retur / Gagal", value="0", delta="0% vs Kemarin", delta_color="inverse")
        with kpi4:
            st.metric(label="Rata-rata Waktu Kirim", value="0 Jam", delta="0 Jam vs Kemarin", delta_color="inverse")

        st.divider()

        # --- 3. VISUALISASI DATA (EMPTY STATE) ---
        st.markdown("#### 📉 Analisis Pengiriman")
        chart_col1, chart_col2 = st.columns([1, 2])
        
        with chart_col1:
            st.markdown("**Status Pengiriman Keseluruhan**")
            # Grafik Donat Kosong
            df_donut_empty = pd.DataFrame({
                "Status": ["Terkirim", "Proses", "Retur"], 
                "Jumlah": [0, 0, 0]
            })
            fig_donut = px.pie(
                df_donut_empty, 
                names="Status", 
                values="Jumlah", 
                hole=0.6,
                color="Status",
                color_discrete_map={"Terkirim": "#2ecc71", "Proses": "#3498db", "Retur": "#e74c3c"}
            )
            fig_donut.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280, showlegend=True)
            # Menampilkan teks "No Data" di tengah donat
            fig_donut.add_annotation(text="No Data", x=0.5, y=0.5, font_size=20, showarrow=False)
            st.plotly_chart(fig_donut, use_container_width=True)

        with chart_col2:
            st.markdown("**Tren Pengiriman (7 Hari Terakhir)**")
            # Grafik Garis Kosong
            tujuh_hari_lalu = [datetime.date.today() - datetime.timedelta(days=i) for i in range(6, -1, -1)]
            df_line_empty = pd.DataFrame({
                "Tanggal": tujuh_hari_lalu,
                "Total Pengiriman": [0, 0, 0, 0, 0, 0, 0]
            })
            fig_line = px.line(
                df_line_empty, 
                x="Tanggal", 
                y="Total Pengiriman", 
                markers=True,
                line_shape="spline"
            )
            fig_line.update_traces(line_color="#2980b9", marker=dict(size=8))
            fig_line.update_layout(
                margin=dict(t=10, b=10, l=10, r=10), 
                height=280, 
                yaxis_title="Jumlah Resi/Faktur", 
                xaxis_title=""
            )
            st.plotly_chart(fig_line, use_container_width=True)

        st.divider()

        # --- 4. TABEL LOG AKTIVITAS TERBARU ---
        st.markdown("#### 📋 Log Antrean & Aktivitas Terbaru")
        # DataFrame Kosong dengan struktur kolom yang rapi
        df_log_empty = pd.DataFrame(columns=[
            "Waktu Update", 
            "No. Tanda Terima", 
            "No. Faktur", 
            "Kurir", 
            "Customer / Toko", 
            "Status Operasional", 
            "Keterangan"
        ])
        
        # Konfigurasi UI Tabel agar tampak proporsional meski kosong
        st.dataframe(
            df_log_empty, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Waktu Update": st.column_config.DatetimeColumn("Waktu Update", format="DD/MM/YYYY HH:mm"),
                "Status Operasional": st.column_config.TextColumn("Status Operasional")
            }
        )
        
    with t_efektif:
        st.caption("PETA KEMACETAN & DISTRIBUSI PENGIRIMAN (Medan Area)")
        
        # 1. Tombol Pintar ke Google Maps Asli (Mode Kemacetan / Traffic Layer AKTIF)
        st.info("Gunakan tombol di bawah untuk memantau kemacetan, penutupan jalan, dan rute real-time di Google Maps.")
        st.link_button(
            "🗺️ Buka Live Traffic Google Maps (Full Fitur)", 
            "https://www.google.com/maps/@3.5852867,98.6756689,13z/data=!5m1!1e1", 
            type="primary", 
            use_container_width=True
        )
        
        st.markdown("---")
        st.write("**Titik Sebaran Area Pengiriman Hari ini:**")
        
        # 2. Peta Bawaan Streamlit (Hanya untuk melihat gambaran titik sebaran toko)
        df_lokasi = pd.DataFrame({
            "lat": [3.595, 3.585, 3.600, 3.570],
            "lon": [98.672, 98.660, 98.680, 98.650],
        })
        st.map(df_lokasi, zoom=12)

def ui_operasional_admin():
    st.markdown("## 🏢 Panel Admin / Fakturis")
    st.info("Buat Tanda Terima (TT) digital agar Kepala Gudang bisa mencocokkan dokumen fisik.")
    
    with st.container(border=True):
        st.markdown("### 📝 Buat Tanda Terima Baru")
        with st.form("form_buat_tt"):
            col1, col2 = st.columns(2)
            no_tt = col1.text_input("Nomor Tanda Terima (TT)", placeholder="Misal: TT-202607-001")
            nama_sales = col2.selectbox("Nama Sales", ["WIRA", "HAMZAH", "FERI", "ADE", "RISKA", "DLL"])
            
            st.write("**Daftar Nomor Faktur yang diserahkan dalam TT ini:**")
            daftar_faktur = st.text_area("Ketik / Scan Barcode Nomor Faktur (Pisahkan dengan koma atau Enter)", placeholder="INV-001\nINV-002\nINV-003", height=100)
            
            submitted = st.form_submit_button("📤 Upload & Serahkan ke Gudang", type="primary")
            if submitted:
                st.success(f"Tanda Terima {no_tt} berhasil dibuat! Status: Menunggu Konfirmasi Kepala Gudang.")
                
    st.divider()
    st.markdown("### 📜 Riwayat Tanda Terima Hari Ini")
    df_history = pd.DataFrame({
        "Waktu": ["10:15 WIB", "09:30 WIB"],
        "No. TT": ["TT-202607-002", "TT-202607-001"],
        "Sales": ["ADE", "WIRA"],
        "Jml Faktur": [5, 12],
        "Status": ["Menunggu Gudang 🟡", "Diterima Gudang 🟢"]
    })
    st.dataframe(df_history, use_container_width=True, hide_index=True)
    st.divider()
    st.markdown("### 🏁 Finalisasi (Closing Faktur)")
    st.caption("Faktur yang sudah kembali dari Gudang akan muncul di sini untuk di-Closing.")
    
    df_closing = pd.DataFrame({
        "No. Faktur": ["INV-001", "INV-002"],
        "Status": ["Kembali dari Gudang", "Kembali dari Gudang"],
        "Aksi": [False, False]
    })
    
    edited_closing = st.data_editor(df_closing, column_config={"Aksi": st.column_config.CheckboxColumn("Finalisasi/Arsip")}, hide_index=True)
    
    if st.button("🔒 Finalisasi & Arsipkan Faktur Terpilih"):
        st.success("Faktur berhasil diarsipkan ke database permanen.")

def ui_operasional_gudang():
    st.markdown("## 🏭 Panel Gudang & Checker (Dwi)")
    
    # --- BAGIAN 1: PENERIMAAN DOKUMEN DARI ADMIN (Langkah 4) ---
    st.markdown("### 📥 Penerimaan Dokumen Tanda Terima (TT)")
    with st.container(border=True):
        col_tt1, col_tt2 = st.columns([3, 1])
        with col_tt1:
            st.write("**No. TT: TT-202607-002** (Sales: ADE)")
            st.code("INV-004\nINV-005\nINV-006\nINV-007\nINV-008")
        with col_tt2:
            st.write("\n\n")
            if st.button("✅ Konfirmasi Terima Dokumen Fisik", use_container_width=True, type="primary"):
                st.success("Terkonfirmasi! Faktur masuk ke Antrean Packing.")
    
    st.divider()
    
    # --- BAGIAN 2: ALUR PACKING & SERAH TERIMA (Langkah 5 - 9) ---
    st.markdown("### 🔄 Alur Operasional (Packing ➡️ Checker ➡️ Delivery)")
    t_packing, t_checker, t_serah = st.tabs([
        "📦 Tahap 1: Packing", "🔍 Tahap 2: Checker (Dwi)", "🤝 Tahap 3: Serah Terima Kurir"
    ])
    
    with t_packing:
        st.info("GUDANG: Centang kotak jika barang sudah siap dan masuk kardus.")
        df_packing = pd.DataFrame({
            "Selesai Packing": [False, False],
            "Waktu Tunggu": ["30 Menit 🟢", "10 Menit 🟢"],
            "No. Faktur": ["INV-001", "INV-002"],
            "Customer": ["Toko SinarKos", "Be Luv Cosmetic"]
        })
        st.data_editor(df_packing, column_config={"Selesai Packing": st.column_config.CheckboxColumn("Selesai Packing", default=False)}, hide_index=True, use_container_width=True, key="pack_edit")
        st.button("Teruskan ke Checker", key="btn_to_check")

    with t_checker:
        st.info("CHECKER (DWI): Cek kembali kesesuaian fisik barang dengan faktur.")
        df_checker = pd.DataFrame({
            "Barang Sesuai": [False],
            "No. Faktur": ["INV-003"],
            "Customer": ["Queen Store"],
            "Total Item": [15]
        })
        st.data_editor(df_checker, column_config={"Barang Sesuai": st.column_config.CheckboxColumn("Barang Sesuai", default=False)}, hide_index=True, use_container_width=True, key="check_edit")
        if st.button("✅ Konfirmasi Sudah Dipacking & Sesuai", type="primary", key="btn_checked"):
            st.success("Terkonfirmasi! Status berubah menjadi 'Siap Dipacking / Menunggu Delivery'.")

    with t_serah:
        st.info("KEPALA GUDANG: Pilih faktur dan serahkan fisik barangnya ke Kurir.")
        df_serah = pd.DataFrame({
            "Pilih": [True, False],
            "No. Faktur": ["INV-004", "INV-005"],
            "Customer": ["Rumah Kosmetik", "Toko Cantik"],
            "Pilih Kurir": ["BIMA", "JONATHAN"]
        })
        st.data_editor(df_serah, column_config={"Pilih": st.column_config.CheckboxColumn("Pilih", default=False), "Pilih Kurir": st.column_config.SelectboxColumn("Pilih Kurir", options=["BIMA", "JONATHAN", "TOMI"])}, hide_index=True, use_container_width=True, key="serah_edit")
        if st.button("🤝 Serahkan ke Delivery", type="primary"):
            st.success("Berhasil diserahkan! Faktur & Barang kini otomatis masuk ke aplikasi HP kurir (Status: Dibawa).")
    st.divider()
    st.markdown("### 📥 Serah Terima Balik dari Kurir")
    st.info("Kepala Gudang: Jika kurir sudah kembali, terima dokumen & barang retur (jika ada).")
    # Tabel untuk mengecek barang balik
    df_balik = pd.DataFrame({"No. Faktur": ["INV-004"], "Status Fisik": ["OK"], "Keterangan": ["Barang Kembali"]})
    st.dataframe(df_balik, use_container_width=True)
    if st.button("🔄 Terima Faktur & Barang Kembali dari Kurir", type="primary"):
        st.success("Dokumen diterima kembali. Faktur diteruskan ke Admin untuk Closing.")

def ui_operasional_driver():
    st.markdown("""
    <div style='background:#0f172a; padding:15px; border-radius:10px; color:white; text-align:center;'>
        <h2>🛵 Panel Kurir (Mobile Mode)</h2>
        <p>Halo, BIMA!</p>
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Dibawa", "5")
    c2.metric("✅ Terkirim", "3")
    c3.metric("🔙 Retur", "0")
    
    st.divider()
    st.write("**Tugas Pengiriman Anda Hari Ini:**")
    st.caption("Data di bawah ini otomatis muncul setelah Kepala Gudang menyerahkan faktur kepada Anda.")
    
    with st.container(border=True):
        # Indikator Status Dibawa
        st.markdown("<div style='background:#dbeafe; padding:5px; border-radius:5px; margin-bottom:10px; text-align:center;'><b style='color:#1e3a8a;'>Status: Dibawa 📦</b></div>", unsafe_allow_html=True)
        
        st.write("### Toko Rumah Kosmetik")
        st.caption("Faktur: INV-004 | Nilai: Rp 2.706.315")
        st.write("📍 Jl. Karya Wisata No. 12, Medan")
        
        col_m1, col_m2 = st.columns(2)
        col_m1.link_button("🗺️ Buka Google Maps", "https://maps.google.com/?q=3.585,98.660", use_container_width=True)
        col_m2.link_button("💬 Chat Toko", "https://wa.me/628111222333", use_container_width=True)
        
        st.markdown("---")
        st.write("**Upload Bukti Pengiriman (PoD):**")
        foto_pod = st.camera_input("Ambil Foto Toko / Penerima", key="cam_1")
        
        if foto_pod:
            st.success("📸 Foto berhasil ditangkap! Siap diunggah.")
            
        col_a, col_b = st.columns(2)
        col_a.button("✅ Konfirmasi Selesai Antar", key="btn_ok_1", use_container_width=True, type="primary")
        col_b.button("🔙 Laporkan Retur", key="btn_retur_1", use_container_width=True)
        # Tombol Retur dengan input alasan manual
        if st.button("🔙 Laporkan Retur", key="btn_retur_open"):
            st.session_state['show_retur_form'] = True
            
        if st.session_state.get('show_retur_form', False):
            st.warning("⚠️ Laporan Retur (Isi alasan di bawah):")
            alasan_retur = st.text_area("Alasan Retur / Tidak Terantar:", placeholder="Contoh: Toko tutup, pemilik sedang keluar kota...")
            catatan_tambahan = st.text_input("Catatan Tambahan:")
            if st.button("Kirim Laporan Retur"):
                st.success("Laporan retur berhasil dikirim ke Gudang.")
                st.session_state['show_retur_form'] = False

def main_dashboard():
    def get_color_achv(val):
        try:
            if val < 0.50: return '#ffcccc' 
            elif val < 0.85: return '#fff2cc' 
            else: return '#d1e7dd' 
        except:
            return ''

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
        # --- PENAMBAHAN ROUTING DASHBOARD ---
        app_mode = "Sales" # Default
        
        if st.session_state['role'] in ['manager', 'direktur']:
            st.markdown("---")
            st.write("### 🔀 Modul Aplikasi")
            app_mode = st.radio("Pilih Modul:", ["Dashboard Sales 📊", "Dashboard Operasional 🚚", "Panel Admin / Fakturis 🏢"])
        elif st.session_state['role'] == 'gudang':
            app_mode = "Gudang"
        elif st.session_state['role'] == 'driver':
            app_mode = "Driver"
        # ------------------------------------
        fast_mode = st.toggle("⚡ Mode Performa Tinggi", value=True, help="Membaca data dari memori (Cache). Matikan jika Anda baru saja menambah data di Google Sheets dan ingin sistem menarik data terbaru.")
        
        st.markdown("---")
        st.write("### 🎬 Mode Presentasi")
        is_presentation_mode = st.toggle("🔦 Aktifkan Sorotan Layar", value=False)
        
        if is_presentation_mode:
            components.html("""
            <script>
                const overlay = window.parent.document.createElement('div');
                overlay.id = 'presentation-spotlight';
                overlay.style.position = 'fixed';
                overlay.style.top = '0';
                overlay.style.left = '0';
                overlay.style.width = '100vw';
                overlay.style.height = '100vh';
                overlay.style.pointerEvents = 'none';
                overlay.style.zIndex = '99998';
                overlay.style.background = 'radial-gradient(circle 250px at 50vw 50vh, transparent 0%, rgba(0, 0, 0, 0.8) 100%)';
                
                const existing = window.parent.document.getElementById('presentation-spotlight');
                if (existing) existing.remove();
                window.parent.document.body.appendChild(overlay);

                window.parent.document.addEventListener('mousemove', function(e) {
                    overlay.style.background = `radial-gradient(circle 250px at ${e.clientX}px ${e.clientY}px, transparent 0%, rgba(0, 0, 0, 0.8) 100%)`;
                });
            </script>
            """, height=0, width=0)
        else:
            components.html("""
            <script>
                const existing = window.parent.document.getElementById('presentation-spotlight');
                if (existing) existing.remove();
            </script>
            """, height=0, width=0)

        if st.session_state['role'] in ['manager', 'direktur']:
            st.markdown("---")
            with st.expander("🔐 Admin Zone", expanded=False):
                token_hari_ini = generate_daily_token()
                st.write(f"**Token Master:** `{token_hari_ini}`")
                
                target_sales = st.text_input("Nama Sales (Generate QR)", placeholder="Ketik nama (mis: Wira)...")
                if target_sales:
                    users_df = load_users()
                    if target_sales in users_df['username'].values:
                        user_record = users_df[users_df['username'] == target_sales].iloc[0]
                        current_secret = user_record.get('secret_key', None)
                        if pd.isna(current_secret) or current_secret == "" or current_secret is None:
                            current_secret = pyotp.random_base32()
                            save_user_secret(target_sales, current_secret)
                            st.success(f"Secret Key Dibuat!")
                        uri = pyotp.totp.TOTP(current_secret).provisioning_uri(name=user_record['sales_name'], issuer_name="Distributor App")
                        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={uri}"
                        st.image(qr_url, width=150)
                    else: st.error("Username tidak ditemukan.")
                
                if st.button("🔄 Force Sync Database", use_container_width=True):
                    st.cache_data.clear() 
                    if os.path.exists("master_database_penjualan.parquet"):
                        os.remove("master_database_penjualan.parquet") 
                    st.success("Tersinkronisasi!")
                    time.sleep(1)
                    st.rerun()
            
        if st.button("🚪 Logout", use_container_width=True):
            log_activity(st.session_state['sales_name'], "LOGOUT")
            st.session_state['logged_in'] = False
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        st.markdown("---")
        # --- PENCEGAT (INTERCEPT) UNTUK MENAMPILKAN UI OPERASIONAL ---
    if app_mode == "Dashboard Operasional 🚚":
        ui_operasional_manager()
        return  
    elif app_mode == "Panel Admin / Fakturis 🏢":
        ui_operasional_admin()
        return
    elif app_mode == "Gudang":
        ui_operasional_gudang()
        return
    elif app_mode == "Driver":
        ui_operasional_driver()
        return
    # -------------------------------------------------------------
            
    df = load_data(fast_mode)
    if df is None or df.empty:
        st.error("⚠️ Gagal memuat data! Periksa koneksi internet atau Link CSV Google Sheet Anda.")
        return

    user_role = st.session_state['role']
    user_name = st.session_state['sales_name']
    role = user_role
    my_name = user_name
    my_name_key = my_name.strip().upper()
    
    is_supervisor_account = my_name_key in TARGET_DATABASE
    
    if role in ['manager', 'direktur'] or my_name.lower() == 'fauziah':
        sales_list = ["SEMUA"] + sorted(list(df['Penjualan'].dropna().astype(str).unique()))
        brands_list = sorted(df['Merk'].dropna().astype(str).unique())
        outlets_list = sorted(df['Nama Outlet'].dropna().astype(str).unique())
    elif is_supervisor_account:
        my_brands = TARGET_DATABASE[my_name_key].keys()
        df_spv_raw = df[df['Merk'].isin(my_brands)]
        sales_list = ["SEMUA"] + sorted(list(df_spv_raw['Penjualan'].dropna().astype(str).unique()))
        brands_list = sorted(df_spv_raw['Merk'].dropna().astype(str).unique())
        outlets_list = sorted(df_spv_raw['Nama Outlet'].dropna().astype(str).unique())
    else:
        sales_list = [my_name]
        df_sales_raw = df[df['Penjualan'] == my_name]
        brands_list = sorted(df_sales_raw['Merk'].dropna().astype(str).unique())
        outlets_list = sorted(df_sales_raw['Nama Outlet'].dropna().astype(str).unique())

    today = datetime.date.today()
    if 'start_date' not in st.session_state:
        st.session_state['start_date'] = df['Tanggal'].max().date().replace(day=1)
        st.session_state['end_date'] = df['Tanggal'].max().date()
        
    st.title("🚀 Executive Dashboard")
    st.markdown("---")

    st.markdown("### 🌐 Filter Ruang Lingkup (Hierarki IJL)")
    list_ijl = ["IJL", "LISMAN", "AKBAR", "MADONG"]
    selected_ijl = st.selectbox("Pilih Ruang Lingkup Dashboard:", list_ijl, index=0)
        
    st.sidebar.markdown("### ⚙️ Panel Filter Executive")
    with st.sidebar.form("main_filter_form"):
        date_range = st.date_input("Rentang Waktu", [st.session_state['start_date'], st.session_state['end_date']])
        
        target_sales_filter = st.selectbox("Pantau Kinerja Sales / Tim:", sales_list)
        pilih_merk = st.multiselect("Filter Spesifik Merk:", brands_list)
        pilih_outlet = st.multiselect("Filter Spesifik Outlet:", outlets_list)
        
        submit_main_filter = st.form_submit_button("🚀 Terapkan Filter", use_container_width=True)

    df_scope_all = df.copy()

    if selected_ijl != "IJL":
        brands_in_ijl = TARGET_DATABASE[selected_ijl].keys()
        allowed_prefixes = []
        for b in brands_in_ijl:
            allowed_prefixes.extend(BRAND_PREFIXES.get(b, [b[:3].upper()]))
        allowed_prefixes = tuple(allowed_prefixes)
        
        mask_merk = df_scope_all['Merk'].isin(brands_in_ijl)
        mask_prefix = df_scope_all['Kode_Global'].astype(str).str.strip().str.upper().apply(lambda x: any(x.startswith(p) for p in allowed_prefixes))
        df_scope_all = df_scope_all[mask_merk | mask_prefix]

    if target_sales_filter != "SEMUA":
        df_scope_all = df_scope_all[df_scope_all['Penjualan'] == target_sales_filter]

    if pilih_merk:
        allowed_prefixes = []
        for b in pilih_merk:
            allowed_prefixes.extend(BRAND_PREFIXES.get(b, [b[:3].upper()]))
        allowed_prefixes = tuple(allowed_prefixes)
        
        mask_merk = df_scope_all['Merk'].isin(pilih_merk)
        mask_prefix = df_scope_all['Kode_Global'].astype(str).str.strip().str.upper().apply(lambda x: any(x.startswith(p) for p in allowed_prefixes))
        df_scope_all = df_scope_all[mask_merk | mask_prefix]

    if pilih_outlet:
        df_scope_all = df_scope_all[df_scope_all['Nama Outlet'].isin(pilih_outlet)]

    if len(date_range) == 2:
        start_date, end_date = date_range
        df_active = df_scope_all[(df_scope_all['Tanggal'].dt.date >= start_date) & (df_scope_all['Tanggal'].dt.date <= end_date)]
        ref_date = end_date
    else:
        df_active = df_scope_all
        start_date = df_scope_all['Tanggal'].min().date() if not df_scope_all.empty else today
        end_date = df_scope_all['Tanggal'].max().date() if not df_scope_all.empty else today
        ref_date = end_date

    df_active_tab = df_active.copy()

    current_omset_total = df_active['Jumlah'].sum()
    
    if len(date_range) == 2:
        try:
            prev_start = start_date.replace(month=start_date.month - 1) if start_date.month > 1 else start_date.replace(year=start_date.year - 1, month=12)
            prev_end = end_date.replace(month=end_date.month - 1) if end_date.month > 1 else end_date.replace(year=end_date.year - 1, month=12)
        except ValueError:
            prev_start = start_date - datetime.timedelta(days=30)
            prev_end = end_date - datetime.timedelta(days=30)
            
        omset_prev_period = df_scope_all[(df_scope_all['Tanggal'].dt.date >= prev_start) & (df_scope_all['Tanggal'].dt.date <= prev_end)]['Jumlah'].sum()
        delta_val = current_omset_total - omset_prev_period
        delta_label = f"vs {prev_start.strftime('%d %b')} - {prev_end.strftime('%d %b')}"
    else:
        prev_date = ref_date - datetime.timedelta(days=1)
        omset_prev_period = df_scope_all[df_scope_all['Tanggal'].dt.date == prev_date]['Jumlah'].sum()
        delta_val = current_omset_total - omset_prev_period
        delta_label = f"vs {prev_date.strftime('%d %b')}"

    c1, c2, c3 = st.columns(3)
    
    delta_str = format_idr(abs(delta_val))
    if delta_val < 0: delta_html = f"<span style='color: #f39c12; font-weight: bold; font-size: 14px;'>▼ - {delta_str} ({delta_label})</span>"
    elif delta_val > 0: delta_html = f"<span style='color: #2ecc71; font-weight: bold; font-size: 14px;'>▲ + {delta_str} ({delta_label})</span>"
    else: delta_html = f"<span style='color: #95a5a6; font-weight: bold; font-size: 14px;'>▬ {delta_str} ({delta_label})</span>"

    c1.markdown(f"""
    <div style="padding: 0px 0px;">
        <p style="margin:0; font-size: 18px; font-weight: 600; color: inherit; padding-bottom: 0.25rem;">💰 Total Omset (Periode)</p>
        <div style="font-size: 36px; font-weight: bold; color: inherit; line-height: 1.2;">{format_idr(current_omset_total)}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)
    
    c2.metric("🏪 Outlet Aktif", f"{df_active['Nama Outlet'].nunique()}")
    
    if 'No Faktur' in df_active.columns:
        valid_faktur = df_active['No Faktur'].astype(str)
        valid_faktur = valid_faktur[~valid_faktur.isin(['nan', 'None', '', '-', '0', 'None', '.'])]
        valid_faktur = valid_faktur[valid_faktur.str.len() > 2]
        transaksi_count = valid_faktur.nunique()
    else: transaksi_count = len(df_active)
        
    c3.metric("🧾 Transaksi", f"{transaksi_count}")

    if role in ['manager', 'direktur'] or is_supervisor_account or target_sales_filter in INDIVIDUAL_TARGETS or target_sales_filter.upper() in TARGET_DATABASE:
        st.markdown("### 🎯 Target Monitor")
        if target_sales_filter == "SEMUA":
            if selected_ijl != "IJL":
                target_val = sum(TARGET_DATABASE[selected_ijl].values())
                title = f"🏢 Target {selected_ijl}"
            else:
                target_val = TARGET_NASIONAL_VAL
                title = "🏢 Target Nasional (All Team)"
            
            realisasi = df_active['Jumlah'].sum()
            render_custom_progress(title, realisasi, target_val)
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
        st.markdown("---")

    t1, t2, t_detail_sales, t3, t5, t_forecast, t4 = st.tabs(["📊 Rapor Brand", "📈 Tren Harian", "👥 Detail Tim", "🏆 Top Produk", "🚀 Kejar Omset", "🔮 Prediksi Omset", "📋 Data Rincian"])
    
    with t1:
        if role in ['manager', 'direktur'] or my_name.lower() == 'fauziah': loop_source = TARGET_DATABASE.items()
        elif is_supervisor_account: loop_source = {my_name_key: TARGET_DATABASE[my_name_key]}.items()
        else: loop_source = None

        if loop_source and (target_sales_filter == "SEMUA" or target_sales_filter.upper() in TARGET_DATABASE):
            st.subheader(f"🏆 Ranking Brand & Detail Sales {('- ' + selected_ijl) if selected_ijl != 'IJL' else ''}")
            
            dict_mtd_brand = df_active_tab.groupby('Merk')['Jumlah'].sum().to_dict() if not df_active_tab.empty else {}
            
            def get_salesmen_dict(df_to_group):
                res = {}
                if not df_to_group.empty:
                    grouped = df_to_group.groupby(['Merk', 'Penjualan'])['Jumlah'].sum()
                    for (b, s), val in grouped.items():
                        if val > 0:
                            if b not in res: res[b] = {}
                            res[b][s] = val
                return res
                
            salesmen_mtd_master = get_salesmen_dict(df_active_tab)
            
            temp_grouped_data = [] 
            for spv, brands_dict in loop_source:
                if selected_ijl != "IJL" and spv != selected_ijl:
                    continue
                    
                for brand, target in brands_dict.items():
                    realisasi_brand = dict_mtd_brand.get(brand, 0.0) 
                    pct_brand = (realisasi_brand / target * 100) if target > 0 else 0
                    brand_row = {
                        "Rank": 0, "Brand / Salesman": brand, "Supervisor": spv, "Target": format_idr(target),
                        "Realisasi": format_idr(realisasi_brand), "Ach (%)": f"{pct_brand:.0f}%",
                        "Bar": pct_brand / 100, "Progress (Detail %)": pct_brand / 100 
                    }
                    sales_rows_list = []
                    
                    salesmen_for_this_brand = salesmen_mtd_master.get(brand, {})
                    for s_name, s_targets in INDIVIDUAL_TARGETS.items():
                        if brand in s_targets:
                            t_indiv = s_targets[brand]
                            r_indiv = salesmen_for_this_brand.get(s_name, 0.0)
                            pct_indiv = (r_indiv / t_indiv * 100) if t_indiv > 0 else 0
                            sales_rows_list.append({
                                "Rank": "", "Brand / Salesman": f"   └─ {s_name}", "Supervisor": "", 
                                "Target": format_idr(t_indiv), "Realisasi": format_idr(r_indiv),
                                "Ach (%)": f"{pct_indiv:.0f}%", "Bar": pct_indiv / 100,
                                "Progress (Detail %)": pct_indiv / 100 
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
                    val = row['Progress (Detail %)']
                    bg_color = get_color_achv(val)
                    if row["Supervisor"]: 
                        return [f'background-color: {bg_color}; color: black; font-weight: bold; border-top: 2px solid white'] * len(row)
                    else: 
                        return [f'background-color: {bg_color}; color: #333; opacity: 0.9; border-bottom: 1px solid #eee'] * len(row)
                        
                st.dataframe(
                    df_summ.style.apply(style_rows, axis=1).hide(axis="columns", subset=['Progress (Detail %)']),
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Rank": st.column_config.TextColumn("🏆 Rank", width="small"),
                        "Brand / Salesman": st.column_config.TextColumn("Brand / Salesman", width="medium"),
                        "Bar": st.column_config.ProgressColumn("Progress", format=" ", min_value=0, max_value=1)
                    }
                )
            else: st.warning("Tidak ada data untuk ditampilkan pada ruang lingkup ini.")
        elif target_sales_filter in INDIVIDUAL_TARGETS: st.info("Lihat progress bar di atas untuk detail target individu.")
        else:
            sales_brands = df_active_tab['Merk'].unique()
            indiv_data = []
            dict_mtd_brand = df_active_tab.groupby('Merk')['Jumlah'].sum().to_dict() if not df_active_tab.empty else {}
            for brand in sales_brands:
                owner, target = "-", 0
                for spv, b_dict in TARGET_DATABASE.items():
                    if brand in b_dict: owner, target = spv, b_dict[brand]; break
                if target > 0:
                    real = dict_mtd_brand.get(brand, 0.0)
                    pct = (real/target)*100
                    indiv_data.append({"Brand": brand, "Owner": owner, "Target Tim": format_idr(target), "Kontribusi": format_idr(real), "Ach (%)": f"{pct:.1f}%", "Pencapaian": pct/100})
            if indiv_data: 
                df_indiv = pd.DataFrame(indiv_data).sort_values("Kontribusi", ascending=False)
                def style_indiv(row):
                    val = row['Pencapaian']
                    bg = get_color_achv(val)
                    return [f'background-color: {bg}; color: black;' if col == 'Ach (%)' else '' for col in row.index]
                st.dataframe(df_indiv.style.apply(style_indiv, axis=1), use_container_width=True, hide_index=True, column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)})
            else: st.warning("Tidak ada data target brand.")

    with t2:
        st.subheader("📈 Tren Harian")
        if not df_active_tab.empty:
            daily = df_active_tab.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig_line = px.line(daily, x='Tanggal', y='Jumlah', markers=True)
            fig_line.update_traces(line_color='#2980b9', line_width=3)
            st.plotly_chart(fig_line, use_container_width=True)

    with t_detail_sales:
        st.subheader("👥 Detail Sales Team per Brand")
        allowed_brands = []
        if role in ['manager', 'direktur']:
            for spv_brands in TARGET_DATABASE.values(): allowed_brands.extend(spv_brands.keys())
        elif is_supervisor_account: allowed_brands = list(TARGET_DATABASE[my_name_key].keys())
        
        if selected_ijl != "IJL":
            allowed_brands = [b for b in allowed_brands if b in TARGET_DATABASE[selected_ijl].keys()]
            
        if allowed_brands:
            selected_brand_detail = st.selectbox("Pilih Brand untuk Detail Sales:", sorted(set(allowed_brands)))
            if selected_brand_detail:
                sales_stats = []
                total_brand_sales = 0
                total_brand_target = 0
                
                h_1_date = end_date - datetime.timedelta(days=1)
                last_day_of_month = calendar.monthrange(end_date.year, end_date.month)[1]
                remaining_workdays = 0
                for day_int in range(end_date.day, last_day_of_month + 1):
                    c_date = datetime.date(end_date.year, end_date.month, day_int)
                    if c_date.weekday() != 6 and c_date.strftime('%Y-%m-%d') not in HOLIDAYS_2026:
                        remaining_workdays += 1
                        
                safe_remaining_days = remaining_workdays if remaining_workdays > 0 else 1
                
                df_brand_active = df_active_tab[df_active_tab['Merk'] == selected_brand_detail]
                dict_sales_mtd = df_brand_active.groupby('Penjualan')['Jumlah'].sum().to_dict()
                
                df_brand_h1 = df_scope_all[(df_scope_all['Tanggal'].dt.date == h_1_date) & (df_scope_all['Merk'] == selected_brand_detail)]
                dict_sales_h1 = df_brand_h1.groupby('Penjualan')['Jumlah'].sum().to_dict()
                dict_toko_h1 = df_brand_h1.groupby('Penjualan')['Nama Outlet'].nunique().to_dict()
                dict_toko_mtd = df_brand_active.groupby('Penjualan')['Nama Outlet'].nunique().to_dict()
                
                for sales_name, targets in INDIVIDUAL_TARGETS.items():
                    if selected_brand_detail in targets:
                        t_pribadi = targets[selected_brand_detail]
                        real_sales = dict_sales_mtd.get(sales_name, 0.0)
                        omset_h1 = dict_sales_h1.get(sales_name, 0.0)
                        toko_h1 = dict_toko_h1.get(sales_name, 0)
                        total_toko_mtd = dict_toko_mtd.get(sales_name, 0)
                        
                        gap_sales = t_pribadi - real_sales
                        if gap_sales < 0:
                            gap_sales = 0
                            
                        target_harian = gap_sales / safe_remaining_days
                        
                        sales_stats.append({
                            "Nama Sales": sales_name, 
                            "Target Pribadi": format_idr(t_pribadi), 
                            "Realisasi": format_idr(real_sales),
                            "Ach %": f"{(real_sales/t_pribadi)*100:.1f}%" if t_pribadi > 0 else "0%", 
                            "Gap Sales": format_idr(gap_sales),
                            "Target Harian": format_idr(target_harian),
                            "Omset H-1": format_idr(omset_h1),
                            "Toko H-1": toko_h1, 
                            "Total Toko MTD": total_toko_mtd,
                            "_real": real_sales, "_target": t_pribadi
                        })
                        total_brand_sales += real_sales; total_brand_target += t_pribadi
                
                if sales_stats:
                    df_sales_stats = pd.DataFrame(sales_stats).drop(columns=["_real", "_target"])
                    def style_sales_stats(row):
                        try: val = float(row['Ach %'].replace('%', '')) / 100
                        except: val = 0
                        bg = get_color_achv(val)
                        return [f'background-color: {bg}; color: black;' if col == 'Ach %' else '' for col in row.index]
                    
                    st.dataframe(df_sales_stats.style.apply(style_sales_stats, axis=1), use_container_width=True)
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric(f"Total Target {selected_brand_detail}", format_idr(total_brand_target))
                    m2.metric(f"Total Omset {selected_brand_detail}", format_idr(total_brand_sales))
                    ach_total = (total_brand_sales/total_brand_target)*100 if total_brand_target > 0 else 0
                    m3.metric("Total Ach %", f"{ach_total:.1f}%")
                else: st.info(f"Belum ada data target sales individu untuk brand {selected_brand_detail}")
        else: st.info("Menu ini khusus untuk melihat detail tim sales per brand.")

    with t3:
        st.subheader("📊 Pareto Analysis (80/20 Rule)")
        selected_brand_t3 = st.selectbox("Pilih Brand (Filter Top Produk & Outlet):", ["SEMUA"] + sorted(df_active_tab['Merk'].dropna().astype(str).unique()))
        df_t3 = df_active_tab if selected_brand_t3 == "SEMUA" else df_active_tab[df_active_tab['Merk'] == selected_brand_t3]

        st.caption("Produk yang berkontribusi terhadap 80% dari total omset.")
        
        grouped_barang = df_t3.groupby('Nama Barang')['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=False)
        total_omset_pareto = grouped_barang['Jumlah'].sum()
        
        if total_omset_pareto > 0:
            pareto_df = grouped_barang.copy()
            pareto_df['Kontribusi %'] = (pareto_df['Jumlah'] / total_omset_pareto) * 100
            pareto_df['Cumulative %'] = pareto_df['Kontribusi %'].cumsum()
            
            top_performers = pareto_df[pareto_df['Cumulative %'] <= 80].copy()
            top_performers.insert(0, '🏆 Rank', range(1, len(top_performers) + 1))
            
            col_pareto1, col_pareto2 = st.columns(2)
            col_pareto1.metric("Total SKU Terjual", len(pareto_df))
            col_pareto2.metric("Produk Kontributor Utama (80%)", len(top_performers))
            
            st.dataframe(
                top_performers[['🏆 Rank', 'Nama Barang', 'Jumlah', 'Kontribusi %']].style.format({'Jumlah': 'Rp {:,.0f}', 'Kontribusi %': '{:.2f}%'}),
                use_container_width=True, hide_index=True
            )
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📦 Top 10 Produk")
            top_prod = grouped_barang.head(10).copy() if not grouped_barang.empty else pd.DataFrame(columns=['Nama Barang', 'Jumlah'])
            fig_bar = px.bar(top_prod, x='Jumlah', y='Nama Barang', orientation='h', text_auto='.2s')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            st.subheader("🏪 Top 10 Outlet")
            top_out = df_t3.groupby('Nama Outlet')['Jumlah'].sum().nlargest(10).reset_index()
            fig_out = px.bar(top_out, x='Jumlah', y='Nama Outlet', orientation='h', text_auto='.2s', color_discrete_sequence=['#2980b9'])
            fig_out.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_out, use_container_width=True)
            
    with t5:
        st.subheader("🚀 Kejar Omset (Actionable Insights)")
        st.write("#### 🚨 Toko Tidur (Potensi Hilang)")
        st.caption("Toko yang bertransaksi di masa lalu tetapi TIDAK bertransaksi di periode yang dipilih.")
        
        all_outlets = df_scope_all['Nama Outlet'].unique()
        active_outlets = df_active_tab['Nama Outlet'].unique()
        sleeping_outlets = list(set(all_outlets) - set(active_outlets))
        
        if sleeping_outlets:
            st.warning(f"Ada {len(sleeping_outlets)} toko yang belum order di periode ini.")
            with st.expander("Lihat Daftar Toko Tidur"):
                last_trx = []
                sleeping_df = df_scope_all[df_scope_all['Nama Outlet'].isin(sleeping_outlets)]
                last_dates = sleeping_df.groupby('Nama Outlet')['Tanggal'].max()
                sales_handlers = sleeping_df.groupby('Nama Outlet')['Penjualan'].first()
                
                today_date = datetime.date.today()
                
                for outlet in sleeping_outlets:
                    last_date = last_dates.get(outlet, pd.to_datetime('2000-01-01'))
                    sales_handler = sales_handlers.get(outlet, "-")
                    
                    if last_date.year == 2000:
                        terakhir_order_str = "Belum Pernah Order (Toko Master)"
                        hari_sejak = 99999
                    else:
                        terakhir_order_str = last_date.strftime('%d %b %Y')
                        hari_sejak = (today_date - last_date.date()).days
                        
                    last_trx.append({"Nama Toko": outlet, "Sales": sales_handler, "Terakhir Order": terakhir_order_str, "Hari Sejak Order Terakhir": hari_sejak})
                
                df_sleeping = pd.DataFrame(last_trx).sort_values("Hari Sejak Order Terakhir")
                df_sleeping["Hari Sejak Order Terakhir"] = df_sleeping["Hari Sejak Order Terakhir"].replace(99999, "Baru/Master")
                st.dataframe(df_sleeping, use_container_width=True)
        else: st.success("Semua toko langganan sudah order di periode ini.")

        st.divider()
        st.write("#### 💎 Peluang Cross-Selling (White Space Analysis)")
        
        relevant_brands = df_active_tab['Merk'].dropna().astype(str).unique()
        
        if len(relevant_brands) > 1:
            col_cs1, col_cs2 = st.columns(2)
            with col_cs1: brand_acuan = st.selectbox("Jika Toko sudah beli Brand:", sorted(relevant_brands), index=0)
            with col_cs2:
                target_options = [b for b in relevant_brands if b != brand_acuan]
                brand_target = st.selectbox("Tapi BELUM beli Brand:", sorted(target_options), index=0 if target_options else None)
            if brand_target:
                outlets_buy_acuan = df_active_tab[df_active_tab['Merk'] == brand_acuan]['Nama Outlet'].unique()
                opportunities = []
                for outlet in outlets_buy_acuan:
                    check = df_active_tab[(df_active_tab['Nama Outlet'] == outlet) & (df_active_tab['Merk'] == brand_target)]
                    if check.empty:
                        sales_name = df_active_tab[df_active_tab['Nama Outlet'] == outlet]['Penjualan'].iloc[0]
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
        
        st.divider()
        st.write("#### 🗺️ Master Visit Plan (Fokus 80/20 Customer Priority)")
        st.caption("Tabel interaktif (bisa dicentang/diedit). Terapkan **5 Step Sales Visit**, **Consultative Selling**, dan **Fast Follow Up** pada toko-toko penyumbang 80% omset ini.")
        
        mvp_df = df_active_tab.groupby(['Nama Outlet'])['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=False)
        total_mvp_omset = mvp_df['Jumlah'].sum()
        if total_mvp_omset > 0:
            mvp_df['Cum %'] = (mvp_df['Jumlah'] / total_mvp_omset).cumsum() * 100
            top_outlets_mvp = mvp_df[mvp_df['Cum %'] <= 80].copy()
            
            sales_dict = df_active_tab.groupby('Nama Outlet')['Penjualan'].first().to_dict()
            top_outlets_mvp['Salesman'] = top_outlets_mvp['Nama Outlet'].map(sales_dict)
            
            top_outlets_mvp.insert(0, 'Prioritas', range(1, len(top_outlets_mvp) + 1))
            top_outlets_mvp['📍 Route Plan (Hari)'] = ""
            top_outlets_mvp['📋 5-Step Visit Done'] = False
            top_outlets_mvp['💡 Consultative Action'] = "Cek Stok & Penawaran Baru"
            top_outlets_mvp['🚀 Follow Up Done'] = False
            
            top_outlets_mvp['Omset Historis'] = top_outlets_mvp['Jumlah'].apply(format_idr)
            
            st.info(f"🎯 Ditemukan **{len(top_outlets_mvp)} Toko Prioritas Utama** yang mewakili 80% omset Anda. Jadikan daftar ini sebagai panduan rute harian!")
            
            st.data_editor(
                top_outlets_mvp[['Prioritas', 'Nama Outlet', 'Salesman', 'Omset Historis', '📍 Route Plan (Hari)', '📋 5-Step Visit Done', '💡 Consultative Action', '🚀 Follow Up Done']],
                use_container_width=True,
                hide_index=True,
                disabled=['Prioritas', 'Nama Outlet', 'Salesman', 'Omset Historis'], 
                column_config={
                    "Jumlah": st.column_config.NumberColumn("Omset Historis", format="Rp %d"),
                    "📍 Route Plan (Hari)": st.column_config.SelectboxColumn("Pilih Hari Kunjungan", options=["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"], required=True),
                }
            )
        else:
            st.info("Belum ada data transaksi yang cukup untuk membuat Master Visit Plan.")
            
    with t_forecast:
        st.subheader("🔮 Prediksi Omset (Forecasting)")
        st.info("Prediksi tren omset 30 hari ke depan berdasarkan data historis harian.")
        
        df_forecast = df_scope_all[df_scope_all['Tanggal'].dt.year > 2000].groupby('Tanggal')['Jumlah'].sum().reset_index().sort_values('Tanggal')
        
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

        tab_pivot, tab_sku, tab_growth, tab_ba, tab_ai = st.tabs(["📊 Pivot Data Customer", "🛒 Detail SKU per Toko", "📈 Rekap Growth Brand", "🎯 Pencapaian Target BA", "🤖 AI Assistant (Gemini)"])
        
        with tab_pivot:
            render_pivot_fragment(df_scope_all, role)

        with tab_sku:
            st.markdown("### 🛒 Detail SKU per Toko")
            df_sku_base = df_scope_all.copy()
            
            list_merk_sku = sorted(df_sku_base['Merk'].dropna().astype(str).unique())
            list_merk_sku = [m for m in list_merk_sku if m != "-"]
            list_tahun_sku = sorted(df_sku_base['Tanggal'].dt.year.dropna().unique(), reverse=True)
            kd_asal = 'Kode_Global' if 'Kode_Global' in df_sku_base.columns else 'Kode Customer'
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                selected_merk_sku = st.selectbox("🎯 Pilih Merk:", ["SEMUA"] + list_merk_sku, key='merk_sku')
            with col_s2:
                selected_tahun_sku = st.multiselect("🗓️ Pilih Tahun:", list_tahun_sku, default=list_tahun_sku, key='tahun_sku')
                
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
                with col_f2: filter_nama_sku = st.multiselect("Nama Customer:", list_nama_all_sku, placeholder="Pilih Customer...")
                with col_f3: filter_provinsi_sku = st.multiselect("Provinsi:", list_provinsi_all_sku, placeholder="Pilih Provinsi...")
                with col_f4: filter_kota_sku = st.multiselect("Kota:", list_kota_all_sku, placeholder="Pilih Kota...")
                
                filter_sku_spesifik = st.multiselect("📦 Nama Barang (SKU):", list_sku_cascading, placeholder="Pilih SKU spesifik (Kosongkan untuk melihat semua)...")

                maximize_toggle_sku = st.toggle("🗖 Mode Layar Penuh (Tabel Super Lebar)", key='fs_sku')
                submit_button_sku = st.form_submit_button(label='🚀 Terapkan Filter (Super Cepat)', use_container_width=True)

            df_sku_filtered = df_sku_for_options.copy() 

            if selected_tahun_sku:
                df_sku_filtered = df_sku_filtered[df_sku_filtered['Tanggal'].dt.year.isin(selected_tahun_sku)]

            if filter_kode_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered[kd_asal].astype(str).isin(filter_kode_sku)]
            if filter_nama_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered['Nama Outlet'].astype(str).isin(filter_nama_sku)]
            if filter_provinsi_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered['Provinsi'].astype(str).isin(filter_provinsi_sku)]
            if filter_kota_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered['Kota'].astype(str).isin(filter_kota_sku)]
            if filter_sku_spesifik: df_sku_filtered = df_sku_filtered[df_sku_filtered['Nama Barang'].astype(str).isin(filter_sku_spesifik)]

            if not filter_nama_sku and not filter_sku_spesifik:
                st.info("👈 Silakan pilih minimal 1 'Nama Customer' ATAU 'Nama Barang (SKU)' di kotak pencarian atas lalu klik 'Terapkan Filter' untuk melihat detail transaksi.")
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
                        if i not in pivot_sku.columns: pivot_sku[i] = 0
                        
                    cols_sku = [display_col] + list(range(1, 13))
                    pivot_sku = pivot_sku[cols_sku]
                    pivot_sku.columns = [display_col] + [bulan_indo_map[i] for i in range(1, 13)]
                    
                    pivot_sku['Total Penjualan'] = pivot_sku[list(bulan_indo_map.values())].sum(axis=1)
                    
                    total_dict_sku = {col: "" for col in pivot_sku.columns}
                    total_dict_sku[display_col] = "GRAND TOTAL"
                    for col in [bulan_indo_map[i] for i in range(1, 13)] + ['Total Penjualan']:
                        total_dict_sku[col] = pivot_sku[col].sum()
                    
                    df_display_sku = pivot_sku.copy()
                    df_display_sku = df_display_sku.loc[:, ~df_display_sku.columns.duplicated()]
                    
                    df_display_sku[display_col] = df_display_sku[display_col].astype(str)
                    num_cols_sku = [bulan_indo_map[i] for i in range(1, 13)] + ['Total Penjualan']
                    for col in num_cols_sku:
                        if col in df_display_sku.columns:
                            df_display_sku[col] = pd.to_numeric(df_display_sku[col], errors='coerce').fillna(0).astype(float)
                    
                    df_display_sku_export = pd.concat([df_display_sku, pd.DataFrame([total_dict_sku])], ignore_index=True)
                    
                    # --- AGGRID FOR SKU TAB ---
                    if AGGRID_AVAILABLE:
                        gb_sku = GridOptionsBuilder.from_dataframe(df_display_sku)
                        
                        currency_formatter = JsCode("""
                        function(params) {
                            if (params.value === null || params.value === undefined || params.value === "") return '-';
                            var val = Number(params.value);
                            if (isNaN(val)) return params.value; 
                            return (val < 0 ? '-' : '') + 'Rp ' + Math.abs(val).toLocaleString('id-ID');
                        }
                        """)
                        
                        for col in df_display_sku.columns:
                            if col in num_cols_sku:
                                gb_sku.configure_column(col, type=["numericColumn"], headerClass="right-aligned-header", filter='agNumberColumnFilter', floatingFilter=True, valueFormatter=currency_formatter)
                            elif col == display_col:
                                gb_sku.configure_column(col, pinned='left', filter='agSetColumnFilter', floatingFilter=True)
                            else:
                                gb_sku.configure_column(col, filter='agSetColumnFilter', floatingFilter=True)
                        
                        gb_sku.configure_default_column(resizable=True, sortable=True)
                        
                        getRowHeightSKU = JsCode("""
                        function(params) {
                            if (params.node.rowPinned === 'bottom') return 45;
                            return 40;
                        }
                        """)
                        
                        gb_sku.configure_grid_options(
                            getRowHeight=getRowHeightSKU,
                            headerHeight=45,
                            floatingFiltersHeight=40,
                            pinnedBottomRowData=[total_dict_sku]
                        )
                        
                        getRowStyleSKU = JsCode("""
                        function(params) {
                            if (params.node.rowPinned === 'bottom') {
                                return { 'background-color': '#FFFF00 !important', 'font-weight': 'bold !important', 'color': 'black !important', 'border-top': '3px solid #333 !important' };
                    }
                            return null;
                        }
                        """)
                        gb_sku.configure_grid_options(getRowStyle=getRowStyleSKU)
                        
                        gridOptions_sku = gb_sku.build()
                        
                        custom_css_sku = {
                            ".ag-root-wrapper": {"font-family": "sans-serif !important"},
                            ".ag-header-cell-label": {"font-size": "14px !important", "color": "white !important", "font-weight": "bold !important"},
                            ".ag-header-cell": {"background-color": "#2980b9 !important", "border-right": "1px solid #555555 !important"},
                            ".ag-header": {"background-color": "#2980b9 !important", "border-bottom": "1px solid #555555 !important"},
                            ".ag-header-row-column-filter": {"background-color": "#2980b9 !important"},
                            ".ag-header .ag-icon": {"color": "white !important", "fill": "white !important"},
                            ".ag-cell": {"font-size": "14px !important", "font-weight": "500 !important", "color": "black !important", "background-color": "white !important", "border-right": "1px solid #555555 !important", "border-bottom": "1px solid #555555 !important", "display": "flex", "align-items": "center"},
                            ".ag-row-hover .ag-cell": {"background-color": "#e3f2fd !important"},
                            ".ag-floating-filter-input input": {"font-size": "13px !important", "background-color": "white !important", "color": "black !important", "border-radius": "3px !important", "padding": "2px 5px !important", "border": "1px solid #ccc !important"},
                            ".right-aligned-header .ag-header-cell-label": {"justify-content": "flex-end !important"},
                            ".ag-floating-bottom-container .ag-row, .ag-pinned-left-floating-bottom .ag-row": {"border-top": "3px solid #333 !important"},
                            ".ag-floating-bottom-container .ag-cell, .ag-pinned-left-floating-bottom .ag-cell": {
                                "font-size": "14px !important", "background-color": "#FFFF00 !important", "color": "black !important", "font-weight": "bold !important", "border-right": "none !important"
                            }
                        }
                        
                        try:
                            AgGrid(df_display_sku, gridOptions=gridOptions_sku, allow_unsafe_jscode=True, theme='balham', height=600, fit_columns_on_grid_load=False, custom_css=custom_css_sku, enable_enterprise_modules=True)
                        except Exception as e:
                            st.dataframe(df_display_sku_export, use_container_width=True)
                    else:
                        st.dataframe(df_display_sku_export, use_container_width=True)
                    
                    user_role_lower = role.lower()
                    if user_role_lower in ['direktur', 'manager', 'supervisor']:
                        output_sku = io.BytesIO()
                        with pd.ExcelWriter(output_sku, engine='xlsxwriter') as writer:
                            df_display_sku_export.to_excel(writer, index=False, sheet_name='Detail SKU')
                            workbook = writer.book
                            worksheet = writer.sheets['Detail SKU']
                            
                            user_identity = f"{st.session_state.get('sales_name', 'Unknown')} ({st.session_state.get('role', 'Unknown').upper()})"
                            time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            watermark_text = f"CONFIDENTIAL DOCUMENT | TRACKED USER: {user_identity} | DOWNLOADED: {time_stamp} | DO NOT DISTRIBUTE"
                            worksheet.set_header(f'&C&10{watermark_text}')
                            
                            format1 = workbook.add_format({'num_format': '#,##0'})
                            worksheet.set_column('B:N', None, format1)
                            bold_format = workbook.add_format({'bold': True, 'bg_color': '#f2f2f2', 'border': 1, 'num_format': '#,##0'})
                            worksheet.set_row(len(df_display_sku_export), None, bold_format)
                            
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
            
            # --- HELPER FUNCTION UNTUK RENDER AGGRID GROWTH ---
            def render_growth_aggrid(df_growth, total_dict_growth=None, pct_col=None, file_prefix="Growth", brand_name=""):
                if not AGGRID_AVAILABLE:
                    st.dataframe(pd.concat([df_growth, pd.DataFrame([total_dict_growth])] if total_dict_growth else [df_growth]), use_container_width=True)
                    return

                gb_growth = GridOptionsBuilder.from_dataframe(df_growth)
                currency_formatter = JsCode("""
                function(params) {
                    if (params.value === null || params.value === undefined || params.value === "") return '-';
                    var val = Number(params.value);
                    if (isNaN(val)) return params.value; 
                    return 'Rp ' + val.toLocaleString('id-ID');
                }
                """)
                pct_formatter = JsCode("""
                function(params) {
                    if (params.value === null || params.value === undefined || params.value === "") return '-';
                    var val = Number(params.value);
                    if (isNaN(val)) return params.value; 
                    return (val * 100).toFixed(1) + '%';
                }
                """)
                pct_cell_style = JsCode("""
                function(params) {
                    if (params.node.rowPinned === 'bottom') {
                        return { 'background-color': '#FFFF00', 'font-weight': 'bold', 'color': 'black', 'border-top': '3px solid #333', 'border-right': '1px solid #555555' };
                    }
                    var val = Number(params.value);
                    if (!isNaN(val)) {
                        if (val < 0.50) return { 'background-color': '#ffcccc', 'color': 'black', 'border-right': '1px solid #555555', 'border-bottom': '1px solid #555555', 'font-weight': '500' };
                        else if (val >= 0.50 && val < 0.85) return { 'background-color': '#fff2cc', 'color': 'black', 'border-right': '1px solid #555555', 'border-bottom': '1px solid #555555', 'font-weight': '500' };
                        else return { 'background-color': '#d1e7dd', 'color': 'black', 'border-right': '1px solid #555555', 'border-bottom': '1px solid #555555', 'font-weight': '500' };
                    }
                    return null;
                }
                """)

                for col in df_growth.columns:
                    if col == pct_col:
                        gb_growth.configure_column(col, valueFormatter=pct_formatter, cellStyle=pct_cell_style, headerClass="right-aligned-header", type=["numericColumn"])
                    elif 'SALES' in col.upper():
                        gb_growth.configure_column(col, valueFormatter=currency_formatter, headerClass="right-aligned-header", type=["numericColumn"])
                    else:
                        gb_growth.configure_column(col)

                gb_growth.configure_default_column(resizable=True, sortable=True)
                getRowHeightGrowth = JsCode("""
                function(params) {
                    if (params.node.rowPinned === 'bottom') return 45;
                    return 40;
                }
                """)
                grid_opts = { "getRowHeight": getRowHeightGrowth, "headerHeight": 45 }
                if total_dict_growth: grid_opts["pinnedBottomRowData"] = [total_dict_growth]
                gb_growth.configure_grid_options(**grid_opts)
                
                getRowStyleGrowth = JsCode("""
                function(params) {
                    if (params.node.rowPinned === 'bottom') {
                        return { 'background-color': '#FFFF00', 'font-weight': 'bold', 'color': 'black', 'border-top': '3px solid #333' };
                    }
                    return null;
                }
                """)
                gb_growth.configure_grid_options(getRowStyle=getRowStyleGrowth)
                
                custom_css_growth = {
                    ".ag-root-wrapper": {"font-family": "sans-serif !important"},
                    ".ag-header-cell-label": {"font-size": "14px !important", "color": "white !important", "font-weight": "bold !important"},
                    ".ag-header-cell": {"background-color": "#2980b9 !important", "border-right": "1px solid #555555 !important"},
                    ".ag-header": {"background-color": "#2980b9 !important", "border-bottom": "1px solid #555555 !important"},
                    ".ag-header-row-column-filter": {"background-color": "#2980b9 !important"},
                    ".ag-header .ag-icon": {"color": "white !important", "fill": "white !important"},
                    ".ag-cell": {"font-size": "14px !important", "font-weight": "500 !important", "color": "black !important", "background-color": "white !important", "border-right": "1px solid #555555 !important", "border-bottom": "1px solid #555555 !important", "display": "flex", "align-items": "center"},
                    ".ag-row-hover .ag-cell": {"background-color": "#e3f2fd !important"},
                    ".ag-floating-filter-input input": {"font-size": "13px !important", "background-color": "white !important", "color": "black !important", "border-radius": "3px !important", "padding": "2px 5px !important", "border": "1px solid #ccc !important"},
                    ".right-aligned-header .ag-header-cell-label": {"justify-content": "flex-end !important"},
                    ".ag-floating-bottom-container .ag-row, .ag-pinned-left-floating-bottom .ag-row": {"border-top": "3px solid #333 !important"},
                    ".ag-floating-bottom-container .ag-cell, .ag-pinned-left-floating-bottom .ag-cell": {
                        "font-size": "14px !important", "background-color": "#FFFF00 !important", "color": "black !important", "font-weight": "bold !important", "border-right": "none !important"
                    }
                }
                
                try:
                    AgGrid(df_growth, gridOptions=gb_growth.build(), allow_unsafe_jscode=True, theme='balham', height=460, fit_columns_on_grid_load=True, custom_css=custom_css_growth, enable_enterprise_modules=True)
                except Exception:
                    st.dataframe(pd.concat([df_growth, pd.DataFrame([total_dict_growth])] if total_dict_growth else [df_growth]), use_container_width=True)

                user_role_lower = st.session_state.get('role', 'staff').lower()
                if user_role_lower in ['direktur', 'manager', 'supervisor']:
                    df_export = pd.concat([df_growth, pd.DataFrame([total_dict_growth])], ignore_index=True) if total_dict_growth else df_growth.copy()
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_export.to_excel(writer, index=False, sheet_name=file_prefix[:30])
                        workbook = writer.book
                        worksheet = writer.sheets[file_prefix[:30]]
                        user_identity = f"{st.session_state.get('sales_name', 'Unknown')} ({st.session_state.get('role', 'Unknown').upper()})"
                        time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        watermark_text = f"CONFIDENTIAL DOCUMENT | TRACKED USER: {user_identity} | DOWNLOADED: {time_stamp} | DO NOT DISTRIBUTE"
                        worksheet.set_header(f'&C&10{watermark_text}')
                        
                        format1 = workbook.add_format({'num_format': '#,##0'})
                        format_pct = workbook.add_format({'num_format': '0.0%'})
                        
                        for col_num, col_name in enumerate(df_export.columns):
                            col_upper = col_name.upper()
                            if col_name in ['RO', 'AO', 'NOO']:
                                worksheet.set_column(col_num, col_num, 10, format1)
                            elif '%' in col_upper or 'GROWTH' in col_upper or 'ACHV' in col_upper:
                                worksheet.set_column(col_num, col_num, 12, format_pct)
                            elif col_upper not in ['MONTH', 'COSTUMER', 'YEAR', 'NAMA OUTLET']:
                                worksheet.set_column(col_num, col_num, 15, format1)
                            else:
                                worksheet.set_column(col_num, col_num, 20)
                        
                        if total_dict_growth:
                            bold_yellow = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'font_color': 'black', 'num_format': '#,##0'})
                            worksheet.set_row(len(df_export), 30, bold_yellow)
                            
                    today_str = datetime.date.today().strftime("%Y%m%d")
                    file_name_clean = re.sub(r'[^A-Za-z0-9_]', '_', f"{file_prefix}_{brand_name}_{today_str}") + ".xlsx"
                    st.download_button(label=f"📥 Download {file_prefix.replace('_', ' ')} (Excel)", data=output.getvalue(), file_name=file_name_clean, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # -----------------------------------------------------------------------------------------
            list_merk_growth = sorted(df['Merk'].dropna().astype(str).unique())
            list_merk_growth = [m for m in list_merk_growth if m != "-"]
            
            if list_merk_growth:
                brand_growth = st.selectbox("Pilih Brand untuk Analisis Growth:", list_merk_growth)
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
                        else: st.success("✅ Tidak ada nama toko yang kodenya ganda.")

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
                            'Year': 2026, 'Month': m, 'SALES': sales, 'RO': ro, 'AO': ao, 'AO VS RO %': ao_vs_ro, 'NOO': noo
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
                                    'MONTH': f"{bulan_dict_short[m]}-26", 'SALES': r['SALES'], 'RO': int(r['RO']), 'AO': int(r['AO']), 'AO VS RO %': r['AO VS RO %'], 'NOO': int(r['NOO'])
                                })
                            else: display_2026.append({'MONTH': f"{bulan_dict_short[m]}-26", 'SALES': 0.0, 'RO': 0, 'AO': 0, 'AO VS RO %': 0.0, 'NOO': 0})
                        
                        df_display_t1 = pd.DataFrame(display_2026)
                        render_growth_aggrid(df_display_t1, total_dict_growth=None, pct_col='AO VS RO %', file_prefix="Aktivitas_Outlet", brand_name=brand_growth)
                        
                        col_g1, col_g2 = st.columns(2)
                        df_2025 = df_team_all[df_team_all['Tahun'] == 2025] 
                        df_2026_sales = df_growth_all[df_growth_all['Year'] == 2026]
                        
                        # --- 2 FUNGSI YANG HILANG DIKEMBALIKAN KE SINI ---
                        def get_sales_2025(df_yr, m, brand_name):
                            res = df_yr[(df_yr['Bulan'] == m) & (df_yr['Merk'] == brand_name)]['Jumlah']
                            return res.sum() if not res.empty else 0
                            
                        def get_sales_2026(df_yr, m):
                            res = df_yr[df_yr['Month'] == m]['SALES']
                            return res.sum() if not res.empty else 0
                        
                        with col_g1:
                            st.write(f"#### **Tabel 2: {brand_growth} 2025 vs 2026 Sales Growth**")
                            yoy_data = []
                            tot_2025, tot_2026 = 0, 0
                            for m in range(1, 13):
                                s25 = get_sales_2025(df_2025, m, brand_growth)
                                s26 = get_sales_2026(df_2026_sales, m)
                                tot_2025 += s25
                                tot_2026 += s26
                                growth = ((s26 - s25) / s25) if s25 > 0 else (1 if s26 > 0 else 0)
                                yoy_data.append({
                                    'MONTH': bulan_dict_short[m], 'SALES 2025': float(s25), 'SALES 2026': float(s26), 'Growth MTM': float(growth)
                                })
                            df_t2 = pd.DataFrame(yoy_data)
                            tot_growth = ((tot_2026 - tot_2025) / tot_2025) if tot_2025 > 0 else (1 if tot_2026 > 0 else 0)
                            total_dict_t2 = {'MONTH': 'GRAND TOTAL', 'SALES 2025': float(tot_2025), 'SALES 2026': float(tot_2026), 'Growth MTM': float(tot_growth)}
                            render_growth_aggrid(df_t2, total_dict_growth=total_dict_t2, pct_col='Growth MTM', file_prefix="Sales_Growth", brand_name=brand_growth)
                        
                        with col_g2:
                            st.write(f"#### **Tabel 3: Quarterly Growth**")
                            q_data = []
                            for q, m_start in [('Q1', 1), ('Q2', 4), ('Q3', 7), ('Q4', 10)]:
                                m_end = m_start + 2
                                q_2025 = sum(get_sales_2025(df_2025, m, brand_growth) for m in range(m_start, m_end + 1))
                                q_2026 = sum(get_sales_2026(df_2026_sales, m) for m in range(m_start, m_end + 1))
                                q_growth = ((q_2026 - q_2025) / q_2025) if q_2025 > 0 else (1 if q_2026 > 0 else 0)
                                q_data.append({
                                    'MONTH': f"Total {q}", 'SALES 2025': float(q_2025), 'SALES 2026': float(q_2026), 'Growth MTM': float(q_growth)
                                })
                            df_q = pd.DataFrame(q_data)
                            render_growth_aggrid(df_q, total_dict_growth=total_dict_t2, pct_col='Growth MTM', file_prefix="Quarterly_Growth", brand_name=brand_growth)
                else: st.info(f"Belum ada data untuk brand {brand_growth}.")
            else: st.info("Tidak ada data.")

        with tab_ba:
            st.markdown("### 🎯 Pencapaian Target BA per Brand (Tahun 2026)")
            
            # --- HELPER FUNCTION UNTUK RENDER AGGRID BA ---
            def render_ba_aggrid(df_ba, total_dict_ba=None, file_prefix="Target_BA", brand_name=""):
                if not AGGRID_AVAILABLE:
                    st.dataframe(pd.concat([df_ba, pd.DataFrame([total_dict_ba])] if total_dict_ba else [df_ba]), use_container_width=True)
                    return

                gb_ba = GridOptionsBuilder.from_dataframe(df_ba)
                currency_formatter = JsCode("""
                function(params) {
                    if (params.value === null || params.value === undefined || params.value === "") return '-';
                    var val = Number(params.value);
                    if (isNaN(val)) return params.value; 
                    return 'Rp ' + val.toLocaleString('id-ID');
                }
                """)
                pct_formatter = JsCode("""
                function(params) {
                    if (params.value === null || params.value === undefined || params.value === "") return '-';
                    var val = Number(params.value);
                    if (isNaN(val)) return params.value; 
                    return (val * 100).toFixed(1) + '%';
                }
                """)
                pct_cell_style = JsCode("""
                function(params) {
                    if (params.node.rowPinned === 'bottom') {
                        return { 'background-color': '#FFFF00', 'font-weight': 'bold', 'color': 'black', 'border-top': '3px solid #333', 'border-right': '1px solid #555555' };
                    }
                    var val = Number(params.value);
                    if (!isNaN(val)) {
                        if (val < 0.50) return { 'background-color': '#ffcccc', 'color': 'black', 'border-right': '1px solid #555555', 'border-bottom': '1px solid #555555', 'font-weight': '500' };
                        else if (val >= 0.50 && val < 0.85) return { 'background-color': '#fff2cc', 'color': 'black', 'border-right': '1px solid #555555', 'border-bottom': '1px solid #555555', 'font-weight': '500' };
                        else return { 'background-color': '#d1e7dd', 'color': 'black', 'border-right': '1px solid #555555', 'border-bottom': '1px solid #555555', 'font-weight': '500' };
                    }
                    return null;
                }
                """)

                for col in df_ba.columns:
                    if col == 'ACHV':
                        gb_ba.configure_column(col, valueFormatter=pct_formatter, cellStyle=pct_cell_style, headerClass="right-aligned-header", type=["numericColumn"])
                    elif col != 'Costumer':
                        gb_ba.configure_column(col, valueFormatter=currency_formatter, headerClass="right-aligned-header", type=["numericColumn"])
                    else: gb_ba.configure_column(col, pinned='left', filter='agSetColumnFilter', floatingFilter=True)

                gb_ba.configure_default_column(resizable=True, sortable=True)
                getRowHeightBA = JsCode("""
                function(params) {
                    if (params.node.rowPinned === 'bottom') return 45;
                    return 40;
                }
                """)
                grid_opts = { "getRowHeight": getRowHeightBA, "headerHeight": 45, "floatingFiltersHeight": 40 }
                if total_dict_ba: grid_opts["pinnedBottomRowData"] = [total_dict_ba]
                gb_ba.configure_grid_options(**grid_opts)
                
                getRowStyleBA = JsCode("""
                function(params) {
                    if (params.node.rowPinned === 'bottom') {
                        return { 'background-color': '#FFFF00', 'font-weight': 'bold', 'color': 'black', 'border-top': '3px solid #333' };
                    }
                    return null;
                }
                """)
                gb_ba.configure_grid_options(getRowStyle=getRowStyleBA)
                
                custom_css_ba = {
                    ".ag-root-wrapper": {"font-family": "sans-serif !important"},
                    ".ag-header-cell-label": {"font-size": "14px !important", "color": "white !important", "font-weight": "bold !important"},
                    ".ag-header-cell": {"background-color": "#2980b9 !important", "border-right": "1px solid #555555 !important"},
                    ".ag-header": {"background-color": "#2980b9 !important", "border-bottom": "1px solid #555555 !important"},
                    ".ag-header-row-column-filter": {"background-color": "#2980b9 !important"},
                    ".ag-header .ag-icon": {"color": "white !important", "fill": "white !important"},
                    ".ag-cell": {"font-size": "14px !important", "font-weight": "500 !important", "color": "black !important", "background-color": "white !important", "border-right": "1px solid #555555 !important", "border-bottom": "1px solid #555555 !important", "display": "flex", "align-items": "center"},
                    ".ag-row-hover .ag-cell": {"background-color": "#e3f2fd !important"},
                    ".ag-floating-filter-input input": {"font-size": "13px !important", "background-color": "white !important", "color": "black !important", "border-radius": "3px !important", "padding": "2px 5px !important", "border": "1px solid #ccc !important"},
                    ".right-aligned-header .ag-header-cell-label": {"justify-content": "flex-end !important"},
                    ".ag-floating-bottom-container .ag-row, .ag-pinned-left-floating-bottom .ag-row": {"border-top": "3px solid #333 !important"},
                    ".ag-floating-bottom-container .ag-cell, .ag-pinned-left-floating-bottom .ag-cell": {
                        "font-size": "14px !important", "background-color": "#FFFF00 !important", "color": "black !important", "font-weight": "bold !important", "border-right": "none !important"
                    }
                }
                try:
                    AgGrid(df_ba, gridOptions=gb_ba.build(), allow_unsafe_jscode=True, theme='balham', height=460, fit_columns_on_grid_load=False, custom_css=custom_css_ba, enable_enterprise_modules=True)
                except Exception:
                    st.dataframe(pd.concat([df_ba, pd.DataFrame([total_dict_ba])] if total_dict_ba else [df_ba]), use_container_width=True)

                user_role_lower = st.session_state.get('role', 'staff').lower()
                if user_role_lower in ['direktur', 'manager', 'supervisor']:
                    df_export = pd.concat([df_ba, pd.DataFrame([total_dict_ba])], ignore_index=True) if total_dict_ba else df_ba.copy()
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_export.to_excel(writer, index=False, sheet_name=file_prefix[:30])
                        workbook = writer.book
                        worksheet = writer.sheets[file_prefix[:30]]
                        user_identity = f"{st.session_state.get('sales_name', 'Unknown')} ({st.session_state.get('role', 'Unknown').upper()})"
                        time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        watermark_text = f"CONFIDENTIAL DOCUMENT | TRACKED USER: {user_identity} | DOWNLOADED: {time_stamp} | DO NOT DISTRIBUTE"
                        worksheet.set_header(f'&C&10{watermark_text}')
                        
                        format1 = workbook.add_format({'num_format': '#,##0'})
                        format_pct = workbook.add_format({'num_format': '0.0%'})
                        
                        for col_num, col_name in enumerate(df_export.columns):
                            col_upper = col_name.upper()
                            if '%' in col_upper or 'ACHV' in col_upper:
                                worksheet.set_column(col_num, col_num, 12, format_pct)
                            elif col_upper not in ['COSTUMER']:
                                worksheet.set_column(col_num, col_num, 15, format1)
                            else: worksheet.set_column(col_num, col_num, 30)
                        
                        if total_dict_ba:
                            bold_yellow = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'font_color': 'black', 'num_format': '#,##0'})
                            worksheet.set_row(len(df_export), 30, bold_yellow)
                            
                    today_str = datetime.date.today().strftime("%Y%m%d")
                    file_name_clean = re.sub(r'[^A-Za-z0-9_]', '_', f"{file_prefix}_{brand_name}_{today_str}") + ".xlsx"
                    st.download_button(label=f"📥 Download {file_prefix.replace('_', ' ')} (Excel)", data=output.getvalue(), file_name=file_name_clean, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # -----------------------------------------------------------------------------------------
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
                        if m not in pivot_ba.columns: pivot_ba[m] = 0
                    pivot_ba = pivot_ba[list(range(1, 13))]
                    pivot_ba.columns = [bulan_dict_ba[m] for m in pivot_ba.columns]
                    pivot_ba = pivot_ba.reset_index().rename(columns={'Nama Outlet': 'Costumer'})
                    merged_ba = pd.merge(ba_df, pivot_ba, on='Costumer', how='left').fillna(0)
                else:
                    merged_ba = ba_df.copy()
                    for m in range(1, 13): merged_ba[bulan_dict_ba[m]] = 0
                
                st.write(f"**Rekap Keseluruhan Toko BA untuk Brand `{selected_ba_brand}` (2026)**")
                total_dict_ba1 = {col: "" for col in merged_ba.columns}
                total_dict_ba1['Costumer'] = "GRAND TOTAL"
                for col in list(bulan_dict_ba.values()) + ['Target BA']:
                    if col in merged_ba.columns: total_dict_ba1[col] = float(merged_ba[col].sum())
                render_ba_aggrid(merged_ba, total_dict_ba=total_dict_ba1, file_prefix="Rekap_Toko_BA", brand_name=selected_ba_brand)
                
                st.divider()
                selected_month_ba = st.selectbox(f"Pilih Bulan untuk Detail Achievement ({selected_ba_brand}):", list(bulan_dict_ba.values()))
                
                achv_data = []
                total_target, total_achv = 0, 0
                for idx, row in merged_ba.iterrows():
                    costumer = row['Costumer']
                    target = row['Target BA']
                    pencapaian = row[selected_month_ba]
                    achv_pct = (pencapaian / target) if target > 0 else 0
                    total_target += target
                    total_achv += pencapaian
                    
                    achv_data.append({
                        'Costumer': costumer, 'Target BA': target, f'Pencapaian {selected_month_ba}': pencapaian, 'ACHV': achv_pct
                    })
                df_achv = pd.DataFrame(achv_data)
                total_dict_ba2 = {
                    'Costumer': 'GRAND TOTAL', 'Target BA': total_target, f'Pencapaian {selected_month_ba}': total_achv, 'ACHV': (total_achv/total_target) if total_target > 0 else 0
                }
                st.write(f"**Tabel Pencapaian Target BA `{selected_ba_brand}` - {selected_month_ba} 2026**")
                render_ba_aggrid(df_achv, total_dict_ba=total_dict_ba2, file_prefix=f"Achv_BA_{selected_month_ba}", brand_name=selected_ba_brand)

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
                                    except Exception: continue 
                                
                                if response:
                                    st.success(f"Analisis Selesai! (Powered by {success_model})")
                                    st.write(response.text)
                                else: st.error("Gagal! API Key Anda tidak memiliki akses.")
                    except Exception as e: st.error(f"Koneksi gagal. Detail: {e}")

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if st.session_state['logged_in']: main_dashboard()
else: login_page()
