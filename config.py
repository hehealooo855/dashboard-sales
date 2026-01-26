# config.py

# ==========================================
# KONFIGURASI DATABASE & TARGET
# ==========================================

TARGET_DATABASE = {
    "MADONG": {
        "Somethinc": 1_200_000_000, 
        "SYB": 150_000_000, 
        "Sekawan": 600_000_000, # AINIE
        "Avione": 300_000_000, 
        "Honor": 125_000_000, 
        "Vlagio": 75_000_000,
        "Ren & R & L": 20_000_000, 
        "Mad For Make Up": 25_000_000, 
        "Satto": 500_000_000,
        "Mykonos": 20_000_000
    },
    "LISMAN": {
        "Javinci": 1_300_000_000, 
        "Careso": 400_000_000, 
        "Newlab": 150_000_000, 
        "Gloow & Be": 130_000_000, # Glowbe
        "Dorskin": 20_000_000, 
        "Whitelab": 150_000_000, 
        "Bonavie": 50_000_000, 
        "Goute": 50_000_000, 
        "Mlen": 100_000_000, 
        "Artist Inc": 130_000_000
    },
    "AKBAR": {
        "Sociolla": 600_000_000, 
        "Thai": 300_000_000, 
        "Inesia": 100_000_000, 
        "Y2000": 180_000_000, 
        "Diosys": 520_000_000,
        "Masami": 40_000_000, 
        "Cassandra": 50_000_000, 
        "Clinelle": 80_000_000
    },
    "WILLIAM": {
        "The Face": 600_000_000, 
        "Yu Chun Mei": 450_000_000, 
        "Milano": 50_000_000, 
        "Remar": 0,
        "Beautica": 100_000_000, 
        "Walnutt": 30_000_000, 
        "Elizabeth Rose": 50_000_000, 
        "Maskit": 30_000_000, 
        "Claresta": 350_000_000, 
        "Birth Beyond": 120_000_000, 
        "OtwooO": 200_000_000, 
        "Rose All Day": 50_000_000
    }
}

INDIVIDUAL_TARGETS = {
    # 1. WIRA 
    "WIRA": { 
        "Somethinc": 660_000_000, "SYB": 75_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000,
        "Elizabeth Rose": 30_000_000, "Walnutt": 20_000_000
    },
    # 2. HAMZAH
    "HAMZAH": { 
        "Somethinc": 540_000_000, "SYB": 75_000_000, "Sekawan": 60_000_000, 
        "Avione": 60_000_000, "Honor": 37_500_000, "Vlagio": 22_500_000 
    },
    # 3. ROZY
    "ROZY": { "Sekawan": 100_000_000, "Avione": 100_000_000 },
    
    # 4. NOVI
    "NOVI": { "Sekawan": 90_000_000, "Avione": 90_000_000 },
    
    # 5. DANI
    "DANI": { "Sekawan": 50_000_000, "Avione": 50_000_000 },
    
    # 6. FERI
    "FERI": { "Honor": 50_000_000, "Thai": 200_000_000, "Vlagio": 30_000_000, "Inesia": 30_000_000 },
    
    # 7. NAUFAL
    "NAUFAL": { "Javinci": 550_000_000 },
    
    # 8. RIZKI
    "RIZKI": { "Javinci": 450_000_000 },
    
    # 9. ADE
    "ADE": { 
        "Javinci": 180_000_000, "Careso": 20_000_000, "Newlab": 75_000_000, 
        "Gloow & Be": 60_000_000, "Dorskin": 10_000_000, "Mlen": 50_000_000 
    },
    # 10. FANDI
    "FANDI": { 
        "Javinci": 40_000_000, "Careso": 20_000_000, "Newlab": 75_000_000, 
        "Gloow & Be": 60_000_000, "Dorskin": 10_000_000, "Whitelab": 75_000_000,
        "Goute": 25_000_000, "Bonavie": 25_000_000, "Mlen": 50_000_000
    },
    # 11. SYAHRUL
    "SYAHRUL": { "Javinci": 40_000_000, "Careso": 10_000_000, "Gloow & Be": 10_000_000 },
    
    # 12. RISKA
    "RISKA": { 
        "Javinci": 40_000_000, "Sociolla": 190_000_000, "Thai": 30_000_000, "Inesia": 20_000_000 
    },
    # 13. DWI
    "DWI": { "Careso": 350_000_000 },
    
    # 14. SANTI
    "SANTI": { "Goute": 25_000_000, "Bonavie": 25_000_000, "Whitelab": 75_000_000 },
    
    # 15. ASWIN
    "ASWIN": { "Artist Inc": 130_000_000 },
    
    # 16. DEVI
    "DEVI": { "Sociolla": 120_000_000, "Y2000": 65_000_000, "Diosys": 175_000_000 },
    
    # 17. GANI
    "GANI": { 
        "The Face": 200_000_000, "Yu Chun Mei": 175_000_000, "Milano": 20_000_000,
        "Sociolla": 80_000_000, "Thai": 85_000_000, "Inesia": 25_000_000
    },
    # 18. BASTIAN
    "BASTIAN": { 
        "Sociolla": 210_000_000, "Thai": 85_000_000, "Inesia": 25_000_000,
        "Y2000": 65_000_000, "Diosys": 175_000_000
    },
    # 19. BAYU
    "BAYU": { "Y2000": 50_000_000, "Diosys": 170_000_000 },
    
    # 20. YOGI
    "YOGI": { "The Face": 400_000_000, "Yu Chun Mei": 275_000_000, "Milano": 30_000_000 },
    
    # 21. LYDIA
    "LYDIA": { "Birth Beyond": 120_000_000 },
    
    # 22. MITHA
    "MITHA": { 
        "Maskit": 30_000_000, "Rose All Day": 30_000_000, 
        "OtwooO": 200_000_000, "Claresta": 350_000_000 
    }
}

