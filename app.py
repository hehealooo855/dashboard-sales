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
HOLIDAYS_2026 = ['2026-01-01', '2026-02-14', '2026-02-17', '2026-03-19', '2026-03-20', '2026-04-03', '2026-05-01', '2026-05-14', '2026-05-26', '2026-06-01', '2026-06-16', '2026-08-17', '2026-08-25', '2026-12-25']

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
    "Javinci": ["JV"], "Careso": ["EPS", "CRS"], "Somethinc": ["SMT", "SOM"], "Newlab": ["NL", "NEW"], "Gloow & Be": ["GB", "GLO"], "Dorskin": ["DRS", "DOR"], "Whitelab": ["WL", "WHI"], "Bonavie": ["BNV", "BON"], "Goute": ["GT", "GOU"],
    "Mlen": ["MLN", "MLE"], "Artist Inc": ["ART"], "Maskit": ["MSK", "MAS"], "Birth Beyond": ["BB", "BIR"], "Sociolla": ["SOC", "SCL"], "Thai": ["TH", "THA"], "Inesia": ["INS", "INE"], "Y2000": ["Y2K", "Y20"], "Diosys": ["DIO", "DS"], 
    "Masami": ["MSM", "MAS"], "Cassandra": ["CAS", "CSD"], "Clinelle": ["CLN", "CLI"], "Beautica": ["BTC", "BEA"], "Claresta": ["CLA", "CLR"], "Rose All Day": ["RAD", "ROS"], "OtwooO": ["OTO", "OTW"], "Sekawan": ["SKW", "SEK", "AINIE", "AIN"], "Avione": ["AV"], 
    "Honor": ["HNR", "HON"], "Vlagio": ["VLG", "VLA"], "Ren & R & L": ["REN", "RRL"], "Mad For Make Up": ["MFM", "MAD"], "Satto": ["STT", "SAT"], "Mykonos": ["MYK", "MYC"], "The Face": ["TF", "TFC"], "Yu Chun Mei": ["YCM", "YUC"], "Milano": ["MIL", "MLN"], 
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

TARGET_DATABASE = {
    "MADONG": { "Somethinc": 1_200_000_000, "SYB": 120_000_000, "Sekawan": 300_000_000, "Avione": 150_000_000, "Honor": 220_000_000, "Vlagio": 50_000_000, "Ren & R & L": 20_000_000, "Mad For Make Up": 40_000_000, "Satto": 525_000_000, "Mykonos": 20_000_000, "The Face": 600_000_000, "Yu Chun Mei": 400_000_000, "Milano": 50_000_000, "Remar": 50_000_000, "Walnutt": 30_000_000, "Elizabeth Rose": 80_000_000, "Sombong": 50_000_000},
    "LISMAN": { "Javinci": 1_300_000_000, "Careso": 400_000_000, "Newlab": 120_000_000, "Gloow & Be": 170_000_000, "Dorskin": 30_000_000, "Whitelab": 100_000_000, "Bonavie": 50_000_000, "Goute": 70_000_000, "Mlen": 225_000_000, "Artist Inc": 150_000_000, "Maskit": 50_000_000, "Birth Beyond": 120_000_000, "Everpure": 0},
    "AKBAR": { "Sociolla": 600_000_000, "Thai": 400_000_000, "Inesia": 80_000_000, "Y2000": 250_000_000, "Diosys": 600_000_000, "Masami": 50_000_000, "Cassandra": 20_000_000, "Clinelle": 80_000_000,"Beautica": 100_000_000, "Claresta": 350_000_000, "Rose All Day": 30_000_000, "OtwooO": 180_000_000}
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
    "Diosys": ["DIOSYS", "DYOSIS", "DIO"], "Y2000": ["Y2000", "Y 2000", "Y-2000"], "Masami": ["MASAMI", "JAYA"], "Cassandra": ["CASSANDRA", "CASANDRA"],
    "Thai": ["THAI", "JINSU"], "Inesia": ["INESIA"], "Honor": ["HONOR"], "Vlagio": ["VLAGIO"], "Sociolla": ["SOCIOLLA"], "Skin1004": ["SKIN1004", "SKIN 1004"], "Oimio": ["OIMIO"],
    "Clinelle": ["CLINELLE", "CLIN"], "Ren & R & L": ["REN", "R & L", "R&L"], "Sekawan": ["SEKAWAN", "AINIE"], "Mad For Make Up": ["MAD FOR", "MAKE UP", "MAJU", "MADFORMAKEUP"], "Avione": ["AVIONE"],
    "SYB": ["SYB"], "Satto": ["SATTO"], "Liora": ["LIORA"], "Mykonos": ["MYKONOS"], "Somethinc": ["SOMETHINC"], "Gloow & Be": ["GLOOW", "GLOOWBI", "GLOW", "GLOWBE"],
    "Artist Inc": ["ARTIST", "ARTIS"], "Bonavie": ["BONAVIE"], "Whitelab": ["WHITELAB"], "Goute": ["GOUTE"], "Dorskin": ["DORSKIN"], "Javinci": ["JAVINCI"], "Madame G": ["MADAM", "MADAME"],
    "Careso": ["CARESO"], "Newlab": ["NEWLAB"], "Mlen": ["MLEN"], "Walnutt": ["WALNUT", "WALNUTT"], "Elizabeth Rose": ["ELIZABETH"], "OtwooO": ["OTWOOO", "O.TWO.O", "O TWO O"],
    "Saviosa": ["SAVIOSA"], "The Face": ["THE FACE", "THEFACE"], "Yu Chun Mei": ["YU CHUN MEI", "YCM"], "Milano": ["MILANO"], "Remar": ["REMAR"], "Beautica": ["BEAUTICA"], "Maskit": ["MASKIT"],
    "Claresta": ["CLARESTA"], "Birth Beyond": ["BIRTH"], "Rose All Day": ["ROSE ALL DAY"], "Everpure": ["EVERPURE"], "COSLINE": ["COSLINE"], "NAMA": ["NAMA"], "Rosanna": ["ROSANNA"], "Summer": ["SUMMER"], "Sombong":["SOMBONG"]
}

