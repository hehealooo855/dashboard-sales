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

# --- AUTO LOGOUT (INACTIVITY TIMEOUT: 15 MENIT) ---
TIMEOUT_SECONDS = 900 
if 'last_activity' in st.session_state and st.session_state.get('logged_in', False):
    if time.time() - st.session_state['last_activity'] > TIMEOUT_SECONDS:
        st.session_state.clear()
        st.session_state['logged_out_due_to_inactivity'] = True
        st.rerun()
st.session_state['last_activity'] = time.time()

# Custom CSS & Tema Corporate Blue (Termasuk Hover Tabs)
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
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
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
    "Walnutt": ["WAL", "WLN"], "Elizabeth Rose": ["ELZ", "ELI"]
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
    "MADONG": { "Somethinc": 1_200_000_000, "SYB": 150_000_000, "Sekawan": 600_000_000, "Avione": 300_000_000, "Honor": 125_000_000, "Vlagio": 75_000_000, "Ren & R & L": 20_000_000, "Mad For Make Up": 25_000_000, "Satto": 500_000_000, "Mykonos": 20_000_000, "The Face": 600_000_000, "Yu Chun Mei": 450_000_000, "Milano": 50_000_000, "Remar": 0, "Walnutt": 30_000_000, "Elizabeth Rose": 50_000_000},
    "LISMAN": { "Javinci": 1_300_000_000, "Careso": 400_000_000, "Newlab": 150_000_000, "Gloow & Be": 130_000_000, "Dorskin": 20_000_000, "Whitelab": 150_000_000, "Bonavie": 50_000_000, "Goute": 50_000_000, "Mlen": 100_000_000, "Artist Inc": 130_000_000, "Maskit": 30_000_000, "Birth Beyond": 120_000_000},
    "AKBAR": { "Sociolla": 600_000_000, "Thai": 300_000_000, "Inesia": 100_000_000, "Y2000": 180_000_000, "Diosys": 520_000_000, "Masami": 40_000_000, "Cassandra": 50_000_000, "Clinelle": 80_000_000,"Beautica": 100_000_000, "Claresta": 350_000_000, "Rose All Day": 50_000_000, "OtwooO": 200_000_000}
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
    "Goute": ["GOUTE"], "Dorskin": ["DORSKIN"], "Javinci": ["JAVINCI"], "Madame G": ["MADAM", "MADAME"],
    "Careso": ["CARESO"], "Newlab": ["NEWLAB"], "Mlen": ["MLEN"], "Walnutt": ["WALNUT", "WALNUTT"],
    "Elizabeth Rose": ["ELIZABETH"], "OtwooO": ["OTWOOO", "O.TWO.O", "O TWO O"],
    "Saviosa": ["SAVIOSA"], "The Face": ["THE FACE", "THEFACE"], "Yu Chun Mei": ["YU CHUN MEI", "YCM"],
    "Milano": ["MILANO"], "Remar": ["REMAR"], "Beautica": ["BEAUTICA"], "Maskit": ["MASKIT"],
    "Claresta": ["CLARESTA"], "Birth Beyond": ["BIRTH"], "Rose All Day": ["ROSE ALL DAY"],
    "Everpure": ["EVERPURE"], "COSLINE": ["COSLINE"], "NAMA": ["NAMA"], "Rosanna": ["ROSANNA"], "Summer": ["SUMMER"]
}

