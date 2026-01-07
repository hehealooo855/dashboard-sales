import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import re 

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sales Dashboard Pro", layout="wide")

# --- DATABASE TARGET (BRAND) ---
TARGET_DATABASE = {
    "LISMAN": {
        "Bonavie": 50_000_000, "Whitelab": 100_000_000, "Goute": 50_000_000,
        "Dorskin": 50_000_000, "Gloow & Be": 100_000_000,
        "Javinci": 1_300_000_000, "Madam G": 100_000_000, "Careso": 400_000_000,
        "Artist Inc": 130_000_000, "Newlab": 150_000_000, "Mlen": 0
    },
    "AKBAR": {
        "Thai": 300_000_000, "Inesia": 100_000_000, "Honor": 125_000_000, "Vlagio": 75_000_000,
        "Y2000": 180_000_000, "Diosys": 520_000_000, 
        "Sociolla": 600_000_000, "Skin1004": 400_000_000,
        "Masami": 40_000_000, "Oimio": 0, "Cassandra": 30_000_000, "Clinelle": 80_000_000
    },
    "WILLIAM": {
        "The Face": 600_000_000, "Yu Chun Mei": 450_000_000, "Milano": 50_000_000, "Remar": 0,
        "Beautica": 100_000_000, "Walnutt": 50_000_000, "Elizabeth Rose": 50_000_000,
        "Maskit": 100_000_000, "Claresta": 350_000_000, "Birth Beyond": 120_000_000,
        "OtwooO": 200_000_000, "Saviosa": 0, "Rose All Day": 50_000_000
    },
    "MADONG": {
        "Ren & R & L": 20_000_000, "Sekawan": 350_000_000, "Avione": 250_000_000,
        "SYB": 100_000_000, "Mad For Make Up": 50_000_000, "Satto": 500_000_000,
        "Liora": 0, "Mykonos": 20_000_000, "Somethinc": 1_100_000_000
    }
}

# --- DATABASE TARGET TOTAL SUPERVISOR (REQ TERBARU) ---
SUPERVISOR_TOTAL_TARGETS = {
    "LISMAN": 2_430_000_000,
    "AKBAR": 2_450_000_000,
    "WILLIAM": 2_120_000_000,
    "MADONG": 2_390_000_000
}
TARGET_NASIONAL_VAL = 9_390_000_000

# --- KAMUS "BELAJAR" OTOMATIS (BRAND ALIASES) ---
BRAND_ALIASES = {
    # AKBAR
    "Diosys": ["DIOSYS", "DYOSIS", "DIO"], 
    "Y2000": ["Y2000", "Y 2000", "Y-2000"], 
    "Masami": ["MASAMI", "JAYA"],
    "Cassandra": ["CASSANDRA", "CASANDRA"],
    "Thai": ["THAI"], "Inesia": ["INESIA"], "Honor": ["HONOR"], "Vlagio": ["VLAGIO"],
    "Sociolla": ["SOCIOLLA"], "Skin1004": ["SKIN1004", "SKIN 1004"],
    "Oimio": ["OIMIO"], "Clinelle": ["CLINELLE"],

    # MADONG
    "Ren & R & L": ["REN", "R & L", "R&L"], 
    "Sekawan": ["SEKAWAN", "AINIE"],
    "Mad For Make Up": ["MAD FOR", "MAKE UP", "MAJU", "MADFORMAKEUP"], 
    "Avione": ["AVIONE"], "SYB": ["SYB"], "Satto": ["SATTO"],
    "Liora": ["LIORA"], "Mykonos": ["MYKONOS"], "Somethinc": ["SOMETHINC"],

    # LISMAN
    "Gloow & Be": ["GLOOW", "GLOOWBI", "GLOW"],
    "Artist Inc": ["ARTIST", "ARTIS"],
    "Bonavie": ["BONAVIE"], "Whitelab": ["WHITELAB"], "Goute": ["GOUTE"],
    "Dorskin": ["DORSKIN"], "Javinci": ["JAVINCI"], "Madam G": ["MADAM", "MADAME"],
    "Careso": ["CARESO"], "Newlab": ["NEWLAB"], "Mlen": ["MLEN"],

    # WILLIAM
    "Walnutt": ["WALNUT", "WALNUTT"],
    "Elizabeth Rose": ["ELIZABETH"],
    "OtwooO": ["OTWOOO", "O.TWO.O", "O TWO O"],
    "Saviosa": ["SAVIOSA"],
    "The Face": ["THE FACE", "THEFACE"], "Yu Chun Mei": ["YU CHUN MEI", "YCM"],
    "Milano": ["MILANO"], "Remar": ["REMAR"], "Beautica": ["BEAUTICA"],
    "Maskit": ["MASKIT"], "Claresta": ["CLARESTA"], "Birth Beyond": ["BIRTH"],
    "Rose All Day": ["ROSE ALL DAY"]
}

