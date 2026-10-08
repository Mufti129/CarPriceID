from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Boolean, DateTime, Date, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from models.database import Base

class MasterBrand(Base):
    __tablename__ = "master_brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True) # e.g. Toyota, Honda, Mitsubishi, Hyundai, Wuling, BYD
    country_origin = Column(String(50), nullable=True) # Jepang, Korea Selatan, China, Jerman, AS
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    models = relationship("MasterModel", back_populates="brand", cascade="all, delete-orphan")


class MasterModel(Base):
    __tablename__ = "master_models"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("master_brands.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, index=True) # e.g. Avanza, Innova, Fortuner, Brio, HR-V, Xpander, Creta, Air EV
    category = Column(String(50), nullable=True) # MPV, SUV, LCGC, City Car, Sedan, Hatchback, Compact Crossover, EV
    engine_capacity_cc = Column(Integer, nullable=True) # 1000, 1200, 1500, 2000, 2400, 2800, 0 (EV)
    fuel_type_default = Column(String(30), default="Bensin") # Bensin, Diesel, Hybrid (HEV), Listrik (BEV)
    seat_capacity = Column(Integer, default=7) # 5, 7, 8
    image_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    brand = relationship("MasterBrand", back_populates="models")
    variants = relationship("MasterVariant", back_populates="model", cascade="all, delete-orphan")


class MasterVariant(Base):
    __tablename__ = "master_variants"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("master_models.id", ondelete="CASCADE"), nullable=False)
    variant_name = Column(String(150), nullable=False, index=True) # e.g. Innova Reborn 2.4 V Diesel AT, Avanza 1.5 G CVT TSS
    release_year_start = Column(Integer, nullable=False) # e.g. 2016
    release_year_end = Column(Integer, nullable=True) # e.g. 2022
    official_msrp_new = Column(Numeric(15, 2), nullable=True) # MSRP baru saat rilis OTR
    transmission_type = Column(String(30), default="Automatic") # Automatic, Manual, CVT, e-CVT, DCT
    fuel_type = Column(String(30), default="Bensin") # Bensin, Diesel Turbo, Hybrid (HEV), Listrik (BEV)
    engine_capacity_cc = Column(Integer, nullable=True)
    image_url = Column(Text, nullable=True)
    aliases = Column(Text, nullable=True) # Comma separated search keywords/aliases
    created_at = Column(DateTime, default=datetime.utcnow)

    model = relationship("MasterModel", back_populates="variants")
    scraped_listings = relationship("ScrapedListing", back_populates="matched_variant")
    auction_lots = relationship("AuctionLot", back_populates="matched_variant")


class ScrapedListing(Base):
    __tablename__ = "scraped_listings"

    id = Column(Integer, primary_key=True, index=True)
    source_platform = Column(String(50), nullable=False, index=True) # 'olx', 'carmudi', 'mobil123', 'facebook', 'carsome'
    external_id = Column(String(100), nullable=False, index=True)
    url = Column(Text, nullable=False)
    title = Column(String(300), nullable=False)
    raw_description = Column(Text, nullable=True)

    # Resolusi Entity oleh AI/Pipeline
    matched_variant_id = Column(Integer, ForeignKey("master_variants.id"), nullable=True, index=True)
    claimed_year = Column(Integer, nullable=True, index=True)

    # Harga & DP Filter
    price = Column(Numeric(15, 2), nullable=False, index=True)
    is_dp_price = Column(Boolean, default=False, index=True)
    odometer_km = Column(Integer, nullable=True)
    transmission = Column(String(30), nullable=True) # 'Automatic', 'Manual'
    fuel_type = Column(String(30), nullable=True) # 'Bensin', 'Diesel', 'Hybrid', 'Listrik'

    # Status Dokumen & Pajak
    tax_status = Column(String(50), nullable=True) # 'Hidup / Panjang', 'Mati / Off', 'Unknown'
    tax_expiry_year = Column(Integer, nullable=True)
    has_bpkb = Column(Boolean, default=True)
    has_stnk = Column(Boolean, default=True)
    has_faktur = Column(Boolean, default=True)
    plate_region = Column(String(20), nullable=True) # Plat B, Plat D, Plat L, Plat N, Plat W, etc.

    # Kondisi & Keistimewaan Mobil (NLP Extracted)
    flood_free = Column(Boolean, default=True) # Bebas banjir
    accident_free = Column(Boolean, default=True) # Bebas tabrak sasis
    service_record = Column(Boolean, default=True) # Record bengkel resmi
    first_hand = Column(Boolean, default=True) # Tangan pertama

    # Lokasi & Penjual
    province = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=True)
    seller_name = Column(String(150), nullable=True)
    seller_type = Column(String(50), nullable=True) # 'Individual', 'Showroom / Dealer'

    # Timestamps
    posted_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="ACTIVE")

    __table_args__ = (
        UniqueConstraint("source_platform", "external_id", name="uq_source_external_id_car"),
    )

    matched_variant = relationship("MasterVariant", back_populates="scraped_listings")


