import random
from typing import List, Dict, Any
from datetime import datetime

class CarAuctionScraper:
    """
    Scraper & Ingestion Engine untuk Balai Lelang Mobil Resmi (JBA Indonesia & IBID Astra).
    """

    AUCTION_POOLS = ["Jakarta (Daan Mogot)", "Jakarta (Tipar Cakung)", "Surabaya", "Bandung", "Medan", "Semarang"]

    def __init__(self):
        pass

    def fetch_live_lots(self, pool_city: str = "Jakarta (Daan Mogot)", page: int = 1) -> List[Dict[str, Any]]:
        """Mengambil katalog lot lelang mobil aktif."""
        sample_cars = [
            {"model": "Toyota Innova Reborn 2.4 G AT Diesel", "year": 2021, "base": 310000000, "km": 48000, "grade_ext": "B", "grade_eng": "A"},
            {"model": "Toyota All New Veloz 1.5 Q CVT", "year": 2022, "base": 225000000, "km": 28000, "grade_ext": "A", "grade_eng": "A"},
            {"model": "Honda Brio Satya 1.2 E CVT", "year": 2022, "base": 125000000, "km": 35000, "grade_ext": "B", "grade_eng": "B"},
            {"model": "Mitsubishi Pajero Sport 2.4 Dakar 4x2", "year": 2020, "base": 420000000, "km": 55000, "grade_ext": "B", "grade_eng": "A"},
            {"model": "Hyundai Creta 1.5 Prime IVT", "year": 2022, "base": 255000000, "km": 31000, "grade_ext": "A", "grade_eng": "A"}
        ]

        lots = []
        for i, c in enumerate(sample_cars):
            lot_id = f"JBA-CAR-{1000 + page * 10 + i}"
            lots.append({
                "source_platform": "jba_indonesia",
                "lot_number": lot_id,
                "auction_date": datetime.utcnow().date(),
                "pool_city": pool_city,
                "title": f"{c['model']} {c['year']}",
                "claimed_year": c["year"],
                "base_limit_price": c["base"],
                "odometer_km": c["km"],
                "grade_exterior": c["grade_ext"],
                "grade_engine": c["grade_eng"],
                "grade_interior": "B",
                "grade_frame_body": "A",
                "status": "Available"
            })
        return lots
