"""
High-Throughput Scraper & Ingestion Pipeline Orchestrator untuk Seluruh Platform Mobil Bekas.
"""

from models.database import SessionLocal, init_db
from data.seed_master_cars import seed_master_car_database
from data.seed_car_auctions import seed_car_auction_database
from data.generate_car_market import generate_massive_car_dataset
from analytics.pricing_engine import PricingAnalyticsEngine

def run_full_car_ingestion_pipeline():
    print("=================================================================")
    print("🚀 MEMULAI PIPELINE HARVESTING & INGESTION CARPRICE ID")
    print("=================================================================")
    
    # 1. Inisialisasi Database & Seeder Master Catalog
    print("\n[Step 1/4] Inisialisasi Database & Master Catalog Mobil...")
    seed_master_car_database()

    # 2. Seed Lot Lelang JBA & IBID
    print("\n[Step 2/4] Harvesting Data Lot Balai Lelang Resmi (JBA & IBID)...")
    seed_car_auction_database(target_count=5000)

    # 3. Seed Dataset Listing Retail Pasar
    print("\n[Step 3/4] Ingestion Dataset Listing Retail Pasar Multi-Platform...")
    generate_massive_car_dataset(target_per_variant=45)

    # 4. Refresh Pricing Intelligence Stats
    print("\n[Step 4/4] Menghitung Statistik Kuartil & FMV Harian...")
    db = SessionLocal()
    try:
        engine = PricingAnalyticsEngine(db)
        updated = engine.refresh_daily_market_stats()
        print(f"✅ Berhasil menghitung dan memperbarui {updated} statistik FMV pasar mobil.")
    finally:
        db.close()

    print("\n🎉 SELURUH PIPELINE DATA TELAH SUKSES DIJALANKAN!")
    print("=================================================================")

if __name__ == "__main__":
    run_full_car_ingestion_pipeline()
