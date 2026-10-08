"""
Indeks Disparitas Harga Mobil Multi-Wilayah Indonesia.
Memetakan koefisien disparitas harga pasar mobil bekas antar-provinsi dan pulau di Indonesia
berdasarkan faktor biaya logistik ekspedisi kapal roro/kontainer, bea balik nama (BBN-KB R4), dan likuiditas pasar regional.
"""

from typing import Dict, Any, List

REGIONAL_PRICE_INDEX: Dict[str, Dict[str, Any]] = {
    "Jabodetabek (DKI Jakarta, Bogor, Depok, Tangerang, Bekasi)": {
        "multiplier": 1.000,
        "region_code": "JABO",
        "description": "Wilayah acuan standar nasional (Baseline Likuiditas Tertinggi & Volume Terbesar)",
        "bbn_rate": "12.5%",
        "provinces": ["DKI Jakarta", "Banten (Tangerang)", "Jawa Barat (Depok/Bekasi/Bogor)"]
    },
    "Jawa Barat (Bandung, Cirebon, Tasikmalaya, Karawang, Sukabumi)": {
        "multiplier": 0.990,
        "region_code": "JABAR",
        "description": "Pasar sekunder sangat aktif, harga kompetitif mendekati Jabodetabek",
        "bbn_rate": "12.5%",
        "provinces": ["Jawa Barat"]
    },
    "Jawa Tengah & D.I. Yogyakarta (Semarang, Solo, Jogja, Banyumas)": {
        "multiplier": 0.980,
        "region_code": "JATENG_DIY",
        "description": "Pasar mobil keluarga stabil, harga rata-rata 2% lebih terjangkau dari Jabodetabek",
        "bbn_rate": "12.0%",
        "provinces": ["Jawa Tengah", "D.I. Yogyakarta"]
    },
    "Jawa Timur (Surabaya, Malang, Kediri, Jember, Banyuwangi)": {
        "multiplier": 0.985,
        "region_code": "JATIM",
        "description": "Pusat industri Jawa Timur dengan perputaran unit cepat (Plat L / W / N)",
        "bbn_rate": "12.5%",
        "provinces": ["Jawa Timur"]
    },
    "Bali & Nusa Tenggara (Denpasar, Badung, Mataram, Kupang)": {
        "multiplier": 1.040,
        "region_code": "BALI_NUSRA",
        "description": "Tingginya permintaan rental pariwisata & biaya penyeberangan feri (+4.0%)",
        "bbn_rate": "15.0%",
        "provinces": ["Bali", "Nusa Tenggara Barat", "Nusa Tenggara Timur"]
    },
    "Sumatera (Medan, Palembang, Pekanbaru, Lampung, Padang, Batam)": {
        "multiplier": 1.060,
        "region_code": "SUMATERA",
        "description": "Biaya ekspedisi lintas selat & tingginya retensi mobil diesel turbo (+6.0%)",
        "bbn_rate": "15.0%",
        "provinces": ["Sumatera Utara", "Sumatera Selatan", "Riau", "Lampung", "Sumatera Barat", "Kepulauan Riau", "Aceh", "Jambi", "Bengkulu"]
    },
    "Kalimantan & IKN (Balikpapan, Samarinda, Banjarmasin, Pontianak, Nusantara)": {
        "multiplier": 1.090,
        "region_code": "KALIMANTAN_IKN",
        "description": "Biaya kargo roro & tingginya daya beli sektor energi/komoditas/IKN (+9.0%)",
        "bbn_rate": "15.0%",
        "provinces": ["Kalimantan Timur", "Kalimantan Selatan", "Kalimantan Barat", "Kalimantan Tengah", "Kalimantan Utara"]
    },
    "Sulawesi, Maluku & Papua (Makassar, Manado, Ambon, Jayapura)": {
        "multiplier": 1.110,
        "region_code": "TIMUR_INDONESIA",
        "description": "Wilayah kepulauan timur dengan jarak ekspedisi terjauh & retensi harga tinggi (+11.0%)",
        "bbn_rate": "15.0%",
        "provinces": ["Sulawesi Selatan", "Sulawesi Utara", "Sulawesi Tengah", "Maluku", "Papua"]
    }
}

def get_all_regions() -> List[str]:
    return list(REGIONAL_PRICE_INDEX.keys())

def get_region_multiplier(region_name: str) -> float:
    data = REGIONAL_PRICE_INDEX.get(region_name)
    if data:
        return data["multiplier"]
    return 1.000

def apply_regional_pricing(base_fmv: float, region_name: str) -> Dict[str, Any]:
    multiplier = get_region_multiplier(region_name)
    regional_price = base_fmv * multiplier
    diff = regional_price - base_fmv
    return {
        "region": region_name,
        "multiplier": multiplier,
        "baseline_fmv": base_fmv,
        "regional_fmv": regional_price,
        "regional_delta": diff,
        "description": REGIONAL_PRICE_INDEX.get(region_name, {}).get("description", "")
    }
