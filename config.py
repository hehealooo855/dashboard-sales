# config.py
# File ini khusus untuk menyimpan Konfigurasi Data (Roadmap 1)

TARGET_DATABASE = {
    "MADONG": {
        "Somethinc": 1_200_000_000, "SYB": 150_000_000, "Sekawan": 600_000_000, "Avione": 300_000_000, 
        "Honor": 125_000_000, "Vlagio": 75_000_000, "Ren & R & L": 20_000_000, "Mad For Make Up": 25_000_000, 
        "Satto": 500_000_000, "Mykonos": 20_000_000
    },
    "LISMAN": {
        "Javinci": 1_300_000_000, "Careso": 400_000_000, "Newlab": 150_000_000, "Gloow & Be": 130_000_000, 
        "Dorskin": 20_000_000, "Whitelab": 150_000_000, "Bonavie": 50_000_000, "Goute": 50_000_000, 
        "Mlen": 100_000_000, "Artist Inc": 130_000_000
    },
    "AKBAR": {
        "Sociolla": 600_000_000, "Thai": 300_000_000, "Inesia": 100_000_000, "Y2000": 180_000_000, 
        "Diosys": 520_000_000, "Masami": 40_000_000, "Cassandra": 50_000_000, "Clinelle": 80_000_000
    },
    "WILLIAM": {
        "The Face": 600_000_000, "Yu Chun Mei": 450_000_000, "Milano": 50_000_000, "Remar": 0, 
        "Beautica": 100_000_000, "Walnutt": 30_000_000, "Elizabeth Rose": 50_000_000, "Maskit": 30_000_000, 
        "Claresta": 350_000_000, "Birth Beyond": 120_000_000, "OtwooO": 200_000_000, "Rose All Day": 50_000_000
    }
}

INDIVIDUAL_TARGETS = {
    "WIRA": { "Somethinc": 660_000_000, "SYB": 75_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000, "Elizabeth Rose": 30_000_000, "Walnutt": 20_000_000 },
    "HAMZAH": { "Somethinc": 540_000_000, "SYB": 75_000_000, "Sekawan": 60_000_000, "Avione": 60_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000 },
    "ROZY": { "Sekawan": 100_000_000, "Avione": 100_000_000 },
    "NOVI": { "Sekawan": 90_000_000, "Avione": 90_000_000 },
    "DANI": { "Sekawan": 50_000_000, "Avione": 50_000_000 },
    "FERI": { "Honor": 50_000_000, "Thai": 200_000_000, "Vlagio": 30_000_000, "Inesia": 30_000_000 },
    "NAUFAL": { "Javinci": 550_000_000 },
    "RIZKI": { "Javinci": 450_000_000 },
    "ADE": { "Javinci": 180_000_000, "Careso": 20_000_000, "Newlab": 75_000_000, "Gloow & Be": 60_000_000, "Dorskin": 10_000_000, "Mlen": 50_000_000 },
    "FANDI": { "Javinci": 40_000_000, "Careso": 20_000_000, "Newlab": 75_000_000, "Gloow & Be": 60_000_000, "Dorskin": 10_000_000, "Whitelab": 75_000_000, "Goute": 25_000_000, "Bonavie": 25_000_000, "Mlen": 50_000_000 },
    "SYAHRUL": { "Javinci": 40_000_000, "Careso": 10_000_000, "Gloow & Be": 10_000_000 },
    "RISKA": { "Javinci": 40_000_000, "Sociolla": 190_000_000, "Thai": 30_000_000, "Inesia": 20_000_000 },
    "DWI": { "Careso": 350_000_000 },
    "SANTI": { "Goute": 25_000_000, "Bonavie": 25_000_000, "Whitelab": 75_000_000 },
    "ASWIN": { "Artist Inc": 130_000_000 },
    "DEVI": { "Sociolla": 120_000_000, "Y2000": 65_000_000, "Diosys": 175_000_000 },
    "GANI": { "The Face": 200_000_000, "Yu Chun Mei": 175_000_000, "Milano": 200_000_000, "Sociolla": 80_000_000, "Thai": 85_000_000, "Inesia": 25_000_000 },
    "BASTIAN": { "Sociolla": 210_000_000, "Thai": 85_000_000, "Inesia": 25_000_000, "Y2000": 65_000_000, "Diosys": 175_000_000 },
    "BAYU": { "Y2000": 50000000, "Diosys": 170000000 },
    "YOGI": { "The Face": 400000000, "Yu Chun Mei": 275000000, "Milano": 30000000 },
    "LYDIA": { "Birth Beyond": 120000000 },
    "MITHA": { "Maskit": 30000000, "Rose All Day": 30000000, "OtwooO": 200000000, "Claresta": 350000000 }
}

