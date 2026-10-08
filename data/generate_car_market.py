"""
Generator Dataset Listing Pasar Mobil Bekas Berskala Besar (15.000+ Listing Multi-Platform).
Mencakup OLX, Mobil123, Carmudi, Facebook Marketplace, Carsome, dan Carro
dengan variasi harga normal, hot bargain deals, serta noise harga DP semu untuk validasi AI Scam Detector.
"""

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.database import SessionLocal, init_db
from models.catalog import ScrapedListing, MasterVariant, MasterModel, MasterBrand
from pipeline.scam_detector import ScamAndDPDetector

CITIES_DATA = [
    {"city": "Jakarta Selatan", "prov": "DKI Jakarta", "plat": "Plat B"},
    {"city": "Jakarta Barat", "prov": "DKI Jakarta", "plat": "Plat B"},
    {"city": "Jakarta Pusat", "prov": "DKI Jakarta", "plat": "Plat B"},
    {"city": "Jakarta Timur", "prov": "DKI Jakarta", "plat": "Plat B"},
    {"city": "Tangerang", "prov": "Banten", "plat": "Plat B"},
    {"city": "Tangerang Selatan", "prov": "Banten", "plat": "Plat B"},
    {"city": "Bekasi", "prov": "Jawa Barat", "plat": "Plat B"},
    {"city": "Depok", "prov": "Jawa Barat", "plat": "Plat B"},
    {"city": "Bogor", "prov": "Jawa Barat", "plat": "Plat F"},
    {"city": "Bandung", "prov": "Jawa Barat", "plat": "Plat D"},
    {"city": "Surabaya", "prov": "Jawa Timur", "plat": "Plat L"},
    {"city": "Sidoarjo", "prov": "Jawa Timur", "plat": "Plat W"},
    {"city": "Malang", "prov": "Jawa Timur", "plat": "Plat N"},
    {"city": "Semarang", "prov": "Jawa Tengah", "plat": "Plat H"},
    {"city": "Solo", "prov": "Jawa Tengah", "plat": "Plat AD"},
    {"city": "Yogyakarta", "prov": "D.I. Yogyakarta", "plat": "Plat AB"},
    {"city": "Denpasar", "prov": "Bali", "plat": "Plat DK"},
    {"city": "Medan", "prov": "Sumatera Utara", "plat": "Plat BK"},
    {"city": "Palembang", "prov": "Sumatera Selatan", "plat": "Plat BG"},
    {"city": "Balikpapan", "prov": "Kalimantan Timur", "plat": "Plat KT"},
    {"city": "Makassar", "prov": "Sulawesi Selatan", "plat": "Plat DD"}
]

PLATFORMS = ["olx", "mobil123", "carmudi", "facebook", "carsome", "carro"]

SELLER_NAMES = [
    "Dharma Mobilindo", "Garasi Auto Gallery", "Bintang Motor Showroom",
    "Budi Santoso (Pemilik)", "Rendra Putra (Pribadi)", "Kurnia Mobil Bekas",
    "Sentra Mobil ITC Permata Hijau", "Auto Prima WTC Mangga Dua", "Surya Kencana Auto",
    "Agus Wijaya (Tangan Pertama)", "Berkah Motor Mandiri", "Cahaya Otomotif"
]

TITLES_TEMPLATES = [
    "{brand} {model} {variant} {year} Mulus Siap Luar Kota Record Dealer",
    "{brand} {model} {year} Tipe {variant} Tangan 1 Pajak Panjang Plat {plat}",
    "Dijual Cepat {brand} {model} {variant} Tahun {year} Low KM Orisinil",
    "Promo Spesial {brand} {model} {variant} {year} Istimewa Bebas Banjir Bebas Tabrak",
    "{brand} {model} {variant} {year} {trans} Terawat Jarang Pakai SS Lengkap"
]

