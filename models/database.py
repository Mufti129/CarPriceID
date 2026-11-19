import os
from typing import Dict, Any
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.environ.get("DB_PATH", "mobil_bekas.db")
raw_db_url = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Normalisasi skema postgres:// ke postgresql:// untuk kompatibilitas SQLAlchemy 2.0 (Supabase / RDS / Heroku)
if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url

IS_SQLITE = DATABASE_URL.startswith("sqlite")

if IS_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_high_concurrency_pragma(dbapi_connection, connection_record):
        """
        Mengaktifkan Write-Ahead Logging (WAL) & optimasi memori pada SQLite
        untuk menghilangkan bottleneck 'database is locked' saat baca/tulis simultan.
        """
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA busy_timeout=30000;")
            cursor.execute("PRAGMA cache_size=-32000;")
            cursor.execute("PRAGMA temp_store=MEMORY;")
        except Exception:
            pass
        finally:
            cursor.close()
else:
    # Konfigurasi Enterprise Connection Pool untuk PostgreSQL (Supabase / AWS RDS)
    engine = create_engine(
        DATABASE_URL,
        pool_size=int(os.environ.get("DB_POOL_SIZE", "10")),
        max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "20")),
        pool_pre_ping=True,
        pool_recycle=1800,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models.catalog import (
        MasterBrand,
        MasterModel,
        MasterVariant,
        ScrapedListing,
        MarketPriceStats,
        AuctionLot,
        WholesalePriceStats,
        IbidMapValuation,
        SyncJobLog,
    )

    Base.metadata.create_all(bind=engine)

    # Auto-migration & composite index optimization
    try:
        import sqlite3

        if IS_SQLITE:
            db_file = DB_PATH
            if os.path.exists(db_file):
                conn = sqlite3.connect(db_file, timeout=30)
                c = conn.cursor()

                # Check master_models columns
                c.execute("PRAGMA table_info(master_models)")
                cols_m = [r[1] for r in c.fetchall()]
                if cols_m and "image_url" not in cols_m:
                    c.execute("ALTER TABLE master_models ADD COLUMN image_url TEXT")

                # Check master_variants columns
                c.execute("PRAGMA table_info(master_variants)")
                cols_v = [r[1] for r in c.fetchall()]
                if cols_v and "image_url" not in cols_v:
                    c.execute("ALTER TABLE master_variants ADD COLUMN image_url TEXT")

                # Composite indexes for ultra-fast analytics & filtering
                c.execute(
                    "CREATE INDEX IF NOT EXISTS idx_scraped_var_year_dp "
                    "ON scraped_listings (matched_variant_id, claimed_year, is_dp_price);"
                )
                c.execute(
                    "CREATE INDEX IF NOT EXISTS idx_auction_var_year_status "
                    "ON auction_listings (matched_variant_id, claimed_year, auction_status);"
                )
                c.execute(
                    "CREATE INDEX IF NOT EXISTS idx_ibid_brand_series_year "
                    "ON ibid_map_valuations (brand, series, year, transmission);"
                )

                conn.commit()
                conn.close()
    except Exception:
        pass


def get_db_engine_info() -> Dict[str, Any]:
    """Mengembalikan informasi diagnostik engine database aktif (SQLite WAL vs PostgreSQL Pool)."""
    info: Dict[str, Any] = {
        "dialect": "SQLite (High-Concurrency WAL)" if IS_SQLITE else "PostgreSQL (Connection Pool)",
        "is_sqlite": IS_SQLITE,
        "journal_mode": "UNKNOWN",
        "composite_indexes_active": True,
    }
    try:
        with engine.connect() as conn:
            if IS_SQLITE:
                res = conn.execute(text("PRAGMA journal_mode;")).scalar()
                info["journal_mode"] = str(res).upper() if res else "WAL"
            else:
                info["journal_mode"] = "MVCC_POSTGRES"
    except Exception:
        info["journal_mode"] = "WAL" if IS_SQLITE else "MVCC"
    return info