BRAND_ALIASES = {
    "Diosys": ["DIOSYS", "DYOSIS", "DIO"], "Y2000": ["Y2000", "Y 2000", "Y-2000"],
    "Masami": ["MASAMI", "JAYA"], "Cassandra": ["CASSANDRA", "CASANDRA"],
    "Thai": ["THAI"], "Inesia": ["INESIA"], "Honor": ["HONOR"], "Vlagio": ["VLAGIO"],
    "Sociolla": ["SOCIOLLA"], "Skin1004": ["SKIN1004", "SKIN 1004"], "Oimio": ["OIMIO"],
    "Clinelle": ["CLINELLE", "CLIN"], "Ren & R & L": ["REN", "R & L", "R&L"], "Sekawan": ["SEKAWAN", "AINIE"],
    "Mad For Make Up": ["MAD FOR", "MAKE UP", "MAJU", "MADFORMAKEUP"], "Avione": ["AVIONE"],
    "SYB": ["SYB"], "Satto": ["SATTO"], "Liora": ["LIORA"], "Mykonos": ["MYKONOS"],
    "Somethinc": ["SOMETHINC"], "Gloow & Be": ["GLOOW", "GLOOWBI", "GLOW", "GLOWBE"],
    "Artist Inc": ["ARTIST", "ARTIS"], "Bonavie": ["BONAVIE"], "Whitelab": ["WHITELAB"],
    "Goute": ["GOUTE"], "Dorskin": ["DORSKIN"], "Javinci": ["JAVINCI"], "Madam G": ["MADAM", "MADAME"],
    "Careso": ["CARESO"], "Newlab": ["NEWLAB"], "Mlen": ["MLEN"], "Walnutt": ["WALNUT", "WALNUTT"],
    "Elizabeth Rose": ["ELIZABETH"], "OtwooO": ["OTWOOO", "O.TWO.O", "O TWO O"],
    "Saviosa": ["SAVIOSA"], "The Face": ["THE FACE", "THEFACE"], "Yu Chun Mei": ["YU CHUN MEI", "YCM"],
    "Milano": ["MILANO"], "Remar": ["REMAR"], "Beautica": ["BEAUTICA"], "Maskit": ["MASKIT"],
    "Claresta": ["CLARESTA"], "Birth Beyond": ["BIRTH"], "Rose All Day": ["ROSE ALL DAY"],
}

SALES_MAPPING = {
    "WIRA VG": "WIRA", "WIRA SOMETHINC": "WIRA", "PMT-WIRA": "WIRA",
    "HAMZAH VG": "HAMZAH", "FERI VG": "FERI", "YOGI TF": "YOGI", 
    "GANI TF": "GANI", "MITHA MASKIT": "MITHA", "LYDIA KITO": "LYDIA",
    "NOVI AINIE": "NOVI", "ROZY AINIE": "ROZY", "DANI AINIE": "DANI",
    "MADONG - MYKONOS": "MADONG", "RISKA AV": "RISKA", "ADE CLA": "ADE",
    "FANDI - BONAVIE": "FANDI", "SAHRUL JAVINCI": "SYAHRUL", "SANTI BONAVIE": "SANTI",
    "DWI CRS": "DWI", "ASWIN ARTIS": "ASWIN", "BASTIAN CASANDRA": "BASTIAN",
    "SSL - DEVI": "DEVI", "SSL- BAYU": "BAYU", "HABIBI - FZ": "HABIBI",
    "GLOOW - LISMAN": "LISMAN", "WILLIAM BTC": "WILLIAM"
}

# Hitung Target Nasional di sini agar app.py bersih
SUPERVISOR_TOTAL_TARGETS = {k: sum(v.values()) for k, v in TARGET_DATABASE.items()}
TARGET_NASIONAL_VAL = sum(SUPERVISOR_TOTAL_TARGETS.values())