def generate_massive_car_dataset(target_per_variant: int = 40):
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(ScrapedListing).count()
        if existing >= 10000:
            print(f"ℹ️ Listing retail mobil sudah terisi ({existing} listings). Melanjutkan...")
            return

        variants = db.query(
            MasterVariant,
            MasterModel.name.label("model_name"),
            MasterBrand.name.label("brand_name")
        ).join(
            MasterModel, MasterVariant.model_id == MasterModel.id
        ).join(
            MasterBrand, MasterModel.brand_id == MasterBrand.id
        ).all()

        if not variants:
            print("⚠️ Katalog varian mobil belum ada. Harap jalankan seed_master_cars.py dulu.")
            return

        print(f"🚀 Memulai generate dataset 15.000+ listing retail mobil bekas...")
        listings_to_add = []
        base_time = datetime(2026, 10, 8, 10, 0, 0)
        ext_counter = 100000

        for var, model_name, brand_name in variants:
            msrp = float(var.official_msrp_new) if var.official_msrp_new else 280000000.0
            start_yr = var.release_year_start
            end_yr = min(2026, var.release_year_end or 2026)

            for _ in range(target_per_variant):
                ext_counter += 1
                year = random.randint(start_yr, end_yr)
                age = max(0, 2026 - year)
                loc = random.choice(CITIES_DATA)
                platform = random.choice(PLATFORMS)
                seller = random.choice(SELLER_NAMES)
                seller_type = "Individual" if "Pribadi" in seller or "Pemilik" in seller or "Tangan Pertama" in seller else "Showroom / Dealer"

                # Hitung Nilai Wajar Baseline
                depr_rate = max(0.35, 1.0 - (0.17 + (age * 0.062)))
                base_fmv = msrp * depr_rate

                # Tentukan kategori listing: Normal, Bargain Deal, atau DP Scam
                rand_scenario = random.random()
                if rand_scenario < 0.07: # 7% Kasus DP Semu / Scam Clickbait
                    is_dp = True
                    # Nominal DP murah (Rp 15jt - Rp 35jt)
                    price = float(random.choice([15000000, 20000000, 25000000, 30000000, 35000000]))
                    title = f"TDP Ringan {brand_name} {model_name} {var.variant_name} {year} Angsuran Murah"
                    raw_desc = f"Total DP hanya Rp {price:,.0f}, angsuran terjangkau, proses leasing dibantu sampai acc!"
                elif rand_scenario < 0.22: # 15% Hot Bargain Deal (Diskon 10% - 20% di bawah FMV)
                    is_dp = False
                    discount = random.uniform(0.10, 0.22)
                    price = round(base_fmv * (1.0 - discount), -5)
                    title = f"BU Jual Cepat {brand_name} {model_name} {var.variant_name} {year} Nego Tipis"
                    raw_desc = f"Butuh uang segera! {brand_name} {model_name} {year} kondisi mulus mesin sehat tangan 1 siap pakai."
                else: # Listing Retail Normal
                    is_dp = False
                    noise = random.uniform(-0.06, 0.08)
                    price = round(base_fmv * (1.0 + noise), -5)
                    title_tpl = random.choice(TITLES_TEMPLATES)
                    title = title_tpl.format(
                        brand=brand_name,
                        model=model_name,
                        variant=var.variant_name,
                        year=year,
                        plat=loc["plat"].replace("Plat ", ""),
                        trans=var.transmission_type or "Automatic"
                    )
                    raw_desc = f"Dijual {brand_name} {model_name} {var.variant_name} {year} warna terawat, bodi orisinil, bebas banjir & bebas tabrak, service record resmi."

                # Parameter Odometer & Kondisi
                base_km = max(7000, age * random.randint(11000, 16000))
                odometer = base_km + random.randint(-4000, 6000)
                odometer = max(2000, odometer)

                tax_status = "Pajak Hidup / Panjang" if random.random() < 0.88 else "Mati 1 Tahun"
                posted_time = base_time - timedelta(days=random.randint(0, 30), hours=random.randint(1, 23))

                listing = ScrapedListing(
                    source_platform=platform,
                    external_id=f"CAR-{platform[:3].upper()}-{ext_counter}",
                    url=f"https://www.{platform}.co.id/mobil-bekas/iklan-{ext_counter}",
                    title=title,
                    raw_description=raw_desc,
                    matched_variant_id=var.id,
                    claimed_year=year,
                    price=price,
                    is_dp_price=is_dp,
                    odometer_km=odometer,
                    transmission=var.transmission_type or "Automatic",
                    fuel_type=var.fuel_type or "Bensin",
                    tax_status=tax_status,
                    tax_expiry_year=2027 if tax_status == "Pajak Hidup / Panjang" else 2025,
                    has_bpkb=True,
                    has_stnk=True,
                    has_faktur=True,
                    plate_region=loc["plat"],
                    flood_free=True,
                    accident_free=True,
                    service_record=True if random.random() < 0.65 else False,
                    first_hand=True if seller_type == "Individual" or random.random() < 0.5 else False,
                    province=loc["prov"],
                    city=loc["city"],
                    district=loc["city"],
                    seller_name=seller,
                    seller_type=seller_type,
                    posted_at=posted_time,
                    scraped_at=datetime.utcnow(),
                    status="ACTIVE"
                )
                listings_to_add.append(listing)

                if len(listings_to_add) >= 1500:
                    db.bulk_save_objects(listings_to_add)
                    db.commit()
                    listings_to_add = []

        if listings_to_add:
            db.bulk_save_objects(listings_to_add)
            db.commit()

        print(f"✅ Selesai men-generate dataset pasar mobil retail ({ext_counter - 100000} listings).")
    except Exception as e:
        db.rollback()
        print(f"❌ Error generating car market dataset: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    generate_massive_car_dataset()