SALES_MAPPING = {
    "WIRA VG": "WIRA", "WIRA - VG": "WIRA", "WIRA VLAGIO": "WIRA", "WIRA HONOR": "WIRA", "WIRA - HONOR": "WIRA", "WIRA HR": "WIRA", "WIRA SYB": "WIRA", "WIRA - SYB": "WIRA", "WIRA SOMETHINC": "WIRA", "PMT-WIRA": "WIRA", "WIRA ELIZABETH": "WIRA", "WIRA WALNUTT": "WIRA", "WIRA ELZ": "WIRA",
    "HAMZAH VG": "HAMZAH", "HAMZAH - VG": "HAMZAH", "HAMZAH HONOR": "HAMZAH", "HAMZAH - HONOR": "HAMZAH", "HAMZAH SYB": "HAMZAH", "HAMZAH AV": "HAMZAH", "HAMZAH AINIE": "HAMZAH", "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH", "HAMZA AV": "HAMZAH",
    "FERI VG": "FERI", "FERI - VG": "FERI", "FERI HONOR": "FERI", "FERI - HONOR": "FERI", "FERI THAI": "FERI", "FERI - INESIA": "FERI",
    "YOGI TF": "YOGI", "YOGI THE FACE": "YOGI", "YOGI YCM": "YOGI", "YOGI MILANO": "YOGI", "MILANO - YOGI": "YOGI", "YOGI REMAR": "YOGI",
    "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI", "GANI TF": "GANI", "GANI - YCM": "GANI", "GANI - MILANO": "GANI", "GANI - HONOR": "GANI", "GANI - VG": "GANI", "GANI - TH": "GANI", "GANI INESIA": "GANI", "GANI - KSM": "GANI", "SSL - GANI": "GANI", "GANI ELIZABETH": "GANI", "GANI WALNUTT": "GANI",
    "MITHA MASKIT": "MITHA", "MITHA RAD": "MITHA", "MITHA CLA": "MITHA", "MITHA OT": "MITHA", "MAS - MITHA": "MITHA", "SSL BABY - MITHA ": "MITHA", "SAVIOSA - MITHA": "MITHA", "MITHA ": "MITHA",
    "LYDIA KITO": "LYDIA", "LYDIA K": "LYDIA", "LYDIA BB": "LYDIA", "LYDIA - KITO": "LYDIA",
    "NOVI AINIE": "NOVI", "NOVI AV": "NOVI", "NOVI DAN RAFFI": "NOVI", "NOVI & RAFFI": "NOVI", "RAFFI": "NOVI", "RAFI": "NOVI", "RAPI": "NOVI", "RAPI AV":"NOVI",
    "ROZY AINIE": "ROZY", "ROZY AV": "ROZY",
    "DANI AINIE": "DANI", "DANI AV": "DANI", "DANI SEKAWAN": "DANI",
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
    "FAUZIAH CLA": "FAUZIAH", "FAUZIAH ST": "FAUZIAH", "MARIANA CLIN": "MARIANA", "JAYA - MARIANA": "MARIANA"
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
# CACHE & DATA LOADER
# =========================================================================
@st.cache_data(ttl=3600) 
def load_data_from_url():
    urls = [
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vSaGwT-qw0iz6kKhkwep4R5b-TWlegy8rHdBU3HcY_veP8KEsiLmKpCemC-D1VA2STstlCjA2VLUM-Q/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vT6KbuunLLoGQRSanRK_A8e5jgXcJ-FCZCEb8dr611HdJQi40dFr_HNMItnodJEwD7dKk7woC7Ud-DG/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vQyEgQMxR75QW7HYKbJov4WtNuZmghPAhMHeH-cI5Wem_NwIMuC95sqa8QzXh2p1DX-HxQSJGptz_xy/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBTn4hKKl-e9BFITUW2dYBsKfMbTBc-zrdn3qweQxzL_tiTr3FMi4cGE-17IrixYwg9T-4YugLcQdq/pub?output=csv",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vTVyv41klRlykXzW5wYo01y5a4HtplUEXVMpt05DzEO-ijxJ9T2Xk5Yiruv4uZW--QM0NIU3fnww_xX/pub?output=csv"  
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
# PIVOT FAST ENGINE
# =========================================================================
@st.cache_data(show_spinner=False)
def generate_pivot_fast(df_pivot_source, selected_merk_excel, selected_tahun_excel_tuple, group_cols_tuple, brand_prefixes_dict):
    group_cols = list(group_cols_tuple)
    master_pivot = pd.DataFrame()
    
    if not df_pivot_source.empty:
        if selected_merk_excel != "SEMUA":
            prefixes = brand_prefixes_dict.get(selected_merk_excel, [selected_merk_excel[:3].upper()])
            prefix_tuple = tuple(prefixes)
            
            mask_history = df_pivot_source['Merk'] == selected_merk_excel
            
            kd_col = None
            for col in ['Kode Customer', 'Kode Costumer', 'Kode Outlet', 'Kode_Global']:
                if col in df_pivot_source.columns:
                    kd_col = col
                    break
            
            if kd_col:
                mask_prefix = df_pivot_source[kd_col].astype(str).str.strip().str.upper().apply(lambda x: any(x.startswith(p) for p in prefix_tuple))
                final_mask = mask_history | mask_prefix
            else:
                final_mask = mask_history
                
            base_customers = df_pivot_source[final_mask][group_cols].drop_duplicates()
            df_excel = df_pivot_source[(mask_history) & (df_pivot_source['Tanggal'].dt.year.isin(selected_tahun_excel_tuple))].copy()
            
            if not df_excel.empty:
                df_excel['Bulan Angka'] = df_excel['Tanggal'].dt.month
                master_pivot = pd.pivot_table(df_excel, values='Jumlah', index=group_cols, columns='Bulan Angka', aggfunc='sum', fill_value=0).reset_index()
                master_pivot = pd.merge(base_customers, master_pivot, on=group_cols, how='left').fillna(0)
            else:
                master_pivot = base_customers.copy()
                for i in range(1, 13): master_pivot[i] = 0
        else:
            df_excel = df_pivot_source[df_pivot_source['Tanggal'].dt.year.isin(selected_tahun_excel_tuple)].copy()
            if not df_excel.empty:
                df_excel['Bulan Angka'] = df_excel['Tanggal'].dt.month
                master_pivot = pd.pivot_table(df_excel, values='Jumlah', index=group_cols, columns='Bulan Angka', aggfunc='sum', fill_value=0).reset_index()

    return master_pivot

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
    elif 'Nama Outlet' in df_scope_all.columns: grp_cols.append('Nama Outlet')
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
        cols_to_keep = grp_cols + list(range(1, 13))
        master_pivot = master_pivot[cols_to_keep]
        master_pivot.columns = grp_cols + [bulan_indo_map[i] for i in range(1, 13)]
        master_pivot['Total Penjualan'] = master_pivot[list(bulan_indo_map.values())].sum(axis=1)
        
        ren_dict = {'Kode_Global': 'Kode Customer'}
        for col in master_pivot.columns:
            c_low = str(col).lower()
            if 'nama' in c_low and 'barang' not in c_low and 'sales' not in c_low: ren_dict[col] = 'Nama Customer'
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
                iframe[title="streamlit_aggrid.agGrid"] {
                    position: fixed !important;
                    top: 0 !important; left: 0 !important;
                    width: 100vw !important; height: 100vh !important;
                    z-index: 999999 !important; background-color: white !important;
                }
                header {visibility: hidden !important;}
                [data-testid="stSidebar"] {display: none !important;}
            </style>
            """, unsafe_allow_html=True)

        if not df_filtered.empty:
            bulan_indo_list = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
            num_cols = bulan_indo_list + ['Total Penjualan']
            total_dict = {col: "" for col in df_filtered.columns}
            total_dict['Nama Customer'] = "GRAND TOTAL" 
            for col in num_cols:
                total_dict[col] = df_filtered[col].sum()
            df_display = pd.concat([df_filtered, pd.DataFrame([total_dict])], ignore_index=True)
        else:
            df_display = df_filtered.copy()

        if AGGRID_AVAILABLE:
            gb = GridOptionsBuilder.from_dataframe(df_display)
            gb.configure_pagination(enabled=False)
            gb.configure_side_bar()
            gb.configure_default_column(filter='agSetColumnFilter', sortable=True, resizable=True, floatingFilter=True, minWidth=160)
            
            for col in num_cols:
                gb.configure_column(col, type=["numericColumn","numberColumnFilter"], valueFormatter="x.toLocaleString('id-ID', {style: 'currency', currency: 'IDR', minimumFractionDigits: 0})")
            
            jscode = JsCode("""
            function(params) {
                if (params.data['Nama Customer'] === 'GRAND TOTAL') {
                    return {
                        'font-weight': 'bold',
                        'background-color': '#f8f9fa',
                        'border-top': '2px solid #2980b9'
                    }
                }
            }
            """)
            gb.configure_grid_options(getRowStyle=jscode, domLayout='autoHeight')
            gridOptions = gb.build()
            
            grid_css = {
                ".ag-header": {"background-color": "#2980b9 !important"},
                ".ag-header-cell": {"border-right": "1px solid #ffffff44 !important"},
                ".ag-header-cell-label": {"color": "#ffffff !important", "font-weight": "bold !important", "font-size": "14px !important"},
                ".ag-header-icon": {"color": "#ffffff !important"},
                ".ag-cell": {"border-right": "1px solid #e2e8f0 !important", "display": "flex", "align-items": "center"},
                ".ag-row-hover": {
                    "background-color": "#e3f2fd !important", 
                    "transition": "background-color 0.15s ease-in-out !important"
                },
                ".ag-floating-filter-button": {"filter": "brightness(0) invert(1)"}
            }
            
            AgGrid(
                df_display, 
                gridOptions=gridOptions, 
                enable_enterprise_modules=True, 
                theme='alpine', 
                allow_unsafe_jscode=True,
                custom_css=grid_css,
                update_mode='NO_UPDATE',
                data_return_mode='FILTERED_AND_SORTED'
            )
        else:
            format_dict = {col: "Rp {:,.0f}" for col in num_cols}
            st.dataframe(df_display.style.format(format_dict), use_container_width=True, hide_index=True)
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
        
    st.sidebar.markdown("### ⚙️ Panel Filter Executive")
    with st.sidebar.form("main_filter_form"):
        date_range = st.date_input("Rentang Waktu", [st.session_state['start_date'], st.session_state['end_date']])
        
        target_sales_filter = st.selectbox("Pantau Kinerja Sales / Tim:", sales_list)
        pilih_merk = st.multiselect("Filter Spesifik Merk:", brands_list)
        pilih_outlet = st.multiselect("Filter Spesifik Outlet:", outlets_list)
        
        submit_main_filter = st.form_submit_button("🚀 Terapkan Filter", use_container_width=True)

    if target_sales_filter == "SEMUA":
        if role in ['manager', 'direktur'] or my_name.lower() == 'fauziah':
            df_scope_all = df.copy()
        elif is_supervisor_account:
            my_brands = TARGET_DATABASE[my_name_key].keys()
            df_scope_all = df[df['Merk'].isin(my_brands)].copy()
        else:
            df_scope_all = df[df['Penjualan'] == my_name].copy()
    else:
        if target_sales_filter.upper() in TARGET_DATABASE:
            tim_sales_list = list(TARGET_DATABASE[target_sales_filter.upper()].keys())
            brands_of_spv = TARGET_DATABASE[target_sales_filter.upper()].keys()
            df_scope_all = df[df['Merk'].isin(brands_of_spv)].copy()
        else:
            df_scope_all = df[df['Penjualan'] == target_sales_filter].copy()

    if pilih_merk: df_scope_all = df_scope_all[df_scope_all['Merk'].isin(pilih_merk)]
    if pilih_outlet: df_scope_all = df_scope_all[df_scope_all['Nama Outlet'].isin(pilih_outlet)]

    if len(date_range) == 2:
        start_date, end_date = date_range
        df_active = df_scope_all[(df_scope_all['Tanggal'].dt.date >= start_date) & (df_scope_all['Tanggal'].dt.date <= end_date)]
        ref_date = end_date
    else:
        df_active = df_scope_all
        start_date = df_scope_all['Tanggal'].min().date() if not df_scope_all.empty else today
        end_date = df_scope_all['Tanggal'].max().date() if not df_scope_all.empty else today
        ref_date = end_date

    st.title("🚀 Executive Dashboard")
    st.markdown("---")
    
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
            realisasi_nasional = df[(df['Tanggal'].dt.date >= start_date) & (df['Tanggal'].dt.date <= end_date)]['Jumlah'].sum()
            render_custom_progress("🏢 Target Nasional (All Team)", realisasi_nasional, TARGET_NASIONAL_VAL)
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

    st.markdown("### 🌐 Filter Ruang Lingkup (Hierarki IJL)")
    list_ijl = ["SEMUA", "MADONG", "LISMAN", "AKBAR"]
    selected_ijl = st.selectbox("Pilih Ruang Lingkup untuk Dashboard Bawah:", list_ijl, index=0)

    df_active_tab = df_active.copy()
    if selected_ijl != "SEMUA":
        brands_in_ijl = TARGET_DATABASE[selected_ijl].keys()
        df_active_tab = df_active_tab[df_active_tab['Merk'].isin(brands_in_ijl)]

    t1, t2, t_detail_sales, t3, t5, t_forecast, t4 = st.tabs(["📊 Rapor Brand", "📈 Tren Harian", "👥 Detail Tim", "🏆 Top Produk", "🚀 Kejar Omset", "🔮 Prediksi Omset", "📋 Data Rincian"])
    
    with t1:
        if role in ['manager', 'direktur'] or my_name.lower() == 'fauziah': loop_source = TARGET_DATABASE.items()
        elif is_supervisor_account: loop_source = {my_name_key: TARGET_DATABASE[my_name_key]}.items()
        else: loop_source = None

        if loop_source and (target_sales_filter == "SEMUA" or target_sales_filter.upper() in TARGET_DATABASE):
            st.subheader(f"🏆 Ranking Brand & Detail Sales {('- ' + selected_ijl) if selected_ijl != 'SEMUA' else ''}")
            temp_grouped_data = [] 
            for spv, brands_dict in loop_source:
                if selected_ijl != "SEMUA" and spv != selected_ijl:
                    continue
                    
                for brand, target in brands_dict.items():
                    realisasi_brand = df_active_tab[df_active_tab['Merk'] == brand]['Jumlah'].sum()
                    pct_brand = (realisasi_brand / target * 100) if target > 0 else 0
                    brand_row = {
                        "Rank": 0, "Item": brand, "Supervisor": spv, "Target": format_idr(target),
                        "Realisasi": format_idr(realisasi_brand), "Ach (%)": f"{pct_brand:.0f}%",
                        "Bar": pct_brand / 100, "Progress (Detail %)": pct_brand / 100 
                    }
                    sales_rows_list = []
                    for s_name, s_targets in INDIVIDUAL_TARGETS.items():
                        if brand in s_targets:
                            t_indiv = s_targets[brand]
                            r_indiv = df_active_tab[(df_active_tab['Penjualan'] == s_name) & (df_active_tab['Merk'] == brand)]['Jumlah'].sum()
                            pct_indiv = (r_indiv / t_indiv * 100) if t_indiv > 0 else 0
                            sales_rows_list.append({
                                "Rank": "", "Item": f"   └─ {s_name}", "Supervisor": "", 
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
                        "Item": st.column_config.TextColumn("Brand / Salesman", width="medium"),
                        "Bar": st.column_config.ProgressColumn("Progress", format=" ", min_value=0, max_value=1)
                    }
                )
            else: st.warning("Tidak ada data untuk ditampilkan pada ruang lingkup ini.")
        elif target_sales_filter in INDIVIDUAL_TARGETS: st.info("Lihat progress bar di atas untuk detail target individu.")
        else:
            sales_brands = df_active_tab['Merk'].unique()
            indiv_data = []
            for brand in sales_brands:
                owner, target = "-", 0
                for spv, b_dict in TARGET_DATABASE.items():
                    if brand in b_dict: owner, target = spv, b_dict[brand]; break
                if target > 0:
                    real = df_active_tab[df_active_tab['Merk'] == brand]['Jumlah'].sum()
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
        
        if selected_ijl != "SEMUA":
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
                
                for sales_name, targets in INDIVIDUAL_TARGETS.items():
                    if selected_brand_detail in targets:
                        t_pribadi = targets[selected_brand_detail]
                        real_sales = df_active_tab[(df_active_tab['Penjualan'] == sales_name) & (df_active_tab['Merk'] == selected_brand_detail)]['Jumlah'].sum()
                        
                        df_h1 = df_scope_all[(df_scope_all['Tanggal'].dt.date == h_1_date) & (df_scope_all['Penjualan'] == sales_name) & (df_scope_all['Merk'] == selected_brand_detail)]
                        omset_h1 = df_h1['Jumlah'].sum()
                        toko_h1 = df_h1['Nama Outlet'].nunique()
                        total_toko_mtd = df_active_tab[(df_active_tab['Penjualan'] == sales_name) & (df_active_tab['Merk'] == selected_brand_detail)]['Nama Outlet'].nunique()
                        
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
        
        pareto_df = df_t3.groupby('Nama Barang')['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=False)
        total_omset_pareto = pareto_df['Jumlah'].sum()
        
        if total_omset_pareto > 0:
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
            top_prod = df_t3.groupby('Nama Barang')['Jumlah'].sum().nlargest(10).reset_index()
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
                for outlet in sleeping_outlets:
                    outlet_df = df_scope_all[df_scope_all['Nama Outlet'] == outlet]
                    last_date = outlet_df['Tanggal'].max()
                    sales_handler = outlet_df['Penjualan'].iloc[0] if not outlet_df.empty else "-"
                    
                    if last_date.year == 2000:
                        terakhir_order_str = "Belum Pernah Order (Toko Master)"
                        hari_sejak = 99999
                    else:
                        terakhir_order_str = last_date.strftime('%d %b %Y')
                        hari_sejak = (datetime.date.today() - last_date.date()).days
                        
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

        tab_pivot, tab_growth, tab_ba, tab_ai = st.tabs(["📊 Pivot Data Customer", "📈 Rekap Growth Brand", "🎯 Pencapaian Target BA", "🤖 AI Assistant (Gemini)"])
        
        with tab_pivot:
            render_pivot_fragment(df_scope_all, role)

        with tab_growth:
            st.markdown("### 📈 Rekap Growth Brand")
            list_merk_growth = sorted(df_scope_all['Merk'].dropna().astype(str).unique())
            
            if list_merk_growth:
                brand_growth = st.selectbox("Pilih Brand untuk Analisis Growth:", list_merk_growth)
                
                if st.checkbox("🔍 Buka Radar Detektif (Cek Toko Double)"):
                    df_cek = df_scope_all[df_scope_all['Merk'] == brand_growth].copy()
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
                
                df_team_all = df_scope_all.copy()
                if target_sales_filter != "SEMUA":
                    if target_sales_filter.upper() in TARGET_DATABASE:
                        tim_sales_list = list(TARGET_DATABASE[target_sales_filter.upper()].keys())
                        df_team_all = df_team_all[df_team_all['Penjualan'].isin(tim_sales_list)]
                    else:
                        df_team_all = df_team_all[df_team_all['Penjualan'] == target_sales_filter]
                elif role not in ['manager', 'direktur', 'supervisor'] and my_name.lower() != 'fauziah':
                    df_team_all = df_team_all[df_team_all['Penjualan'] == my_name]

                if not df_team_all.empty:
                    df_team_all['Tahun'] = df_team_all['Tanggal'].dt.year
                    df_team_all['Bulan'] = df_team_all['Tanggal'].dt.month
                    df_team_all['Bulan-Tahun'] = df_team_all['Tanggal'].dt.to_period('M')
                    
                    all_months = sorted(df_team_all[df_team_all['Tanggal'].dt.year >= 2025]['Bulan-Tahun'].dropna().unique())
                    
                    invalid_codes = ['-', '', 'NAN', 'NONE', '0.0']
                    df_team_all['ID_Patokan'] = np.where(
                        df_team_all['Kode_Global'].str.strip().str.upper().isin(invalid_codes),
                        df_team_all['Nama Outlet'].str.strip(),
                        df_team_all['Kode_Global'].str.strip()
                    )
                    
                    prefixes = BRAND_PREFIXES.get(brand_growth, [brand_growth[:3].upper()])
                    prefix_tuple = tuple(prefixes)
                    
                    df_brand_only = df_team_all[df_team_all['Merk'] == brand_growth]
                    sales_per_month = df_brand_only.groupby('Bulan-Tahun')['Jumlah'].sum().to_dict()
                    ao_sets = df_brand_only.groupby('Bulan-Tahun')['ID_Patokan'].apply(set).to_dict()
                    hist_sets = df_brand_only.groupby('Bulan-Tahun')['ID_Patokan'].apply(set).to_dict()

                    mask_prefix = df_team_all['Kode_Global'].astype(str).str.strip().str.upper().apply(lambda x: any(x.startswith(p) for p in prefix_tuple))
                    pref_sets = df_team_all[mask_prefix].groupby('Bulan-Tahun')['ID_Patokan'].apply(set).to_dict()
                    
                    growth_data = []
                    ro_accumulated = set()
                    
                    for period in all_months:
                        sales = sales_per_month.get(period, 0.0)
                        current_ao = ao_sets.get(period, set())
                        ao = len(current_ao)
                        
                        combined_ro_prev = set(ro_accumulated)
                        
                        ro_accumulated.update(hist_sets.get(period, set()))
                        ro_accumulated.update(pref_sets.get(period, set()))
                        
                        ro = len(ro_accumulated)
                        noo = len(current_ao - combined_ro_prev)
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