SALES_MAPPING = {
    "WIRA VG": "WIRA", "WIRA - VG": "WIRA", "WIRA VLAGIO": "WIRA", "WIRA HONOR": "WIRA", "WIRA - HONOR": "WIRA", "WIRA HR": "WIRA", "WIRA SYB": "WIRA", "WIRA - SYB": "WIRA", "WIRA SOMETHINC": "WIRA", "PMT-WIRA": "WIRA", "WIRA ELIZABETH": "WIRA", "WIRA WALNUTT": "WIRA", "WIRA ELZ": "WIRA", "WIRA SBG": "WIRA", 
    "HAMZAH VG": "HAMZAH", "HAMZAH - VG": "HAMZAH", "HAMZAH HONOR": "HAMZAH", "HAMZAH - HONOR": "HAMZAH", "HAMZAH SYB": "HAMZAH", "HAMZAH AV": "HAMZAH", "HAMZAH AINIE": "HAMZAH", "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH", "HAMZA AV": "HAMZAH", "HAMZA SBG": "HAMZAH",
    "FERI VG": "FERI", "FERI - VG": "FERI", "FERI HONOR": "FERI", "FERI - HONOR": "FERI", "FERI THAI": "FERI", "FERI - INESIA": "FERI", "YOGI TF": "YOGI", "YOGI THE FACE": "YOGI", "YOGI YCM": "YOGI", "YOGI MILANO": "YOGI", "MILANO - YOGI": "YOGI", "YOGI REMAR": "YOGI",
    "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI", "GANI TF": "GANI", "GANI - YCM": "GANI", "GANI - MILANO": "GANI", "GANI - HONOR": "GANI", "GANI - VG": "GANI", "GANI - TH": "GANI", "GANI INESIA": "GANI", "GANI - KSM": "GANI", "SSL - GANI": "GANI", "GANI ELIZABETH": "GANI", "GANI WALNUTT": "GANI",
    "MITHA MASKIT": "MITHA", "MITHA RAD": "MITHA", "MITHA CLA": "MITHA", "MITHA OT": "MITHA", "MAS - MITHA": "MITHA", "SSL BABY - MITHA ": "MITHA", "SAVIOSA - MITHA": "MITHA", "MITHA ": "MITHA", "LYDIA KITO": "LYDIA", "LYDIA K": "LYDIA", "LYDIA BB": "LYDIA", "LYDIA - KITO": "LYDIA",
    "RAPI": "RAPI", "RAPI AV": "RAPI", "NOVI DAN RAFFI": "NOVI", "NOVI & RAFFI": "NOVI", "RAPI AV":"RAPI", "RAPI SBG": "RAPI", "ROZY AINIE": "ROZY", "ROZY AV": "ROZY", "SRI RAMADHANI": "SRI RAMADHANI", "SRI RAMADHANI SEKAWAN": "SRI RAMADHANI", "SRI RAMADHANI SBG": "SRI RAMADHANI",
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG", "MADONG MYK": "MADONG", "RISKA AV": "RISKA", "RISKA BN": "RISKA", "RISKA CRS": "RISKA", "RISKA E-WL": "RISKA", "RISKA JV": "RISKA", "RISKA REN": "RISKA", "RISKA R&L": "RISKA", "RISKA SMT": "RISKA", "RISKA ST": "RISKA", "RISKA SYB": "RISKA", "RISKA - MILANO": "RISKA", "RISKA TF": "RISKA", "RISKA - YCM": "RISKA", "RISKA HONOR": "RISKA", "RISKA - VG": "RISKA", "RISKA TH": "RISKA", "RISKA - INESIA": "RISKA", "SSL - RISKA": "RISKA", "SKIN - RIZKA": "RISKA", 
    "ADE CLA": "ADE", "ADE CRS": "ADE", "GLOOW - ADE": "ADE", "ADE JAVINCI": "ADE", "ADE JV": "ADE", "ADE SVD": "ADE", "ADE RAM PUTRA M.GIE": "ADE", "ADE - MLEN1": "ADE", "ADE NEWLAB": "ADE", "DORS - ADE": "ADE",
    "FANDI - BONAVIE": "FANDI", "DORS- FANDI": "FANDI", "FANDY CRS": "FANDI", "FANDI AFDILLAH": "FANDI", "FANDY WL": "FANDI", "GLOOW - FANDY": "FANDI", "FANDI - GOUTE": "FANDI", "FANDI MG": "FANDI", "FANDI - NEWLAB": "FANDI", "FANDY - YCM": "FANDI", "FANDY YLA": "FANDI", "FANDI JV": "FANDI", "FANDI MLEN": "FANDI",
    "NAUFAL - JAVINCI": "NAUFAL", "NAUFAL JV": "NAUFAL", "NAUFAL SVD": "NAUFAL", "RIZKI JV": "RIZKI", "RIZKI SVD": "RIZKI", "SAHRUL JAVINCI": "SYAHRUL", "SAHRUL TF": "SYAHRUL", "SAHRUL JV": "SYAHRUL", "GLOOW - SAHRUL": "SYAHRUL", "SANTI BONAVIE": "SANTI", "SANTI WHITELAB": "SANTI", "SANTI GOUTE": "SANTI", "DWI CRS": "DWI", "DWI NLAB": "DWI", 
    "ASWIN ARTIS": "ASWIN", "ASWIN AI": "ASWIN", "ASWIN Inc": "ASWIN", "ASWIN INC": "ASWIN", "ASWIN - ARTIST INC": "ASWIN", "BASTIAN CASANDRA": "BASTIAN", "SSL- BASTIAN": "BASTIAN", "SKIN - BASTIAN": "BASTIAN", "BASTIAN - HONOR": "BASTIAN", "BASTIAN - VG": "BASTIAN", "BASTIAN TH": "BASTIAN", "BASTIAN YL": "BASTIAN", "BASTIAN YL-DIO CAT": "BASTIAN", "BASTIAN SHMP": "BASTIAN", "BASTIAN-DIO 45": "BASTIAN",
    "SSL - DEVI": "DEVI", "SKIN - DEVI": "DEVI", "DEVI Y- DIOSYS CAT": "DEVI", "DEVI YL": "DEVI", "DEVI SHMP": "DEVI", "DEVI-DIO 45": "DEVI", "DEVI YLA": "DEVI", "SSL- BAYU": "BAYU", "SKIN - BAYU": "BAYU", "BAYU-DIO 45": "BAYU", "BAYU YL-DIO CAT": "BAYU", "BAYU SHMP": "BAYU", "BAYU YL": "BAYU", 
    "HABIBI - FZ": "HABIBI", "HABIBI SYB": "HABIBI", "HABIBI TH": "HABIBI", "GLOOW - LISMAN": "LISMAN", "LISMAN - NEWLAB": "LISMAN", "WILLIAM BTC": "WILLIAM", "WILLI - ROS": "WILLIAM", "WILLI - WAL": "WILLIAM", "RINI JV": "RINI", "RINI SYB": "RINI", 
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
    hash_object = hashlib.sha256(f"{time_key}-{secret_salt}".encode())
    return "".join(filter(str.isdigit, hash_object.hexdigest()))[:4].ljust(4, '0')

def render_custom_progress(title, current, target):
    if target == 0: target = 1
    pct = (current / target) * 100
    visual_pct = min(pct, 100)
    bar_color = "linear-gradient(90deg, #ff4b4b, #e74c3c)" if pct < 50 else ("linear-gradient(90deg, #f1c40f, #f39c12)" if pct < 85 else "linear-gradient(90deg, #2ecc71, #27ae60)") 
    st.markdown(f"""
    <div style="margin-bottom: 20px; background-color: #fcfcfc; padding: 15px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-weight: 700; font-size: 15px; color: #34495e;">{title}</span>
            <span style="font-weight: 600; color: #555; font-size: 14px;">{format_idr(current)} <span style="color:#999; font-weight:normal;">/ {format_idr(target)}</span></span>
        </div>
        <div style="width: 100%; background-color: #ecf0f1; border-radius: 20px; height: 26px; position: relative; overflow: hidden;">
            <div style="width: {visual_pct}%; background: {bar_color}; height: 100%; border-radius: 20px; transition: width 0.8s ease;"></div>
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; z-index: 10; font-weight: 800; font-size: 13px; color: #222; text-shadow: 0px 0px 4px #fff;">{pct:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================================
# DATATABLES HTML GENERATOR (SUNTIKAN JAVASCRIPT UNTUK OPSI B)
# =========================================================================
def get_datatable_html(df, num_cols, table_id):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
        <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: white; margin: 0; padding: 0; }}
            #{table_id} {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
            #{table_id} thead th {{ background-color: #2980b9; color: white; border: 1px solid #555; padding: 10px; text-align: center; }}
            #{table_id} tbody td {{ border: 1px solid #ddd; padding: 8px; color: #333; }}
            #{table_id} tbody tr:nth-child(even) {{ background-color: #f9f9f9; }}
            #{table_id} tbody tr:hover {{ background-color: #e3f2fd !important; }}
            .grand-total {{ background-color: #FFFF00 !important; font-weight: bold; color: black !important; }}
            .grand-total td {{ border-top: 2px solid #333 !important; border-bottom: 2px solid #333 !important; color: black !important;}}
            .dataTables_wrapper .dataTables_filter input {{ border: 1px solid #aaa; border-radius: 4px; padding: 5px; margin-left: 5px; outline: none; }}
            .dataTables_wrapper .dataTables_filter input:focus {{ border-color: #2980b9; box-shadow: 0 0 3px #2980b9; }}
        </style>
    </head>
    <body>
        <table id="{table_id}" class="display nowrap" style="width:100%">
            <thead><tr>
    """
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    
    for _, row in df.iterrows():
        is_gt = False
        for col in df.columns:
            if str(row[col]) == 'GRAND TOTAL': 
                is_gt = True; break
        
        tr_class = "grand-total" if is_gt else ""
        html += f'<tr class="{tr_class}">'
        
        for col in df.columns:
            val = row[col]
            if col in num_cols:
                if pd.isna(val) or val == 0 or val == "": val_str = "-"
                else:
                    try: val_str = f"Rp {float(val):,.0f}".replace(',', '.')
                    except: val_str = str(val)
                html += f'<td style="text-align: right; white-space: nowrap;">{val_str}</td>'
            else:
                val_str = str(val) if pd.notna(val) and str(val).strip() != "" else "-"
                align = 'center' if is_gt else 'left'
                html += f'<td style="text-align: {align}; white-space: nowrap;">{val_str}</td>'
        html += "</tr>"
    
    html += f"""
            </tbody>
        </table>
        <script>
            $(document).ready(function() {{
                $('#{table_id}').DataTable({{
                    "paging": false,
                    "info": false,
                    "searching": true,
                    "ordering": true,
                    "order": [],
                    "scrollX": true,
                    "scrollY": "500px",
                    "scrollCollapse": true,
                    "language": {{ "search": "🔍 Cari Data:" }}
                }});
            }});
        </script>
    </body>
    </html>
    """
    return html

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
            try: return pd.read_csv(f"{url}&t={int(time.time())}", dtype=str, engine='pyarrow')
            except Exception: return None
        return None

    all_dfs = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(fetch_url, urls)
        for res in results:
            if res is not None and not res.empty: all_dfs.append(res)
    if not all_dfs: return None
        
    df = pd.concat(all_dfs, ignore_index=True)
    df.columns = df.columns.str.strip()
    
    for alt_col in ['Sales', 'Salesman', 'Nama Sales']:
        if alt_col in df.columns:
            df['Penjualan'] = df['Penjualan'].fillna(df[alt_col]) if 'Penjualan' in df.columns else df[alt_col]
                
    for col_name in ['Kode Customer', 'Kode Costumer', 'Kode Outlet']:
        if col_name in df.columns:
            df['Kode_Global'] = df['Kode_Global'].fillna(df[col_name]) if 'Kode_Global' in df.columns else df[col_name]
    if 'Kode_Global' not in df.columns: df['Kode_Global'] = "-"

    faktur_col = next((col for col in df.columns if any(x in col.lower() for x in ['faktur', 'bukti', 'invoice'])), None)
    if faktur_col: df = df.rename(columns={faktur_col: 'No Faktur'})
    
    if 'Nama Barang' in df.columns:
        df = df[~df['Nama Barang'].astype(str).str.match(r'^(Total|Jumlah)', case=False, na=False)]
        df['Nama Barang'] = df['Nama Barang'].fillna("-")

    if 'Nama Outlet' in df.columns:
        df = df[~df['Nama Outlet'].astype(str).str.match(r'^(Total|Jumlah|Subtotal|Grand|Rekap)', case=False, na=False)]
        df = df[(df['Nama Outlet'].astype(str).str.strip() != '') & (df['Nama Outlet'].astype(str).str.lower() != 'nan')]

    def clean_rupiah(x):
        x = re.sub(r'[^\d-]', '', re.sub(r'[,.]\d{2}$', '', re.sub(r'\s+', '', str(x).upper().replace('RP', '').strip())).replace(',', '').replace('.', '')) 
        try: return float(x)
        except: return 0.0

    df['Jumlah'] = df['Jumlah'].apply(clean_rupiah) if 'Jumlah' in df.columns else 0.0

    if 'Tanggal' in df.columns:
        tanggal_raw = df['Tanggal'].astype(str).str.strip()
        df['Tanggal'] = pd.to_datetime(tanggal_raw, format='%d/%m/%Y', errors='coerce').fillna(
            pd.to_datetime(tanggal_raw, format='%d-%m-%Y', errors='coerce')).fillna(
            pd.to_datetime(tanggal_raw, dayfirst=True, errors='coerce', format='mixed')).fillna(pd.to_datetime('2000-01-01'))
    else: df['Tanggal'] = pd.to_datetime('2000-01-01')

    if 'Penjualan' in df.columns:
        df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(SALES_MAPPING)
        valid_sales_names = list(INDIVIDUAL_TARGETS.keys()) + ["MADONG", "LISMAN", "AKBAR"]
        df.loc[~df['Penjualan'].isin(valid_sales_names), 'Penjualan'] = 'Non-Sales'
        outlet_to_sales = df[df['Penjualan'] != 'Non-Sales'].groupby('Nama Outlet')['Penjualan'].first().to_dict()
        mask_non = df['Penjualan'] == 'Non-Sales'
        df.loc[mask_non, 'Penjualan'] = df.loc[mask_non, 'Nama Outlet'].map(outlet_to_sales).fillna('Non-Sales')
        df['Penjualan'] = df['Penjualan'].astype('category')
    else: df['Penjualan'] = 'Non-Sales'

    def normalize_brand(raw_brand):
        raw_upper = str(raw_brand).upper()
        for t_brand, kw in BRAND_ALIASES.items(): 
            if any(k in raw_upper for k in kw): return t_brand
        return raw_brand
        
    df['Merk'] = df['Merk'].fillna("-").apply(normalize_brand).astype('category') if 'Merk' in df.columns else "-"
    
    for col in ['Kota', 'Nama Outlet', 'No Faktur', 'Kode_Global']:
        if col in df.columns: df[col] = df[col].fillna("-").astype(str).str.strip().replace({'nan': '-', 'NaN': '-', '0.0': '-', 'None': '-', '': '-'})
    
    df['Provinsi'] = df['Kota'].apply(map_city_to_province) if 'Kota' in df.columns else "-"
    
    try: df.to_parquet("master_database_penjualan.parquet", index=False)
    except: pass 
    return df

def load_data(fast_mode=False):
    if fast_mode and os.path.exists("master_database_penjualan.parquet"):
        try: return pd.read_parquet("master_database_penjualan.parquet")
        except: pass
    return load_data_from_url()

def generate_pivot_fast(df_pivot_source, selected_merk_excel, selected_tahun_excel_tuple, group_cols_tuple, brand_prefixes_dict):
    group_cols = list(group_cols_tuple)
    if 'Nama Outlet' in df_pivot_source.columns and 'Nama Customer' not in df_pivot_source.columns:
        df_pivot_source = df_pivot_source.rename(columns={'Nama Outlet': 'Nama Customer'})
        if 'Nama Outlet' in group_cols: group_cols[group_cols.index('Nama Outlet')] = 'Nama Customer'

    df_pivot_source['ID_Patokan'] = np.where(df_pivot_source['Kode_Global'].astype(str).str.strip().str.upper().isin(['-', '', 'NAN', 'NONE', '0.0']), df_pivot_source['Nama Customer'].astype(str).str.strip(), df_pivot_source['Kode_Global'].astype(str).str.strip())

    if not df_pivot_source.empty:
        if selected_merk_excel != "SEMUA":
            prefixes = brand_prefixes_dict.get(selected_merk_excel, [selected_merk_excel[:3].upper()])
            final_mask = (df_pivot_source['Merk'] == selected_merk_excel) | (df_pivot_source['Kode_Global'].astype(str).str.strip().str.upper().apply(lambda x: any(x.startswith(p) for p in tuple(prefixes))))
        else: final_mask = pd.Series(True, index=df_pivot_source.index)
            
        df_filtered = df_pivot_source[final_mask].copy()
        if df_filtered.empty: return pd.DataFrame()

        base_customers = df_filtered.sort_values('Tanggal', ascending=False).drop_duplicates(subset=['ID_Patokan'], keep='first')[['ID_Patokan'] + group_cols]
        df_excel = df_filtered[df_filtered['Tanggal'].dt.year.isin(selected_tahun_excel_tuple)].copy()
        
        if not df_excel.empty:
            df_excel['Bulan Angka'] = df_excel['Tanggal'].dt.month
            pivot_sales = pd.pivot_table(df_excel, values='Jumlah', index='ID_Patokan', columns='Bulan Angka', aggfunc='sum', fill_value=0).reset_index()
            return pd.merge(base_customers, pivot_sales, on='ID_Patokan', how='left').fillna(0).drop(columns=['ID_Patokan'])
        else:
            master_pivot = base_customers.copy()
            for i in range(1, 13): master_pivot[i] = 0
            return master_pivot.drop(columns=['ID_Patokan'])
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
    pair_support = Counter([p for sublist in pair_df for p in sublist])
    rules = []
    for (A, B), supp_ab in pair_support.items():
        rules.append({'antecedent': A, 'consequent': B, 'support': supp_ab / total_transactions, 'confidence': supp_ab / item_support[A]})
        rules.append({'antecedent': B, 'consequent': A, 'support': supp_ab / total_transactions, 'confidence': supp_ab / item_support[B]})
    if not rules: return None
    return pd.DataFrame(rules).drop_duplicates().sort_values('confidence', ascending=False)[lambda x: x['confidence'] > 0.5]

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
            for _, rule in rules_df[rules_df['antecedent'] == item].iterrows():
                consequent, conf = rule['consequent'], rule['confidence']
                if consequent not in purchased and (consequent not in possible_recs or conf > possible_recs[consequent][1]):
                    possible_recs[consequent] = (item, conf)
        if possible_recs:
            top_consequent, (antecedent, conf) = max(possible_recs.items(), key=lambda x: x[1][1])
            recommendations.append({'Toko': outlet, 'Sales': sales, 'Rekomendasi': f"Tawarkan {top_consequent}, karena {conf*100:.0f}% toko yang beli {antecedent} juga membelinya."})
    return pd.DataFrame(recommendations) if recommendations else None

@st.fragment
def render_pivot_fragment(df_scope_all, role):
    list_merk_excel = sorted(df_scope_all['Merk'].dropna().astype(str).unique())
    list_tahun = sorted(df_scope_all['Tanggal'].dt.year.dropna().unique(), reverse=True)
    
    grp_cols = []
    if 'Kode_Global' in df_scope_all.columns: grp_cols.append('Kode_Global'); kd_asal = 'Kode_Global'
    else: df_scope_all['Kode_Global'] = "-"; grp_cols.append('Kode_Global'); kd_asal = 'Kode_Global'
        
    if 'Nama Customer' in df_scope_all.columns: grp_cols.append('Nama Customer')
    elif 'Nama Outlet' in df_scope_all.columns: grp_cols.append('Nama Outlet'); df_scope_all['Nama Customer'] = df_scope_all['Nama Outlet']
    else: df_scope_all['Nama Customer'] = "-"; grp_cols.append('Nama Customer')
    
    if 'Provinsi' in df_scope_all.columns: grp_cols.append('Provinsi')
    else: df_scope_all['Provinsi'] = "-"; grp_cols.append('Provinsi')
    
    if 'Kota' in df_scope_all.columns: grp_cols.append('Kota')
    else: df_scope_all['Kota'] = "-"; grp_cols.append('Kota')

    with st.form(key='pivot_filter_form'):
        col_piv1, col_piv2 = st.columns(2)
        with col_piv1: selected_merk_excel = st.selectbox("🎯 Pilih Merk:", ["SEMUA"] + list_merk_excel)
        with col_piv2: selected_tahun_excel = st.multiselect("🗓️ Pilih Tahun:", list_tahun, default=list_tahun)
            
        st.markdown("#### 🔎 Filter Spesifik (Batch Processing)")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1: filter_kode = st.multiselect("Kode Customer:", sorted(df_scope_all[kd_asal].astype(str).unique()), placeholder="Pilih Kode...")
        with col_f2: filter_nama = st.multiselect("Nama Customer:", sorted(df_scope_all['Nama Outlet'].astype(str).unique()) if 'Nama Outlet' in df_scope_all.columns else sorted(df_scope_all['Nama Customer'].astype(str).unique()), placeholder="Pilih Customer...")
        with col_f3: filter_provinsi = st.multiselect("Provinsi:", sorted(df_scope_all['Provinsi'].astype(str).unique()), placeholder="Pilih Provinsi...")
        with col_f4: filter_kota = st.multiselect("Kota:", sorted(df_scope_all['Kota'].astype(str).unique()), placeholder="Pilih Kota...")

        maximize_toggle = st.toggle("🗖 Mode Layar Penuh (Tabel Super Lebar)")
        submit_button = st.form_submit_button(label='🚀 Terapkan Filter (Super Cepat)', use_container_width=True)

    master_pivot = generate_pivot_fast(df_scope_all, selected_merk_excel, tuple(selected_tahun_excel), tuple(grp_cols), BRAND_PREFIXES)

    if not master_pivot.empty:
        bulan_indo_map = {1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'}
        for i in range(1, 13):
            if i not in master_pivot.columns: master_pivot[i] = 0
        
        cols_to_keep = [c for c in grp_cols if c in master_pivot.columns] + list(range(1, 13))
        master_pivot = master_pivot[cols_to_keep]
        master_pivot.columns = [bulan_indo_map[c] if isinstance(c, int) else c for c in cols_to_keep]
        master_pivot['Total Penjualan'] = master_pivot[list(bulan_indo_map.values())].sum(axis=1)
        master_pivot = master_pivot.rename(columns={'Kode_Global': 'Kode Customer'})
        
        for col in ['Kode Customer', 'Nama Customer', 'Provinsi', 'Kota']:
            if col not in master_pivot.columns: master_pivot[col] = "-"

        df_filtered = master_pivot.copy()
        if filter_kode: df_filtered = df_filtered[df_filtered['Kode Customer'].astype(str).isin(filter_kode)]
        if filter_nama: df_filtered = df_filtered[df_filtered['Nama Customer'].astype(str).isin(filter_nama)]
        if filter_provinsi: df_filtered = df_filtered[df_filtered['Provinsi'].astype(str).isin(filter_provinsi)]
        if filter_kota: df_filtered = df_filtered[df_filtered['Kota'].astype(str).isin(filter_kota)]

        st.caption(f"Menampilkan {len(df_filtered)} data customer.")

        if not df_filtered.empty:
            bulan_indo_list = list(bulan_indo_map.values())
            num_cols = bulan_indo_list + ['Total Penjualan']
            total_dict = {col: "" for col in df_filtered.columns}
            total_dict['Nama Customer'] = "GRAND TOTAL" 
            for col in num_cols: total_dict[col] = df_filtered[col].sum()
            
            df_display = pd.concat([df_filtered, pd.DataFrame([total_dict])], ignore_index=True)
            
            # --- PENGHANCUR BUG KOLOM GANDA ---
            df_display = df_display.loc[:, ~df_display.columns.duplicated()]

            # --- RENDER DATATABLES (OPSI B) ---
            html_table = get_datatable_html(df_display, num_cols, "pivotDataTbl")
            
            if maximize_toggle:
                st.markdown("""<style>header {display: none !important;} [data-testid="stSidebar"] {display: none !important;} .block-container {max-width: 100% !important; padding: 1rem !important;}</style>""", unsafe_allow_html=True)
                st.info("ℹ️ Mode Layar Penuh aktif. Hilangkan centang pada toggle 'Mode Layar Penuh' di atas untuk kembali.")
                components.html(html_table, height=800, scrolling=True)
            else:
                components.html(html_table, height=600, scrolling=True)
        else: st.info("Data Kosong setelah difilter.")
            
        user_role_lower = role.lower()
        if user_role_lower in ['direktur', 'manager', 'supervisor']:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                if 'df_display' in locals() and not df_display.empty: df_display.to_excel(writer, index=False, sheet_name='Master Data')
                workbook, worksheet = writer.book, writer.sheets['Master Data']
                user_identity = f"{st.session_state.get('sales_name', 'Unknown')} ({st.session_state.get('role', 'Unknown').upper()})"
                worksheet.set_header(f'&C&10CONFIDENTIAL DOCUMENT | TRACKED USER: {user_identity} | DOWNLOADED: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | DO NOT DISTRIBUTE')
                worksheet.set_column('D:P', None, workbook.add_format({'num_format': '#,##0'})) 
                if 'df_display' in locals() and not df_display.empty: worksheet.set_row(len(df_display), None, workbook.add_format({'bold': True, 'bg_color': '#f2f2f2', 'border': 1, 'num_format': '#,##0'}))
            st.download_button(label="📥 Download Laporan Excel (XLSX)", data=output.getvalue(), file_name=f"Laporan_Master_{selected_merk_excel}_{datetime.date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else: st.info("Data Kosong.")

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
                                st.error(f"🔒 Akses ditolak! Akun terkunci. Coba lagi dalam {int((st.session_state['lockout_until'][username] - time.time()) / 60) + 1} menit.")
                                return
                            else:
                                st.session_state['failed_attempts'][username] = 0
                                del st.session_state['lockout_until'][username]

                        if captcha_val != 100: st.error("🚨 Verifikasi Captcha gagal! Geser slider hingga angka 100.")
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
                                    if user_row['role'] in ['direktur', 'manager']:
                                        st.session_state['logged_in'] = True
                                        st.session_state['role'] = user_row['role']
                                        st.session_state['sales_name'] = user_row['sales_name']
                                        log_activity(user_row['sales_name'], "LOGIN SUCCESS")
                                        st.rerun()
                                    else:
                                        st.session_state['temp_user_data'] = user_row
                                        st.session_state['login_step'] = '2fa_check'
                                        st.rerun()
                                    
            elif st.session_state['login_step'] == '2fa_check':
                user_data = st.session_state['temp_user_data']
                secret, username_2fa = user_data.get('secret_key', None), user_data['username']
                
                if username_2fa in st.session_state.get('lockout_until', {}):
                    if time.time() < st.session_state['lockout_until'][username_2fa]:
                        st.error(f"🔒 Akses ditolak! Akun terkunci. Coba lagi dalam {int((st.session_state['lockout_until'][username_2fa] - time.time()) / 60) + 1} menit.")
                        if st.button("Kembali ke Awal"): st.session_state['login_step'] = 'credentials'; st.rerun()
                        return
                
                if pd.isna(secret) or not secret:
                    st.error("⛔ Akun Anda belum diaktivasi 2FA."); st.info("Silakan hubungi Direktur/Manager untuk mendapatkan QR Code Aktivasi.")
                    if st.button("Kembali"): st.session_state['login_step'] = 'credentials'; st.rerun()
                else:
                    st.write(f"Halo, **{user_data['sales_name']}** 👋"); st.caption("Buka Google Authenticator di HP Anda.")
                    code_input = st.text_input("Masukkan Kode 6 Digit:", max_chars=6)
                    if st.button("Masuk"):
                        if pyotp.TOTP(secret).verify(code_input):
                            st.session_state['failed_attempts'][username_2fa] = 0
                            st.session_state['logged_in'], st.session_state['role'], st.session_state['sales_name'] = True, user_data['role'], user_data['sales_name']
                            log_activity(user_data['sales_name'], "LOGIN SUCCESS (2FA)")
                            st.rerun()
                        else:
                            st.error("Kode OTP Salah!"); log_activity(user_data['sales_name'], "FAILED LOGIN - WRONG OTP")
                            st.session_state['failed_attempts'][username_2fa] = st.session_state['failed_attempts'].get(username_2fa, 0) + 1
                            if st.session_state['failed_attempts'][username_2fa] >= 3:
                                st.session_state['lockout_until'][username_2fa] = time.time() + 600
                                st.error("🔒 Akun dikunci selama 10 menit karena 3x percobaan gagal.")
                    if st.button("Kembali"): st.session_state['login_step'] = 'credentials'; st.rerun()

def main_dashboard():
    def get_color_achv(val):
        try: return '#ffcccc' if val < 0.50 else ('#fff2cc' if val < 0.85 else '#d1e7dd')
        except: return ''

    def add_aggressive_watermark():
        user_name, role_name = st.session_state.get('sales_name', 'User'), st.session_state.get('role', 'staff')
        if role_name != 'direktur':
            st.markdown(f"""<style>.watermark-container {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 99999; pointer-events: none; overflow: hidden; display: flex; flex-wrap: wrap; opacity: 0.15; }} .watermark-text {{ font-family: 'Arial', sans-serif; font-size: 16px; color: #555; font-weight: 700; transform: rotate(-30deg); white-space: nowrap; margin: 20px; user-select: none; }}</style><div class="watermark-container">{''.join([f'<div class="watermark-text">{user_name} • CONFIDENTIAL • {get_current_time_wib().strftime("%H:%M")}</div>' for _ in range(300)])}</div><script>window.addEventListener('blur', () => {{ document.body.style.filter = 'blur(20px) brightness(0.4)'; document.body.style.backgroundColor = '#000'; }}); window.addEventListener('focus', () => {{ document.body.style.filter = 'none'; document.body.style.backgroundColor = '#fff'; }}); document.addEventListener('keydown', (e) => {{ if ((e.ctrlKey || e.metaKey) && (e.key === 'p' || e.key === 's')) {{ e.preventDefault(); alert('⚠️ Action Disabled for Security Reasons!'); }} }});</script>""", unsafe_allow_html=True)
    add_aggressive_watermark()

    if st.session_state['role'] != 'direktur': st.markdown("<style>@media print { body { display: none !important; } } body { -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none; } img { pointer-events: none; }</style>", unsafe_allow_html=True)

    with st.sidebar:
        st.write("## 👤 User Profile"); st.info(f"**{st.session_state['sales_name']}**\n\nRole: {st.session_state['role'].upper()}")
        fast_mode = st.toggle("⚡ Mode Performa Tinggi", value=True, help="Membaca data dari memori (Cache). Matikan jika Anda baru saja menambah data di Google Sheets dan ingin sistem menarik data terbaru.")
        st.markdown("---"); st.write("### 🎬 Mode Presentasi")
        if st.toggle("🔦 Aktifkan Sorotan Layar", value=False):
            components.html("""<script>const overlay = window.parent.document.createElement('div'); overlay.id = 'presentation-spotlight'; overlay.style.position = 'fixed'; overlay.style.top = '0'; overlay.style.left = '0'; overlay.style.width = '100vw'; overlay.style.height = '100vh'; overlay.style.pointerEvents = 'none'; overlay.style.zIndex = '99998'; overlay.style.background = 'radial-gradient(circle 250px at 50vw 50vh, transparent 0%, rgba(0, 0, 0, 0.8) 100%)'; const existing = window.parent.document.getElementById('presentation-spotlight'); if (existing) existing.remove(); window.parent.document.body.appendChild(overlay); window.parent.document.addEventListener('mousemove', function(e) { overlay.style.background = `radial-gradient(circle 250px at ${e.clientX}px ${e.clientY}px, transparent 0%, rgba(0, 0, 0, 0.8) 100%)`; });</script>""", height=0, width=0)
        else: components.html("""<script>const existing = window.parent.document.getElementById('presentation-spotlight'); if (existing) existing.remove();</script>""", height=0, width=0)

        if st.session_state['role'] in ['manager', 'direktur']:
            st.markdown("---")
            with st.expander("🔐 Admin Zone", expanded=False):
                st.write(f"**Token Master:** `{generate_daily_token()}`")
                target_sales = st.text_input("Nama Sales (Generate QR)", placeholder="Ketik nama (mis: Wira)...")
                if target_sales:
                    users_df = load_users()
                    if target_sales in users_df['username'].values:
                        user_record = users_df[users_df['username'] == target_sales].iloc[0]
                        current_secret = user_record.get('secret_key', None)
                        if pd.isna(current_secret) or not current_secret:
                            current_secret = pyotp.random_base32(); save_user_secret(target_sales, current_secret); st.success(f"Secret Key Dibuat!")
                        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={pyotp.totp.TOTP(current_secret).provisioning_uri(name=user_record['sales_name'], issuer_name='Distributor App')}", width=150)
                    else: st.error("Username tidak ditemukan.")
                if st.button("🔄 Force Sync Database", use_container_width=True):
                    st.cache_data.clear() 
                    if os.path.exists("master_database_penjualan.parquet"): os.remove("master_database_penjualan.parquet") 
                    st.success("Tersinkronisasi!"); time.sleep(1); st.rerun()
            
        if st.button("🚪 Logout", use_container_width=True):
            log_activity(st.session_state['sales_name'], "LOGOUT"); st.session_state['logged_in'] = False
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        st.markdown("---")
            
    df = load_data(fast_mode)
    if df is None or df.empty: st.error("⚠️ Gagal memuat data! Periksa koneksi internet atau Link CSV Google Sheet Anda."); return

    user_role, user_name = st.session_state['role'], st.session_state['sales_name']
    role, my_name, my_name_key = user_role, user_name, user_name.strip().upper()
    is_supervisor_account = my_name_key in TARGET_DATABASE
    
    if role in ['manager', 'direktur'] or my_name.lower() == 'fauziah':
        sales_list, brands_list, outlets_list = ["SEMUA"] + sorted(list(df['Penjualan'].dropna().astype(str).unique())), sorted(df['Merk'].dropna().astype(str).unique()), sorted(df['Nama Outlet'].dropna().astype(str).unique())
    elif is_supervisor_account:
        df_spv_raw = df[df['Merk'].isin(TARGET_DATABASE[my_name_key].keys())]
        sales_list, brands_list, outlets_list = ["SEMUA"] + sorted(list(df_spv_raw['Penjualan'].dropna().astype(str).unique())), sorted(df_spv_raw['Merk'].dropna().astype(str).unique()), sorted(df_spv_raw['Nama Outlet'].dropna().astype(str).unique())
    else:
        df_sales_raw = df[df['Penjualan'] == my_name]
        sales_list, brands_list, outlets_list = [my_name], sorted(df_sales_raw['Merk'].dropna().astype(str).unique()), sorted(df_sales_raw['Nama Outlet'].dropna().astype(str).unique())

    today = datetime.date.today()
    if 'start_date' not in st.session_state:
        st.session_state['start_date'], st.session_state['end_date'] = df['Tanggal'].max().date().replace(day=1), df['Tanggal'].max().date()
        
    st.title("🚀 Executive Dashboard"); st.markdown("---")
    st.markdown("### 🌐 Filter Ruang Lingkup (Hierarki IJL)")
    selected_ijl = st.selectbox("Pilih Ruang Lingkup Dashboard:", ["IJL", "LISMAN", "AKBAR", "MADONG"], index=0)
        
    st.sidebar.markdown("### ⚙️ Panel Filter Executive")
    with st.sidebar.form("main_filter_form"):
        date_range = st.date_input("Rentang Waktu", [st.session_state['start_date'], st.session_state['end_date']])
        target_sales_filter = st.selectbox("Pantau Kinerja Sales / Tim:", sales_list)
        pilih_merk, pilih_outlet = st.multiselect("Filter Spesifik Merk:", brands_list), st.multiselect("Filter Spesifik Outlet:", outlets_list)
        submit_main_filter = st.form_submit_button("🚀 Terapkan Filter", use_container_width=True)

    df_scope_all = df.copy()

    if selected_ijl != "IJL":
        allowed_prefixes = tuple([p for b in TARGET_DATABASE[selected_ijl].keys() for p in BRAND_PREFIXES.get(b, [b[:3].upper()])])
        df_scope_all = df_scope_all[(df_scope_all['Merk'].isin(TARGET_DATABASE[selected_ijl].keys())) | (df_scope_all['Kode_Global'].astype(str).str.strip().str.upper().apply(lambda x: any(x.startswith(p) for p in allowed_prefixes)))]

    if target_sales_filter != "SEMUA": df_scope_all = df_scope_all[df_scope_all['Penjualan'] == target_sales_filter]
    if pilih_merk:
        allowed_prefixes = tuple([p for b in pilih_merk for p in BRAND_PREFIXES.get(b, [b[:3].upper()])])
        df_scope_all = df_scope_all[(df_scope_all['Merk'].isin(pilih_merk)) | (df_scope_all['Kode_Global'].astype(str).str.strip().str.upper().apply(lambda x: any(x.startswith(p) for p in allowed_prefixes)))]
    if pilih_outlet: df_scope_all = df_scope_all[df_scope_all['Nama Outlet'].isin(pilih_outlet)]

    if len(date_range) == 2:
        start_date, end_date = date_range
        df_active = df_scope_all[(df_scope_all['Tanggal'].dt.date >= start_date) & (df_scope_all['Tanggal'].dt.date <= end_date)]
        ref_date = end_date
    else:
        start_date, end_date = df_scope_all['Tanggal'].min().date() if not df_scope_all.empty else today, df_scope_all['Tanggal'].max().date() if not df_scope_all.empty else today
        df_active, ref_date = df_scope_all, end_date

    df_active_tab = df_active.copy()
    current_omset_total = df_active['Jumlah'].sum()
    
    if len(date_range) == 2:
        try: prev_start, prev_end = start_date.replace(month=start_date.month - 1) if start_date.month > 1 else start_date.replace(year=start_date.year - 1, month=12), end_date.replace(month=end_date.month - 1) if end_date.month > 1 else end_date.replace(year=end_date.year - 1, month=12)
        except ValueError: prev_start, prev_end = start_date - datetime.timedelta(days=30), end_date - datetime.timedelta(days=30)
        omset_prev_period = df_scope_all[(df_scope_all['Tanggal'].dt.date >= prev_start) & (df_scope_all['Tanggal'].dt.date <= prev_end)]['Jumlah'].sum()
        delta_val, delta_label = current_omset_total - omset_prev_period, f"vs {prev_start.strftime('%d %b')} - {prev_end.strftime('%d %b')}"
    else:
        prev_date = ref_date - datetime.timedelta(days=1)
        omset_prev_period = df_scope_all[df_scope_all['Tanggal'].dt.date == prev_date]['Jumlah'].sum()
        delta_val, delta_label = current_omset_total - omset_prev_period, f"vs {prev_date.strftime('%d %b')}"

    c1, c2, c3 = st.columns(3)
    delta_str = format_idr(abs(delta_val))
    delta_html = f"<span style='color: #f39c12; font-weight: bold; font-size: 14px;'>▼ - {delta_str} ({delta_label})</span>" if delta_val < 0 else (f"<span style='color: #2ecc71; font-weight: bold; font-size: 14px;'>▲ + {delta_str} ({delta_label})</span>" if delta_val > 0 else f"<span style='color: #95a5a6; font-weight: bold; font-size: 14px;'>▬ {delta_str} ({delta_label})</span>")

    c1.markdown(f"""<div style="padding: 0px 0px;"><p style="margin:0; font-size: 18px; font-weight: 600; color: inherit; padding-bottom: 0.25rem;">💰 Total Omset (Periode)</p><div style="font-size: 36px; font-weight: bold; color: inherit; line-height: 1.2;">{format_idr(current_omset_total)}</div>{delta_html}</div>""", unsafe_allow_html=True)
    c2.metric("🏪 Outlet Aktif", f"{df_active['Nama Outlet'].nunique()}")
    
    if 'No Faktur' in df_active.columns:
        valid_faktur = df_active['No Faktur'].astype(str)
        c3.metric("🧾 Transaksi", f"{valid_faktur[~valid_faktur.isin(['nan', 'None', '', '-', '0', 'None', '.'])][valid_faktur.str.len() > 2].nunique()}")
    else: c3.metric("🧾 Transaksi", f"{len(df_active)}")

    if role in ['manager', 'direktur'] or is_supervisor_account or target_sales_filter in INDIVIDUAL_TARGETS or target_sales_filter.upper() in TARGET_DATABASE:
        st.markdown("### 🎯 Target Monitor")
        if target_sales_filter == "SEMUA":
            render_custom_progress(f"🏢 Target {selected_ijl}" if selected_ijl != "IJL" else "🏢 Target Nasional (All Team)", df_active['Jumlah'].sum(), sum(TARGET_DATABASE[selected_ijl].values()) if selected_ijl != "IJL" else TARGET_NASIONAL_VAL)
        elif target_sales_filter in INDIVIDUAL_TARGETS:
            st.info(f"📋 Target Spesifik: **{target_sales_filter}**")
            for brand, target_val in INDIVIDUAL_TARGETS[target_sales_filter].items(): render_custom_progress(f"👤 {brand} - {target_sales_filter}", df_active[df_active['Merk'] == brand]['Jumlah'].sum(), target_val)
        elif target_sales_filter.upper() in TARGET_DATABASE:
             render_custom_progress(f"👤 Target Tim {target_sales_filter.upper()}", df_active['Jumlah'].sum(), SUPERVISOR_TOTAL_TARGETS.get(target_sales_filter.upper(), 0))
        st.markdown("---")

    t1, t2, t_detail_sales, t3, t5, t_forecast, t4 = st.tabs(["📊 Rapor Brand", "📈 Tren Harian", "👥 Detail Tim", "🏆 Top Produk", "🚀 Kejar Omset", "🔮 Prediksi Omset", "📋 Data Rincian"])
    
    with t1:
        if role in ['manager', 'direktur'] or my_name.lower() == 'fauziah': loop_source = TARGET_DATABASE.items()
        elif is_supervisor_account: loop_source = {my_name_key: TARGET_DATABASE[my_name_key]}.items()
        else: loop_source = None

        if loop_source and (target_sales_filter == "SEMUA" or target_sales_filter.upper() in TARGET_DATABASE):
            st.subheader(f"🏆 Ranking Brand & Detail Sales {('- ' + selected_ijl) if selected_ijl != 'IJL' else ''}")
            dict_mtd_brand = df_active_tab.groupby('Merk')['Jumlah'].sum().to_dict() if not df_active_tab.empty else {}
            salesmen_mtd_master = {}
            if not df_active_tab.empty:
                for (b, s), val in df_active_tab.groupby(['Merk', 'Penjualan'])['Jumlah'].sum().items():
                    if val > 0:
                        if b not in salesmen_mtd_master: salesmen_mtd_master[b] = {}
                        salesmen_mtd_master[b][s] = val
            
            temp_grouped_data = [] 
            for spv, brands_dict in loop_source:
                if selected_ijl != "IJL" and spv != selected_ijl: continue
                for brand, target in brands_dict.items():
                    realisasi_brand = dict_mtd_brand.get(brand, 0.0) 
                    pct_brand = (realisasi_brand / target * 100) if target > 0 else 0
                    brand_row = {"Rank": 0, "Brand / Salesman": brand, "Supervisor": spv, "Target": format_idr(target), "Realisasi": format_idr(realisasi_brand), "Ach (%)": f"{pct_brand:.0f}%", "Bar": pct_brand / 100, "Progress (Detail %)": pct_brand / 100}
                    sales_rows_list = []
                    for s_name, s_targets in INDIVIDUAL_TARGETS.items():
                        if brand in s_targets:
                            t_indiv, r_indiv = s_targets[brand], salesmen_mtd_master.get(brand, {}).get(s_name, 0.0)
                            pct_indiv = (r_indiv / t_indiv * 100) if t_indiv > 0 else 0
                            sales_rows_list.append({"Rank": "", "Brand / Salesman": f"   └─ {s_name}", "Supervisor": "", "Target": format_idr(t_indiv), "Realisasi": format_idr(r_indiv), "Ach (%)": f"{pct_indiv:.0f}%", "Bar": pct_indiv / 100, "Progress (Detail %)": pct_indiv / 100})
                    temp_grouped_data.append({"parent": brand_row, "children": sales_rows_list, "sort_val": realisasi_brand})

            temp_grouped_data.sort(key=lambda x: x['sort_val'], reverse=True)
            final_summary_data = []
            for idx, group in enumerate(temp_grouped_data, 1):
                group['parent']['Rank'] = idx 
                final_summary_data.append(group['parent']); final_summary_data.extend(group['children'])

            df_summ = pd.DataFrame(final_summary_data)
            if not df_summ.empty:
                df_summ = df_summ[['Rank'] + [c for c in df_summ.columns if c != 'Rank']]
                def style_rows(row):
                    bg_color = '#ffcccc' if row['Progress (Detail %)'] < 0.50 else ('#fff2cc' if row['Progress (Detail %)'] < 0.85 else '#d1e7dd')
                    return [f'background-color: {bg_color}; color: black; font-weight: bold; border-top: 2px solid white'] * len(row) if row["Supervisor"] else [f'background-color: {bg_color}; color: #333; opacity: 0.9; border-bottom: 1px solid #eee'] * len(row)
                st.dataframe(df_summ.style.apply(style_rows, axis=1).hide(axis="columns", subset=['Progress (Detail %)']), use_container_width=True, hide_index=True, column_config={"Rank": st.column_config.TextColumn("🏆 Rank", width="small"), "Brand / Salesman": st.column_config.TextColumn("Brand / Salesman", width="medium"), "Bar": st.column_config.ProgressColumn("Progress", format=" ", min_value=0, max_value=1)})
            else: st.warning("Tidak ada data untuk ditampilkan pada ruang lingkup ini.")
        elif target_sales_filter in INDIVIDUAL_TARGETS: st.info("Lihat progress bar di atas untuk detail target individu.")
        else:
            indiv_data, dict_mtd_brand = [], df_active_tab.groupby('Merk')['Jumlah'].sum().to_dict() if not df_active_tab.empty else {}
            for brand in df_active_tab['Merk'].unique():
                owner, target = "-", 0
                for spv, b_dict in TARGET_DATABASE.items():
                    if brand in b_dict: owner, target = spv, b_dict[brand]; break
                if target > 0:
                    real = dict_mtd_brand.get(brand, 0.0); pct = (real/target)*100
                    indiv_data.append({"Brand": brand, "Owner": owner, "Target Tim": format_idr(target), "Kontribusi": format_idr(real), "Ach (%)": f"{pct:.1f}%", "Pencapaian": pct/100})
            if indiv_data: 
                def style_indiv(row): return [f"background-color: {'#ffcccc' if row['Pencapaian'] < 0.50 else ('#fff2cc' if row['Pencapaian'] < 0.85 else '#d1e7dd')}; color: black;" if col == 'Ach (%)' else '' for col in row.index]
                st.dataframe(pd.DataFrame(indiv_data).sort_values("Kontribusi", ascending=False).style.apply(style_indiv, axis=1), use_container_width=True, hide_index=True, column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)})
            else: st.warning("Tidak ada data target brand.")

    with t2:
        st.subheader("📈 Tren Harian")
        if not df_active_tab.empty:
            fig_line = px.line(df_active_tab.groupby('Tanggal')['Jumlah'].sum().reset_index(), x='Tanggal', y='Jumlah', markers=True)
            fig_line.update_traces(line_color='#2980b9', line_width=3); st.plotly_chart(fig_line, use_container_width=True)

    with t_detail_sales:
        st.subheader("👥 Detail Sales Team per Brand")
        allowed_brands = []
        if role in ['manager', 'direktur']:
            for spv_brands in TARGET_DATABASE.values(): allowed_brands.extend(spv_brands.keys())
        elif is_supervisor_account: allowed_brands = list(TARGET_DATABASE[my_name_key].keys())
        if selected_ijl != "IJL": allowed_brands = [b for b in allowed_brands if b in TARGET_DATABASE[selected_ijl].keys()]
            
        if allowed_brands:
            selected_brand_detail = st.selectbox("Pilih Brand untuk Detail Sales:", sorted(set(allowed_brands)))
            if selected_brand_detail:
                sales_stats, total_brand_sales, total_brand_target = [], 0, 0
                h_1_date = end_date - datetime.timedelta(days=1)
                safe_remaining_days = max(1, sum(1 for day_int in range(end_date.day, calendar.monthrange(end_date.year, end_date.month)[1] + 1) if datetime.date(end_date.year, end_date.month, day_int).weekday() != 6 and datetime.date(end_date.year, end_date.month, day_int).strftime('%Y-%m-%d') not in HOLIDAYS_2026))
                
                df_brand_active = df_active_tab[df_active_tab['Merk'] == selected_brand_detail]
                dict_sales_mtd = df_brand_active.groupby('Penjualan')['Jumlah'].sum().to_dict()
                df_brand_h1 = df_scope_all[(df_scope_all['Tanggal'].dt.date == h_1_date) & (df_scope_all['Merk'] == selected_brand_detail)]
                dict_sales_h1, dict_toko_h1, dict_toko_mtd = df_brand_h1.groupby('Penjualan')['Jumlah'].sum().to_dict(), df_brand_h1.groupby('Penjualan')['Nama Outlet'].nunique().to_dict(), df_brand_active.groupby('Penjualan')['Nama Outlet'].nunique().to_dict()
                
                for sales_name, targets in INDIVIDUAL_TARGETS.items():
                    if selected_brand_detail in targets:
                        t_pribadi, real_sales = targets[selected_brand_detail], dict_sales_mtd.get(sales_name, 0.0)
                        gap_sales = max(0, t_pribadi - real_sales)
                        sales_stats.append({"Nama Sales": sales_name, "Target Pribadi": format_idr(t_pribadi), "Realisasi": format_idr(real_sales), "Ach %": f"{(real_sales/t_pribadi)*100:.1f}%" if t_pribadi > 0 else "0%", "Gap Sales": format_idr(gap_sales), "Target Harian": format_idr(gap_sales / safe_remaining_days), "Omset H-1": format_idr(dict_sales_h1.get(sales_name, 0.0)), "Toko H-1": dict_toko_h1.get(sales_name, 0), "Total Toko MTD": dict_toko_mtd.get(sales_name, 0), "_real": real_sales, "_target": t_pribadi})
                        total_brand_sales += real_sales; total_brand_target += t_pribadi
                
                if sales_stats:
                    def style_sales_stats(row):
                        try: val = float(row['Ach %'].replace('%', '')) / 100
                        except: val = 0
                        return [f"background-color: {'#ffcccc' if val < 0.50 else ('#fff2cc' if val < 0.85 else '#d1e7dd')}; color: black;" if col == 'Ach %' else '' for col in row.index]
                    st.dataframe(pd.DataFrame(sales_stats).drop(columns=["_real", "_target"]).style.apply(style_sales_stats, axis=1), use_container_width=True)
                    m1, m2, m3 = st.columns(3)
                    m1.metric(f"Total Target {selected_brand_detail}", format_idr(total_brand_target)); m2.metric(f"Total Omset {selected_brand_detail}", format_idr(total_brand_sales)); m3.metric("Total Ach %", f"{(total_brand_sales/total_brand_target)*100:.1f}%" if total_brand_target > 0 else "0%")
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
            col_pareto1.metric("Total SKU Terjual", len(pareto_df)); col_pareto2.metric("Produk Kontributor Utama (80%)", len(top_performers))
            st.dataframe(top_performers[['🏆 Rank', 'Nama Barang', 'Jumlah', 'Kontribusi %']].style.format({'Jumlah': 'Rp {:,.0f}', 'Kontribusi %': '{:.2f}%'}), use_container_width=True, hide_index=True)
        
        st.divider(); c1, c2 = st.columns(2)
        with c1:
            st.subheader("📦 Top 10 Produk")
            fig_bar = px.bar(grouped_barang.head(10).copy() if not grouped_barang.empty else pd.DataFrame(columns=['Nama Barang', 'Jumlah']), x='Jumlah', y='Nama Barang', orientation='h', text_auto='.2s')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}); st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            st.subheader("🏪 Top 10 Outlet")
            fig_out = px.bar(df_t3.groupby('Nama Outlet')['Jumlah'].sum().nlargest(10).reset_index(), x='Jumlah', y='Nama Outlet', orientation='h', text_auto='.2s', color_discrete_sequence=['#2980b9'])
            fig_out.update_layout(yaxis={'categoryorder':'total ascending'}); st.plotly_chart(fig_out, use_container_width=True)
            
    with t5:
        st.subheader("🚀 Kejar Omset (Actionable Insights)")
        st.write("#### 🚨 Toko Tidur (Potensi Hilang)"); st.caption("Toko yang bertransaksi di masa lalu tetapi TIDAK bertransaksi di periode yang dipilih.")
        sleeping_outlets = list(set(df_scope_all['Nama Outlet'].unique()) - set(df_active_tab['Nama Outlet'].unique()))
        
        if sleeping_outlets:
            st.warning(f"Ada {len(sleeping_outlets)} toko yang belum order di periode ini.")
            with st.expander("Lihat Daftar Toko Tidur"):
                sleeping_df = df_scope_all[df_scope_all['Nama Outlet'].isin(sleeping_outlets)]
                last_dates, sales_handlers = sleeping_df.groupby('Nama Outlet')['Tanggal'].max(), sleeping_df.groupby('Nama Outlet')['Penjualan'].first()
                last_trx = [{"Nama Toko": outlet, "Sales": sales_handlers.get(outlet, "-"), "Terakhir Order": "Belum Pernah Order (Toko Master)" if last_dates.get(outlet, pd.to_datetime('2000-01-01')).year == 2000 else last_dates.get(outlet).strftime('%d %b %Y'), "Hari Sejak Order Terakhir": 99999 if last_dates.get(outlet, pd.to_datetime('2000-01-01')).year == 2000 else (datetime.date.today() - last_dates.get(outlet).date()).days} for outlet in sleeping_outlets]
                df_sleeping = pd.DataFrame(last_trx).sort_values("Hari Sejak Order Terakhir"); df_sleeping["Hari Sejak Order Terakhir"] = df_sleeping["Hari Sejak Order Terakhir"].replace(99999, "Baru/Master")
                st.dataframe(df_sleeping, use_container_width=True)
        else: st.success("Semua toko langganan sudah order di periode ini.")

        st.divider(); st.write("#### 💎 Peluang Cross-Selling (White Space Analysis)")
        relevant_brands = df_active_tab['Merk'].dropna().astype(str).unique()
        if len(relevant_brands) > 1:
            col_cs1, col_cs2 = st.columns(2)
            with col_cs1: brand_acuan = st.selectbox("Jika Toko sudah beli Brand:", sorted(relevant_brands), index=0)
            with col_cs2: brand_target = st.selectbox("Tapi BELUM beli Brand:", sorted([b for b in relevant_brands if b != brand_acuan]), index=0 if [b for b in relevant_brands if b != brand_acuan] else None)
            if brand_target:
                opportunities = [{"Nama Toko": outlet, "Salesman": df_active_tab[df_active_tab['Nama Outlet'] == outlet]['Penjualan'].iloc[0], "Potensi": f"Tawarkan {brand_target}"} for outlet in df_active_tab[df_active_tab['Merk'] == brand_acuan]['Nama Outlet'].unique() if df_active_tab[(df_active_tab['Nama Outlet'] == outlet) & (df_active_tab['Merk'] == brand_target)].empty]
                if opportunities: st.info(f"Ditemukan **{len(opportunities)} Toko** yang beli {brand_acuan} tapi belum beli {brand_target}."); st.dataframe(pd.DataFrame(opportunities), use_container_width=True)
                else: st.success(f"Semua toko yang beli {brand_acuan} juga sudah membeli {brand_target}.")
        else: st.info("Data tidak cukup untuk analisa cross-selling (perlu minimal 2 brand aktif).")
        
        st.divider(); st.write("#### 🧠 Rekomendasi Cross-Selling Cerdas (Berdasarkan Pola Transaksi)"); st.caption("AI menganalisa pola pembelian dari ribuan transaksi untuk menemukan rekomendasi tersembunyi.")
        recs_df = get_cross_sell_recommendations(df_scope_all)
        if recs_df is not None and not recs_df.empty: st.success(f"Ditemukan {len(recs_df)} rekomendasi cerdas berdasarkan pola pembelian."); st.dataframe(recs_df, use_container_width=True)
        elif recs_df is None: st.warning("Kolom 'No Faktur' atau 'Nama Barang' tidak ditemukan. Tidak bisa menghitung pola.")
        else: st.info("Tidak ada rekomendasi cerdas yang memenuhi threshold (confidence > 50%). Perlu lebih banyak data transaksi.")
        
        st.divider(); st.write("#### 🗺️ Master Visit Plan (Fokus 80/20 Customer Priority)"); st.caption("Tabel interaktif (bisa dicentang/diedit). Terapkan **5 Step Sales Visit**, **Consultative Selling**, dan **Fast Follow Up** pada toko-toko penyumbang 80% omset ini.")
        mvp_df = df_active_tab.groupby(['Nama Outlet'])['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=False)
        if mvp_df['Jumlah'].sum() > 0:
            mvp_df['Cum %'] = (mvp_df['Jumlah'] / mvp_df['Jumlah'].sum()).cumsum() * 100
            top_outlets_mvp = mvp_df[mvp_df['Cum %'] <= 80].copy()
            top_outlets_mvp['Salesman'] = top_outlets_mvp['Nama Outlet'].map(df_active_tab.groupby('Nama Outlet')['Penjualan'].first().to_dict())
            top_outlets_mvp.insert(0, 'Prioritas', range(1, len(top_outlets_mvp) + 1))
            top_outlets_mvp['📍 Route Plan (Hari)'], top_outlets_mvp['📋 5-Step Visit Done'], top_outlets_mvp['💡 Consultative Action'], top_outlets_mvp['🚀 Follow Up Done'] = "", False, "Cek Stok & Penawaran Baru", False
            top_outlets_mvp['Omset Historis'] = top_outlets_mvp['Jumlah'].apply(format_idr)
            st.info(f"🎯 Ditemukan **{len(top_outlets_mvp)} Toko Prioritas Utama** yang mewakili 80% omset Anda. Jadikan daftar ini sebagai panduan rute harian!")
            st.data_editor(top_outlets_mvp[['Prioritas', 'Nama Outlet', 'Salesman', 'Omset Historis', '📍 Route Plan (Hari)', '📋 5-Step Visit Done', '💡 Consultative Action', '🚀 Follow Up Done']], use_container_width=True, hide_index=True, disabled=['Prioritas', 'Nama Outlet', 'Salesman', 'Omset Historis'], column_config={"Jumlah": st.column_config.NumberColumn("Omset Historis", format="Rp %d"), "📍 Route Plan (Hari)": st.column_config.SelectboxColumn("Pilih Hari Kunjungan", options=["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"], required=True)})
        else: st.info("Belum ada data transaksi yang cukup untuk membuat Master Visit Plan.")
            
    with t_forecast:
        st.subheader("🔮 Prediksi Omset (Forecasting)"); st.info("Prediksi tren omset 30 hari ke depan berdasarkan data historis harian.")
        df_forecast = df_scope_all[df_scope_all['Tanggal'].dt.year > 2000].groupby('Tanggal')['Jumlah'].sum().reset_index().sort_values('Tanggal')
        if len(df_forecast) > 10:
            df_forecast['Date_Ordinal'] = df_forecast['Tanggal'].apply(lambda x: x.toordinal())
            z = np.polyfit(df_forecast['Date_Ordinal'].values, df_forecast['Jumlah'].values, 1); p = np.poly1d(z)
            future_dates = [df_forecast['Tanggal'].max() + datetime.timedelta(days=i) for i in range(1, 31)]
            df_combined = pd.concat([df_forecast[['Tanggal', 'Jumlah']].assign(Type='Historis'), pd.DataFrame({'Tanggal': future_dates, 'Jumlah': p([d.toordinal() for d in future_dates]), 'Type': 'Prediksi'})])
            fig_forecast = px.line(df_combined, x='Tanggal', y='Jumlah', color='Type', line_dash='Type', color_discrete_map={'Historis': '#2980b9', 'Prediksi': '#e74c3c'})
            fig_forecast.update_layout(title="Proyeksi Omset 30 Hari Kedepan", xaxis_title="Tanggal", yaxis_title="Omset")
            st.plotly_chart(fig_forecast, use_container_width=True); st.write(f"**Analisa Tren:** Berdasarkan data historis, tren penjualan terlihat **{'NAIK 📈' if z[0] > 0 else 'TURUN 📉'}**.")
        else: st.warning("Data belum cukup untuk melakukan prediksi (minimal 10 hari transaksi).")

    with t4:
        st.subheader("📋 Data Rincian & Analisis Spesifik")
        tab_pivot, tab_sku, tab_growth, tab_ba, tab_ai = st.tabs(["📊 Pivot Data Customer", "🛒 Detail SKU per Toko", "📈 Rekap Growth Brand", "🎯 Pencapaian Target BA", "🤖 AI Assistant (Gemini)"])
        
        with tab_pivot:
            list_merk_excel = sorted(df_scope_all['Merk'].dropna().astype(str).unique())
            list_tahun = sorted(df_scope_all['Tanggal'].dt.year.dropna().unique(), reverse=True)
            grp_cols = []
            if 'Kode_Global' in df_scope_all.columns: grp_cols.append('Kode_Global'); kd_asal = 'Kode_Global'
            else: df_scope_all['Kode_Global'] = "-"; grp_cols.append('Kode_Global'); kd_asal = 'Kode_Global'
            if 'Nama Customer' in df_scope_all.columns: grp_cols.append('Nama Customer')
            elif 'Nama Outlet' in df_scope_all.columns: grp_cols.append('Nama Outlet'); df_scope_all['Nama Customer'] = df_scope_all['Nama Outlet']
            else: df_scope_all['Nama Customer'] = "-"; grp_cols.append('Nama Customer')
            if 'Provinsi' in df_scope_all.columns: grp_cols.append('Provinsi')
            else: df_scope_all['Provinsi'] = "-"; grp_cols.append('Provinsi')
            if 'Kota' in df_scope_all.columns: grp_cols.append('Kota')
            else: df_scope_all['Kota'] = "-"; grp_cols.append('Kota')

            with st.form(key='pivot_filter_form'):
                col_piv1, col_piv2 = st.columns(2)
                with col_piv1: selected_merk_excel = st.selectbox("🎯 Pilih Merk:", ["SEMUA"] + list_merk_excel)
                with col_piv2: selected_tahun_excel = st.multiselect("🗓️ Pilih Tahun:", list_tahun, default=list_tahun)
                st.markdown("#### 🔎 Filter Spesifik (Batch Processing)")
                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                with col_f1: filter_kode = st.multiselect("Kode Customer:", sorted(df_scope_all[kd_asal].astype(str).unique()), placeholder="Pilih Kode...")
                with col_f2: filter_nama = st.multiselect("Nama Customer:", sorted(df_scope_all['Nama Outlet'].astype(str).unique()) if 'Nama Outlet' in df_scope_all.columns else sorted(df_scope_all['Nama Customer'].astype(str).unique()), placeholder="Pilih Customer...")
                with col_f3: filter_provinsi = st.multiselect("Provinsi:", sorted(df_scope_all['Provinsi'].astype(str).unique()), placeholder="Pilih Provinsi...")
                with col_f4: filter_kota = st.multiselect("Kota:", sorted(df_scope_all['Kota'].astype(str).unique()), placeholder="Pilih Kota...")
                maximize_toggle = st.toggle("🗖 Mode Layar Penuh (Tabel Super Lebar)")
                submit_button = st.form_submit_button(label='🚀 Terapkan Filter (Super Cepat)', use_container_width=True)

            master_pivot = generate_pivot_fast(df_scope_all, selected_merk_excel, tuple(selected_tahun_excel), tuple(grp_cols), BRAND_PREFIXES)

            if not master_pivot.empty:
                bulan_indo_map = {1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'}
                for i in range(1, 13):
                    if i not in master_pivot.columns: master_pivot[i] = 0
                cols_to_keep = [c for c in grp_cols if c in master_pivot.columns] + list(range(1, 13))
                master_pivot = master_pivot[cols_to_keep]
                master_pivot.columns = [bulan_indo_map[c] if isinstance(c, int) else c for c in cols_to_keep]
                master_pivot['Total Penjualan'] = master_pivot[list(bulan_indo_map.values())].sum(axis=1)
                master_pivot = master_pivot.rename(columns={'Kode_Global': 'Kode Customer'})
                for col in ['Kode Customer', 'Nama Customer', 'Provinsi', 'Kota']:
                    if col not in master_pivot.columns: master_pivot[col] = "-"

                df_filtered = master_pivot.copy()
                if filter_kode: df_filtered = df_filtered[df_filtered['Kode Customer'].astype(str).isin(filter_kode)]
                if filter_nama: df_filtered = df_filtered[df_filtered['Nama Customer'].astype(str).isin(filter_nama)]
                if filter_provinsi: df_filtered = df_filtered[df_filtered['Provinsi'].astype(str).isin(filter_provinsi)]
                if filter_kota: df_filtered = df_filtered[df_filtered['Kota'].astype(str).isin(filter_kota)]

                st.caption(f"Menampilkan {len(df_filtered)} data customer.")

                if not df_filtered.empty:
                    bulan_indo_list = list(bulan_indo_map.values())
                    num_cols = bulan_indo_list + ['Total Penjualan']
                    total_dict = {col: "" for col in df_filtered.columns}
                    total_dict['Nama Customer'] = "GRAND TOTAL" 
                    for col in num_cols: total_dict[col] = df_filtered[col].sum()
                    
                    df_display = pd.concat([df_filtered, pd.DataFrame([total_dict])], ignore_index=True)
                    df_display = df_display.loc[:, ~df_display.columns.duplicated()] # PENGHANCUR KOLOM GANDA

                    html_table = get_datatable_html(df_display, num_cols, "pivotDataTbl")
                    
                    if maximize_toggle:
                        st.markdown("""<style>header {display: none !important;} [data-testid="stSidebar"] {display: none !important;} .block-container {max-width: 100% !important; padding: 1rem !important;}</style>""", unsafe_allow_html=True)
                        st.info("ℹ️ Mode Layar Penuh aktif. Hilangkan centang pada toggle 'Mode Layar Penuh' di atas untuk kembali.")
                        components.html(html_table, height=800, scrolling=True)
                    else:
                        components.html(html_table, height=600, scrolling=True)
                else: st.info("Data Kosong setelah difilter.")
                    
                user_role_lower = role.lower()
                if user_role_lower in ['direktur', 'manager', 'supervisor']:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        if 'df_display' in locals() and not df_display.empty: df_display.to_excel(writer, index=False, sheet_name='Master Data')
                        workbook, worksheet = writer.book, writer.sheets['Master Data']
                        user_identity = f"{st.session_state.get('sales_name', 'Unknown')} ({st.session_state.get('role', 'Unknown').upper()})"
                        worksheet.set_header(f'&C&10CONFIDENTIAL DOCUMENT | TRACKED USER: {user_identity} | DOWNLOADED: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | DO NOT DISTRIBUTE')
                        worksheet.set_column('D:P', None, workbook.add_format({'num_format': '#,##0'})) 
                        if 'df_display' in locals() and not df_display.empty: worksheet.set_row(len(df_display), None, workbook.add_format({'bold': True, 'bg_color': '#f2f2f2', 'border': 1, 'num_format': '#,##0'}))
                    st.download_button(label="📥 Download Laporan Excel (XLSX)", data=output.getvalue(), file_name=f"Laporan_Master_{selected_merk_excel}_{datetime.date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else: st.info("Data Kosong.")

        with tab_sku:
            st.markdown("### 🛒 Detail SKU per Toko")
            df_sku_base = df_scope_all.copy()
            kd_asal = 'Kode_Global' if 'Kode_Global' in df_sku_base.columns else 'Kode Customer'
            
            # --- CASCADING DROPDOWN ---
            col_s1, col_s2 = st.columns(2)
            with col_s1: selected_merk_sku = st.selectbox("🎯 Pilih Merk:", ["SEMUA"] + sorted([m for m in df_sku_base['Merk'].dropna().astype(str).unique() if m != "-"]), key='merk_sku')
            with col_s2: selected_tahun_sku = st.multiselect("🗓️ Pilih Tahun:", sorted(df_sku_base['Tanggal'].dt.year.dropna().unique(), reverse=True), default=sorted(df_sku_base['Tanggal'].dt.year.dropna().unique(), reverse=True), key='tahun_sku')
                
            df_sku_for_options = df_sku_base.copy()
            if selected_merk_sku != "SEMUA":
                prefix_tuple = tuple(BRAND_PREFIXES.get(selected_merk_sku, [selected_merk_sku[:3].upper()]))
                df_sku_for_options = df_sku_for_options[(df_sku_for_options['Merk'] == selected_merk_sku) | (df_sku_for_options[kd_asal].astype(str).str.strip().str.upper().apply(lambda x: any(x.startswith(p) for p in prefix_tuple)))]
                
            with st.form(key='sku_filter_form'):
                st.markdown("#### 🔎 Filter Spesifik (Batch Processing)")
                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                with col_f1: filter_kode_sku = st.multiselect("Kode Customer:", sorted(df_sku_for_options[kd_asal].astype(str).unique()), placeholder="Pilih Kode...")
                with col_f2: filter_nama_sku = st.multiselect("Nama Customer:", sorted(df_sku_for_options['Nama Outlet'].astype(str).unique()), placeholder="Pilih Customer...")
                with col_f3: filter_provinsi_sku = st.multiselect("Provinsi:", sorted(df_sku_for_options['Provinsi'].astype(str).unique()), placeholder="Pilih Provinsi...")
                with col_f4: filter_kota_sku = st.multiselect("Kota:", sorted(df_sku_for_options['Kota'].astype(str).unique()), placeholder="Pilih Kota...")
                filter_sku_spesifik = st.multiselect("📦 Nama Barang (SKU):", sorted(df_sku_for_options['Nama Barang'].dropna().astype(str).unique()), placeholder="Pilih SKU spesifik (Kosongkan untuk melihat semua)...")
                submit_button_sku = st.form_submit_button(label='🚀 Terapkan Filter (Super Cepat)', use_container_width=True)

            df_sku_filtered = df_sku_for_options.copy() 
            if selected_tahun_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered['Tanggal'].dt.year.isin(selected_tahun_sku)]
            if filter_kode_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered[kd_asal].astype(str).isin(filter_kode_sku)]
            if filter_nama_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered['Nama Outlet'].astype(str).isin(filter_nama_sku)]
            if filter_provinsi_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered['Provinsi'].astype(str).isin(filter_provinsi_sku)]
            if filter_kota_sku: df_sku_filtered = df_sku_filtered[df_sku_filtered['Kota'].astype(str).isin(filter_kota_sku)]
            if filter_sku_spesifik: df_sku_filtered = df_sku_filtered[df_sku_filtered['Nama Barang'].astype(str).isin(filter_sku_spesifik)]

            if not filter_nama_sku and not filter_sku_spesifik:
                st.info("👈 Silakan pilih minimal 1 'Nama Customer' ATAU 'Nama Barang (SKU)' di kotak pencarian atas lalu klik 'Terapkan Filter' untuk melihat detail transaksi.")
            else:
                st.caption(f"Menampilkan transaksi dari {df_sku_filtered['Nama Outlet'].nunique()} toko.")
                if not df_sku_filtered.empty:
                    df_sku_filtered['Bulan Angka'] = df_sku_filtered['Tanggal'].dt.month
                    
                    # --- CHAMELEON TABLE LOGIC (TABEL BUNGLON) ---
                    if filter_sku_spesifik and not filter_nama_sku:
                        pivot_idx, display_label = 'Nama Outlet', 'Nama Customer'
                        df_sku_filtered['Pivot_Index'] = df_sku_filtered['Nama Outlet']
                    elif filter_nama_sku and not filter_sku_spesifik:
                        pivot_idx, display_label = 'Nama Barang', 'Nama Barang'
                        df_sku_filtered['Pivot_Index'] = df_sku_filtered['Nama Barang']
                    else:
                        pivot_idx, display_label = 'Pivot_Index', 'Customer ➔ SKU'
                        df_sku_filtered['Pivot_Index'] = df_sku_filtered['Nama Outlet'].astype(str) + " ➔ " + df_sku_filtered['Nama Barang'].astype(str)
                        
                    pivot_sku = pd.pivot_table(df_sku_filtered, values='Jumlah', index='Pivot_Index', columns='Bulan Angka', aggfunc='sum', fill_value=0).reset_index()
                    bulan_indo_map = {1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'}
                    for i in range(1, 13):
                        if i not in pivot_sku.columns: pivot_sku[i] = 0
                        
                    pivot_sku = pivot_sku[['Pivot_Index'] + list(range(1, 13))]
                    pivot_sku.columns = [display_label] + [bulan_indo_map[i] for i in range(1, 13)]
                    pivot_sku['Total Penjualan'] = pivot_sku[list(bulan_indo_map.values())].sum(axis=1)
                    
                    total_dict_sku = {col: pivot_sku[col].sum() for col in [bulan_indo_map[i] for i in range(1, 13)] + ['Total Penjualan']}
                    total_dict_sku[display_label] = "GRAND TOTAL"
                    df_display_sku = pd.concat([pivot_sku, pd.DataFrame([total_dict_sku])], ignore_index=True)
                    df_display_sku = df_display_sku.loc[:, ~df_display_sku.columns.duplicated()] # Hancurkan kolom duplikat
                    
                    # --- RENDER DATATABLES (OPSI B) ---
                    html_table_sku = get_datatable_html(df_display_sku, list(bulan_indo_map.values()) + ['Total Penjualan'], "skuDataTbl")
                    components.html(html_table_sku, height=600, scrolling=True)
                    
                    if role.lower() in ['direktur', 'manager', 'supervisor']:
                        output_sku = io.BytesIO()
                        with pd.ExcelWriter(output_sku, engine='xlsxwriter') as writer:
                            df_display_sku.to_excel(writer, index=False, sheet_name='Detail SKU')
                            workbook, worksheet = writer.book, writer.sheets['Detail SKU']
                            worksheet.set_header(f'&C&10CONFIDENTIAL DOCUMENT | TRACKED USER: {user_name} ({role.upper()}) | DOWNLOADED: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
                            worksheet.set_column('B:N', None, workbook.add_format({'num_format': '#,##0'}))
                            worksheet.set_row(len(df_display_sku), None, workbook.add_format({'bold': True, 'bg_color': '#f2f2f2', 'border': 1, 'num_format': '#,##0'}))
                        st.download_button(label="📥 Download Detail SKU (Excel)", data=output_sku.getvalue(), file_name=f"Detail_SKU_{datetime.date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else: st.warning("Tidak ada transaksi untuk filter tersebut.")

        with tab_growth:
            st.markdown("### 📈 Rekap Growth Brand")
            list_merk_growth = sorted([m for m in df['Merk'].dropna().astype(str).unique() if m != "-"])
            if list_merk_growth:
                brand_growth = st.selectbox("Pilih Brand untuk Analisis Growth:", list_merk_growth)
                df_team_all = df[df['Penjualan'].isin(list(TARGET_DATABASE[target_sales_filter.upper()].keys())) if target_sales_filter != "SEMUA" and target_sales_filter.upper() in TARGET_DATABASE else (df['Penjualan'] == target_sales_filter if target_sales_filter != "SEMUA" else df['Penjualan'].notna())].copy()
                df_team_all['ID_Patokan'] = np.where(df_team_all['Kode_Global'].str.strip().str.upper().isin(['-', '', 'NAN', 'NONE', '0.0']), df_team_all['Nama Outlet'].str.strip(), df_team_all['Kode_Global'].str.strip())
                prefix_tuple = tuple(BRAND_PREFIXES.get(brand_growth, [brand_growth[:3].upper()]))
                is_valid_ro = (df_team_all['Merk'] == brand_growth) | (df_team_all['Kode_Global'].astype(str).str.strip().str.upper().apply(lambda x: any(x.startswith(p) for p in prefix_tuple)))

                if st.checkbox("🔍 Buka Radar Detektif (Cek Toko Double)"):
                    df_cek, kd_col_cek = df_team_all[is_valid_ro].copy(), 'Kode_Global' if 'Kode_Global' in df_team_all.columns else 'Kode Customer'
                    if kd_col_cek in df_cek.columns:
                        duplikat = df_cek.groupby('Nama Outlet')[kd_col_cek].nunique().reset_index()
                        toko_double = duplikat[duplikat[kd_col_cek] > 1]['Nama Outlet'].tolist()
                        if toko_double:
                            st.error(f"🚨 Ditemukan {len(toko_double)} Toko yang tercatat ganda (karena beda Kode)!")
                            st.dataframe(df_cek[df_cek['Nama Outlet'].isin(toko_double)][['Nama Outlet', kd_col_cek, 'Provinsi', 'Kota']].drop_duplicates().sort_values('Nama Outlet'), use_container_width=True)
                        else: st.success("✅ Tidak ada nama toko yang kodenya ganda.")
                    else: st.warning("Kolom Kode tidak ditemukan untuk pengecekan.")

                if not df_team_all.empty:
                    df_team_all['Tahun'], df_team_all['Bulan'], df_team_all['Bulan-Tahun'] = df_team_all['Tanggal'].dt.year, df_team_all['Tanggal'].dt.month, df_team_all['Tanggal'].dt.to_period('M')
                    ro_accumulated = set(df_team_all[(df_team_all['Bulan-Tahun'] < pd.Period('2026-01', freq='M')) & is_valid_ro]['ID_Patokan'].dropna().unique())
                    growth_data = []
                    
                    for m in range(1, 13):
                        period = pd.Period(f"2026-{m:02d}", freq='M')
                        current_ao = set(df_team_all[(df_team_all['Bulan-Tahun'] == period) & (df_team_all['Merk'] == brand_growth)]['ID_Patokan'].dropna().unique())
                        sales = df_team_all[(df_team_all['Bulan-Tahun'] == period) & (df_team_all['Merk'] == brand_growth)]['Jumlah'].sum()
                        noo = len(current_ao - ro_accumulated)
                        ro_accumulated.update(df_team_all[(df_team_all['Bulan-Tahun'] == period) & is_valid_ro]['ID_Patokan'].dropna().unique())
                        ro, ao = len(ro_accumulated), len(current_ao)
                        growth_data.append({'Year': 2026, 'Month': m, 'SALES': sales, 'RO': ro, 'AO': ao, 'AO VS RO %': (ao / ro) if ro > 0 else 0, 'NOO': noo})
                    
                    df_growth_all = pd.DataFrame(growth_data)
                    if not df_growth_all.empty:
                        bulan_dict_short = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
                        st.divider(); st.write(f"#### **Tabel 1: Aktivitas Outlet {brand_growth} (Tahun 2026)**")
                        display_2026 = [{'MONTH': f"{bulan_dict_short[m]}-26", 'SALES': r['SALES'], 'RO': int(r['RO']), 'AO': int(r['AO']), 'AO VS RO %': r['AO VS RO %'], 'NOO': int(r['NOO'])} if not (row := df_growth_all[(df_growth_all['Year'] == 2026) & (df_growth_all['Month'] == m)]).empty and not isinstance((r := row.iloc[0]), type(None)) else {'MONTH': f"{bulan_dict_short[m]}-26", 'SALES': 0, 'RO': 0, 'AO': 0, 'AO VS RO %': 0, 'NOO': 0} for m in range(1, 13)]
                        
                        def style_tab1(row): return ['border: 1px solid #dcdcdc; ' + (f'background-color: {get_color_achv(row[col])}; color: black;' if col == 'AO VS RO %' else '') for col in row.index]
                        st.dataframe(pd.DataFrame(display_2026).style.format({'SALES': 'Rp {:,.0f}', 'AO VS RO %': '{:.0%}'}).apply(style_tab1, axis=1), use_container_width=True)
                        
                        st.divider(); col_g1, col_g2 = st.columns(2)
                        df_2025, df_2026_sales = df_team_all[df_team_all['Tahun'] == 2025], df_growth_all[df_growth_all['Year'] == 2026]
                        
                        with col_g1:
                            st.write(f"#### **Tabel 2: {brand_growth} 2025 vs 2026 Sales Growth**")
                            yoy_data, tot_2025, tot_2026 = [], 0, 0
                            for m in range(1, 13):
                                s25 = df_2025[(df_2025['Bulan'] == m) & (df_2025['Merk'] == brand_growth)]['Jumlah'].sum()
                                s26 = df_2026_sales[df_2026_sales['Month'] == m]['SALES'].sum() if not df_2026_sales[df_2026_sales['Month'] == m].empty else 0
                                tot_2025 += s25; tot_2026 += s26
                                yoy_data.append({'MONTH': bulan_dict_short[m], 'SALES 2025': s25, 'SALES 2026': s26, 'Growth MTM': ((s26 - s25) / s25) if s25 > 0 else (1 if s26 > 0 else 0)})
                            df_t2_display = pd.concat([pd.DataFrame(yoy_data), pd.DataFrame([{'MONTH': 'Total Sales', 'SALES 2025': tot_2025, 'SALES 2026': tot_2026, 'Growth MTM': ((tot_2026 - tot_2025) / tot_2025) if tot_2025 > 0 else (1 if tot_2026 > 0 else 0)}])], ignore_index=True)
                            
                            def style_tab2(row): return ['border: 1px solid #dcdcdc; ' + (f"background-color: {get_color_achv(row[col])}; color: black; font-weight: bold;" if col == 'Growth MTM' else 'background-color: lightblue; font-weight: bold; color: black;') if row['MONTH'] == 'Total Sales' else 'border: 1px solid #dcdcdc; ' + (f"background-color: {get_color_achv(row[col])}; color: black;" if col == 'Growth MTM' else '') for col in row.index]
                            st.dataframe(df_t2_display.style.format({'SALES 2025': 'Rp {:,.0f}', 'SALES 2026': 'Rp {:,.0f}', 'Growth MTM': '{:.0%}'}).apply(style_tab2, axis=1), use_container_width=True)
                        
                        with col_g2:
                            st.write(f"#### **Tabel 3: Quarterly Growth**")
                            q_data = []
                            for q, m_start in [('Q1', 1), ('Q2', 4), ('Q3', 7), ('Q4', 10)]:
                                q_2025 = sum(df_2025[(df_2025['Bulan'] == m) & (df_2025['Merk'] == brand_growth)]['Jumlah'].sum() for m in range(m_start, m_start + 3))
                                q_2026 = sum(df_2026_sales[df_2026_sales['Month'] == m]['SALES'].sum() if not df_2026_sales[df_2026_sales['Month'] == m].empty else 0 for m in range(m_start, m_start + 3))
                                q_data.append({'MONTH': f"Total {q}", 'SALES 2025': q_2025, 'SALES 2026': q_2026, 'Growth MTM': ((q_2026 - q_2025) / q_2025) if q_2025 > 0 else (1 if q_2026 > 0 else 0)})
                            st.dataframe(pd.concat([pd.DataFrame(q_data), pd.DataFrame([{'MONTH': 'Total Sales', 'SALES 2025': tot_2025, 'SALES 2026': tot_2026, 'Growth MTM': ((tot_2026 - tot_2025) / tot_2025) if tot_2025 > 0 else (1 if tot_2026 > 0 else 0)}])], ignore_index=True).style.format({'SALES 2025': 'Rp {:,.0f}', 'SALES 2026': 'Rp {:,.0f}', 'Growth MTM': '{:.0%}'}).apply(style_tab2, axis=1), use_container_width=True)
                else: st.info(f"Belum ada data untuk brand {brand_growth}.")
            else: st.info("Tidak ada data.")

        with tab_ba:
            st.markdown("### 🎯 Pencapaian Target BA per Brand (Tahun 2026)")
            TARGET_BA_PER_BRAND = {"Careso": {"PT. PESONA ASIA GROUP ( GM STORE )": 30_000_000, "TOKO DUTA COSMETIK ( BIREUEN )": 50_000_000, "HIJRAH STORE COSMETIK": 50_000_000, "TOKO UNDERPRICE SKIN CARE": 50_000_000, "PT.RADYSA DHARMA ABADI": 50_000_000, "TOKO BEAUTY ART": 30_000_000, "PT.PINMOOD INDONESIA SEJAHTERA": 30_000_000}, "Somethinc": {"PT. PESONA ASIA GROUP ( GM STORE )": 40_000_000, "TOKO DUTA COSMETIK ( BIREUEN )": 25_000_000, "TOKO BEAUTY ART": 35_000_000}, "Javinci": {"HIJRAH STORE COSMETIK": 20_000_000, "TOKO UNDERPRICE SKIN CARE": 25_000_000, "PT.PINMOOD INDONESIA SEJAHTERA": 15_000_000}}
            if selected_ba_brand := st.selectbox("Pilih Brand untuk melihat Target BA:", list(TARGET_BA_PER_BRAND.keys())):
                current_target_dict = TARGET_BA_PER_BRAND[selected_ba_brand]
                df_ba_all = df_scope_all[(df_scope_all['Merk'] == selected_ba_brand) & (df_scope_all['Nama Outlet'].isin(current_target_dict.keys())) & (df_scope_all['Tanggal'].dt.year == 2026)].copy()
                bulan_dict_ba = {1:'Januari', 2:'Februari', 3:'Maret', 4:'April', 5:'Mei', 6:'Juni', 7:'Juli', 8:'Agustus', 9:'September', 10:'Oktober', 11:'November', 12:'Desember'}
                ba_df = pd.DataFrame(list(current_target_dict.items()), columns=['Costumer', 'Target BA'])
                
                if not df_ba_all.empty:
                    df_ba_all['Bulan Angka'] = df_ba_all['Tanggal'].dt.month
                    pivot_ba = pd.pivot_table(df_ba_all, values='Jumlah', index='Nama Outlet', columns='Bulan Angka', aggfunc='sum', fill_value=0)
                    for m in range(1, 13):
                        if m not in pivot_ba.columns: pivot_ba[m] = 0
                    pivot_ba = pivot_ba[list(range(1, 13))]
                    pivot_ba.columns = [bulan_dict_ba[m] for m in pivot_ba.columns]
                    merged_ba = pd.merge(ba_df, pivot_ba.reset_index().rename(columns={'Nama Outlet': 'Costumer'}), on='Costumer', how='left').fillna(0)
                else:
                    merged_ba = ba_df.copy()
                    for m in range(1, 13): merged_ba[bulan_dict_ba[m]] = 0
                
                st.write(f"**Rekap Keseluruhan Toko BA untuk Brand `{selected_ba_brand}` (2026)**")
                st.dataframe(merged_ba.style.format({col: 'Rp {:,.0f}' for col in list(bulan_dict_ba.values()) + ['Target BA']}), use_container_width=True, hide_index=True)
                
                st.divider(); selected_month_ba = st.selectbox(f"Pilih Bulan untuk Detail Achievement ({selected_ba_brand}):", list(bulan_dict_ba.values()))
                achv_data = [{'Costumer': row['Costumer'], 'Target BA': row['Target BA'], f'Pencapaian {selected_month_ba}': row[selected_month_ba], 'ACHV': (row[selected_month_ba] / row['Target BA']) if row['Target BA'] > 0 else 0} for _, row in merged_ba.iterrows()]
                total_target, total_achv = sum(row['Target BA'] for row in achv_data), sum(row[f'Pencapaian {selected_month_ba}'] for row in achv_data)
                df_achv_display = pd.concat([pd.DataFrame(achv_data), pd.DataFrame([{'Costumer': 'Total Achievement', 'Target BA': total_target, f'Pencapaian {selected_month_ba}': total_achv, 'ACHV': (total_achv/total_target) if total_target > 0 else 0}])], ignore_index=True)
                
                st.write(f"**Tabel Pencapaian Target BA `{selected_ba_brand}` - {selected_month_ba} 2026**")
                def style_ba(row): return ['border: 1px solid #dcdcdc; ' + (f"background-color: {get_color_achv(row[col])}; color: black; font-weight: bold;" if col == 'ACHV' else 'background-color: lightblue; font-weight: bold; color: black;') if row['Costumer'] == 'Total Achievement' else 'border: 1px solid #dcdcdc; ' + (f"background-color: {get_color_achv(row[col])}; color: black;" if col == 'ACHV' else '') for col in row.index]
                st.dataframe(df_achv_display.style.format({'Target BA': 'Rp {:,.0f}', f'Pencapaian {selected_month_ba}': 'Rp {:,.0f}', 'ACHV': '{:.0%}'}).apply(style_ba, axis=1), use_container_width=True)

        with tab_ai:
            st.markdown("### 🤖 Asisten AI Gemini (Enterprise Secure Mode)"); st.info("🔒 **Keamanan Aktif:** Sistem HANYA mengirimkan ringkasan angka statistik ke AI. Data mentah dan nama toko rahasia Anda tetap berada di dalam server ini.")
            try: import google.generativeai as genai; GENAI_AVAILABLE = True
            except ImportError: GENAI_AVAILABLE = False
                
            if not GENAI_AVAILABLE: st.error("⚠️ Library AI belum terinstal di Server. Pastikan Anda telah menambahkan 'google-generativeai' ke dalam file requirements.txt di Github Anda.")
            elif api_key_input := st.text_input("🔑 Masukkan API Key Gemini Anda:", type="password", help="Dapatkan API Key gratis di aistudio.google.com"):
                try:
                    genai.configure(api_key=api_key_input)
                    user_question = st.text_area("Tanya AI tentang performa data yang sedang Anda filter:", placeholder="Contoh: Berdasarkan data ini, apa evaluasi untuk tim sales?")
                    if st.button("💡 Analisis Sekarang"):
                        with st.spinner("AI sedang membaca ringkasan data Anda..."):
                            context = f"""TOTAL OMSET SAAT INI: Rp {current_omset_total:,.0f}\nJUMLAH TRANSAKSI: {transaksi_count}\n\nTOP 5 BRAND:\n{df_active.groupby('Merk')['Jumlah'].sum().nlargest(5).reset_index().to_string()}\n\nTOP 5 SALESMAN:\n{df_active.groupby('Penjualan')['Jumlah'].sum().nlargest(5).reset_index().to_string()}\n\nTOP 3 PRODUK PALING LAKU:\n{df_active.groupby('Nama Barang')['Jumlah'].sum().nlargest(3).reset_index().to_string()}"""
                            response, success_model = None, ""
                            for m_name in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-pro']:
                                try: response = genai.GenerativeModel(m_name).generate_content(f"Anda adalah Konsultan Bisnis Ahli. Berikut adalah ringkasan data penjualan perusahaan bulan ini:\n{context}\n\nPertanyaan User: {user_question}\nBerikan jawaban yang taktis, cerdas, profesional, dan berbahasa Indonesia."); success_model = m_name; break
                                except Exception: continue 
                            if response: st.success(f"Analisis Selesai! (Powered by {success_model})"); st.write(response.text)
                            else: st.error("Gagal! API Key Anda tidak memiliki akses ke versi Gemini apa pun.")
                except Exception as e: st.error(f"Koneksi gagal. Detail: {e}")

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if st.session_state['logged_in']: main_dashboard()
else: login_page()
