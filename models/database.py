import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.environ.get("DB_PATH", "mobil_bekas.db")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
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
        MasterBrand, MasterModel, MasterVariant, ScrapedListing, MarketPriceStats,
        AuctionLot, WholesalePriceStats, IbidMapValuation
    )
    Base.metadata.create_all(bind=engine)
    
    # Auto-migration check for SQLite
    try:
        import sqlite3
        if DATABASE_URL.startswith("sqlite"):
            db_file = DB_PATH
            if os.path.exists(db_file):
                conn = sqlite3.connect(db_file)
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
                    
                conn.commit()
                conn.close()
    except Exception:
        pass
