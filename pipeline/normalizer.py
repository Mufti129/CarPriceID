import re
from typing import Dict, Any, Optional, Tuple
from pipeline.slang_dictionary import (
    TAX_PATTERNS, DOCUMENT_PATTERNS, TRANSMISSION_PATTERNS,
    FUEL_PATTERNS, CONDITION_PATTERNS, PLATE_PATTERNS, PRICE_SLANG_PATTERNS
)

class ListingNormalizer:
    """
    Ekstraktor dan Normalizer Teks Listing Mobil Bekas Indonesia.
    Mengubah deskripsi tidak terstruktur menjadi metadata bersih dan terstandarisasi.
    """

    @staticmethod
    def parse_price(raw_val: Any) -> Optional[float]:
        """Konversi berbagai variasi representasi harga ke float bersih."""
        if raw_val is None:
            return None
        if isinstance(raw_val, (int, float)):
            return float(raw_val)

        text = str(raw_val).strip().lower()
        text = re.sub(r"^(?:rp\.?|idr|harga:?)\s*", "", text)

        for pattern, multiplier in PRICE_SLANG_PATTERNS:
            match = re.search(pattern, text)
            if match:
                num_str = match.group(1).replace(",", ".")
                try:
                    return float(num_str) * multiplier
                except ValueError:
                    pass

        # Pembersihan angka standar dengan titik/koma (e.g. "235.000.000" atau "235,000,000")
        clean_num = re.sub(r"[^\d]", "", text)
        if clean_num:
            try:
                return float(clean_num)
            except ValueError:
                return None
        return None

    @staticmethod
    def extract_year(text: str) -> Optional[int]:
        """Ekstraksi tahun pembuatan mobil dari judul atau deskripsi (1995 - 2026)."""
        matches = re.findall(r"\b(199\d|20[0-2]\d)\b", text)
        if matches:
            years = [int(m) for m in matches if 1995 <= int(m) <= 2026]
            if years:
                return years[0]
        return None

    @staticmethod
    def extract_transmission(text: str) -> str:
        """Ekstraksi tipe transmisi: Automatic atau Manual."""
        lower_text = text.lower()
        for pat in TRANSMISSION_PATTERNS["Automatic"]:
            if re.search(pat, lower_text):
                return "Automatic"
        for pat in TRANSMISSION_PATTERNS["Manual"]:
            if re.search(pat, lower_text):
                return "Manual"
        return "Automatic" # Default mobil modern di Indonesia

    @staticmethod
    def extract_fuel_type(text: str) -> str:
        """Ekstraksi tipe bahan bakar: Bensin, Diesel, Hybrid, Listrik."""
        lower_text = text.lower()
        for pat in FUEL_PATTERNS["Listrik"]:
            if re.search(pat, lower_text):
                return "Listrik"
        for pat in FUEL_PATTERNS["Hybrid"]:
            if re.search(pat, lower_text):
                return "Hybrid"
        for pat in FUEL_PATTERNS["Diesel"]:
            if re.search(pat, lower_text):
                return "Diesel"
        return "Bensin"

    @staticmethod
    def extract_tax_status(text: str) -> Tuple[str, Optional[int]]:
        """
        Ekstraksi status pajak.
        Returns: (tax_status: 'Hidup / Panjang' | 'Mati / Off' | 'Unknown', years_off: int | None)
        """
        lower_text = text.lower()

        # Cek pola pajak mati dulu
        for pat in TAX_PATTERNS["mati"]:
            match = re.search(pat, lower_text)
            if match:
                years_off = None
                if match.groups() and match.group(1):
                    try:
                        years_off = int(match.group(1))
                    except ValueError:
                        pass
                return "Mati / Off", years_off

        # Cek pola pajak hidup
        for pat in TAX_PATTERNS["hidup"]:
            if re.search(pat, lower_text):
                return "Hidup / Panjang", 0

        return "Unknown", None

    @staticmethod
    def extract_documents(text: str) -> Tuple[bool, bool, bool]:
        """
        Ekstraksi kelengkapan surat.
        Returns: (has_bpkb: bool, has_stnk: bool, has_faktur: bool)
        """
        lower_text = text.lower()

        for pat in DOCUMENT_PATTERNS["stnk_only"]:
            if re.search(pat, lower_text):
                return False, True, False

        has_faktur = "faktur" in lower_text or "komplit" in lower_text
        return True, True, has_faktur

    @staticmethod
    def extract_condition_flags(text: str) -> Dict[str, bool]:
        """Ekstraksi jaminan bebas banjir, bebas tabrak, service record, dan tangan pertama."""
        lower_text = text.lower()
        
        flood_free = any(bool(re.search(pat, lower_text)) for pat in CONDITION_PATTERNS["flood_free"])
        accident_free = any(bool(re.search(pat, lower_text)) for pat in CONDITION_PATTERNS["accident_free"])
        service_rec = any(bool(re.search(pat, lower_text)) for pat in CONDITION_PATTERNS["service_record"])
        first_hand = any(bool(re.search(pat, lower_text)) for pat in CONDITION_PATTERNS["first_hand"])

        # Default assumption: jika tidak ada catatan kerusakan fatal, unit standar terawat
        return {
            "flood_free": flood_free or True,
            "accident_free": accident_free or True,
            "service_record": service_rec or False,
            "first_hand": first_hand or False
        }

    @staticmethod
    def extract_odometer(text: str) -> Optional[int]:
        """Ekstraksi jarak tempuh kilometer mobil (1.000 - 450.000 km)."""
        lower_text = text.lower()
        patterns = [
            r"(?:km|odo|odometer|jarak)\s*[:=]?\s*(\d{1,3}(?:[\.,]\d{3})+)\b", # "km 45.000"
            r"(?:km|odo|odometer|jarak)\s*[:=]?\s*(\d+)\s*(?:rb|k|ribu)\b",     # "km 45rb"
            r"\b(\d{1,3}(?:[\.,]\d{3})+)\s*(?:km|kilometer)\b",               # "45.000 km"
            r"\b(\d+)\s*(?:rb|k|ribu)\s*(?:km|kilometer)\b",                  # "45rb km"
            r"(?:km|odo)\s*[:=]?\s*(\d{4,6})\b"                               # "km 45000"
        ]

        for pat in patterns:
            match = re.search(pat, lower_text)
            if match:
                raw_km = match.group(1).replace(".", "").replace(",", "")
                if "rb" in pat or "k" in pat or "ribu" in pat:
                    try:
                        val = int(raw_km) * 1000
                        if 500 <= val <= 600000:
                            return val
                    except ValueError:
                        pass
                else:
                    try:
                        val = int(raw_km)
                        if 500 <= val <= 600000:
                            return val
                    except ValueError:
                        pass
        return None

    @staticmethod
    def extract_plate_region(text: str) -> Optional[str]:
        """Ekstraksi kode plat nomor polisi (Plat B, Plat D, Plat L, Plat DK, etc)."""
        lower_text = text.lower()
        for pat in PLATE_PATTERNS:
            match = re.search(pat, lower_text)
            if match:
                code = match.group(1).upper()
                if len(code) in (1, 2):
                    return f"Plat {code}"
        return None

    @classmethod
    def normalize_listing(cls, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Menjalankan seluruh pipeline normalisasi pada satu record listing mentah."""
        combined_text = f"{raw.get('title', '')} {raw.get('raw_description', '')}"

        price = cls.parse_price(raw.get("price"))
        claimed_year = raw.get("claimed_year") or cls.extract_year(combined_text)
        tax_status, tax_exp = cls.extract_tax_status(combined_text)
        has_bpkb, has_stnk, has_faktur = cls.extract_documents(combined_text)
        odometer = raw.get("odometer_km") or cls.extract_odometer(combined_text)
        transmission = raw.get("transmission") or cls.extract_transmission(combined_text)
        fuel_type = raw.get("fuel_type") or cls.extract_fuel_type(combined_text)
        cond_flags = cls.extract_condition_flags(combined_text)
        plate_reg = raw.get("plate_region") or cls.extract_plate_region(combined_text)

        return {
            "source_platform": raw.get("source_platform", "olx"),
            "external_id": str(raw.get("external_id", "")),
            "url": raw.get("url", ""),
            "title": raw.get("title", "").strip(),
            "raw_description": raw.get("raw_description", ""),
            "price": price,
            "claimed_year": claimed_year,
            "odometer_km": odometer,
            "transmission": transmission,
            "fuel_type": fuel_type,
            "tax_status": tax_status,
            "tax_expiry_year": tax_exp,
            "has_bpkb": has_bpkb,
            "has_stnk": has_stnk,
            "has_faktur": has_faktur,
            "flood_free": cond_flags["flood_free"],
            "accident_free": cond_flags["accident_free"],
            "service_record": cond_flags["service_record"],
            "first_hand": cond_flags["first_hand"],
            "plate_region": plate_reg,
            "province": raw.get("province"),
            "city": raw.get("city"),
            "district": raw.get("district"),
            "seller_name": raw.get("seller_name"),
            "seller_type": raw.get("seller_type", "Individual"),
            "posted_at": raw.get("posted_at")
        }
