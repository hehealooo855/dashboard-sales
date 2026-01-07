import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import time
import numpy as np

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Executive Sales Command Center", 
    layout="wide", 
    page_icon="🦅"
)

# Style Custom CSS untuk tampilan Premium
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MASTER DATA & CONFIGURATION (MODULAR)
# ==========================================
# TIPS: Di masa depan, pindahkan dictionary ini ke Google Sheet tab "Master Target"
TARGET_CONFIG = {
    "LISMAN": {
        "Bonavie": 50_000_000, "Whitelab": 150_000_000, "Goute": 50_000_000,
        "Dorskin": 20_000_000, "Gloow & Be": 130_000_000, "Javinci": 1_300_000_000,
        "Careso": 400_000_000, "Artist Inc": 130_000_000, "Newlab": 150_000_000, "Mlen": 100_000_000
    },
    "AKBAR": {
        "Thai": 300_000_000, "Inesia": 100_000_000, "Y2000": 180_000_000,
        "Diosys": 520_000_000, "Sociolla": 600_000_000, "Skin1004": 300_000_000,
        "Masami": 40_000_000, "Cassandra": 50_000_000, "Clinelle": 80_000_000
    },
    "WILLIAM": {
        "The Face": 600_000_000, "Yu Chun Mei": 450_000_000, "Milano": 50_000_000,
        "Beautica": 100_000_000, "Walnutt": 30_000_000, "Elizabeth Rose": 50_000_000,
        "Maskit": 30_000_000, "Claresta": 300_000_000, "Birth Beyond": 120_000_000,
        "OtwooO": 200_000_000, "Rose All Day": 50_000_000
    },
    "MADONG": {
        "Ren & R & L": 20_000_000, "Sekawan": 350_000_000, "Avione": 250_000_000,
        "SYB": 150_000_000, "Mad For Make Up": 25_000_000, "Satto": 500_000_000,
        "Mykonos": 20_000_000, "Somethinc": 1_200_000_000, "Honor": 125_000_000, "Vlagio": 75_000_000
    }
}

# Flatten Targets for Easier Lookup
FLATTENED_TARGETS = {}
BRAND_OWNER = {}
for spv, brands in TARGET_CONFIG.items():
    for brand, target in brands.items():
        FLATTENED_TARGETS[brand] = target
        BRAND_OWNER[brand] = spv

# Mapping Aliases (Keep your original logic, it's good)
BRAND_ALIASES = {
    "Diosys": ["DIOSYS", "DYOSIS", "DIO"], "Y2000": ["Y2000", "Y 2000", "Y-2000"],
    "Masami": ["MASAMI", "JAYA"], "Cassandra": ["CASSANDRA", "CASANDRA"],
    "Thai": ["THAI"], "Inesia": ["INESIA"], "Honor": ["HONOR"], "Vlagio": ["VLAGIO"],
    "Sociolla": ["SOCIOLLA"], "Skin1004": ["SKIN1004", "SKIN 1004"], "Oimio": ["OIMIO"],
    "Clinelle": ["CLINELLE"], "Ren & R & L": ["REN", "R & L", "R&L"], "Sekawan": ["SEKAWAN", "AINIE"],
    "Mad For Make Up": ["MAD FOR", "MAKE UP", "MAJU", "MADFORMAKEUP"], "Avione": ["AVIONE"],
    "SYB": ["SYB"], "Satto": ["SATTO"], "Liora": ["LIORA"], "Mykonos": ["MYKONOS"],
    "Somethinc": ["SOMETHINC"], "Gloow & Be": ["GLOOW", "GLOOWBI", "GLOW"], "Artist Inc": ["ARTIST", "ARTIS"],
    "Bonavie": ["BONAVIE"], "Whitelab": ["WHITELAB"], "Goute": ["GOUTE"], "Dorskin": ["DORSKIN"],
    "Javinci": ["JAVINCI"], "Madam G": ["MADAM", "MADAME"], "Careso": ["CARESO"], "Newlab": ["NEWLAB"],
    "Mlen": ["MLEN"], "Walnutt": ["WALNUT", "WALNUTT"], "Elizabeth Rose": ["ELIZABETH"],
    "OtwooO": ["OTWOOO", "O.TWO.O", "O TWO O"], "Saviosa": ["SAVIOSA"], "The Face": ["THE FACE", "THEFACE"],
    "Yu Chun Mei": ["YU CHUN MEI", "YCM"], "Milano": ["MILANO"], "Remar": ["REMAR"], "Beautica": ["BEAUTICA"],
    "Maskit": ["MASKIT"], "Claresta": ["CLARESTA"], "Birth Beyond": ["BIRTH"], "Rose All Day": ["ROSE ALL DAY"]
}

