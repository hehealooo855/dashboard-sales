import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import re 

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sales Dashboard", layout="wide")

# --- DATABASE TARGET (HARDCODED SESUAI REQUEST) ---
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

# --- KAMUS PERBAIKAN NAMA SALES ---
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

# --- KAMUS PERBAIKAN BRAND (NORMALISASI AGAR DATA TIDAK TERTUKAR) ---
BRAND_MAPPING_NORMALIZATION = {
    # Format: "NAMA DI CSV" : "NAMA BAKU (SESUAI TARGET DATABASE)"
    "JAYA": "Masami",
    "MAJU": "Mad For Make Up",
    "MAD FOR MAKEUP": "Mad For Make Up", # Variasi spasi
    "GLOOWBI": "Gloow & Be",
    "GLOOW BI": "Gloow & Be",
    "CASANDRA": "Cassandra",
    "WALNUTS": "Walnutt",
    "ELIZABETH": "Elizabeth Rose",
    "O.TWO.O": "OtwooO",
    "SAVIOSA": "Saviosa",
    "ARTIS": "Artist Inc",
    "REN": "Ren & R & L",
    "AINIE": "Sekawan",
    # PERBAIKAN Y2000 & DIOSYS (MAPPING PASTI)
    "DYOSIS": "Diosys",
    "DIOSYS": "Diosys",
    "Y2000": "Y2000",
    "Y 2000": "Y2000",
    "Y-2000": "Y2000"
}

# --- HELPER FUNCTION: FORMAT RUPIAH ---
def format_idr(value):
    return f"Rp {value:,.0f}".replace(",", ".")

