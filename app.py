# ==========================================
# 2. KONFIGURASI DATABASE DINAMIS (LEVEL 2 - FULL CONTROL)
# ==========================================

# 🔴 TUGAS ANDA: PASTE LINK CSV DARI GOOGLE SHEET DI SINI 🔴
URL_TARGETS     = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=2102937723&single=true&output=csv"
URL_MAP_SALES   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=518733046&single=true&output=csv"
URL_MAP_BRAND   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=1629420292&single=true&output=csv"
URL_USERS       = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=1022938468&single=true&output=csv"
URL_SYSTEM      = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"  # <--- LINK BARU (TAB 5)

@st.cache_data(ttl=300)
def load_configuration():
    try:
        # 1. Load Targets
        df_t = pd.read_csv(URL_TARGETS, on_bad_lines='skip')
        target_db, indiv_targets = {}, {}
        if not df_t.empty:
            for _, row in df_t.iterrows():
                try:
                    name, brand = str(row['Name']).strip(), str(row['Brand']).strip()
                    amt = float(str(row['Amount']).replace(',', '').replace('.', '').replace('Rp', ''))
                    if str(row['Type']).strip().upper() == 'SPV':
                        target_db.setdefault(name, {})[brand] = amt
                    elif str(row['Type']).strip().upper() == 'SALES':
                        indiv_targets.setdefault(name, {})[brand] = amt
                except: continue

        # 2. Load Mappings
        df_ms = pd.read_csv(URL_MAP_SALES, on_bad_lines='skip')
        sales_map = dict(zip(df_ms['Alias'], df_ms['Real_Name']))

        df_mb = pd.read_csv(URL_MAP_BRAND, on_bad_lines='skip')
        brand_map_raw = {} 
        for _, row in df_mb.iterrows():
            real, key = str(row['Real_Brand']), str(row['Keyword']).upper()
            brand_map_raw.setdefault(real, []).append(key)

        # 3. Load System Config (Data Transaction URL)
        df_sys = pd.read_csv(URL_SYSTEM, on_bad_lines='skip')
        # Ambil nilai dari baris dimana Key = DATA_URL
        data_url = df_sys.loc[df_sys['Key'] == 'DATA_URL', 'Value'].values[0]

        return target_db, indiv_targets, sales_map, brand_map_raw, data_url

    except Exception as e:
        return {}, {}, {}, {}, ""

# --- Load All Configs ---
TARGET_DATABASE, INDIVIDUAL_TARGETS, SALES_MAPPING, BRAND_ALIASES, DYNAMIC_DATA_URL = load_configuration()

# Hitung Total
if TARGET_DATABASE:
    SUPERVISOR_TOTAL_TARGETS = {k: sum(v.values()) for k, v in TARGET_DATABASE.items()}
    TARGET_NASIONAL_VAL = sum(SUPERVISOR_TOTAL_TARGETS.values())
else:
    SUPERVISOR_TOTAL_TARGETS, TARGET_NASIONAL_VAL = {}, 1

# ==========================================
# 3. CORE LOGIC
# ==========================================

def get_current_time_wib():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

def format_idr(value):
    try: return f"Rp {value:,.0f}".replace(",", ".")
    except: return "Rp 0"

def render_custom_progress(title, current, target):
    if target == 0: target = 1
    pct = (current / target) * 100
    visual_pct = min(pct, 100)
    bar_color = "linear-gradient(90deg, #e74c3c, #c0392b)" if pct < 50 else "linear-gradient(90deg, #f1c40f, #f39c12)" if pct < 80 else "linear-gradient(90deg, #2ecc71, #27ae60)"
    
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
                        z-index: 10; font-weight: 800; font-size: 13px; color: #222; text-shadow: 0px 0px 4px #fff;">
                {pct:.1f}%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    # MENGGUNAKAN URL DINAMIS DARI GOOGLE SHEET CONFIG
    if not DYNAMIC_DATA_URL:
        return None
        
    try:
        url_with_ts = f"{DYNAMIC_DATA_URL}&t={int(time.time())}"
        df = pd.read_csv(url_with_ts, dtype=str)
    except Exception:
        return None
    
    df.columns = df.columns.str.strip()
    required_cols = ['Penjualan', 'Merk', 'Jumlah', 'Tanggal']
    if not all(col in df.columns for col in required_cols): return None
    
    faktur_col = next((c for c in df.columns if 'faktur' in c.lower() or 'bukti' in c.lower()), None)
    if faktur_col: df = df.rename(columns={faktur_col: 'No Faktur'})
    
    if 'Nama Outlet' in df.columns:
        df = df[~df['Nama Outlet'].astype(str).str.match(r'^(Total|Jumlah|Subtotal|Grand|Rekap)', case=False, na=False)]
        df = df[df['Nama Outlet'].astype(str).str.strip() != ''] 

    if 'Nama Barang' in df.columns:
        df = df[~df['Nama Barang'].astype(str).str.match(r'^(Total|Jumlah)', case=False, na=False)]
        df = df[df['Nama Barang'].astype(str).str.strip() != ''] 

    if SALES_MAPPING: df['Penjualan'] = df['Penjualan'].astype(str).str.strip().replace(SALES_MAPPING)
    
    valid_sales_names = list(INDIVIDUAL_TARGETS.keys()) + list(TARGET_DATABASE.keys())
    df.loc[~df['Penjualan'].isin(valid_sales_names), 'Penjualan'] = 'Non-Sales'
    df['Penjualan'] = df['Penjualan'].astype('category')

    def normalize_brand(raw):
        if BRAND_ALIASES:
            raw_upper = str(raw).upper()
            for target, keywords in BRAND_ALIASES.items():
                for k in keywords:
                    if k in raw_upper: return target
        return raw
    df['Merk'] = df['Merk'].apply(normalize_brand).astype('category')
    
    df['Jumlah'] = pd.to_numeric(df['Jumlah'].astype(str).str.replace(r'[Rp\s.]', '', regex=True).str.replace(',', '.'), errors='coerce').fillna(0)
    
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce', format='mixed')
    df = df.dropna(subset=['Tanggal'])
    
    for c in ['Kota', 'Nama Outlet', 'Nama Barang', 'No Faktur']:
        if c in df.columns: df[c] = df[c].astype(str).str.strip()
            
    return df

def load_users_dynamic():
    try:
        # Cek apakah URL_USERS sudah diisi (bukan placeholder)
        if "PASTE_LINK" in URL_USERS: return pd.DataFrame()
        return pd.read_csv(URL_USERS, dtype=str)
    except: return pd.DataFrame()
