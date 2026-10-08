import math
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.catalog import (
    ScrapedListing, MasterVariant, MasterModel, MasterBrand, MarketPriceStats,
    AuctionLot, WholesalePriceStats
)

try:
    import numpy as np
    def percentile(data, p):
        return float(np.percentile(data, p))
    def median(data):
        return float(np.median(data))
except ImportError:
    def percentile(data, p):
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return float(sorted_data[int(k)])
        d0 = sorted_data[int(f)] * (c - k)
        d1 = sorted_data[int(c)] * (k - f)
        return float(d0 + d1)
    def median(data):
        return percentile(data, 50)

class PricingAnalyticsEngine:
    """
    Kalkulator Fair Market Value (FMV) & Market Intelligence untuk Mobil Bekas.
    Menghitung statistik kuantil harga (P25, Median, P75), 3-Tier Price Corridors, dan Arbitrase Dealer.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def calculate_variant_pricing_stats(
        self,
        variant_id: int,
        year: Optional[int] = None,
        city: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Menghitung statistik harga pasar wajar untuk suatu varian mobil dan tahun tertentu.
        """
        query = self.db.query(ScrapedListing.price).filter(
            ScrapedListing.matched_variant_id == variant_id,
            ScrapedListing.is_dp_price == False,
            ScrapedListing.price > 0
        )

        if year:
            query = query.filter(ScrapedListing.claimed_year == year)
        if city:
            query = query.filter(ScrapedListing.city == city)

        prices = [float(p[0]) for p in query.all() if p[0] is not None]

        if len(prices) < 2:
            return None

        # 1. Outlier Removal menggunakan Interquartile Range (IQR)
        q25_raw = percentile(prices, 25)
        q75_raw = percentile(prices, 75)
        iqr = q75_raw - q25_raw
        lower_bound = max(0, q25_raw - (1.5 * iqr))
        upper_bound = q75_raw + (1.5 * iqr)

        filtered_prices = [p for p in prices if lower_bound <= p <= upper_bound]
        if not filtered_prices:
            filtered_prices = prices

        stats = {
            "variant_id": variant_id,
            "year": year,
            "city": city,
            "sample_count": len(filtered_prices),
            "price_min": float(min(filtered_prices)),
            "price_p25": float(percentile(filtered_prices, 25)),
            "price_median": float(median(filtered_prices)),
            "price_p75": float(percentile(filtered_prices, 75)),
            "price_max": float(max(filtered_prices)),
            "calculated_at": datetime.utcnow()
        }
        return stats

    def refresh_daily_market_stats(self):
        """Menghitung dan memperbarui tabel market_price_stats harian untuk semua kombinasi aktif."""
        combinations = self.db.query(
            ScrapedListing.matched_variant_id,
            ScrapedListing.claimed_year,
            ScrapedListing.city
        ).filter(
            ScrapedListing.matched_variant_id.isnot(None),
            ScrapedListing.claimed_year.isnot(None),
            ScrapedListing.is_dp_price == False
        ).distinct().all()

        today = datetime.utcnow().date()
        updated_count = 0

        for var_id, year, city in combinations:
            stats = self.calculate_variant_pricing_stats(var_id, year, city)
            if not stats:
                continue

            record = self.db.query(MarketPriceStats).filter(
                MarketPriceStats.stat_date == today,
                MarketPriceStats.variant_id == var_id,
                MarketPriceStats.year == year,
                MarketPriceStats.city == city
            ).first()

            if not record:
                record = MarketPriceStats(
                    stat_date=today,
                    variant_id=var_id,
                    year=year,
                    city=city,
                    sample_count=stats["sample_count"],
                    price_min=stats["price_min"],
                    price_p25=stats["price_p25"],
                    price_median=stats["price_median"],
                    price_p75=stats["price_p75"],
                    price_max=stats["price_max"]
                )
                self.db.add(record)
            else:
                record.sample_count = stats["sample_count"]
                record.price_min = stats["price_min"]
                record.price_p25 = stats["price_p25"]
                record.price_median = stats["price_median"]
                record.price_p75 = stats["price_p75"]
                record.price_max = stats["price_max"]

            updated_count += 1

        self.db.commit()
        return updated_count

    def calculate_wholesale_auction_stats(
        self,
        variant_id: int,
        year: Optional[int] = None,
        pool_city: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Menghitung ringkasan statistik lot lelang (JBA & IBID) per varian mobil."""
        query = self.db.query(AuctionLot).filter(
            AuctionLot.matched_variant_id == variant_id
        )
        if year:
            query = query.filter(AuctionLot.claimed_year == year)
        if pool_city:
            query = query.filter(AuctionLot.pool_city == pool_city)

        lots = query.all()
        if not lots:
            return None

        base_prices = [float(l.base_limit_price) for l in lots if l.base_limit_price]
        hammer_prices = [float(l.hammer_price) for l in lots if l.hammer_price and l.auction_status == "Sold"]
        sold_count = len(hammer_prices)
        total_count = len(lots)

        clearance_rate = (sold_count / total_count * 100.0) if total_count > 0 else 0.0

        return {
            "variant_id": variant_id,
            "year": year,
            "pool_city": pool_city,
            "total_lots": total_count,
            "sold_lots": sold_count,
            "clearance_rate_pct": clearance_rate,
            "avg_base_price": float(np.mean(base_prices)) if base_prices else 0.0,
            "median_hammer_price": float(median(hammer_prices)) if hammer_prices else (float(median(base_prices)) if base_prices else 0.0),
            "min_base_price": float(min(base_prices)) if base_prices else 0.0,
            "max_hammer_price": float(max(hammer_prices)) if hammer_prices else 0.0
        }

    def calculate_3tier_price_corridor(
        self,
        variant_id: int,
        year: int,
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Menghitung Koridor Harga 3-Tier untuk Mobil Bekas:
        Tier 1: Clearance Floor (Harga Dasar Limit Lelang)
        Tier 2: Wholesale Market (Harga Ketok Palu Lelang Terbentuk + Admin Fee)
        Tier 3: Retail Fair Market Value (Harga Pasar Eceran Konsumen)
        Serta menghitung Dealer Gross Spread & Net Profit Margin.
        """
        retail_stats = self.calculate_variant_pricing_stats(variant_id, year, city)
        wholesale_stats = self.calculate_wholesale_auction_stats(variant_id, year, city)

        # Baseline fallback jika data salah satu layer tipis
        var = self.db.query(MasterVariant).filter(MasterVariant.id == variant_id).first()
        msrp = float(var.official_msrp_new) if (var and var.official_msrp_new) else 250_000_000.0
        age = max(0, 2026 - year)

        # Teori depresiasi mobil: tahun 1 (~18%), berikutnya ~6.5%/thn
        default_retail_fmv = msrp * max(0.35, 1.0 - (0.18 + (age * 0.065)))
        retail_fmv = retail_stats["price_median"] if retail_stats else default_retail_fmv
        retail_p25 = retail_stats["price_p25"] if retail_stats else (retail_fmv * 0.92)
        retail_p75 = retail_stats["price_p75"] if retail_stats else (retail_fmv * 1.08)

        if wholesale_stats and wholesale_stats["median_hammer_price"] > 0:
            wholesale_hammer = wholesale_stats["median_hammer_price"]
            clearance_floor = wholesale_stats["min_base_price"]
        else:
            # Standar rasio lelang mobil di Indonesia: Hammer Price ~ 82-85% Retail FMV, Floor ~ 74-78% Retail FMV
            wholesale_hammer = retail_fmv * 0.835
            clearance_floor = retail_fmv * 0.760

        admin_fee = 2_500_000.0 # Biaya lelang mobil rata-rata
        modal_unit = wholesale_hammer + admin_fee
        gross_spread = retail_fmv - modal_unit
        gross_margin_pct = (gross_spread / modal_unit * 100.0) if modal_unit > 0 else 0.0

        # Estimasi biaya rekondisi salon mobil, detailing bodi, ganti oli & garansi showroom
        recondition_cost = 4_000_000.0
        net_profit = gross_spread - recondition_cost
        net_margin_pct = (net_profit / modal_unit * 100.0) if modal_unit > 0 else 0.0

        return {
            "variant_id": variant_id,
            "year": year,
            "msrp_new": msrp,
            "tier1_clearance_floor": clearance_floor,
            "tier2_wholesale_hammer": wholesale_hammer,
            "admin_fee": admin_fee,
            "total_cogs_modal": modal_unit,
            "tier3_retail_p25": retail_p25,
            "tier3_retail_fmv": retail_fmv,
            "tier3_retail_p75": retail_p75,
            "dealer_gross_spread_idr": gross_spread,
            "dealer_gross_margin_pct": gross_margin_pct,
            "estimated_reconditioning_idr": recondition_cost,
            "dealer_net_profit_idr": net_profit,
            "dealer_net_margin_pct": net_margin_pct
        }

    def get_top_arbitrage_deals(
        self,
        min_discount_pct: float = 10.0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Mendeteksi listing retail yang dijual jauh di bawah Fair Market Value (FMV).
        """
        listings = self.db.query(
            ScrapedListing,
            MasterVariant.variant_name,
            MasterModel.name.label("model_name"),
            MasterBrand.name.label("brand_name"),
            MasterVariant.official_msrp_new
        ).join(
            MasterVariant, ScrapedListing.matched_variant_id == MasterVariant.id
        ).join(
            MasterModel, MasterVariant.model_id == MasterModel.id
        ).join(
            MasterBrand, MasterModel.brand_id == MasterBrand.id
        ).filter(
            ScrapedListing.is_dp_price == False,
            ScrapedListing.price > 25_000_000,
            ScrapedListing.matched_variant_id.isnot(None),
            ScrapedListing.claimed_year.isnot(None)
        ).all()

        deals = []
        for l, var_name, model_name, brand_name, msrp_new in listings:
            stats = self.calculate_variant_pricing_stats(l.matched_variant_id, l.claimed_year)
            if not stats:
                continue

            fmv = stats["price_median"]
            if fmv <= 0 or float(l.price) >= fmv:
                continue

            discount_idr = fmv - float(l.price)
            discount_pct = (discount_idr / fmv) * 100.0

            if discount_pct >= min_discount_pct:
                deals.append({
                    "id": l.id,
                    "title": l.title,
                    "brand": brand_name,
                    "model": model_name,
                    "variant": var_name,
                    "year": l.claimed_year,
                    "price": float(l.price),
                    "fmv_price": fmv,
                    "p25_target": stats["price_p25"],
                    "discount_idr": discount_idr,
                    "discount_pct": discount_pct,
                    "city": l.city or "Jabodetabek",
                    "odometer_km": l.odometer_km,
                    "transmission": l.transmission,
                    "fuel_type": l.fuel_type,
                    "source": l.source_platform,
                    "url": l.url
                })

        deals.sort(key=lambda x: x["discount_pct"], reverse=True)
        return deals[:limit]