# Calculated Targets
SUPERVISOR_TOTAL_TARGETS = {k: sum(v.values()) for k, v in TARGET_DATABASE.items()}
TARGET_NASIONAL_VAL = sum(SUPERVISOR_TOTAL_TARGETS.values())

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
    # 1. WIRA 
    "WIRA VG": "WIRA", "WIRA - VG": "WIRA", "WIRA VLAGIO": "WIRA",
    "WIRA HONOR": "WIRA", "WIRA - HONOR": "WIRA", "WIRA HR": "WIRA",
    "WIRA SYB": "WIRA", "WIRA - SYB": "WIRA",
    "WIRA SOMETHINC": "WIRA", "PMT-WIRA": "WIRA", 
    "WIRA ELIZABETH": "WIRA", "WIRA WALNUTT": "WIRA", "WIRA ELZ": "WIRA",

    # 2. HAMZAH
    "HAMZAH VG": "HAMZAH", "HAMZAH - VG": "HAMZAH",
    "HAMZAH HONOR": "HAMZAH", "HAMZAH - HONOR": "HAMZAH",
    "HAMZAH SYB": "HAMZAH", "HAMZAH AV": "HAMZAH", "HAMZAH AINIE": "HAMZAH",
    "HAMZAH RAMADANI": "HAMZAH", "HAMZAH RAMADANI ": "HAMZAH", "HAMZA AV": "HAMZAH",

    # 3. FERI
    "FERI VG": "FERI", "FERI - VG": "FERI",
    "FERI HONOR": "FERI", "FERI - HONOR": "FERI",
    "FERI THAI": "FERI", "FERI - INESIA": "FERI",

    # 4. YOGI
    "YOGI TF": "YOGI", "YOGI THE FACE": "YOGI", 
    "YOGI YCM": "YOGI", "YOGI MILANO": "YOGI", "MILANO - YOGI": "YOGI", "YOGI REMAR": "YOGI",

    # 5. GANI
    "GANI CASANDRA": "GANI", "GANI REN": "GANI", "GANI R & L": "GANI", "GANI TF": "GANI", 
    "GANI - YCM": "GANI", "GANI - MILANO": "GANI", "GANI - HONOR": "GANI", "GANI - VG": "GANI", 
    "GANI - TH": "GANI", "GANI INESIA": "GANI", "GANI - KSM": "GANI", "SSL - GANI": "GANI",
    "GANI ELIZABETH": "GANI", "GANI WALNUTT": "GANI",

    # 6. MITHA
    "MITHA MASKIT": "MITHA", "MITHA RAD": "MITHA", "MITHA CLA": "MITHA", "MITHA OT": "MITHA",
    "MAS - MITHA": "MITHA", "SSL BABY - MITHA ": "MITHA", "SAVIOSA - MITHA": "MITHA", "MITHA ": "MITHA",

    # 7. LYDIA
    "LYDIA KITO": "LYDIA", "LYDIA K": "LYDIA", "LYDIA BB": "LYDIA", "LYDIA - KITO": "LYDIA",

    # 8. NOVI (MERGE DENGAN RAFI/RAPI)
    "NOVI AINIE": "NOVI", "NOVI AV": "NOVI", "NOVI DAN RAFFI": "NOVI", "NOVI & RAFFI": "NOVI", 
    "RAFFI": "NOVI", "RAFI": "NOVI", "RAPI": "NOVI", "RAPI AV":"NOVI",

    # 9. ROZY
    "ROZY AINIE": "ROZY", "ROZY AV": "ROZY",

    # 10. DANI
    "DANI AINIE": "DANI", "DANI AV": "DANI", "DANI SEKAWAN": "DANI",

    # 11. MADONG
    "MADONG - MYKONOS": "MADONG", "MADONG - MAJU": "MADONG", "MADONG MYK": "MADONG",

    # 12. RISKA
    "RISKA AV": "RISKA", "RISKA BN": "RISKA", "RISKA CRS": "RISKA", "RISKA E-WL": "RISKA", 
    "RISKA JV": "RISKA", "RISKA REN": "RISKA", "RISKA R&L": "RISKA", "RISKA SMT": "RISKA", 
    "RISKA ST": "RISKA", "RISKA SYB": "RISKA", "RISKA - MILANO": "RISKA", "RISKA TF": "RISKA",
    "RISKA - YCM": "RISKA", "RISKA HONOR": "RISKA", "RISKA - VG": "RISKA", "RISKA TH": "RISKA", 
    "RISKA - INESIA": "RISKA", "SSL - RISKA": "RISKA", "SKIN - RIZKA": "RISKA", 

    # 13. TIM LISMAN (ADE, FANDI, DLL)
    "ADE CLA": "ADE", "ADE CRS": "ADE", "GLOOW - ADE": "ADE", "ADE JAVINCI": "ADE", "ADE JV": "ADE",
    "ADE SVD": "ADE", "ADE RAM PUTRA M.GIE": "ADE", "ADE - MLEN1": "ADE", "ADE NEWLAB": "ADE", "DORS - ADE": "ADE",
    "FANDI - BONAVIE": "FANDI", "DORS- FANDI": "FANDI", "FANDY CRS": "FANDI", "FANDI AFDILLAH": "FANDI", 
    "FANDY WL": "FANDI", "GLOOW - FANDY": "FANDI", "FANDI - GOUTE": "FANDI", "FANDI MG": "FANDI", 
    "FANDI - NEWLAB": "FANDI", "FANDY - YCM": "FANDI", "FANDY YLA": "FANDI", "FANDI JV": "FANDI", "FANDI MLEN": "FANDI",
    "NAUFAL - JAVINCI": "NAUFAL", "NAUFAL JV": "NAUFAL", "NAUFAL SVD": "NAUFAL", 
    "RIZKI JV": "RIZKI", "RIZKI SVD": "RIZKI", 
    "SAHRUL JAVINCI": "SYAHRUL", "SAHRUL TF": "SYAHRUL", "SAHRUL JV": "SYAHRUL", "GLOOW - SHARUL": "SYAHRUL",
    "SANTI BONAVIE": "SANTI", "SANTI WHITELAB": "SANTI", "SANTI GOUTE": "SANTI",
    "DWI CRS": "DWI", "DWI NLAB": "DWI", 
    "ASWIN ARTIS": "ASWIN", "ASWIN AI": "ASWIN", "ASWIN Inc": "ASWIN", "ASWIN INC": "ASWIN", "ASWIN - ARTIST INC": "ASWIN",

    # 14. TIM AKBAR (DEVI, BASTIAN, BAYU)
    "BASTIAN CASANDRA": "BASTIAN", "SSL- BASTIAN": "BASTIAN", "SKIN - BASTIAN": "BASTIAN", 
    "BASTIAN - HONOR": "BASTIAN", "BASTIAN - VG": "BASTIAN", "BASTIAN TH": "BASTIAN", 
    "BASTIAN YL": "BASTIAN", "BASTIAN YL-DIO CAT": "BASTIAN", "BASTIAN SHMP": "BASTIAN", "BASTIAN-DIO 45": "BASTIAN",
    "SSL - DEVI": "DEVI", "SKIN - DEVI": "DEVI", "DEVI Y- DIOSYS CAT": "DEVI",
    "DEVI YL": "DEVI", "DEVI SHMP": "DEVI", "DEVI-DIO 45": "DEVI", "DEVI YLA": "DEVI",
    "SSL- BAYU": "BAYU", "SKIN - BAYU": "BAYU", "BAYU-DIO 45": "BAYU", "BAYU YL-DIO CAT": "BAYU", 
    "BAYU SHMP": "BAYU", "BAYU YL": "BAYU", 

    # 16. LAIN-LAIN
    "HABIBI - FZ": "HABIBI", "HABIBI SYB": "HABIBI", "HABIBI TH": "HABIBI", 
    "GLOOW - LISMAN": "LISMAN", "LISMAN - NEWLAB": "LISMAN", 
    "WILLIAM BTC": "WILLIAM", "WILLI - ROS": "WILLIAM", "WILLI - WAL": "WILLIAM",
    "RINI JV": "RINI", "RINI SYB": "RINI", 
    "FAUZIAH CLA": "FAUZIAH", "FAUZIAH ST": "FAUZIAH", 
    "MARIANA CLIN": "MARIANA", "JAYA - MARIANA": "MARIANA"
}
