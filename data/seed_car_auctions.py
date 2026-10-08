"""
Seeder Data Lelang Mobil Resmi Indonesia (JBA Indonesia & IBID Astra).
Menghasilkan 5.000+ lot lelang mobil dengan data inspeksi teknis 4-titik (eksterior, interior, mesin, struktur sasis),
harga dasar limit, harga terbentuk ketok palu, serta catatan kondisi fisik.
"""

import re
import random
import urllib.parse
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.database import SessionLocal, init_db
from models.catalog import AuctionLot, MasterVariant, MasterModel, MasterBrand

POOL_CITIES = [
    "Jakarta (Daan Mogot)", "Jakarta (Tipar Cakung)", "Tangerang (BSD)",
    "Bekasi (Harapan Indah)", "Surabaya (Margomulyo)", "Bandung (Soekarno Hatta)",
    "Semarang (Genuk)", "Medan (Amplas)", "Balikpapan (Batakan)", "Makassar (Pattallassang)"
]

GRADES = ["A", "B", "C", "D"]
GRADE_WEIGHTS = [0.25, 0.45, 0.22, 0.08]

ENGINE_CONDITIONS = [
    "Kering Sehat (Standard)", "Rembes Oli Ringan Tutup Klep",
    "Suara Halus Terawat", "Perlu Servis Rutin / Ganti Oli",
    "AC Kurang Dingin Minor", "Normal Terawat Record Dealer"
]

NOTES_SAMPLES = [
    "Bodi mulus lecet pemakaian wajar, interior orisinil bersih, bebas banjir 100%, sasis lempeng asli.",
    "Baret bumper depan kiri, interior rapi sarung jok, mesin kering responsif, AC dingin.",
    "Pajak hidup panjang, surat BPKB faktur komplit ready, unit siap pakai tanpa perbaikan berat.",
    "Baret halus pintu samping kanan, ban depan 85%, mesin terawat tarikan padat.",
    "Bekas pemakaian direksi / perorangan tangan pertama, service record teratur di bengkel resmi."
]

COLORS = ["Putih Mutiara", "Hitam Metalik", "Silver Metalik", "Abu-Abu / Grey", "Merah Maroon", "Biru Metalik"]