class AuctionLot(Base):
    """
    Unit Lot Balai Lelang Mobil Resmi (JBA Indonesia & IBID Astra).
    Mencatat data inspeksi teknis 4-titik, grade eksterior, interior, mesin, dan rangka sasis.
    """
    __tablename__ = "auction_listings"

    id = Column(Integer, primary_key=True, index=True)
    source_platform = Column(String(50), nullable=False, index=True) # 'jba_indonesia', 'ibid_astra'
    lot_number = Column(String(50), nullable=False, index=True)
    session_id = Column(String(100), nullable=True)
    auction_date = Column(Date, nullable=False, index=True)
    pool_city = Column(String(100), nullable=False, index=True)
    lane = Column(String(50), nullable=True)

    # Resolusi Varian
    matched_variant_id = Column(Integer, ForeignKey("master_variants.id"), nullable=True, index=True)
    claimed_year = Column(Integer, nullable=True, index=True)
    color = Column(String(50), nullable=True)
    license_plate = Column(String(30), nullable=True)
    plate_region = Column(String(20), nullable=True)
    transmission = Column(String(30), default="Automatic")
    fuel_type = Column(String(30), default="Bensin")

    # Hasil Inspeksi & Kondisi Fisik 4 Titik
    odometer_km = Column(Integer, nullable=True)
    grade_exterior = Column(String(10), nullable=True) # 'A', 'B', 'C', 'D', 'E'
    grade_interior = Column(String(10), nullable=True) # 'A', 'B', 'C', 'D', 'E'
    grade_engine = Column(String(10), nullable=True) # 'A', 'B', 'C', 'D', 'E'
    grade_frame_body = Column(String(10), nullable=True) # 'A', 'B', 'C', 'D' (Bebas Potong Rangka)
    overall_score = Column(String(20), nullable=True) # e.g. "Grade B+", "ACV 4.2"
    engine_condition = Column(String(100), nullable=True) # 'Kering Sehat', 'Rembes Oli Ringan', 'Kasar'
    inspection_notes = Column(Text, nullable=True)

    # Legalitas & Dokumen
    stnk_status = Column(String(50), default="Ada")
    tax_status = Column(String(50), default="Hidup")
    bpkb_status = Column(String(50), default="Ready (Asli)")
    faktur_status = Column(Boolean, default=True)

    # Data Harga & Hasil Lelang
    base_limit_price = Column(Numeric(15, 2), nullable=False) # Harga Dasar Pembukaan
    hammer_price = Column(Numeric(15, 2), nullable=True) # Harga Ketok Palu Terbentuk
    admin_fee = Column(Numeric(15, 2), default=2500000.0) # Biaya admin lelang mobil
    auction_status = Column(String(30), default="Sold") # 'Sold', 'No Bid', 'Withdrawn'
    bid_count = Column(Integer, default=1)

    url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("source_platform", "lot_number", "auction_date", name="uq_auction_platform_lot_date_car"),
    )

    matched_variant = relationship("MasterVariant", back_populates="auction_lots")


class WholesalePriceStats(Base):
    """
    Agregasi Statistik Harga Wholesale & Lelang per Varian Mobil per Tanggal Sesi.
    """
    __tablename__ = "wholesale_price_stats"

    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(Date, nullable=False, default=datetime.utcnow().date, index=True)
    variant_id = Column(Integer, ForeignKey("master_variants.id"), nullable=False)
    year = Column(Integer, nullable=False)
    pool_city = Column(String(100), nullable=True)

    sample_count = Column(Integer, nullable=False)
    avg_base_price = Column(Numeric(15, 2))
    median_hammer_price = Column(Numeric(15, 2))
    min_base_price = Column(Numeric(15, 2))
    max_hammer_price = Column(Numeric(15, 2))
    clearance_rate_pct = Column(Numeric(5, 2), default=82.0)

    __table_args__ = (
        UniqueConstraint("stat_date", "variant_id", "year", "pool_city", name="uq_wholesale_stat_date_var_year_city_car"),
    )


class MarketPriceStats(Base):
    __tablename__ = "market_price_stats"

    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(Date, nullable=False, default=datetime.utcnow().date, index=True)
    variant_id = Column(Integer, ForeignKey("master_variants.id"), nullable=False)
    year = Column(Integer, nullable=False)
    city = Column(String(100), nullable=True)

    sample_count = Column(Integer, nullable=False)
    price_min = Column(Numeric(15, 2))
    price_p25 = Column(Numeric(15, 2)) # Bargain / Target Deal Showroom
    price_median = Column(Numeric(15, 2)) # Fair Market Value (FMV)
    price_p75 = Column(Numeric(15, 2)) # Premium Pristine Price
    price_max = Column(Numeric(15, 2))

    __table_args__ = (
        UniqueConstraint("stat_date", "variant_id", "year", "city", name="uq_stat_date_var_year_city_car"),
    )
