import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from models.catalog import MasterBrand, MasterModel, MasterVariant

try:
    from rapidfuzz import fuzz, process
except ImportError:
    # Fallback Levenshtein sederhana jika rapidfuzz belum terinstall
    class FuzzFallback:
        @staticmethod
        def token_set_ratio(s1: str, s2: str) -> float:
            w1 = set(s1.lower().split())
            w2 = set(s2.lower().split())
            if not w1 or not w2:
                return 0.0
            intersection = w1.intersection(w2)
            return (len(intersection) * 2.0) / (len(w1) + len(w2)) * 100.0

        @staticmethod
        def token_sort_ratio(s1: str, s2: str) -> float:
            return FuzzFallback.token_set_ratio(s1, s2)
    fuzz = FuzzFallback()

class EntityMatcher:
    """
    Mesin AI Pemetaan Entitas (Entity Resolution) Teks Listing Mobil Bekas ke Master Catalog.
    Menerapkan Normalisasi Teks Fonetik, Token Set Weighting, dan Multi-Pass Fuzzy Matcher.
    """

    def __init__(self, db_session: Session, min_match_score: float = 68.0):
        self.db = db_session
        self.min_match_score = min_match_score
        self.variants_cache: List[Dict[str, Any]] = []
        self._load_master_catalog()

    def _load_master_catalog(self):
        """Memuat seluruh data varian master ke RAM untuk pencarian ultra cepat."""
        variants = self.db.query(
            MasterVariant.id,
            MasterVariant.variant_name,
            MasterVariant.release_year_start,
            MasterVariant.release_year_end,
            MasterVariant.official_msrp_new,
            MasterVariant.transmission_type,
            MasterVariant.fuel_type,
            MasterVariant.aliases,
            MasterModel.name.label("model_name"),
            MasterBrand.name.label("brand_name")
        ).join(
            MasterModel, MasterVariant.model_id == MasterModel.id
        ).join(
            MasterBrand, MasterModel.brand_id == MasterBrand.id
        ).all()

        self.variants_cache = []
        for v in variants:
            alias_list = [a.strip().lower() for a in (v.aliases or "").split(",") if a.strip()]
            search_corpus = f"{v.brand_name} {v.model_name} {v.variant_name} {' '.join(alias_list)}".lower()

            self.variants_cache.append({
                "id": v.id,
                "brand_name": v.brand_name,
                "model_name": v.model_name,
                "variant_name": v.variant_name,
                "release_start": v.release_year_start,
                "release_end": v.release_year_end or 2026,
                "msrp_new": float(v.official_msrp_new) if v.official_msrp_new else None,
                "transmission": v.transmission_type,
                "fuel_type": v.fuel_type,
                "search_corpus": search_corpus,
                "aliases": alias_list
            })

    def match_listing(
        self,
        title: str,
        claimed_year: Optional[int] = None,
        description: str = ""
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Mencocokkan judul/deskripsi listing ke katalog master varian mobil.
        Returns: (matched_variant_dict, match_score) atau (None, 0.0)
        """
        if not self.variants_cache:
            self._load_master_catalog()
            if not self.variants_cache:
                return None, 0.0

        clean_query = re.sub(r"[^\w\s]", " ", f"{title} {description}").lower()
        clean_query = re.sub(r"\s+", " ", clean_query).strip()

        best_match = None
        best_score = 0.0

        for candidate in self.variants_cache:
            # 1. Filter tahun rilis (jika tahun listing diketahui)
            if claimed_year:
                # Berikan toleransi 1 tahun untuk registrasi faktur
                if claimed_year < (candidate["release_start"] - 1) or claimed_year > (candidate["release_end"] + 1):
                    continue

            # 2. Cek kecocokan Brand & Model
            brand_in_query = candidate["brand_name"].lower() in clean_query
            model_in_query = candidate["model_name"].lower() in clean_query

            # 3. Hitung Fuzzy Score
            score_set = fuzz.token_set_ratio(candidate["search_corpus"], clean_query)
            score_sort = fuzz.token_sort_ratio(candidate["variant_name"].lower(), clean_query)
            combined_score = (score_set * 0.7) + (score_sort * 0.3)

            # Bonus bobot jika Brand & Model match secara eksplisit
            if brand_in_query and model_in_query:
                combined_score += 15.0
            elif brand_in_query or model_in_query:
                combined_score += 8.0

            # Bonus jika ada exact alias match
            for alias in candidate["aliases"]:
                if alias in clean_query:
                    combined_score += 12.0
                    break

            if combined_score > best_score:
                best_score = combined_score
                best_match = candidate

        if best_score >= self.min_match_score and best_match:
            return best_match, min(100.0, best_score)

        return None, best_score