# --- KAMUS SALES ---
SALES_MAPPING = {
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG",
    "ROZY AINIE": "ROZY", "NOVI AINIE": "NOVI", "NOVI AV": "NOVI",
    "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH", "HAMZA AV": "HAMZAH", "HAMZAH SYB": "HAMZAH",
    "RISKA AV": "RISKA", "RISKA BN": "RISKA", "RISKA CRS": "RISKA", "RISKA  E-WL": "RISKA", 
    "RISKA JV": "RISKA", "RISKA REN": "RISKA", "RISKA R&L": "RISKA", "RISKA SMT": "RISKA", 
    "RISKA ST": "RISKA", "RISKA SYB": "RISKA", "RISKA - MILANO": "RISKA", "RISKA TF": "RISKA",
    "RISKA - YCM": "RISKA", "RISKA HONOR": "RISKA", "RISKA - VG": "RISKA", "RISKA TH": "RISKA", 
    "RISKA - INESIA": "RISKA", "SSL - RISKA": "RISKA", "SKIN - RIZKA": "RISKA", 
    "ADE CLA": "ADE", "ADE CRS": "ADE", "GLOOW - ADE": "ADE", "ADE JAVINCI": "ADE", 
    "ADE SVD": "ADE", "ADE RAM PUTRA M.GIE": "ADE", "ADE - MLEN1": "ADE", "ADE NEWLAB": "ADE", "DORS - ADE": "ADE",
    "FANDI - BONAVIE": "FANDI", "DORS- FANDI": "FANDI", "FANDY CRS": "FANDI", "FANDI AFDILLAH": "FANDI", 
    "FANDY WL": "FANDI", "GLOOW - FANDY": "FANDI", "FANDI - GOUTE": "FANDI", "FANDI MG": "FANDI", 
    "FANDI - NEWLAB": "FANDI", "FANDY - YCM": "FANDI", "FANDY YLA": "FANDI",
    "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI", "GANI TF": "GANI", 
    "GANI - YCM": "GANI", "GANI - MILANO": "GANI", "GANI - HONOR": "GANI", "GANI - VG": "GANI", 
    "GANI - TH": "GANI", "GANI INESIA": "GANI", "GANI - KSM": "GANI",
    "BASTIAN CASANDRA": "BASTIAN", "SSL- BASTIAN": "BASTIAN", "SKIN - BASTIAN": "BASTIAN", 
    "BASTIAN - HONOR": "BASTIAN", "BASTIAN - VG": "BASTIAN", "BASTIAN TH": "BASTIAN", 
    "BASTIAN YL": "BASTIAN", "BASTIAN YL-DIO CAT": "BASTIAN", "BASTIAN SHMP": "BASTIAN", "BASTIAN-DIO 45": "BASTIAN",
    "YOGI REMAR": "YOGI", "YOGI THE FACE": "YOGI", "YOGI YCM": "YOGI", "MILANO - YOGI": "YOGI",
    "FERI - HONOR": "FERI", "FERI - VG": "FERI", "FERI THAI": "FERI", "FERI - INESIA": "FERI",
    "SSL - DEVI": "DEVI", "SKIN - DEVI": "DEVI", "DEVI Y- DIOSYS CAT": "DEVI", "DEVI YL": "DEVI", 
    "DEVI SHMP": "DEVI", "DEVI-DIO 45": "DEVI", "DEVI YLA": "DEVI",
    "SSL- BAYU": "BAYU", "SKIN - BAYU": "BAYU", "BAYU-DIO 45": "BAYU", "BAYU YL-DIO CAT": "BAYU", 
    "BAYU SHMP": "BAYU", "BAYU YL": "BAYU",
    "PMT-WIRA": "WIRA", "WIRA SOMETHINC": "WIRA", "WIRA SYB": "WIRA",
    "SANTI BONAVIE": "SANTI", "SANTI WHITELAB": "SANTI", "SANTI GOUTE": "SANTI",
    "HABIBI - FZ": "HABIBI", "HABIBI SYB": "HABIBI", "HABIBI TH": "HABIBI",
    "MAS - MITHA": "MITHA", "MITHA ": "MITHA", "SSL BABY - MITHA ": "MITHA", "SAVIOSA - MITHA": "MITHA",
    "GLOOW - LISMAN": "LISMAN", "LISMAN - NEWLAB": "LISMAN",
    "WILLIAM BTC": "WILLIAM", "WILLI - ROS": "WILLIAM", "WILLI - WAL": "WILLIAM",
    "NAUFAL - JAVINCI": "NAUFAL", "NAUFAL SVD": "NAUFAL",
    "RIZKI JV": "RIZKI", "RIZKI SVD": "RIZKI",
    "RINI JV": "RINI", "RINI SYB": "RINI",
    "SAHRUL JAVINCI": "SAHRUL", "SAHRUL TF": "SAHRUL",
    "DWI CRS": "DWI", "DWI NLAB": "DWI",
    "FAUZIAH CLA": "FAUZIAH", "FAUZIAH ST": "FAUZIAH",
    "MARIANA CLIN": "MARIANA", "JAYA - MARIANA": "MARIANA"
}

