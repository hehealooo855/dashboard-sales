import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Executive Sales Dashboard", layout="wide", page_icon="📈")

# --- CUSTOM CSS (RAHASIA TAMPILAN KEREN) ---
st.markdown("""
<style>
    /* 1. Background & Font Utama */
    [data-testid="stAppViewContainer"] {
        background-color: #f4f6f9; /* Abu-abu sangat muda (bersih) */
    }
    
    /* 2. Menghapus Header Bawaan Streamlit biar Full Screen */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 3. Desain Kartu (Card) untuk Metrics */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); /* Bayangan halus */
        text-align: center;
        margin-bottom: 10px;
        border-left: 5px solid #1E88E5; /* Garis aksen biru */
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 5px;
    }
    .metric-label {
        font-size: 14px;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* 4. Judul Halaman */
    .title-text {
        color: #1a237e;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
        text-align: center;
        padding-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI LOAD DATA (SAMA SEPERTI SEBELUMNYA) ---
@st.cache_data
def load_data():
    # ---------------------------------------------------------
    # GANTI LINK DI BAWAH INI DENGAN LINK ANDA
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv" 
    # ---------------------------------------------------------
    try:
        df = pd.read_csv(url)
    except Exception as e:
        return None

    if 'Jumlah' in df.columns:
        df['Jumlah'] = df['Jumlah'].astype(str).str.replace('.', '', regex=False)
        df['Jumlah'] = df['Jumlah'].str.split(',').str[0]
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
    
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')
    return df

def load_users():
    try:
        return pd.read_csv('users.csv')
    except:
        return pd.DataFrame()

# --- HALAMAN LOGIN (DESAIN BARU) ---
def login_page():
    # Membuat container di tengah agar rapi
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True) # Spasi atas
        st.markdown("<h2 style='text-align: center; color: #1a237e;'>🔐 Secure Access</h2>", unsafe_allow_html=True)
        st.info("Silakan masukkan kredensial Sales Anda.")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("LOGIN SYSTEM", use_container_width=True)
            
            if submitted:
                users = load_users()
                if users.empty:
                    st.error("Database user tidak ditemukan.")
                else:
                    match = users[(users['username'] == username) & (users['password'] == password)]
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['role'] = match.iloc[0]['role']
                        st.session_state['sales_name'] = match.iloc[0]['sales_name']
                        st.rerun()
                    else:
                        st.error("Akses Ditolak: Username/Password salah.")

# --- DASHBOARD UTAMA (DESAIN BARU) ---
def main_dashboard():
    df = load_data()
    if df is None:
        st.error("Koneksi Data Terputus.")
        return

    # Filter Data
    role = st.session_state['role']
    my_name = st.session_state['sales_name']
    
    # Sidebar Modern
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100) # Placeholder Logo
        st.markdown(f"### Welcome, {my_name.split()[0]}!") # Panggil nama depan saja biar akrab
        st.markdown("---")
        
        if role == 'manager':
            st.success("🔰 Manager Access")
            sales_list = ["SEMUA"] + sorted(list(df['Penjualan'].dropna().unique()))
            selected_sales = st.selectbox("Filter Tim Sales:", sales_list)
            if selected_sales == "SEMUA":
                df_view = df
            else:
                df_view = df[df['Penjualan'] == selected_sales]
        else:
            st.info("👤 Sales Representative")
            df_view = df[df['Penjualan'] == my_name]
            
        st.markdown("---")
        if st.button("LOGOUT", type="primary", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- KONTEN UTAMA ---
    st.markdown("<h1 class='title-text'>Performance Dashboard</h1>", unsafe_allow_html=True)

    if df_view.empty:
        st.warning("Data belum tersedia untuk periode ini.")
    else:
        # HITUNG DATA
        total_omset = df_view['Jumlah'].sum()
        total_trx = len(df_view)
        avg_basket = total_omset / total_trx if total_trx > 0 else 0
        
        # TAMPILAN KARTU (METRIC CARDS) - INI YANG BIKIN KEREN
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Omset</div>
                <div class="metric-value" style="color: #27ae60;">Rp {total_omset:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Faktur Terbit</div>
                <div class="metric-value" style="color: #2980b9;">{total_trx}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Rata-rata Order</div>
                <div class="metric-value" style="color: #e67e22;">Rp {avg_basket:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # GRAFIK CHART YANG LEBIH CLEAN
        c1, c2 = st.columns([2, 1]) # Kolom kiri lebih lebar
        
        with c1:
            st.subheader("📈 Tren Performa")
            if 'Tanggal' in df_view.columns:
                daily = df_view.groupby('Tanggal')['Jumlah'].sum().reset_index()
                # Grafik Line lebih elegan untuk tren
                fig = px.area(daily, x='Tanggal', y='Jumlah', template='plotly_white')
                fig.update_traces(line_color='#1E88E5', fill='tozeroy') # Warna Biru Profesional
                fig.update_layout(xaxis_title=None, yaxis_title=None, height=350)
                st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.subheader("🏆 Top Produk")
            if 'Nama Barang' in df_view.columns:
                top_prod = df_view.groupby('Nama Barang')['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=False).head(5)
                # Tampilkan sebagai bar chart horizontal biar enak dibaca di HP
                fig_bar = px.bar(top_prod, x='Jumlah', y='Nama Barang', orientation='h', template='plotly_white')
                fig_bar.update_traces(marker_color='#26a69a') # Warna Teal
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title=None, yaxis_title=None, height=350, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig_bar, use_container_width=True)

        # DATA RINCIAN (Expandable)
        with st.expander("📂 Klik untuk melihat Rincian Data Transaksi"):
            st.dataframe(df_view, use_container_width=True)

# --- ALUR UTAMA ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    main_dashboard()
