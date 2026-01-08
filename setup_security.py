import bcrypt
import os

# --- DATA USER LENGKAP (Sesuai Request) ---
# Format: [Username, Password, Role, Nama Asli Sales]
raw_users = [
    ["direktur", "bos2026", "direktur", "All"],
    ["manager", "admin2026", "manager", "All"],
    ["madong", "123", "supervisor", "MADONG"],
    ["lisman", "123", "supervisor", "LISMAN"],
    ["akbar", "123", "supervisor", "AKBAR"],
    ["william", "123", "supervisor", "WILLIAM"],
    ["rozy", "123", "sales", "ROZY"],
    ["sherin", "123", "sales", "SHERIN"],
    ["novi", "123", "sales", "NOVI"],
    ["hamzah", "123", "sales", "HAMZAH"],
    ["sri", "123", "sales", "SRI RAMADHANI"],
    ["aswin", "123", "sales", "ASWIN"],
    ["riska", "123", "sales", "RISKA"],
    ["santi", "123", "sales", "SANTI"],
    ["fandi", "123", "sales", "FANDI"],
    ["fitri", "123", "sales", "FITRI"],
    ["sinta", "123", "sales", "SINTA"],
    ["dewy", "123", "sales", "DEWY CLA"],
    ["fauziah", "123", "sales", "FAUZIAH"],
    ["ade", "123", "sales", "ADE"],
    ["mariana", "123", "sales", "MARIANA"],
    ["bastian", "123", "sales", "BASTIAN"],
    ["gani", "123", "sales", "GANI"],
    ["dwi", "123", "sales", "DWI"],
    ["jaya", "123", "sales", "MARIANA"],
    ["rizki", "123", "sales", "RIZKI"],
    ["naufal", "123", "sales", "NAUFAL"],
    ["sahrul", "123", "sales", "SAHRUL"],
    ["rini", "123", "sales", "RINI"],
    ["lydia", "123", "sales", "LYDIA"],
    ["yani", "123", "sales", "KITO - YANI"],
    ["yogi", "123", "sales", "YOGI"],
    ["mitha", "123", "sales", "MITHA"],
    ["wira", "123", "sales", "WIRA"],
    ["bayu", "123", "sales", "BAYU"],
    ["devi", "123", "sales", "DEVI"],
    ["erni", "123", "sales", "ERNI ST"],
    ["aprilika", "123", "sales", "APRILIKA ST"],
    ["evri", "123", "sales", "EVRI ST"],
    ["nabilla", "123", "sales", "NABILLA"],
    ["betty", "123", "sales", "BETTY"],
    ["habibi", "123", "sales", "HABIBI"],
    ["faisal", "123", "sales", "FAISAL SYB"],
    ["yuda", "123", "sales", "YUDA TF"],
    ["dimas", "123", "sales", "DIMAS TF"],
    ["feri", "123", "sales", "FERI"],
    ["nita", "123", "sales", "NITA REN"],
    ["dani", "123", "sales", "DANI"]
]

def generate_secrets():
    print("⏳ Memproses enkripsi keamanan untuk semua user...")
    
    # Header Konfigurasi
    content = '[gsheet]\n'
    content += 'url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ4rlPNXu3jTQcwv2CIvyXCZvXKV3ilOtsuhhlXRB01qk3zMBGchNvdQRypOcUDnFsObK3bUov5nG72/pub?gid=0&single=true&output=csv"\n\n'
    
    for u in raw_users:
        user, pwd, role, name = u
        # Enkripsi Password
        hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        content += f'[users.{user}]\n'
        content += f'name = "{name}"\n'
        content += f'role = "{role}"\n'
        content += f'password = "{hashed}"\n\n'
    
    # Buat Folder & File
    if not os.path.exists(".streamlit"):
        os.makedirs(".streamlit")
        
    with open(".streamlit/secrets.toml", "w") as f:
        f.write(content)
        
    print("✅ SUKSES! Database User & Password Terenkripsi berhasil dibuat di .streamlit/secrets.toml")

if __name__ == "__main__":
    generate_secrets()