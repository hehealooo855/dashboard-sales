import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Executive Sales Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. KAMUS PERBAIKAN NAMA SALES (OTOMATIS DARI DATA EXCEL) ---
# Saya sudah rapikan semua variasi nama yang ada di Excel Anda.
SALES_MAPPING = {
    # GRUP MADONG
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG",
    
    # GRUP ROZY
    "ROZY AINIE": "ROZY", "ROZY": "ROZY",
    
    # GRUP NOVI
    "NOVI AINIE": "NOVI", "NOVI AV": "NOVI",
    
    # GRUP HAMZAH
    "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH",
    "HAMZA AV": "HAMZAH", "HAMZAH SYB": "HAMZAH",
    
    # GRUP RISKA (Sangat Banyak)
    "RISKA AV": "RISKA", "RISKA BN": "RISKA", "RISKA CRS": "RISKA",
    "RISKA  E-WL": "RISKA", "RISKA JV": "RISKA", "RISKA REN": "RISKA",
    "RISKA R&L": "RISKA", "RISKA SMT": "RISKA", "RISKA ST": "RISKA",
    "RISKA SYB": "RISKA", "RISKA - MILANO": "RISKA", "RISKA TF": "RISKA",
    "RISKA - YCM": "RISKA", "RISKA HONOR": "RISKA", "RISKA - VG": "RISKA",
    "RISKA TH": "RISKA", "RISKA - INESIA": "RISKA", "SSL - RISKA": "RISKA",
    "SKIN - RIZKA": "RISKA", 
    
    # GRUP ADE
    "ADE CLA": "ADE", "ADE CRS": "ADE", "GLOOW - ADE": "ADE",
    "ADE JAVINCI": "ADE", "ADE SVD": "ADE", "ADE RAM PUTRA M.GIE": "ADE",
    "ADE - MLEN1": "ADE", "ADE NEWLAB": "ADE", "DORS - ADE": "ADE",
    
    # GRUP FANDI (Fandi/Fandy)
    "FANDI - BONAVIE": "FANDI", "DORS- FANDI": "FANDI", "FANDY CRS": "FANDI",
    "FANDI AFDILLAH": "FANDI", "FANDY WL": "FANDI", "GLOOW - FANDY": "FANDI",
    "FANDI - GOUTE": "FANDI", "FANDI MG": "FANDI", "FANDI - NEWLAB": "FANDI",
    "FANDY - YCM": "FANDI", "FANDY YLA": "FANDI",
    
    # GRUP GANI
    "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI",
    "GANI TF": "GANI", "GANI - YCM": "GANI", "GANI - MILANO": "GANI",
    "GANI - HONOR": "GANI", "GANI - VG": "GANI", "GANI - TH": "GANI",
    "GANI INESIA": "GANI", "GANI - KSM": "GANI",
    
    # GRUP BASTIAN
    "BASTIAN CASANDRA": "BASTIAN", "SSL- BASTIAN": "BASTIAN", "SKIN - BASTIAN": "BASTIAN",
    "BASTIAN - HONOR": "BASTIAN", "BASTIAN - VG": "BASTIAN", "BASTIAN TH": "BASTIAN",
    "BASTIAN YL": "BASTIAN", "BASTIAN YL-DIO CAT": "BASTIAN", "BASTIAN SHMP": "BASTIAN",
    "BASTIAN-DIO 45": "BASTIAN",
    
    # GRUP YOGI
    "YOGI REMAR": "YOGI", "YOGI THE FACE": "YOGI", "YOGI YCM": "YOGI",
    "MILANO - YOGI": "YOGI",
    
    # GRUP LAINNYA
    "FERI - HONOR": "FERI", "FERI - VG": "FERI", "FERI THAI": "FERI", "FERI - INESIA": "FERI",
    "SSL - DEVI": "DEVI", "SKIN - DEVI": "DEVI", "DEVI Y- DIOSYS CAT": "DEVI", "DEVI YL": "DEVI", "DEVI SHMP": "DEVI", "DEVI-DIO 45": "DEVI", "DEVI YLA": "DEVI",
    "SSL- BAYU": "BAYU", "SKIN - BAYU": "BAYU", "BAYU-DIO 45": "BAYU", "BAYU YL-DIO CAT": "BAYU", "BAYU SHMP": "BAYU", "BAYU YL": "BAYU",
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

# --- 3. CSS CUSTOM (UI EXCLUSIVE) ---
st.markdown("""
<style>
    .stApp { background-color: #f4f7f6; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    
    .kpi-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #1a237e;
        text-align: center;
        margin-bottom: 15px;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-value { font-size: 24px; font-weight: 700; color: #2c3e50; }
    .kpi-label { font-size: 13px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 5px; }
    
    .header-style { font-size: 28px; font-weight: 700; color: #1a237e; margin-bottom: 20px; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 4. FUNGSI LOAD DATA ---
@st.cache_data(ttl=3600)
def load_data():
    # LINK GOOGLE SHEET (DATA LIVE)
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        return pd.DataFrame()

    # --- STANDARDISASI NAMA SALES (CORE FEATURE) ---
    if 'Penjualan' in df.columns:
        # Bersihkan spasi depan/belakang
        df['Penjualan'] = df['Penjualan'].str.strip()
        # Lakukan penggantian nama sesuai kamus di atas
        df['Penjualan'] = df['Penjualan'].replace(SALES_MAPPING)

    # CLEANING ANGKA
    if 'Jumlah' in df.columns:
        df['Jumlah'] = df['Jumlah'].astype(str).str.replace('.', '', regex=False)
        df['Jumlah'] = df['Jumlah'].str.split(',').str[0]
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    # FORMAT TANGGAL
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')

    # PASTIKAN STRING
    for col in ['Kota', 'Nama Outlet', 'Nama Barang', 'Merk', 'Penjualan']:
        if col in df.columns:
            df[col] = df[col].astype(str)

    return df

# --- 5. FUNGSI LOAD USER ---
def load_users():
    try:
        return pd.read_csv('users.csv')
    except:
        return pd.DataFrame()

# --- 6. HALAMAN LOGIN ---
def login_page():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #1a237e;'>🔐 Sales Portal</h2>", unsafe_allow_html=True)
        st.info("Masukkan username dan password Anda.")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("LOGIN", use_container_width=True)
            
            if submitted:
                users = load_users()
                if not users.empty:
                    match = users[(users['username'] == username) & (users['password'] == password)]
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['role'] = match.iloc[0]['role']
                        st.session_state['sales_name'] = match.iloc[0]['sales_name']
                        st.rerun()
                    else:
                        st.error("Login Gagal: Username/Password salah.")
                else:
                    st.error("Database User tidak ditemukan.")

# --- 7. DASHBOARD UTAMA ---
def main_dashboard():
    df = load_data()
    if df.empty:
        st.error("Gagal memuat data. Periksa koneksi internet.")
        return

    # --- SIDEBAR FILTER ---
    with st.sidebar:
        st.write(f"Halo, **{st.session_state['sales_name']}**")
        if st.button("Log Out", type="secondary"):
            st.session_state['logged_in'] = False
            st.rerun()
        st.markdown("---")
        st.subheader("🔍 Filter Pencarian")

        # FILTER TANGGAL
        min_d = df['Tanggal'].min().date() if pd.notnull(df['Tanggal'].min()) else datetime.date.today()
        max_d = df['Tanggal'].max().date() if pd.notnull(df['Tanggal'].max()) else datetime.date.today()
        date_range = st.date_input("Periode:", [min_d, max_d])
        
        # Dataframe Global untuk hitung Total Perusahaan
        if len(date_range) == 2:
            df_period = df[
                (df['Tanggal'].dt.date >= date_range[0]) & 
                (df['Tanggal'].dt.date <= date_range[1])
            ]
        else:
            df_period = df

        # Hitung TOTAL OMSET PERUSAHAAN (Untuk Chart Donut)
        total_omset_perusahaan = df_period['Jumlah'].sum()

        # PILIH SALES
        if st.session_state['role'] == 'manager':
            # Dropdown Sales (Nama sudah bersih/disatukan)
            sales_list = ["SEMUA"] + sorted(list(df_period['Penjualan'].unique()))
            selected_sales = st.selectbox("Tim Sales:", sales_list)
            if selected_sales == "SEMUA":
                df_filtered = df_period
            else:
                df_filtered = df_period[df_period['Penjualan'] == selected_sales]
        else:
            # Sales User
            df_filtered = df_period[df_period['Penjualan'] == st.session_state['sales_name']]

        # FILTER LANJUTAN
        kota_list = sorted(df_filtered['Kota'].unique())
        selected_kota = st.multiselect("Kota:", kota_list)
        if selected_kota:
            df_filtered = df_filtered[df_filtered['Kota'].isin(selected_kota)]

        outlet_list = sorted(df_filtered['Nama Outlet'].unique())
        selected_outlet = st.multiselect("Outlet:", outlet_list)
        if selected_outlet:
            df_filtered = df_filtered[df_filtered['Nama Outlet'].isin(selected_outlet)]

        if 'Merk' in df_filtered.columns:
            merk_list = sorted(df_filtered['Merk'].unique())
            selected_merk = st.multiselect("Merk:", merk_list)
            if selected_merk:
                df_filtered = df_filtered[df_filtered['Merk'].isin(selected_merk)]

    # --- MAIN CONTENT ---
    st.markdown("<div class='header-style'>Dashboard Performa Sales</div>", unsafe_allow_html=True)

    if df_filtered.empty:
        st.info("⚠️ Data tidak ditemukan.")
    else:
        # KPI Calculation
        total_omset_saya = df_filtered['Jumlah'].sum()
        total_toko_aktif = df_filtered['Nama Outlet'].nunique()
        
        # Hitung Market Share
        if total_omset_perusahaan > 0:
            share_pct = (total_omset_saya / total_omset_perusahaan) * 100
        else:
            share_pct = 0
            
        omset_sisa = total_omset_perusahaan - total_omset_saya
        if omset_sisa < 0: omset_sisa = 0

        # --- LAYOUT KPI CARDS (3 Kolom) ---
        col1, col2, col3 = st.columns([1, 1, 1.3]) 
        
        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Omset</div>
                <div class="kpi-value" style="color: #27ae60;">Rp {total_omset_saya:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Jumlah Toko Aktif</div>
                <div class="kpi-value" style="color: #2980b9;">{total_toko_aktif}</div>
            </div>
            """, unsafe_allow_html=True)

        # CHART DONUT (MARKET SHARE)
        with col3:
            with st.container():
                st.markdown("""<div style="background-color: white; border-radius: 10px; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border-left: 5px solid #e67e22; height: 140px;">
                <div class="kpi-label">Kontribusi vs Total Perusahaan</div>
                """, unsafe_allow_html=True)
                
                labels = ['Omset Terpilih', 'Sales Lainnya']
                values = [total_omset_saya, omset_sisa]
                colors = ['#e67e22', '#f0f2f5']

                fig_donut = go.Figure(data=[go.Pie(
                    labels=labels, 
                    values=values, 
                    hole=.65, 
                    textinfo='none',
                    marker=dict(colors=colors),
                    sort=False
                )])
                
                fig_donut.update_layout(
                    showlegend=False,
                    margin=dict(t=0, b=0, l=0, r=0),
                    height=90,
                    annotations=[dict(text=f"{share_pct:.1f}%", x=0.5, y=0.5, font_size=20, showarrow=False, font_weight='bold', font_color='#2c3e50')]
                )
                st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- CHARTS AREA ---
        c_chart1, c_chart2 = st.columns([2, 1])
        
        with c_chart1:
            st.subheader("Tren Penjualan Harian")
            daily_trend = df_filtered.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig1 = px.area(daily_trend, x='Tanggal', y='Jumlah', template='plotly_white')
            fig1.update_traces(line_color='#1a237e', fill_color='rgba(26, 35, 126, 0.2)')
            fig1.update_layout(height=350, margin=dict(t=10, b=0, l=0, r=0), xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig1, use_container_width=True)
            
        with c_chart2:
            st.subheader("Top Brand")
            if 'Merk' in df_filtered.columns:
                top_merk = df_filtered.groupby('Merk')['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=False).head(5)
                fig2 = px.bar(top_merk, x='Jumlah', y='Merk', orientation='h', template='plotly_white')
                fig2.update_traces(marker_color='#00897b') 
                fig2.update_layout(height=350, margin=dict(t=10, b=0, l=0, r=0), xaxis_title=None, yaxis_title=None, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig2, use_container_width=True)

        # --- TABEL RINCIAN ---
        st.markdown("### 📋 Rincian Transaksi")
        cols_needed = ['Tanggal', 'Nama Outlet', 'Merk', 'Jumlah']
        final_cols = [c for c in cols_needed if c in df_filtered.columns]
        
        st.dataframe(
            df_filtered[final_cols].sort_values('Tanggal', ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"),
                "Jumlah": st.column_config.NumberColumn("Omset", format="Rp %d"),
            }
        )

# --- EXECUTION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()