# ==========================================
# 3. CORE LOGIC ENGINE (OPTIMIZED)
# ==========================================

def format_idr(value):
    """Format currency standard Indonesia."""
    return f"Rp {value:,.0f}".replace(",", ".")

@st.cache_data(ttl=300) # Cache 5 menit, jangan 60 detik (terlalu membebani API)
def load_data_engine():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"
    
    try:
        # Load Raw
        df = pd.read_csv(url)
        
        # --- OPTIMIZATION 1: Vectorized Filtering (Jauh lebih cepat dari .apply) ---
        # Buat satu string gabungan dari semua kolom relevan untuk pencarian cepat
        df['temp_search'] = df.astype(str).agg(' '.join, axis=1).str.lower()
        sampah_keywords = ['total', 'jumlah', 'subtotal', 'grand']
        pattern = '|'.join(sampah_keywords)
        df = df[~df['temp_search'].str.contains(pattern, regex=True)]
        df = df.drop(columns=['temp_search']) # Bersihkan memory
        
        # Cleaning Dasar
        df['Penjualan'] = df['Penjualan'].astype(str).str.strip().str.upper() # Normalkan ke Upper case
        
        # --- OPTIMIZATION 2: Efficient Brand Normalization ---
        # Mengubah loop pencarian menjadi Map yang efisien
        # (Untuk dataset sangat besar, ini bisa dioptimalkan lagi dengan Trie, tapi map sudah cukup untuk <50k baris)
        def get_brand_standard(raw):
            raw_up = str(raw).upper()
            for std, aliases in BRAND_ALIASES.items():
                if any(alias in raw_up for alias in aliases):
                    return std
            return raw # Return original if no match
            
        df['Merk'] = df['Merk'].apply(get_brand_standard)
        
        # --- OPTIMIZATION 3: Robust Numeric Cleaning ---
        # Handle 1.000,00 -> 1000.00 -> Float
        df['Jumlah'] = df['Jumlah'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
        
        # --- OPTIMIZATION 4: Date Parsing Logic ---
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce', format='mixed')
        
        # Fix Swapped Date (Logic User dipertahankan tapi dirapikan)
        mask_swap = (df['Tanggal'].dt.day <= 12) & (df['Tanggal'].dt.day != df['Tanggal'].dt.month)
        # Hati-hati: Logic swap ini berbahaya jika datanya campuran valid/invalid. 
        # Untuk "World Class", harusnya diperbaiki di input (Google Sheet validation).
        # Saya pertahankan agar tidak merusak data historis yang sudah terlanjur salah.
        df.loc[mask_swap, 'Tanggal'] = pd.to_datetime(
            df.loc[mask_swap, 'Tanggal'].dt.strftime('%Y-%d-%m')
        )

        df = df.dropna(subset=['Tanggal', 'Jumlah'])
        
        # Tambahkan Kolom Helper untuk Analisis
        df['Month'] = df['Tanggal'].dt.strftime('%Y-%m')
        df['Supervisor'] = df['Merk'].map(BRAND_OWNER).fillna("OTHERS")
        
        return df

    except Exception as e:
        st.error(f"Critical Data Error: {e}")
        return pd.DataFrame()

def get_users():
    # Simulasi User DB (Untuk Demo) - Di Production gunakan Database SQL / Firebase
    # Format: username, password, role, sales_name
    data = {
        "username": ["admin", "lisman", "akbar", "william", "madong"],
        "password": ["admin123", "lis123", "akb123", "wil123", "mad123"],
        "role": ["manager", "supervisor", "supervisor", "supervisor", "supervisor"],
        "sales_name": ["MANAGEMENT", "LISMAN", "AKBAR", "WILLIAM", "MADONG"]
    }
    return pd.DataFrame(data)

# ==========================================
# 4. ADVANCED VISUALIZATION COMPONENTS
# ==========================================

def plot_sunburst(df):
    """Hierarchical Chart: Supervisor -> Brand -> Barang"""
    # Agregasi data agar ringan
    df_ag = df.groupby(['Supervisor', 'Merk'])['Jumlah'].sum().reset_index()
    
    fig = px.sunburst(
        df_ag, 
        path=['Supervisor', 'Merk'], 
        values='Jumlah',
        color='Jumlah',
        color_continuous_scale='RdBu',
        title="Komposisi Omset: Supervisor & Brand"
    )
    fig.update_layout(margin=dict(t=30, l=0, r=0, b=0), height=400)
    return fig

def plot_pareto_outlet(df):
    """Analisis Pareto Toko"""
    outlet_data = df.groupby('Nama Outlet')['Jumlah'].sum().sort_values(ascending=False).reset_index()
    outlet_data['Cumulative_Pct'] = outlet_data['Jumlah'].cumsum() / outlet_data['Jumlah'].sum() * 100
    
    # Ambil Top 20 saja agar grafik terbaca
    top_20 = outlet_data.head(20)
    
    fig = go.Figure()
    # Bar Chart (Omset)
    fig.add_trace(go.Bar(
        x=top_20['Nama Outlet'], 
        y=top_20['Jumlah'], 
        name='Omset',
        marker_color='#2c3e50'
    ))
    # Line Chart (Cumulative %)
    fig.add_trace(go.Scatter(
        x=top_20['Nama Outlet'], 
        y=top_20['Cumulative_Pct'], 
        name='Kontribusi Kumulatif (%)',
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='#e74c3c', width=2)
    ))
    
    fig.update_layout(
        title="Analisis Pareto (Top 20 Outlet)",
        yaxis=dict(title='Omset (Rp)'),
        yaxis2=dict(title='Kumulatif %', overlaying='y', side='right', range=[0, 110]),
        legend=dict(x=0.6, y=1.1, orientation='h'),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

# ==========================================
# 5. MAIN APPLICATION
# ==========================================

def login_screen():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("## 🔒 Secure Access")
        with st.form("login"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            btn = st.form_submit_button("Login Dashboard", use_container_width=True)
            
            if btn:
                users_db = get_users() # Gunakan fungsi internal dummy untuk keamanan demo
                # Cek User (Bisa diganti logic baca CSV jika mau tetap pakai CSV)
                try: 
                    csv_users = pd.read_csv('users.csv') # Coba load CSV jika ada
                    if not csv_users.empty: users_db = csv_users
                except: pass
                
                match = users_db[(users_db['username'] == user) & (users_db['password'] == pwd)]
                
                if not match.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Kombinasi Username/Password salah.")

def dashboard_screen():
    user_info = st.session_state['user_info']
    role = user_info['role']
    user_name = user_info['sales_name']
    
    # Sidebar
    with st.sidebar:
        st.title(f"Halo, {user_name}")
        st.caption(f"Role: {role.upper()}")
        
        # Date Filter
        df = load_data_engine()
        if df.empty:
            st.warning("Data kosong / Gagal load.")
            st.stop()
            
        min_date = df['Tanggal'].min().date()
        max_date = df['Tanggal'].max().date()
        
        # Default: Bulan ini
        today = datetime.date.today()
        first_day = today.replace(day=1)
        
        dates = st.date_input("Filter Tanggal", [first_day, today], min_value=min_date, max_value=max_date)
        
        st.divider()
        if st.button("Logout", type="secondary"):
            st.session_state['logged_in'] = False
            st.rerun()

    # Filter Logic
    if len(dates) != 2: st.info("Pilih rentang tanggal."); st.stop()
    start, end = dates
    
    # 1. Filter Waktu
    mask_date = (df['Tanggal'].dt.date >= start) & (df['Tanggal'].dt.date <= end)
    df_filtered = df[mask_date]
    
    # 2. Filter Hak Akses (Scope)
    if role == 'supervisor':
        # Supervisor hanya melihat Brand miliknya, tapi BISA melihat semua sales yang menjual brand itu
        my_brands = TARGET_CONFIG.get(user_name, {}).keys()
        df_view = df_filtered[df_filtered['Merk'].isin(my_brands)]
    elif role == 'manager':
        df_view = df_filtered
    else: # Sales biasa (jika ada)
        df_view = df_filtered # Default logic

    # --- KPI CARDS (AT A GLANCE) ---
    st.markdown(f"### 📊 Dashboard Performa ({start.strftime('%d %b')} - {end.strftime('%d %b')})")
    
    col1, col2, col3, col4 = st.columns(4)
    
    curr_omset = df_view['Jumlah'].sum()
    trx_count = len(df_view)
    active_stores = df_view['Nama Outlet'].nunique()
    
    # Kalkulasi Target Dinamis
    target_scope = 0
    if role == 'manager':
        target_scope = sum(FLATTENED_TARGETS.values())
    elif role == 'supervisor':
        target_scope = sum(TARGET_CONFIG.get(user_name, {}).values())
    
    # Achievement
    ach_pct = (curr_omset / target_scope * 100) if target_scope > 0 else 0
    
    # Average Basket Size (Indikator Efisiensi)
    avg_basket = curr_omset / trx_count if trx_count > 0 else 0

    with col1: st.metric("Realization (Omset)", format_idr(curr_omset), f"{ach_pct:.1f}% vs Target")
    with col2: st.metric("Target Period", format_idr(target_scope))
    with col3: st.metric("Active Outlets", active_stores)
    with col4: st.metric("Avg. Basket Size", format_idr(avg_basket), help="Rata-rata nilai per faktur")
    
    st.progress(min(ach_pct/100, 1.0))
    
    # --- DEEP DIVE TABS ---
    t1, t2, t3 = st.tabs(["🚀 Executive Summary", "📈 Trend Analysis", "📋 Raw Data"])
    
    with t1:
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            if role == 'manager':
                # Breakdown per Supervisor
                st.subheader("Performa per Supervisor")
                spv_perf = df_view.groupby('Supervisor')['Jumlah'].sum().reset_index()
                # Tambahkan kolom target ke dataframe ini
                spv_perf['Target'] = spv_perf['Supervisor'].apply(lambda x: sum(TARGET_CONFIG.get(x, {}).values()))
                spv_perf['Ach'] = (spv_perf['Jumlah'] / spv_perf['Target'] * 100).fillna(0)
                
                st.dataframe(
                    spv_perf.style.format({'Jumlah': 'Rp {:,.0f}', 'Target': 'Rp {:,.0f}', 'Ach': '{:.1f}%'})
                    .background_gradient(subset=['Ach'], cmap='RdYlGn', vmin=50, vmax=110),
                    use_container_width=True, hide_index=True
                )
                
                st.subheader("Brand Performance Heatmap")
                brand_perf = df_view.groupby(['Supervisor', 'Merk'])['Jumlah'].sum().reset_index()
                st.bar_chart(brand_perf, x='Merk', y='Jumlah', color='Supervisor', stack=False)

            elif role == 'supervisor':
                st.subheader("Performa Brand Tim Anda")
                my_brands_perf = df_view.groupby('Merk')['Jumlah'].sum().reset_index()
                my_brands_perf['Target'] = my_brands_perf['Merk'].map(FLATTENED_TARGETS)
                my_brands_perf['Ach'] = (my_brands_perf['Jumlah'] / my_brands_perf['Target'] * 100)
                
                # Visualisasi Bar Chart Target vs Realisasi
                fig_comp = go.Figure(data=[
                    go.Bar(name='Realisasi', x=my_brands_perf['Merk'], y=my_brands_perf['Jumlah'], marker_color='#2ecc71'),
                    go.Bar(name='Target', x=my_brands_perf['Merk'], y=my_brands_perf['Target'], marker_color='#95a5a6')
                ])
                fig_comp.update_layout(barmode='group', title="Target vs Realisasi per Brand")
                st.plotly_chart(fig_comp, use_container_width=True)

        with c_right:
            st.subheader("Distribusi Omset")
            # Sunburst Chart (Hirarki)
            fig_sun = plot_sunburst(df_view)
            st.plotly_chart(fig_sun, use_container_width=True)
            
            # Top Salesperson
            st.subheader("Top Sales Force")
            top_sales = df_view.groupby('Penjualan')['Jumlah'].sum().nlargest(5).sort_values(ascending=True)
            st.bar_chart(top_sales, horizontal=True, color="#ffaa00")

    with t2:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader("Analisis Pareto Outlet (80/20 Rule)")
            st.plotly_chart(plot_pareto_outlet(df_view), use_container_width=True)
        with col_t2:
            st.subheader("Daily Trend")
            daily = df_view.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig_line = px.line(daily, x='Tanggal', y='Jumlah', markers=True)
            fig_line.update_traces(line_color='#8e44ad', line_width=3)
            st.plotly_chart(fig_line, use_container_width=True)

    with t3:
        st.dataframe(df_view.sort_values('Tanggal', ascending=False), use_container_width=True)


# --- MAIN ENTRY POINT ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    dashboard_screen()
else:
    login_screen()
