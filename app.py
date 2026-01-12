import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import time
import pytz
import io 
from calendar import monthrange

# --- 1. KONFIGURASI HALAMAN & CSS PREMIUM ---
st.set_page_config(
    page_title="Dashboard Sales Level 2", 
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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONFIGURASI DATABASE DINAMIS (LEVEL 2)
# ==========================================

# 🔴🔴🔴 PASTE 5 LINK CSV GOOGLE SHEET DI SINI 🔴🔴🔴
URL_TARGETS     = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=2102937723&single=true&output=csv"
URL_MAP_SALES   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=518733046&single=true&output=csv"
URL_MAP_BRAND   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=1629420292&single=true&output=csv"
URL_USERS       = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=1022938468&single=true&output=csv"
URL_SYSTEM      = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=598865740&single=true&output=csv" 

@st.cache_data(ttl=300)
def load_configuration():
    try:
        # 1. Load Targets
        df_t = pd.read_csv(URL_TARGETS, on_bad_lines='skip')
        target_db = {}
        indiv_targets = {}
        
        if not df_t.empty:
            for _, row in df_t.iterrows():
                try:
                    name = str(row['Name']).strip()
                    brand = str(row['Brand']).strip()
                    amt_str = str(row['Amount']).replace(',', '').replace('.', '').replace('Rp', '')
                    amount = float(amt_str)
                    
                    if str(row['Type']).strip().upper() == 'SPV':
                        if name not in target_db: target_db[name] = {}
                        target_db[name][brand] = amount
                    elif str(row['Type']).strip().upper() == 'SALES':
                        if name not in indiv_targets: indiv_targets[name] = {}
                        indiv_targets[name][brand] = amount
                except: continue

        # 2. Load Sales Mapping
        df_ms = pd.read_csv(URL_MAP_SALES, on_bad_lines='skip')
        sales_map = dict(zip(df_ms['Alias'], df_ms['Real_Name']))

        # 3. Load Brand Aliases
        df_mb = pd.read_csv(URL_MAP_BRAND, on_bad_lines='skip')
        brand_map_raw = {} 
        for _, row in df_mb.iterrows():
            real = str(row['Real_Brand'])
            key = str(row['Keyword']).upper()
            if real not in brand_map_raw: brand_map_raw[real] = []
            brand_map_raw[real].append(key)

        return target_db, indiv_targets, sales_map, brand_map_raw

    except Exception as e:
        return {}, {}, {}, {}

# --- Load Config saat Startup ---
TARGET_DATABASE, INDIVIDUAL_TARGETS, SALES_MAPPING, BRAND_ALIASES = load_configuration()

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
    # LANGSUNG BACA URL SYSTEM SEBAGAI DATA TRANSAKSI
    if "PASTE_LINK" in URL_SYSTEM: return None
    try:
        url_with_ts = f"{URL_SYSTEM}&t={int(time.time())}"
        df = pd.read_csv(url_with_ts, dtype=str)
    except Exception: return None
    
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
        if "PASTE_LINK" in URL_USERS: return pd.DataFrame()
        return pd.read_csv(URL_USERS, dtype=str)
    except: return pd.DataFrame()

# ==========================================
# 4. MAIN DASHBOARD LOGIC
# ==========================================

def login_page():
    st.markdown("<br><br><h1 style='text-align: center;'>🦅 Executive Command Center</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Masuk Sistem", use_container_width=True)
                
                if submitted:
                    users = load_users_dynamic()
                    if users.empty:
                        st.error("Gagal memuat database user. Cek konfigurasi URL_USERS.")
                    else:
                        match = users[(users['username'] == username) & (users['password'] == password)]
                        if not match.empty:
                            st.session_state['logged_in'] = True
                            st.session_state['role'] = match.iloc[0]['role']
                            st.session_state['sales_name'] = match.iloc[0]['sales_name']
                            st.success("Login Berhasil! Mengalihkan...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Username atau Password salah.")

def main_dashboard():
    with st.sidebar:
        st.write("## 👤 User Profile")
        st.info(f"**{st.session_state['sales_name']}**\n\nRole: {st.session_state['role'].upper()}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
        st.markdown("---")
        st.caption(f"Last Updated: {get_current_time_wib().strftime('%H:%M:%S')} WIB")
            
    df = load_data()
    if df is None or df.empty:
        st.error("⚠️ Gagal memuat data Transaksi! Periksa Link di Config Tab SYSTEM.")
        return

    st.sidebar.subheader("📅 Filter Periode")
    col_p1, col_p2 = st.sidebar.columns(2)
    if col_p1.button("Bulan Ini", use_container_width=True):
        today = datetime.date.today()
        st.session_state['start_date'] = today.replace(day=1)
        st.session_state['end_date'] = today
    
    if 'start_date' not in st.session_state:
        st.session_state['start_date'] = df['Tanggal'].max().date().replace(day=1)
        st.session_state['end_date'] = df['Tanggal'].max().date()

    date_range = st.sidebar.date_input("Rentang Waktu", [st.session_state['start_date'], st.session_state['end_date']])

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
            if sub_filter == "SEMUA": df_scope_all = df_spv_raw
            else: df_scope_all = df_spv_raw[df_spv_raw['Penjualan'] == sub_filter]
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
    
    valid_faktur = df_active['No Faktur'].astype(str) if 'No Faktur' in df_active.columns else pd.Series()
    if not valid_faktur.empty:
        valid_faktur = valid_faktur[~valid_faktur.isin(['nan', 'None', '', '-', '0', 'None', '.'])]
        valid_faktur = valid_faktur[valid_faktur.str.len() > 2]
        transaksi_count = valid_faktur.nunique()
    else:
        transaksi_count = len(df_active)
    c3.metric("🧾 Transaksi", f"{transaksi_count}")

    try:
        from calendar import monthrange
        today = datetime.date.today()
        if len(date_range) == 2 and (date_range[1].month == today.month and date_range[1].year == today.year):
            days_in_month = monthrange(today.year, today.month)[1]
            day_current = today.day
            if day_current > 0:
                run_rate = (current_omset_total / day_current) * days_in_month
                st.info(f"📈 **Proyeksi Akhir Bulan (Run Rate):** {format_idr(run_rate)} (Estimasi)")
    except: pass

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
        st.markdown("---")

    t1, t2, t_detail_sales, t3, t4 = st.tabs(["📊 Rapor Brand", "📈 Tren Harian", "👥 Detail Tim", "🏆 Top Produk", "📋 Data Rincian"])
    
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
                        "Rank": 0, 
                        "Item": brand,
                        "Supervisor": spv,
                        "Target": format_idr(target),
                        "Realisasi": format_idr(realisasi_brand),
                        "Ach (%)": f"{pct_brand:.0f}%",
                        "Bar": pct_brand / 100, 
                        "Progress (Detail %)": pct_brand 
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
                    bg_color = '#d1e7dd' if pct >= 80 else '#fff3cd' if pct >= 50 else '#f8d7da'
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
            for spv_brands in TARGET_DATABASE.values(): allowed_brands.extend(spv_brands.keys())
        elif is_supervisor_account:
            allowed_brands = list(TARGET_DATABASE[my_name_key].keys())
        
        if allowed_brands:
            selected_brand_detail = st.selectbox("Pilih Brand untuk Detail Sales:", sorted(set(allowed_brands)))
            if selected_brand_detail:
                sales_stats = []
                total_brand_sales = 0
                total_brand_target = 0
                today = datetime.date.today()
                
                next_month = today.replace(day=28) + datetime.timedelta(days=4)
                last_day_month = next_month - datetime.timedelta(days=next_month.day)
                date_range_rest = pd.date_range(start=today, end=last_day_month)
                remaining_workdays = sum(1 for d in date_range_rest if d.weekday() != 6) # Excluding Sundays
                
                if len(date_range) == 2:
                    start_d, end_d = date_range
                    total_days = (end_d - start_d).days + 1
                    if end_d < today: days_gone = total_days
                    elif start_d > today: days_gone = 0
                    else:
                        days_gone = (today - start_d).days + 1
                        if days_gone > total_days: days_gone = total_days
                        if days_gone < 0: days_gone = 0
                else:
                    total_days = 1
                    days_gone = 1
                
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
                    m1, m2, m3 = st.columns(3)
                    m1.metric(f"Total Target {selected_brand_detail}", format_idr(total_brand_target))
                    m2.metric(f"Total Omset {selected_brand_detail}", format_idr(total_brand_sales))
                    ach_total = (total_brand_sales/total_brand_target)*100 if total_brand_target > 0 else 0
                    m3.metric("Total Ach %", f"{ach_total:.1f}%")
                else: st.info(f"Belum ada data target sales individu untuk brand {selected_brand_detail}")
        else: st.info("Menu ini khusus untuk melihat detail tim sales per brand.")

    with t3:
        st.subheader("📊 Pareto Analysis (80/20 Rule)")
        pareto_df = df_active.groupby('Nama Barang')['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=False)
        total_omset_pareto = pareto_df['Jumlah'].sum()
        pareto_df['Kontribusi %'] = (pareto_df['Jumlah'] / total_omset_pareto) * 100
        pareto_df['Cumulative %'] = pareto_df['Kontribusi %'].cumsum()
        top_performers = pareto_df[pareto_df['Cumulative %'] <= 80]
        
        col_pareto1, col_pareto2 = st.columns(2)
        col_pareto1.metric("Total Produk Unik", len(pareto_df))
        col_pareto2.metric("Produk Kontributor Utama (80%)", len(top_performers))
        st.dataframe(top_performers.style.format({'Jumlah': 'Rp {:,.0f}', 'Kontribusi %': '{:.2f}%', 'Cumulative %': '{:.2f}%'}), use_container_width=True)
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

    with t4:
        st.subheader("📋 Rincian Transaksi Lengkap")
        with st.expander("🕵️‍♂️ DETEKTIF DATA: Cek Transaksi Terbesar"):
            st.warning("Gunakan tabel ini untuk mencari baris 'Total' yang menyusup.")
            st.dataframe(df_active.nlargest(10, 'Jumlah')[['Tanggal', 'Nama Outlet', 'Nama Barang', 'Jumlah']], use_container_width=True)

        cols_to_show = ['Tanggal', 'No Faktur', 'Nama Outlet', 'Merk', 'Nama Barang', 'Jumlah', 'Penjualan']
        final_cols = [c for c in cols_to_show if c in df_active.columns]
        st.dataframe(df_active[final_cols].sort_values('Tanggal', ascending=False), use_container_width=True, hide_index=True, column_config={"Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"), "Jumlah": st.column_config.NumberColumn("Omset", format="Rp %d")})
        
        if role.lower() in ['manager', 'direktur']:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_active[final_cols].to_excel(writer, index=False, sheet_name='Sales Data')
                workbook = writer.book
                worksheet = writer.sheets['Sales Data']
                format1 = workbook.add_format({'num_format': '#,##0'})
                worksheet.set_column('F:F', None, format1) 
            st.download_button(label="📥 Download Laporan Excel (XLSX)", data=output.getvalue(), file_name=f"Laporan_Sales_{datetime.date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- 5. ALUR UTAMA ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()
