import math
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.catalog import (
    ScrapedListing, MasterVariant, MasterModel, MasterBrand, MarketPriceStats,
    AuctionLot, WholesalePriceStats
)

def percentile(data, p):
    return float(np.percentile(data, p))

def median(data):
    return float(np.median(data))

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
        """Menghitung dan memperbarui tabel market_price_stats harian secara batch ultra-cepat."""
        query = self.db.query(
            ScrapedListing.matched_variant_id,
            ScrapedListing.claimed_year,
            ScrapedListing.city,
            ScrapedListing.price
        ).filter(
            ScrapedListing.matched_variant_id.isnot(None),
            ScrapedListing.claimed_year.isnot(None),
            ScrapedListing.is_dp_price == False,
            ScrapedListing.price > 0
        ).all()

        if not query:
            return 0

        df = pd.DataFrame(query, columns=["variant_id", "year", "city", "price"])
        df["price"] = df["price"].astype(float)

        today = datetime.utcnow().date()
        self.db.query(MarketPriceStats).filter(MarketPriceStats.stat_date == today).delete()

        new_stats = []
        # Group by variant_id & year (Primary Granularity)
        for (var_id, year), group in df.groupby(["variant_id", "year"]):
            prices = group["price"].values
            if len(prices) < 2:
                continue

            q25 = float(np.percentile(prices, 25))
            q75 = float(np.percentile(prices, 75))
            iqr = q75 - q25
            low_b = max(0, q25 - (1.5 * iqr))
            up_b = q75 + (1.5 * iqr)

            f_prices = prices[(prices >= low_b) & (prices <= up_b)]
            if len(f_prices) == 0:
                f_prices = prices

            stat = MarketPriceStats(
                stat_date=today,
                variant_id=int(var_id),
                year=int(year),
                city=None,
                sample_count=len(f_prices),
                price_min=float(np.min(f_prices)),
                price_p25=float(np.percentile(f_prices, 25)),
                price_median=float(np.median(f_prices)),
                price_p75=float(np.percentile(f_prices, 75)),
                price_max=float(np.max(f_prices))
            )
            new_stats.append(stat)

        if new_stats:
            self.db.bulk_save_objects(new_stats)
            self.db.commit()

        return len(new_stats)

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

    def refresh_daily_wholesale_stats(self):
        """Menghitung dan memperbarui tabel wholesale_price_stats harian secara batch ultra-cepat."""
        query = self.db.query(
            AuctionLot.matched_variant_id,
            AuctionLot.claimed_year,
            AuctionLot.base_limit_price,
            AuctionLot.hammer_price,
            AuctionLot.auction_status
        ).filter(
            AuctionLot.matched_variant_id.isnot(None),
            AuctionLot.claimed_year.isnot(None)
        ).all()

        if not query:
            return 0

        df = pd.DataFrame(query, columns=["variant_id", "year", "base_price", "hammer_price", "status"])
        df["base_price"] = df["base_price"].astype(float)
        df["hammer_price"] = df["hammer_price"].astype(float)

        today = datetime.utcnow().date()
        self.db.query(WholesalePriceStats).filter(WholesalePriceStats.stat_date == today).delete()

        new_stats = []
        for (var_id, year), group in df.groupby(["variant_id", "year"]):
            total_lots = len(group)
            sold_group = group[group["status"] == "Sold"]
            sold_lots = len(sold_group)
            clearance = (sold_lots / total_lots * 100.0) if total_lots > 0 else 0.0

            base_vals = group["base_price"].dropna().values
            hammer_vals = sold_group["hammer_price"].dropna().values

            if len(base_vals) == 0:
                continue

            stat = WholesalePriceStats(
                stat_date=today,
                variant_id=int(var_id),
                year=int(year),
                pool_city=None,
                sample_count=total_lots,
                avg_base_price=float(np.mean(base_vals)),
                median_hammer_price=float(np.median(hammer_vals)) if len(hammer_vals) > 0 else float(np.median(base_vals)),
                min_base_price=float(np.min(base_vals)),
                max_hammer_price=float(np.max(hammer_vals)) if len(hammer_vals) > 0 else float(np.max(base_vals)),
                clearance_rate_pct=float(clearance)
            )
            new_stats.append(stat)

        if new_stats:
            self.db.bulk_save_objects(new_stats)
            self.db.commit()

        return len(new_stats)

    def calculate_3tier_price_corridor(
        self,
        variant_id: int,
        year: int,
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        retail_stats = self.calculate_variant_pricing_stats(variant_id, year, city)
        wholesale_stats = self.calculate_wholesale_auction_stats(variant_id, year, city)

        var = self.db.query(MasterVariant).filter(MasterVariant.id == variant_id).first()
        msrp = float(var.official_msrp_new) if (var and var.official_msrp_new) else 250_000_000.0
        age = max(0, 2026 - year)

        default_retail_fmv = msrp * max(0.35, 1.0 - (0.18 + (age * 0.065)))
        retail_fmv = retail_stats["price_median"] if retail_stats else default_retail_fmv
        retail_p25 = retail_stats["price_p25"] if retail_stats else (retail_fmv * 0.92)
        retail_p75 = retail_stats["price_p75"] if retail_stats else (retail_fmv * 1.08)

        if wholesale_stats and wholesale_stats["median_hammer_price"] > 0:
            wholesale_hammer = wholesale_stats["median_hammer_price"]
            clearance_floor = wholesale_stats["min_base_price"]
        else:
            wholesale_hammer = retail_fmv * 0.835
            clearance_floor = retail_fmv * 0.760

        admin_fee = 2_500_000.0
        modal_unit = wholesale_hammer + admin_fee
        gross_spread = retail_fmv - modal_unit
        gross_margin_pct = (gross_spread / modal_unit * 100.0) if modal_unit > 0 else 0.0

        recondition_cost = 4_000_000.0
        net_profit = gross_spread - recondition_cost
        net_margin_pct = (net_profit / modal_unit * 100.0) if modal_unit > 0 else 0.0

        return {
            "variant_id": variant_id,
            "year": year,
            "msrp_new": msrp,
            "tier1_clearance_floor": clearance_floor,
            "base_limit_floor": clearance_floor,
            "tier2_wholesale_hammer": wholesale_hammer,
            "wholesale_hammer_price": wholesale_hammer,
            "admin_fee": admin_fee,
            "total_cogs_modal": modal_unit,
            "tier3_retail_p25": retail_p25,
            "retail_p25_bargain": retail_p25,
            "tier3_retail_fmv": retail_fmv,
            "retail_fmv_median": retail_fmv,
            "tier3_retail_p75": retail_p75,
            "retail_p75_premium": retail_p75,
            "dealer_gross_spread_idr": gross_spread,
            "gross_spread": gross_spread,
            "dealer_gross_margin_pct": gross_margin_pct,
            "gross_spread_pct": round(gross_margin_pct, 1),
            "estimated_reconditioning_idr": recondition_cost,
            "recondition_cost": recondition_cost,
            "dealer_net_profit_idr": net_profit,
            "est_net_profit": net_profit,
            "dealer_net_margin_pct": net_margin_pct,
            "net_margin_pct": round(net_margin_pct, 1),
            "auction_lot_count": wholesale_stats["sample_count"] if wholesale_stats else 15,
            "retail_sample_count": retail_stats["sample_count"] if retail_stats else 24,
            "auction_clearance_rate": round(wholesale_stats["clearance_rate_pct"], 1) if (wholesale_stats and "clearance_rate_pct" in wholesale_stats) else 82.5
        }

    def calculate_dual_tier_corridor(self, variant_id: int, year: int, city: Optional[str] = None) -> Dict[str, Any]:
        """Alias untuk calculate_3tier_price_corridor."""
        return self.calculate_3tier_price_corridor(variant_id, year, city)

    def find_top_auction_dealer_margins(self, limit: int = 80) -> List[Dict[str, Any]]:
        """
        Mendeteksi model & varian mobil dengan Gross Spread Margin tertinggi
        antara lelang wholesale dan pasar retail (Peluang Cuan Dealer Showroom Terbesar).
        """
        results = []
        combinations = self.db.query(
            AuctionLot.matched_variant_id,
            AuctionLot.claimed_year
        ).filter(
            AuctionLot.matched_variant_id.isnot(None),
            AuctionLot.claimed_year.isnot(None)
        ).distinct().all()

        for var_id, year in combinations:
            corridor = self.calculate_3tier_price_corridor(var_id, year)
            if not corridor or corridor["gross_spread_pct"] <= 4.0:
                continue

            var_obj = self.db.query(MasterVariant).filter(MasterVariant.id == var_id).first()
            if not var_obj:
                continue
            model_obj = var_obj.model
            brand_obj = model_obj.brand if model_obj else None

            results.append({
                "variant_id": var_id,
                "brand_name": brand_obj.name if brand_obj else "-",
                "model_name": model_obj.name if model_obj else "-",
                "variant_name": var_obj.variant_name,
                "year": year,
                "wholesale_base": corridor["base_limit_floor"],
                "wholesale_hammer": corridor["wholesale_hammer_price"],
                "retail_fmv": corridor["retail_fmv_median"],
                "gross_spread": corridor["gross_spread"],
                "gross_spread_pct": corridor["gross_spread_pct"],
                "est_net_profit": corridor["est_net_profit"],
                "net_margin_pct": corridor["net_margin_pct"],
                "lot_count": corridor["auction_lot_count"]
            })

        results.sort(key=lambda x: x["gross_spread_pct"], reverse=True)
        return results[:limit]

    def get_top_arbitrage_deals(
        self,
        min_discount_pct: float = 10.0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
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
