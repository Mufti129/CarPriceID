import re
from typing import Dict, Any, Optional
from pipeline.slang_dictionary import DP_SCAM_PATTERNS

class ScamAndDPDetector:
    """
    Detektor Harga Semu, Uang Muka (DP Clickbait), dan Listing Penipuan Mobil Bekas.
    Memisahkan listing tunai murni (Cash Price) dari jebakan Down Payment.
    """

    # Ambang batas harga minimum wajar mobil bekas berdasarkan rentang tahun
    YEAR_MIN_CASH_PRICE_THRESHOLDS = {
        2024: 100_000_000, # Mobil baru 2024-2026 wajar cash >= Rp 100jt (kecuali EV mikro)
        2022: 75_000_000,
        2020: 60_000_000,
        2018: 50_000_000,
        2015: 45_000_000,
        2010: 35_000_000,
        2000: 25_000_000
    }
    ABSOLUTE_MIN_PRICE = 20_000_000 # Di bawah Rp 20jt hampir pasti DP / scam / mobil rongsok

    @classmethod
    def is_dp_or_scam(
        cls,
        price: Optional[float],
        title: str = "",
        description: str = "",
        claimed_year: Optional[int] = None,
        msrp_new: Optional[float] = None
    ) -> bool:
        """
        Menilai apakah suatu listing merupakan harga DP/Scam/Kredit palsu.
        Returns: True jika DP/Scam, False jika Cash Price valid.
        """
        if price is None or price <= 0:
            return True

        # 1. Cek batas absolut dasar mobil
        if price < cls.ABSOLUTE_MIN_PRICE:
            return True

        combined_text = f"{title} {description}".lower()

        # 2. Cek rasio terhadap MSRP Baru (Jika harga < 18% MSRP pada mobil < 6 tahun, pasti DP)
        if msrp_new and claimed_year:
            age = max(0, 2026 - claimed_year)
            if age <= 6 and (price / msrp_new) < 0.18:
                return True

        # 3. Cek pola kata kunci DP / Uang Muka di judul atau deskripsi
        has_dp_keyword = any(bool(re.search(pat, combined_text)) for pat in DP_SCAM_PATTERNS)

        # 4. Evaluasi threshold berbasis tahun
        if claimed_year:
            for cutoff_year, min_price in sorted(cls.YEAR_MIN_CASH_PRICE_THRESHOLDS.items(), reverse=True):
                if claimed_year >= cutoff_year:
                    if price < min_price and has_dp_keyword:
                        return True
                    if price < (min_price * 0.55): # Jauh di bawah batas normal tanpa keyword pun dicurigai DP
                        return True
                    break

        return False

    @classmethod
    def classify_listing_price(cls, listing_dict: Dict[str, Any], msrp_new: Optional[float] = None) -> Dict[str, Any]:
        """Menambahkan field 'is_dp_price' dan 'price_classification' ke record listing."""
        is_dp = cls.is_dp_or_scam(
            price=listing_dict.get("price"),
            title=listing_dict.get("title", ""),
            description=listing_dict.get("raw_description", ""),
            claimed_year=listing_dict.get("claimed_year"),
            msrp_new=msrp_new
        )

        listing_dict["is_dp_price"] = is_dp
        listing_dict["price_type"] = "DP / Clickbait" if is_dp else "Cash"
        return listing_dict
