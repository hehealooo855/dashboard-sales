import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import re 

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sales Dashboard", layout="wide")

# --- DATABASE TARGET ---
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

# --- KONFIGURASI TIM SUPERVISOR (BARU) ---
# Masukkan nama Sales (sesuai hasil Mapping) ke bawah nama Supervisornya.
SUPERVISOR_TEAMS = {
    "LISMAN": ["ADE", "FANDI", "SANTI", "FITRI", "SINTA", "LISMAN"],
    "AKBAR": ["GANI", "FERI", "WILLIAM", "DEWY", "FAUZIAH", "AKBAR"],
    "WILLIAM": ["YOGI", "BASTIAN", "DEVI", "BAYU", "WIRA", "MITHA"],
    "MADONG": ["RISKA", "HAMZAH", "NOVI", "ROZY", "SRI", "MADONG"]
}

# --- KAMUS "BELAJAR" OTOMATIS (BRAND) ---
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
    "Mad For Make Up": ["MAD FOR", "MAKE UP", "MAJU"], 
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
    "ROZY AINIE": "ROZY",
    "NOVI AINIE": "NOVI", "NOVI AV": "NOVI",
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
    return f"Rp {value:,.0f}".replace(",", ".")

# --- 1. FUNGSI LOAD DATA (DENGAN LOGIKA BELAJAR OTOMATIS) ---
@st.cache_data(ttl=3600) 
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    try:
        df = pd.read_csv(url)
    except Exception as e:
        return None

    if 'Penjualan' in df.columns:
        df['Penjualan'] = df['Penjualan'].astype(str).str.strip()
        df['Penjualan'] = df['Penjualan'].replace(SALES_MAPPING)

    if 'Merk' in df.columns:
        def normalize_brand(raw_brand):
            raw_upper = str(raw_brand).upper()
            for target_brand, keywords in BRAND_ALIASES.items():
                for keyword in keywords:
                    if keyword in raw_upper:
                        return target_brand
            return raw_brand
        df['Merk'] = df['Merk'].apply(normalize_brand)

    if 'Jumlah' in df.columns:
        df['Jumlah'] = df['Jumlah'].astype(str).str.replace('.', '', regex=False)
        df['Jumlah'] = df['Jumlah'].str.split(',').str[0]
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')

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
    st.markdown("<h1 style='text-align: center;'>🔒 Login Sales Dashboard</h1>", unsafe_allow_html=True)
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
    if df is None:
        st.error("⚠️ Gagal memuat data! Pastikan Link Google Sheet benar.")
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

    # --- LOGIKA FILTER SALES (BARU) ---
    role = st.session_state['role']
    my_name = st.session_state['sales_name']
    my_name_key = my_name.strip().upper()
    
    target_sales_filter = "SEMUA" 
    # Cek apakah user adalah supervisor berdasarkan kamus tim
    is_supervisor_role = my_name_key in SUPERVISOR_TEAMS 

    # --- 1. FILTER UNTUK MANAGER/DIREKTUR ---
    if role == 'manager':
        # Bisa cari SIAPA SAJA
        sales_list = ["SEMUA"] + sorted(list(df_global_period['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Pantau Kinerja Sales:", sales_list)
        
        if target_sales_filter == "SEMUA":
            df_view = df_global_period
        else:
            df_view = df_global_period[df_global_period['Penjualan'] == target_sales_filter]

    # --- 2. FILTER UNTUK SUPERVISOR ---
    elif is_supervisor_role:
        # Ambil daftar anak buah dari kamus
        my_team = SUPERVISOR_TEAMS[my_name_key]
        # Dropdown hanya isi anak buah
        team_options = ["SEMUA TIM SAYA"] + sorted(my_team)
        target_sales_filter = st.sidebar.selectbox("Pantau Tim Anda:", team_options)
        
        if target_sales_filter == "SEMUA TIM SAYA":
            # Tampilkan data yang Namanya ada di daftar tim
            df_view = df_global_period[df_global_period['Penjualan'].isin(my_team)]
            # Override nama filter untuk keperluan chart (agar labelnya 'Tim Saya')
            chart_label = my_name 
        else:
            # Tampilkan data sales spesifik (anak buah)
            df_view = df_global_period[df_global_period['Penjualan'] == target_sales_filter]
            chart_label = target_sales_filter

    # --- 3. FILTER UNTUK SALES BIASA ---
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

        # --- RAPOR TARGET MANAGER & SUPERVISOR (TABEL WARNA) ---
        # Manager lihat semua, Supervisor lihat target timnya saja
        if (role == 'manager' and target_sales_filter == "SEMUA") or (is_supervisor_role and target_sales_filter == "SEMUA TIM SAYA"):
            st.markdown("### 🏢 Rapor Target (Brand Focus)")
            with st.expander("Klik untuk melihat Detail Target", expanded=True):
                summary_data = []
                
                # Tentukan scope loop: Semua SPV (Manager) atau Hanya Diri Sendiri (Supervisor)
                spv_loop = TARGET_DATABASE.items() if role == 'manager' else {k:v for k,v in TARGET_DATABASE.items() if k == my_name_key}.items()

                for spv, brands_dict in spv_loop:
                    for brand, target in brands_dict.items():
                        # Hitung Realisasi (Global Data, karena target berbasis Brand bukan Salesman)
                        # Kita filter df_global_period berdasarkan Brand yang dipegang SPV ini
                        realisasi = df_global_period[df_global_period['Merk'] == brand]['Jumlah'].sum()
                        
                        pct_val = (realisasi / target) * 100 if target > 0 else 0
                        status_text = "✅" if pct_val >= 80 else "⚠️"
                        
                        summary_data.append({
                            "Supervisor": spv,
                            "Brand": brand,
                            "Target": format_idr(target),
                            "Realisasi": format_idr(realisasi),
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
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Pencapaian": st.column_config.ProgressColumn(
                            format="%.0f%%",
                            min_value=0,
                            max_value=1,
                        ),
                        "Status": st.column_config.TextColumn("Ket")
                    }
                )
            st.divider()

        # --- KPI CARDS & GROWTH ---
        prev_omset = 0
        growth_html = ""
        if len(date_range) == 2:
            start_date, end_date = date_range
            days_diff = (end_date - start_date).days + 1
            prev_start = start_date - datetime.timedelta(days=days_diff)
            prev_end = end_date - datetime.timedelta(days=days_diff)
            
            df_prev_global = df[(df['Tanggal'].dt.date >= prev_start) & (df['Tanggal'].dt.date <= prev_end)]
            
            # Logic Filter Growth harus sama dengan Logic Filter Utama
            if role == 'manager':
                if target_sales_filter == "SEMUA":
                    df_prev = df_prev_global
                else:
                    df_prev = df_prev_global[df_prev_global['Penjualan'] == target_sales_filter]
            elif is_supervisor_role:
                if target_sales_filter == "SEMUA TIM SAYA":
                    df_prev = df_prev_global[df_prev_global['Penjualan'].isin(SUPERVISOR_TEAMS[my_name_key])]
                else:
                    df_prev = df_prev_global[df_prev_global['Penjualan'] == target_sales_filter]
            else:
                df_prev = df_prev_global[df_prev_global['Penjualan'] == my_name]
            
            prev_omset = df_prev['Jumlah'].sum()

        if prev_omset > 0:
            diff = total_omset - prev_omset
            pct_change = (diff / prev_omset) * 100
            color = "#27ae60" if diff >= 0 else "#c0392b"
            arrow = "▲" if diff >= 0 else "▼"
            growth_html = f"<div style='color: {color}; font-size: 14px; margin-top: 5px;'>{arrow} <b>{pct_change:.1f}%</b> vs periode lalu</div>"
        else:
            growth_html = "<div style='color: #95a5a6; font-size: 12px; margin-top: 5px;'>- Data pembanding N/A -</div>"

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Omset", format_idr(total_omset))
            st.markdown(growth_html, unsafe_allow_html=True)
        with col2:
            st.metric("Jumlah Toko Aktif", f"{total_toko} Outlet")
        with col3:
            if not df_global_period.empty:
                st.caption("Market Share / Kontribusi")
                # Jika Manager lihat SEMUA atau SPV lihat SEMUA TIM -> Tampilkan Pie Rincian
                if (role == 'manager' and target_sales_filter == "SEMUA") or (is_supervisor_role and target_sales_filter == "SEMUA TIM SAYA"):
                    # Tampilkan kontribusi per SALES di tim tersebut
                    sales_breakdown = df_view.groupby('Penjualan')['Jumlah'].sum().reset_index()
                    fig_share = px.pie(sales_breakdown, names='Penjualan', values='Jumlah', hole=0.5)
                else:
                    # Individual View (Manager liat 1 org, SPV liat 1 anak buah, atau Sales liat diri sendiri)
                    omset_lainnya = total_omset_perusahaan - total_omset
                    fig_share = px.pie(names=['Omset Terpilih', 'Lainnya'], values=[total_omset, max(0, omset_lainnya)], hole=0.5, color_discrete_sequence=['#3498db', '#ecf0f1'])
                
                fig_share.update_traces(textposition='inside', textinfo='percent')
                fig_share.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=120)
                st.plotly_chart(fig_share, use_container_width=True)

        st.divider()

        # --- DETAIL TARGET PER BRAND (JIKA SALES DIPILIH) ---
        # Fitur ini muncul jika kita melihat Sales Spesifik (bukan View ALL Manager/SPV)
        # Tujuannya agar Manager bisa lihat detail target per sales jika diperlukan, 
        # ATAU (Simplifikasi): Kita tampilkan target brand berdasarkan Supervisor dari sales tersebut.
        
        # Cek apakah view saat ini adalah view individual (Sales, atau Manager/SPV klik satu nama)
        is_individual_view = (role != 'manager' or target_sales_filter != "SEMUA") and \
                             (not is_supervisor_role or target_sales_filter != "SEMUA TIM SAYA")
        
        if is_individual_view:
            # Kita perlu tahu siapa Supervisor dari Sales yang sedang dilihat ini untuk menarik targetnya
            # Cari di dictionary SUPERVISOR_TEAMS
            current_sales_name = target_sales_filter
            found_spv = None
            for spv, members in SUPERVISOR_TEAMS.items():
                if current_sales_name in members:
                    found_spv = spv
                    break
            
            # Jika sales ini punya supervisor yang ada di database target
            if found_spv and found_spv in TARGET_DATABASE:
                active_target_data = TARGET_DATABASE[found_spv]
                # Hitung total target (ini target tim sebenarnya, tapi kita tampilkan sebagai referensi)
                # Atau kita bisa breakdown per brand saja
                
                with st.expander(f"Rincian Kontribusi {current_sales_name} terhadap Target {found_spv}", expanded=True):
                    brand_data = []
                    for brand, target_brand in active_target_data.items():
                        # Hitung Omset SALES INI SAJA untuk brand tersebut
                        # Gunakan Exact Match karena sudah dinormalisasi
                        realisasi_sales = df_view[df_view['Merk'] == brand]['Jumlah'].sum()
                        
                        # Persentase kontribusi dia terhadap target tim
                        pct = (realisasi_sales / target_brand) * 100 if target_brand > 0 else 0
                        
                        brand_data.append({
                            "Brand": brand,
                            "Target Tim": format_idr(target_brand),
                            "Kontribusi Dia": format_idr(realisasi_sales),
                            "Pencapaian": pct / 100, 
                            "_pct_val": pct
                        })
                    
                    df_target_breakdown = pd.DataFrame(brand_data)
                    st.dataframe(
                        df_target_breakdown.drop(columns=['_pct_val']),
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "Pencapaian": st.column_config.ProgressColumn(
                                format="%.1f%%", # Disini pakai desimal biar kelihatan kalau kecil
                                min_value=0,
                                max_value=1,
                            ),
                        }
                    )

        st.divider()

        # Grafik Tren & Tabel Rincian
        st.subheader("📈 Tren Penjualan Harian")
        if 'Tanggal' in df_view.columns:
            daily = df_view.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig = px.bar(daily, x='Tanggal', y='Jumlah')
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Rincian Transaksi")
        target_cols = ['Tanggal', 'Nama Outlet', 'Merk', 'Jumlah', 'Penjualan']
        final_cols = [c for c in target_cols if c in df_view.columns]
        
        st.dataframe(
            df_view[final_cols].sort_values('Tanggal', ascending=False), 
            use_container_width=True, 
            hide_index=True,
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
