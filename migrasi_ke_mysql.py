import pandas as pd
import re
import sqlalchemy
import concurrent.futures
import time

# ==========================================
# 1. KONFIGURASI DATABASE MYSQL ANDA
# ==========================================
DB_USER = "root"          # Default XAMPP biasanya root
DB_PASS = ""              # Default XAMPP biasanya kosong
DB_HOST = "localhost"     # Server XAMPP
DB_PORT = "3306"          # Port MySQL default
DB_NAME = "db_sales_perusahaan" # Nama database yang dibuat tadi
TABLE_NAME = "nama_tabel_penjualan" # Nama tabel yang dibuat tadi

# Buat koneksi SQLAlchemy
try:
    engine = sqlalchemy.create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("✅ Berhasil terhubung ke database MySQL!")
except Exception as e:
    print(f"❌ Gagal terhubung ke MySQL. Error: {e}")
    exit()

# ==========================================
# 2. LINK GOOGLE SHEETS
# ==========================================
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
    print(f"Mengunduh data dari link...")
    try:
        url_with_ts = f"{url}&t={int(time.time())}"
        return pd.read_csv(url_with_ts, dtype=str, engine='pyarrow')
    except Exception as e:
        print(f"Gagal unduh: {e}")
        return None

print("\n🚀 Memulai proses download data dari 7 Google Sheets secara paralel...")
all_dfs = []
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = executor.map(fetch_url, urls)
    for res in results:
        if res is not None and not res.empty:
            all_dfs.append(res)

if not all_dfs:
    print("❌ Tidak ada data yang berhasil diunduh.")
    exit()

df = pd.concat(all_dfs, ignore_index=True)
df.columns = df.columns.str.strip()
print(f"✅ Download selesai! Total {len(df)} baris data mentah ditarik.")

# ==========================================
# 3. PEMBERSIHAN & STANDARISASI KOLOM (Sesuai MySQL)
# ==========================================
print("🧹 Membersihkan dan menyesuaikan nama kolom...")

# Penyesuaian Kolom Penjualan (Sales)
for alt_col in ['Sales', 'Salesman', 'Nama Sales']:
    if alt_col in df.columns:
        if 'Penjualan' in df.columns:
            df['Penjualan'] = df['Penjualan'].fillna(df[alt_col])
        else:
            df['Penjualan'] = df[alt_col]

# Penyesuaian Kode Outlet
for col_name in ['Kode Customer', 'Kode Costumer', 'Kode_Global']:
    if col_name in df.columns:
        if 'Kode Outlet' not in df.columns:
            df['Kode Outlet'] = df[col_name]
        else:
            df['Kode Outlet'] = df['Kode Outlet'].fillna(df[col_name])
if 'Kode Outlet' not in df.columns: df['Kode Outlet'] = "-"

# Penyesuaian No Faktur
faktur_col = None
for col in df.columns:
    if 'faktur' in col.lower() or 'bukti' in col.lower() or 'invoice' in col.lower():
        faktur_col = col; break
if faktur_col: df = df.rename(columns={faktur_col: 'No. Faktur'})
if 'No. Faktur' not in df.columns: df['No. Faktur'] = "-"

# FILTER BARIS "TOTAL" (Membuang Data Hantu)
if 'Nama Barang' in df.columns:
    df['Nama Barang'] = df['Nama Barang'].fillna("-")
    df.loc[df['Nama Barang'].astype(str).str.strip() == '', 'Nama Barang'] = "-"
else: df['Nama Barang'] = "-"

if 'Nama Outlet' in df.columns:
    # Hapus baris yang diawali Total/Jumlah/Rekap di kolom Nama Outlet
    df = df[~df['Nama Outlet'].astype(str).str.match(r'^(Total|Jumlah|Subtotal|Grand|Rekap)', case=False, na=False)]
    df['Nama Outlet'] = df['Nama Outlet'].fillna("-")
    df.loc[df['Nama Outlet'].astype(str).str.strip() == '', 'Nama Outlet'] = "-"
else: df['Nama Outlet'] = "-"

# Membersihkan format Rupiah & Retur (Support Minus)
def clean_rupiah(x):
    s = str(x).upper().replace('RP', '').replace(' ', '').strip()
    if not s or s == '-': return 0.0
    is_negative = False
    if (s.startswith('(') and s.endswith(')')) or s.startswith('-') or s.endswith('-') or s.startswith('–') or s.startswith('—'):
        is_negative = True
    s = re.sub(r'[,.]\d{2}$', '', s) 
    s = re.sub(r'[^\d]', '', s) 
    try: 
        val = float(s)
        return -val if is_negative else val
    except: return 0.0

if 'Jumlah' in df.columns:
    df['Jumlah'] = df['Jumlah'].apply(clean_rupiah)
else: df['Jumlah'] = 0.0

# Mengamankan Kolom Qty
if 'Qty' in df.columns:
    df['Qty'] = pd.to_numeric(df['Qty'].astype(str).str.replace(r'[^\d-]', '', regex=True), errors='coerce').fillna(0).astype(int)
else: df['Qty'] = 0

# Mengamankan Kolom Tanggal (Tetap jadi string agar aman masuk MySQL)
if 'Tanggal' in df.columns:
    df['Tanggal'] = df['Tanggal'].astype(str)
else: df['Tanggal'] = "-"

# Pastikan semua kolom yang diperlukan MySQL ada (dan hilangkan yang tidak perlu)
kolom_wajib_mysql = [
    'Kode Outlet', 'Nama Outlet', 'Kota', 'No. Faktur', 'Tanggal', 'Bulan', 
    'Penjualan', 'Vendor', 'Merk', 'Item#', 'Nama Barang', 'Qty', 'Jumlah', 'Provinsi'
]

# Tambahkan kolom yang hilang dengan nilai kosong
for col in kolom_wajib_mysql:
    if col not in df.columns:
        df[col] = "-" if col not in ['Qty', 'Jumlah'] else 0

# Pilih hanya kolom yang masuk ke tabel MySQL
df_final = df[kolom_wajib_mysql].copy()

# Pastikan tipe data string (varchar) bersih dari null object
cols_str = ['Kode Outlet', 'Nama Outlet', 'Kota', 'No. Faktur', 'Tanggal', 'Bulan', 'Penjualan', 'Vendor', 'Merk', 'Item#', 'Nama Barang', 'Provinsi']
for col in cols_str:
    df_final[col] = df_final[col].fillna("-").astype(str).str.strip()

# ==========================================
# 4. INJECT DATA KE MYSQL (PUMP DATA!)
# ==========================================
print(f"🔥 Memulai transfer {len(df_final)} data bersih ke MySQL...")

try:
    # if_exists='replace' artinya tabel akan dikosongkan dan diisi ulang dengan data baru yang rapi.
    # Jika Bos ingin menambah data baru tanpa menghapus yang lama, ganti jadi 'append'
    df_final.to_sql(name=TABLE_NAME, con=engine, if_exists='replace', index=False)
    print("🎉 MANTAP BOS! Data berhasil di-migrasi ke MySQL sepenuhnya!")
except Exception as e:
    print(f"❌ Gagal memasukkan data ke MySQL. Error: {e}")