def seed_car_auction_database(target_count: int = 5000):
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(AuctionLot).count()
        if existing >= target_count:
            print(f"ℹ️ Auction lots sudah terisi ({existing} lots). Melanjutkan...")
            return

        variants = db.query(MasterVariant).all()
        if not variants:
            print("⚠️ Harap jalankan seed_master_car_database() terlebih dahulu.")
            return

        print(f"🚀 Memulai seeding {target_count} lot lelang mobil (JBA Indonesia & IBID Astra)...")
        lots_to_add = []
        base_date = datetime(2026, 10, 7).date()

        for i in range(target_count):
            var = random.choice(variants)
            platform = random.choice(["jba_indonesia", "ibid_astra"])
            lot_no = f"LOT-{1000 + i}"
            sess_id = f"SESS-{20260900 + (i % 30)}"
            days_ago = random.randint(0, 45)
            auction_date = base_date - timedelta(days=days_ago)
            pool_city = random.choice(POOL_CITIES)

            start_yr = var.release_year_start
            end_yr = var.release_year_end or 2026
            claimed_year = random.randint(start_yr, min(2026, end_yr))
            age = max(0, 2026 - claimed_year)

            # Odometer realistis: ~12.000 - 15.000 km per tahun
            base_km = max(8000, age * random.randint(11000, 16000))
            odometer = base_km + random.randint(-4000, 8000)
            odometer = max(2500, odometer)

            # Depresiasi mobil untuk perhitungan harga lelang
            msrp = float(var.official_msrp_new) if var.official_msrp_new else 280000000.0
            depr_factor = max(0.35, 1.0 - (0.17 + (age * 0.062)))
            market_val = msrp * depr_factor

            # Wholesale discount lelang
            is_sold = random.random() < 0.84 # 84% Clearance Rate
            base_limit = market_val * random.uniform(0.72, 0.78)
            hammer_price = (market_val * random.uniform(0.80, 0.86)) if is_sold else None
            status = "Sold" if is_sold else ("No Bid" if random.random() < 0.8 else "Withdrawn")
            bids = random.randint(2, 9) if is_sold else 0

            ext_grade = random.choices(GRADES, weights=GRADE_WEIGHTS)[0]
            int_grade = random.choices(GRADES, weights=GRADE_WEIGHTS)[0]
            eng_grade = random.choices(GRADES, weights=GRADE_WEIGHTS)[0]
            frame_grade = "A" if random.random() < 0.88 else "B" # 88% lulus sasis A
            overall = f"Grade {ext_grade}{eng_grade}"

            plat_letters = random.choice(["B", "D", "L", "N", "W", "H", "AD", "AB", "BK", "BG", "DK", "KT"])
            nopol = f"{plat_letters} {random.randint(1000, 9999)} {random.choice(['XX', 'YY', 'ZZ', 'AB', 'CD', 'EF'])}"

            brand_n = var.model.brand.name if (var.model and var.model.brand) else "Toyota"
            model_n = var.model.name if var.model else "Avanza"
            v_clean = re.sub(r'\(.*?\)', '', var.variant_name).strip()
            v_clean = re.sub(r'^(All\s+New|New)\s+', '', v_clean, flags=re.IGNORECASE).strip()
            v_tokens = v_clean.split()
            if len(v_tokens) >= 2 and v_tokens[1].lower() in ['zenix', 'reborn', 'cross', 'satya', 'ev', 'sport', 'prime', 'signature', 'dakar', 'hybrid', 'venturer', 'urbanite']:
                car_sub = f"{v_tokens[0]} {v_tokens[1]}"
            elif len(v_tokens) >= 1:
                car_sub = v_tokens[0]
            else:
                car_sub = model_n.split('&')[0].strip()
            clean_car_str = f"{brand_n} {car_sub}".strip()
            q_enc = urllib.parse.quote_plus(clean_car_str)

            if "jba" in platform.lower():
                lot_url = f"https://www.jba.co.id/id/lelang-mobil?keyword={q_enc}"
            else:
                lot_url = f"https://www.ibid.astra.co.id/cari-otomotif?keyword={q_enc}&kategori=mobil"

            lot = AuctionLot(
                source_platform=platform,
                lot_number=lot_no,
                session_id=sess_id,
                auction_date=auction_date,
                pool_city=pool_city,
                lane=random.choice(["Lane A (SUV/MPV)", "Lane B (City Car)", "Lane C (Commercial/Fleet)"]),
                matched_variant_id=var.id,
                claimed_year=claimed_year,
                color=random.choice(COLORS),
                license_plate=nopol,
                plate_region=f"Plat {plat_letters}",
                transmission=var.transmission_type or "Automatic",
                fuel_type=var.fuel_type or "Bensin",
                odometer_km=odometer,
                grade_exterior=ext_grade,
                grade_interior=int_grade,
                grade_engine=eng_grade,
                grade_frame_body=frame_grade,
                overall_score=overall,
                engine_condition=random.choice(ENGINE_CONDITIONS),
                inspection_notes=random.choice(NOTES_SAMPLES),
                stnk_status="Ada (Asli)",
                tax_status="Hidup / Panjang" if random.random() < 0.85 else "Mati 1 Tahun",
                bpkb_status="Ready (Asli)",
                faktur_status=True,
                base_limit_price=round(base_limit, -5),
                hammer_price=round(hammer_price, -5) if hammer_price else None,
                admin_fee=2500000.0,
                auction_status=status,
                bid_count=bids,
                url=lot_url
            )
            lots_to_add.append(lot)

            if len(lots_to_add) >= 1000:
                db.bulk_save_objects(lots_to_add)
                db.commit()
                lots_to_add = []

        if lots_to_add:
            db.bulk_save_objects(lots_to_add)
            db.commit()

        print(f"✅ Selesai menyemai {target_count} Lot Lelang Mobil JBA & IBID.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding car auctions: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_car_auction_database()
