"""
Kamus Slang, Terminologi, & Pola Regex Pasar Jual Beli Mobil Bekas di Indonesia.
Digunakan oleh NLP Normalizer dan AI Entity Resolver.
"""

TAX_PATTERNS = {
    "hidup": [
        r"pajak\s*(?:hidup|on|pjg|panjang|aktif|jalan|tertib)",
        r"pjk\s*(?:hidup|on|pjg|panjang|aktif|jln|jalan)",
        r"taat\s*pajak",
        r"surat\s*hidup",
        r"tertib\s*pajak",
        r"plat\s*panjang",
        r"kaleng\s*20(?:2[6-9]|3\d)"
    ],
    "mati": [
        r"pjk\s*off\s*(\d+)\s*(?:th|thn|tahun|x|kali)?",
        r"pajak\s*off\s*(\d+)\s*(?:th|thn|tahun|x|kali)?",
        r"pajak\s*mati\s*(\d+)\s*(?:th|thn|tahun|x|kali)?",
        r"telat\s*(?:pajak\s*)?(\d+)\s*(?:th|thn|tahun|x|kali)?",
        r"pajak\s*lewat\s*(\d+)\s*(?:th|thn|tahun)?",
        r"pajak\s*(?:mati|off|tewas|lewat|tidur|bobok)",
        r"pjk\s*(?:mati|off|tewas|lewat|tdr|bobok)"
    ]
}

DOCUMENT_PATTERNS = {
    "lengkap": [
        r"(?:stnk\s*[\+,dan\s]*\s*bpkb)",
        r"(?:surat\s*(?:lengkap|komplit|fullset|komplit plit|ready))",
        r"(?:bpkb\s*[\+,dan\s]*\s*stnk\s*(?:[\+,dan\s]*\s*faktur)?)",
        r"(?:ss\s*(?:lengkap|komplit|ready))",
        r"(?:komplit\s*(?:faktur|form\s*a)?)",
        r"(?:buku\s*(?:servis|service|manual))",
        r"(?:kunci\s*(?:serep|cadangan))"
    ],
    "stnk_only": [
        r"stnk\s*(?:only|tok|aja|doang)",
        r"batangan",
        r"non\s*bpkb",
        r"bpkb\s*(?:hilang|ilang|nyusul|sekolah|fidusia)",
        r"surat\s*sebelah",
        r"ss\s*stnk\s*only"
    ]
}

TRANSMISSION_PATTERNS = {
    "Automatic": [
        r"\b(?:matic|matick|matang|at|a/t|cvt|e-cvt|ecvt|tiptronic|dual\s*clutch|dct|steptronic|otomatis)\b"
    ],
    "Manual": [
        r"\b(?:manual|mt|m/t|tongkat|kopling)\b"
    ]
}

FUEL_PATTERNS = {
    "Diesel": [
        r"\b(?:diesel|solar|dex|d-4d|2gd|1gd|4n15|common\s*rail|turbo\s*diesel)\b"
    ],
    "Hybrid": [
        r"\b(?:hybrid|hev|phev|mild\s*hybrid|e-power|shvs)\b"
    ],
    "Listrik": [
        r"\b(?:listrik|ev|bev|electric|baterai|battery)\b"
    ],
    "Bensin": [
        r"\b(?:bensin|gasoline|petrol|pertalite|pertamax|vvt-i|dual\s*vvt-i|i-vtec|mivec)\b"
    ]
}

CONDITION_PATTERNS = {
    "flood_free": [
        r"(?:bebas|anti|bukan\s*bekas|jaminan\s*bukan)\s*(?:banjir|kebanjiran|rendam|terendam)",
        r"bebas\s*banjir\s*100%",
        r"garansi\s*bebas\s*banjir"
    ],
    "accident_free": [
        r"(?:bebas|anti|bukan\s*bekas|jaminan\s*bukan)\s*(?:tabrak|benturan|laka|insiden|kecelakaan)",
        r"(?:tulang|sasis|chassis|chasis)\s*(?:aman|utuh|lempeng|orisinil)",
        r"garansi\s*bebas\s*tabrakan"
    ],
    "service_record": [
        r"service\s*record\s*(?:resmi|auto2000|honda|beres|dealer|authorized)",
        r"buku\s*servis\s*(?:lengkap|teratur|rapi)",
        r"rawatan\s*(?:resmi|dealer|bengkel\s*resmi)"
    ],
    "first_hand": [
        r"(?:tangan\s*pertama|tangan\s*1|tgn\s*1|an\s*perorangan|dari\s*baru|pemilik\s*langsung)"
    ]
}

PLATE_PATTERNS = [
    r"\bplat\s*([a-zA-Z]{1,2})\b",
    r"\bplat\s*([a-zA-Z]{1,2})\s*(?:dki|jakarta|tangerang|bekasi|depok|bogor|bandung|jogja|surabaya|semarang|medan|bali)?\b",
    r"\b([a-zA-Z]{1,2})\s*dki\b",
    r"\b([a-zA-Z]{1,2})\s*kab\b",
    r"\b([a-zA-Z]{1,2})\s*kotamadya\b"
]

DP_SCAM_PATTERNS = [
    r"\bdp\b",
    r"\btanda\s*jadi\b",
    r"\buang\s*muka\b",
    r"\btotal\s*dp\b",
    r"\btdp\b",
    r"\bcicilan\b",
    r"\bangsuran\b",
    r"\bkredit\b",
    r"\bcredit\b",
    r"\bleasing\b",
    r"\boper\s*kredit\b",
    r"\bover\s*kredit\b",
    r"\btake\s*over\b",
    r"\bkhusus\s*kredit\b",
    r"\bharga\s*kredit\b",
    r"\bdp\s*ceper\b",
    r"\bdp\s*minim\b"
]

PRICE_SLANG_PATTERNS = [
    (r"(\d+(?:[\.,]\d+)?)\s*(?:m|miliar|milyar)\b", 1_000_000_000),
    (r"(\d+(?:[\.,]\d+)?)\s*(?:jt|juta)\b", 1_000_000),
    (r"(\d+(?:[\.,]\d+)?)\s*k\b", 1_000),
    (r"(\d+(?:[\.,]\d+)?)\s*rb\b", 1_000),
]