# --- 1. FUNGSI LOAD DATA ---
@st.cache_data(ttl=3600) 
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    try:
        df = pd.read_csv(url)
    except Exception as e:
        return None

    # Normalisasi Nama Sales
    if 'Penjualan' in df.columns:
        df['Penjualan'] = df['Penjualan'].astype(str).str.strip()
        df['Penjualan'] = df['Penjualan'].replace(SALES_MAPPING)

    # Normalisasi Nama Brand (KUNCI PERBAIKAN DATA Y2000/DIOSYS)
    if 'Merk' in df.columns:
        # Ubah ke uppercase dulu biar match
        df['Merk'] = df['Merk'].astype(str).str.strip().str.upper() 
        # Buat dictionary map juga jadi uppercase key-nya
        brand_map_upper = {k.upper(): v for k, v in BRAND_MAPPING_NORMALIZATION.items()}
        # Replace
        df['Merk'] = df['Merk'].replace(brand_map_upper)
        # Kembalikan ke Title Case agar rapi di tabel (Opsional, tapi bagus utk display)
        # Tapi karena Target Database kuncinya Case Sensitive (huruf besar kecil ngaruh),
        # Kita harus pastikan data di df['Merk'] SAMA PERSIS dengan key di TARGET_DATABASE.
        # Strategi: Kita biarkan saja apa adanya hasil replace, karena values di BRAND_MAPPING_NORMALIZATION
        # sudah kita set sama persis dengan Key di TARGET_DATABASE.

    # Cleaning Angka
    if 'Jumlah' in df.columns:
        df['Jumlah'] = df['Jumlah'].astype(str).str.replace('.', '', regex=False)
        df['Jumlah'] = df['Jumlah'].str.split(',').str[0]
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    # Cleaning Tanggal
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')

    # Pastikan kolom lain string
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

    # --- LOGIKA FILTER SALES ---
    role = st.session_state['role']
    my_name = st.session_state['sales_name']
    my_name_key = my_name.strip().upper()
    target_sales_filter = "SEMUA" 
    is_supervisor = my_name_key in TARGET_DATABASE

    if role == 'manager':
        sales_list = ["SEMUA"] + sorted(list(df_global_period['Penjualan'].dropna().unique()))
        target_sales_filter = st.sidebar.selectbox("Pantau Kinerja Sales:", sales_list)
        if target_sales_filter == "SEMUA":
            df_view = df_global_period
        else:
            df_view = df_global_period[df_global_period['Penjualan'] == target_sales_filter]
    elif is_supervisor:
        my_brands = TARGET_DATABASE[my_name_key].keys()
        # Filter data global hanya yang Merk-nya ada di list brand supervisor ini
        # Gunakan isin() untuk pencocokan pasti (Exact Match) agar Diosys tidak kecampur Y2000
        df_view = df_global_period[df_global_period['Merk'].isin(my_brands)]
        target_sales_filter = my_name 
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

        # --- RAPOR TARGET MANAGER (TABEL WARNA FIX) ---
        if role == 'manager' and target_sales_filter == "SEMUA":
            st.markdown("### 🏢 Rapor Target Supervisor (All Brand)")
            with st.expander("Klik untuk melihat Detail Target Semua Supervisor", expanded=True):
                summary_data = []
                for spv, brands_dict in TARGET_DATABASE.items():
                    for brand, target in brands_dict.items():
                        # Hitung Realisasi dengan EXACT MATCH (isin) agar akurat
                        # Data 'Merk' di df_global_period sudah dinormalisasi di load_data
                        realisasi = df_global_period[df_global_period['Merk'] == brand]['Jumlah'].sum()
                        
                        pct_val = (realisasi / target) * 100 if target > 0 else 0
                        status_text = "✅" if pct_val >= 80 else "⚠️"
                        
                        summary_data.append({
                            "Supervisor": spv,
                            "Brand": brand,
                            "Target": format_idr(target),
                            "Realisasi": format_idr(realisasi),
                            "Pencapaian": pct_val / 100, # Float 0.0 - 1.0 untuk progress bar
                            "Status": status_text,
                            "_pct_raw": pct_val # Kolom rahasia untuk logic warna
                        })
                
                df_summary = pd.DataFrame(summary_data)
                
                # Logic Warna Baris (Hijau jika >= 80)
                def highlight_row_manager(row):
                    color = '#d4edda' if row['_pct_raw'] >= 80 else '#f8d7da' 
                    return [f'background-color: {color}; color: black'] * len(row)

                # Tampilkan Tabel (Hide _pct_raw)
                st.dataframe(
                    df_summary.style.apply(highlight_row_manager, axis=1).hide(axis="columns", subset=['_pct_raw']),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Pencapaian": st.column_config.ProgressColumn(
                            format="%.0f%%", # Tampil sebagai 80%
                            min_value=0,
                            max_value=1,
                        )
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
            
            if role == 'manager' and target_sales_filter == "SEMUA":
                df_prev = df_prev_global
            elif role == 'manager':
                df_prev = df_prev_global[df_prev_global['Penjualan'] == target_sales_filter]
            elif is_supervisor:
                 my_brands_prev = TARGET_DATABASE[my_name_key].keys()
                 # Exact match untuk supervisor juga
                 df_prev = df_prev_global[df_prev_global['Merk'].isin(my_brands_prev)]
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
                if role == 'manager' or is_supervisor:
                    sales_breakdown = df_view.groupby('Merk')['Jumlah'].sum().reset_index()
                    fig_share = px.pie(sales_breakdown, names='Merk', values='Jumlah', hole=0.5)
                else:
                    omset_lainnya = total_omset_perusahaan - total_omset
                    fig_share = px.pie(names=['Omset Saya', 'Sales Lain'], values=[total_omset, max(0, omset_lainnya)], hole=0.5, color_discrete_sequence=['#3498db', '#ecf0f1'])
                fig_share.update_traces(textposition='inside', textinfo='percent')
                fig_share.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=120)
                st.plotly_chart(fig_share, use_container_width=True)

        st.divider()

        # --- DETAIL TARGET PER BRAND (UNTUK SPV & SALES) ---
        active_target_data = {}
        target_key_check = target_sales_filter.strip().upper()
        
        if target_key_check in TARGET_DATABASE:
            active_target_data = TARGET_DATABASE[target_key_check]
            total_target_val = sum(active_target_data.values())
            
            st.subheader(f"🎯 Target {target_sales_filter}: {format_idr(total_target_val)}")
            
            if total_target_val > 0:
                achievement = (total_omset / total_target_val)
                st.progress(min(achievement, 1.0))
                st.caption(f"Pencapaian: **{achievement*100:.0f}%** dari Target")

                with st.expander("Lihat Rincian Target per Brand", expanded=True):
                    brand_data = []
                    for brand, target_brand in active_target_data.items():
                        # Exact Match
                        realisasi_brand = df_global_period[df_global_period['Merk'] == brand]['Jumlah'].sum()
                        pct = (realisasi_brand / target_brand) * 100 if target_brand > 0 else 0
                        status_label = "✅ Achieved" if pct >= 80 else "⚠️ On Process"
                        
                        brand_data.append({
                            "Brand": brand,
                            "Target": format_idr(target_brand),
                            "Realisasi": format_idr(realisasi_brand),
                            "Pencapaian": pct / 100, 
                            "Status": status_label,
                            "_pct_val": pct
                        })
                    
                    df_target_breakdown = pd.DataFrame(brand_data)
                    
                    def highlight_row(row):
                        color = '#d4edda' if row['_pct_val'] >= 80 else '#f8d7da'
                        return [f'background-color: {color}; color: black'] * len(row)

                    st.dataframe(
                        df_target_breakdown.style.apply(highlight_row, axis=1).hide(axis="columns", subset=['_pct_val']),
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "Pencapaian": st.column_config.ProgressColumn(
                                format="%.0f%%",
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