# --- HELPER FUNCTION: FORMAT RUPIAH ---
def format_idr(value):
    try:
        return f"Rp {value:,.0f}".replace(",", ".")
    except:
        return "Rp 0"

# --- HELPER: CUSTOM PROGRESS BAR (UI MENARIK) ---
def render_custom_progress(title, current, target, color_theme="blue"):
    if target == 0: target = 1
    pct = (current / target) * 100
    pct = min(pct, 100) # Cap at 100 for bar visual
    
    # Color Logic
    if color_theme == "blue":
        bar_color = "linear-gradient(90deg, #3498db, #2980b9)"
    else:
        # Green to Red gradient if logic needed, or just solid
        bar_color = "linear-gradient(90deg, #2ecc71, #27ae60)" if pct >= 80 else "linear-gradient(90deg, #e74c3c, #c0392b)"

    st.markdown(f"""
    <div style="margin-bottom: 15px; background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="font-weight: bold; font-size: 16px; color: #333;">{title}</span>
            <span style="font-weight: bold; color: #555;">{format_idr(current)} / {format_idr(target)}</span>
        </div>
        <div style="width: 100%; background-color: #dcdcdc; border-radius: 20px; height: 20px;">
            <div style="width: {pct}%; background: {bar_color}; height: 20px; border-radius: 20px; text-align: center; color: white; font-size: 12px; line-height: 20px; transition: width 1s;">
                {pct:.1f}%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 1. FUNGSI LOAD DATA (ROBUST) ---
@st.cache_data(ttl=60) 
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    try:
        url_with_ts = f"{url}&t={datetime.datetime.now().timestamp()}"
        df = pd.read_csv(url_with_ts)
    except Exception as e:
        return None

    required_cols = ['Penjualan', 'Merk', 'Jumlah', 'Tanggal']
    if not all(col in df.columns for col in required_cols):
        return None

    df['Penjualan'] = df['Penjualan'].astype(str).str.strip()
    df['Penjualan'] = df['Penjualan'].replace(SALES_MAPPING)

    def normalize_brand(raw_brand):
        raw_upper = str(raw_brand).upper()
        for target_brand, keywords in BRAND_ALIASES.items():
            for keyword in keywords:
                if keyword in raw_upper:
                    return target_brand
        return raw_brand
    df['Merk'] = df['Merk'].apply(normalize_brand)

    df['Jumlah'] = df['Jumlah'].astype(str).str.replace('.', '', regex=False)
    df['Jumlah'] = df['Jumlah'].str.split(',').str[0]
    df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Tanggal'])

    for col in ['Kota', 'Nama Outlet', 'Nama Barang']:
        if col in df.columns:
            df[col] = df[col].astype(str)

    return df

# --- 2. FUNGSI LOAD USER ---
def load_users():
    try:
        return pd.read_csv('users.csv')
    except:
        return pd.DataFrame()

# --- 3. HALAMAN LOGIN ---
def login_page():
    st.markdown("<h1 style='text-align: center;'>🔒 Login Sales Dashboard Pro</h1>", unsafe_allow_html=True)
    users = load_users()
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Masuk", use_container_width=True)
            if submitted:
                if users.empty:
                    st.error("File users.csv tidak ditemukan!")
                else:
                    match = users[(users['username'] == username) & (users['password'] == password)]
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['role'] = match.iloc[0]['role']
                        st.session_state['sales_name'] = match.iloc[0]['sales_name']
                        st.rerun()
                    else:
                        st.error("Username atau Password salah!")

# --- 4. DASHBOARD UTAMA ---
def main_dashboard():
    with st.sidebar:
        st.write(f"Halo, **{st.session_state['sales_name']}**")
        if st.button("Logout", type="primary"):
            st.session_state['logged_in'] = False
            st.rerun()

    df = load_data()
    
    if df is None or df.empty:
        st.error("⚠️ Gagal memuat data! Periksa Link Google Sheet atau Format Kolom.")
        return

    # --- FILTER TANGGAL ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter Tanggal")
    min_date = df['Tanggal'].min().date() if pd.notnull(df['Tanggal'].min()) else datetime.date.today()
    max_date = df['Tanggal'].max().date() if pd.notnull(df['Tanggal'].max()) else datetime.date.today()
    date_range = st.sidebar.date_input("Periode", [min_date, max_date])
    
    if len(date_range) == 2:
        df_global_period = df[(df['Tanggal'].dt.date >= date_range[0]) & (df['Tanggal'].dt.date <= date_range[1])]
    else:
        df_global_period = df

    total_omset_perusahaan = df_global_period['Jumlah'].sum()

    # --- LOGIKA FILTER ---
    role = st.session_state['role']
    my_name = st.session_state['sales_name']
    my_name_key = my_name.strip().upper()
    target_sales_filter = "SEMUA" 
    
    is_supervisor_account = my_name_key in TARGET_DATABASE

    # 1. MANAGER
    if role == 'manager':
        sales_list = ["SEMUA"] + sorted(list(df_global_period['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Pantau Kinerja Sales:", sales_list)
        if target_sales_filter == "SEMUA":
            df_view = df_global_period
        else:
            df_view = df_global_period[df_global_period['Penjualan'] == target_sales_filter]

    # 2. SUPERVISOR
    elif is_supervisor_account:
        my_brands = TARGET_DATABASE[my_name_key].keys()
        df_supervisor_scope = df_global_period[df_global_period['Merk'].isin(my_brands)]
        team_list = sorted(list(df_supervisor_scope['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Filter Tim (Berdasarkan Brand Anda):", ["SEMUA"] + team_list)
        
        if target_sales_filter == "SEMUA":
            df_view = df_supervisor_scope
        else:
            df_view = df_supervisor_scope[df_supervisor_scope['Penjualan'] == target_sales_filter]

    # 3. SALES
    else:
        target_sales_filter = my_name
        df_view = df_global_period[df_global_period['Penjualan'] == my_name]

    # --- FILTER LANJUTAN ---
    st.sidebar.subheader("Filter Lanjutan")
    if 'Kota' in df_view.columns:
        pilih_kota = st.sidebar.multiselect("Pilih Kota", sorted(df_view['Kota'].unique()))
        if pilih_kota: df_view = df_view[df_view['Kota'].isin(pilih_kota)]
    if 'Nama Outlet' in df_view.columns:
        pilih_outlet = st.sidebar.multiselect("Pilih Nama Outlet", sorted(df_view['Nama Outlet'].unique()))
        if pilih_outlet: df_view = df_view[df_view['Nama Outlet'].isin(pilih_outlet)]
    if 'Merk' in df_view.columns:
        pilih_merk = st.sidebar.multiselect("Pilih Merk", sorted(df_view['Merk'].unique()))
        if pilih_merk: df_view = df_view[df_view['Merk'].isin(pilih_merk)]

    # --- TAMPILAN DASHBOARD ---
    st.title("🚀 Dashboard Performa Sales")
    
    if df_view.empty:
        st.warning("Belum ada data penjualan yang cocok dengan filter.")
    else:
        total_omset = df_view['Jumlah'].sum()
        total_toko = df_view['Nama Outlet'].nunique() 

        # --- SECTION KPI ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Omset", format_idr(total_omset))
        with col2:
            st.metric("Jumlah Toko Aktif", f"{total_toko} Outlet")
        with col3:
            if not df_global_period.empty:
                st.caption("Market Share")
                if (role == 'manager' and target_sales_filter == "SEMUA") or (is_supervisor_account and target_sales_filter == "SEMUA"):
                    sales_breakdown = df_view.groupby('Penjualan')['Jumlah'].sum().reset_index()
                    fig_share = px.pie(sales_breakdown, names='Penjualan', values='Jumlah', hole=0.5)
                else:
                    omset_lainnya = total_omset_perusahaan - total_omset
                    fig_share = px.pie(names=['Omset Terpilih', 'Lainnya'], values=[total_omset, max(0, omset_lainnya)], hole=0.5, color_discrete_sequence=['#3498db', '#ecf0f1'])
                fig_share.update_traces(textposition='inside', textinfo='percent')
                fig_share.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=120)
                st.plotly_chart(fig_share, use_container_width=True)

        st.divider()

        # --- SECTION TARGET VISUAL (UI MENARIK) ---
        # Logic: Muncul hanya untuk Direktur, Manager, dan Supervisor
        if role == 'manager' or is_supervisor_account:
            st.subheader("🎯 Monitoring Target (Real-Time)")
            
            # 1. TARGET NASIONAL (Untuk Manager & Supervisor)
            # Hitung Realisasi Nasional (Ambil dari df_global_period tanpa filter sales)
            realisasi_nasional = df_global_period['Jumlah'].sum()
            render_custom_progress("🏢 Target Nasional (All Team)", realisasi_nasional, TARGET_NASIONAL_VAL, "blue")

            # 2. TARGET SUPERVISOR PRIBADI (Hanya untuk Supervisor yang sedang login)
            if is_supervisor_account:
                # Ambil Target Total Supervisor dari Dictionary
                target_pribadi_spv = SUPERVISOR_TOTAL_TARGETS.get(my_name_key, 0)
                
                # Hitung Realisasi Supervisor (Total semua brand milik dia)
                my_brands_list = TARGET_DATABASE[my_name_key].keys()
                realisasi_pribadi_spv = df_global_period[df_global_period['Merk'].isin(my_brands_list)]['Jumlah'].sum()
                
                render_custom_progress(f"👤 Target Tim {my_name}", realisasi_pribadi_spv, target_pribadi_spv, "green")

            st.divider()

        # --- TABS ANALISIS ---
        tab1, tab2, tab3 = st.tabs(["📊 Rincian Target Brand", "🏆 Top Performance", "📉 Rincian Data"])

        with tab1:
            # --- TABEL RAPOR TARGET PER BRAND ---
            show_rapor = False
            if role == 'manager' and target_sales_filter == "SEMUA": show_rapor = True
            elif is_supervisor_account and target_sales_filter == "SEMUA": show_rapor = True

            if show_rapor:
                summary_data = []
                target_loop = TARGET_DATABASE.items() if role == 'manager' else {my_name_key: TARGET_DATABASE[my_name_key]}.items()

                for spv, brands_dict in target_loop:
                    for brand, target in brands_dict.items():
                        realisasi = df_global_period[df_global_period['Merk'] == brand]['Jumlah'].sum()
                        if target > 0: pct_val = (realisasi / target) * 100
                        else: pct_val = 0
                        
                        status_text = "✅" if pct_val >= 80 else "⚠️"
                        
                        summary_data.append({
                            "Supervisor": spv,
                            "Brand": brand,
                            "Target": format_idr(target),
                            "Realisasi": format_idr(realisasi),
                            "Ach (%)": f"{pct_val:.0f}%", 
                            "Pencapaian": pct_val / 100, 
                            "Status": status_text,
                            "_pct_raw": pct_val 
                        })
                
                df_summary = pd.DataFrame(summary_data)
                def highlight_row_manager(row):
                    color = '#d4edda' if row['_pct_raw'] >= 80 else '#f8d7da' 
                    return [f'background-color: {color}; color: black'] * len(row)

                st.dataframe(
                    df_summary.style.apply(highlight_row_manager, axis=1).hide(axis="columns", subset=['_pct_raw']),
                    use_container_width=True, hide_index=True,
                    column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)}
                )
            
            else:
                # View Individual Sales (Kontribusi dia terhadap target Tim)
                sales_brands = df_view['Merk'].unique()
                brand_data = []
                for brand in sales_brands:
                    target_found = 0
                    spv_name = "-"
                    for spv, brands_dict in TARGET_DATABASE.items():
                        if brand in brands_dict:
                            target_found = brands_dict[brand]
                            spv_name = spv
                            break
                    if target_found > 0:
                        realisasi_sales = df_view[df_view['Merk'] == brand]['Jumlah'].sum()
                        pct = (realisasi_sales / target_found) * 100
                        brand_data.append({
                            "Brand": brand,
                            "Supervisor": spv_name,
                            "Target Tim": format_idr(target_found),
                            "Kontribusi Dia": format_idr(realisasi_sales),
                            "Ach (%)": f"{pct:.1f}%", 
                            "Pencapaian": pct / 100, 
                            "_pct_val": pct
                        })
                if brand_data:
                    df_target_breakdown = pd.DataFrame(brand_data)
                    st.dataframe(
                        df_target_breakdown.style.hide(axis="columns", subset=['_pct_val']),
                        use_container_width=True, hide_index=True,
                        column_config={"Pencapaian": st.column_config.ProgressColumn("Bar", format=" ", min_value=0, max_value=1)}
                    )

        with tab2:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📦 Top 10 Produk")
                top_products = df_view.groupby('Nama Barang')['Jumlah'].sum().nlargest(10).reset_index()
                fig_prod = px.bar(top_products, x='Jumlah', y='Nama Barang', orientation='h', text_auto='.2s')
                st.plotly_chart(fig_prod, use_container_width=True)
            with c2:
                st.subheader("🏪 Top 10 Toko")
                top_outlets = df_view.groupby('Nama Outlet')['Jumlah'].sum().nlargest(10).reset_index()
                fig_outlet = px.bar(top_outlets, x='Jumlah', y='Nama Outlet', orientation='h', text_auto='.2s', color_discrete_sequence=['#2ecc71'])
                st.plotly_chart(fig_outlet, use_container_width=True)

        with tab3:
            st.subheader("📋 Rincian Transaksi")
            target_cols = ['Tanggal', 'Nama Outlet', 'Merk', 'Jumlah', 'Penjualan']
            final_cols = [c for c in target_cols if c in df_view.columns]
            st.dataframe(
                df_view[final_cols].sort_values('Tanggal', ascending=False), 
                use_container_width=True, hide_index=True,
                column_config={
                    "Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"),
                    "Jumlah": st.column_config.NumberColumn("Omset (Rp)", format="Rp %d")
                }
            )
            csv_data = df_view[final_cols].sort_values('Tanggal', ascending=False).to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Download Data Excel", data=csv_data, file_name="laporan_penjualan.csv", mime="text/csv")

# --- 5. ALUR UTAMA ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    main_dashboard()
