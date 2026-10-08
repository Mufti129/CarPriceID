"""
CLI & Pipeline Orchestrator untuk CarPrice ID.
"""

import sys
import argparse
from models.database import SessionLocal, init_db
from models.catalog import MasterBrand, MasterModel, MasterVariant, ScrapedListing, AuctionLot
from scrapers.expand_car_dataset import run_full_car_ingestion_pipeline
from analytics.pricing_engine import PricingAnalyticsEngine
from analytics.ml_car_valuation import ml_car_model_v7

def print_banner():
    print("""
========================================================================
   CARPRICE ID — USED CAR INTELLIGENCE & HEDONIC VALUATION ENGINE
   Versi 7.4.0-Enterprise (Automotive Indonesia Edition 2026)
========================================================================
""")

def show_summary():
    init_db()
    db = SessionLocal()
    try:
        brands = db.query(MasterBrand).count()
        models = db.query(MasterModel).count()
        variants = db.query(MasterVariant).count()
        listings = db.query(ScrapedListing).count()
        cash_listings = db.query(ScrapedListing).filter(ScrapedListing.is_dp_price == False).count()
        dp_scams = db.query(ScrapedListing).filter(ScrapedListing.is_dp_price == True).count()
        lots = db.query(AuctionLot).count()

        print(f"📊 DATABASE SUMMARY STATS:")
        print(f"  • Master Brands       : {brands}")
        print(f"  • Master Models       : {models}")
        print(f"  • Master Variants     : {variants}")
        print(f"  • Total Retail Ads    : {listings:,}")
        print(f"  • Verified Cash Price : {cash_listings:,}")
        print(f"  • DP / Clickbait Ads  : {dp_scams:,}")
        print(f"  • Auction Lots (JBA)  : {lots:,}")
        print(f"\n🧠 ML VALUATION MODEL:")
        print(f"  • Model Version       : {ml_car_model_v7.version}")
        print(f"  • R2 Determination    : {ml_car_model_v7.evaluation_metrics['r2_score']}")
        print(f"  • MAE Accuracy        : Rp {ml_car_model_v7.evaluation_metrics['mae_idr']:,.0f}")
        print(f"  • MAPE Accuracy       : {ml_car_model_v7.evaluation_metrics['mape_pct']}%")
    finally:
        db.close()

def main():
    print_banner()
    parser = argparse.ArgumentParser(description="CarPrice ID CLI Runner")
    parser.add_argument("--seed", action="store_true", help="Jalankan full seeding & harvesting pipeline")
    parser.add_argument("--summary", action="store_true", help="Tampilkan ringkasan statistik database")
    parser.add_argument("--refresh-stats", action="store_true", help="Hitung ulang statistik FMV harian")

    args = parser.parse_args()

    if args.seed:
        run_full_car_ingestion_pipeline()
        show_summary()
    elif args.refresh_stats:
        init_db()
        db = SessionLocal()
        try:
            engine = PricingAnalyticsEngine(db)
            c = engine.refresh_daily_market_stats()
            print(f"✅ Selesai memperbarui {c} baris statistik pasar.")
        finally:
            db.close()
    elif args.summary:
        show_summary()
    else:
        show_summary()
        print("\nGunakan flag '--seed' untuk inisialisasi dataset baru atau '--help' untuk opsi.")

if __name__ == "__main__":
    main()
