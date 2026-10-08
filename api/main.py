from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from models.database import get_db, init_db
from models.catalog import MasterBrand, MasterModel, MasterVariant, ScrapedListing, MarketPriceStats
from analytics.ml_car_valuation import ml_car_model_v7
from analytics.pricing_engine import PricingAnalyticsEngine
from analytics.regional_index import apply_regional_pricing, get_all_regions

app = FastAPI(
    title="CarPrice ID API",
    description="Automotive Valuation & Market Intelligence REST API for Indonesian Used Cars",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return {
        "service": "CarPrice ID Automotive Valuation Engine",
        "version": "1.0.0",
        "ml_model": ml_car_model_v7.version,
        "status": "OPERATIONAL"
    }

@app.get("/api/v1/brands")
def get_brands(db: Session = Depends(get_db)):
    brands = db.query(MasterBrand).filter(MasterBrand.is_active == True).all()
    return [{"id": b.id, "name": b.name, "country": b.country_origin} for b in brands]

@app.get("/api/v1/models/{brand_id}")
def get_models(brand_id: int, db: Session = Depends(get_db)):
    models = db.query(MasterModel).filter(MasterModel.brand_id == brand_id).all()
    return [{
        "id": m.id,
        "name": m.name,
        "category": m.category,
        "engine_cc": m.engine_capacity_cc,
        "fuel_default": m.fuel_type_default,
        "seats": m.seat_capacity
    } for m in models]

@app.get("/api/v1/variants/{model_id}")
def get_variants(model_id: int, db: Session = Depends(get_db)):
    variants = db.query(MasterVariant).filter(MasterVariant.model_id == model_id).all()
    return [{
        "id": v.id,
        "name": v.variant_name,
        "year_start": v.release_year_start,
        "year_end": v.release_year_end,
        "official_msrp_new": float(v.official_msrp_new) if v.official_msrp_new else None,
        "transmission": v.transmission_type,
        "fuel_type": v.fuel_type
    } for v in variants]

@app.get("/api/v1/valuation")
def calculate_car_valuation(
    variant_id: int,
    year: int = Query(..., ge=2000, le=2026),
    odometer_km: int = Query(..., ge=0, le=500000),
    transmission: str = "Automatic",
    fuel_type: str = "Bensin",
    tax_status: str = "Pajak Hidup / Panjang",
    has_bpkb: bool = True,
    is_flood_free: bool = True,
    is_accident_free: bool = True,
    region: str = "Jabodetabek (DKI Jakarta, Bogor, Depok, Tangerang, Bekasi)",
    db: Session = Depends(get_db)
):
    variant = db.query(MasterVariant).filter(MasterVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Varian mobil tidak ditemukan")

    msrp = float(variant.official_msrp_new) if variant.official_msrp_new else 280000000.0

    eval_result = ml_car_model_v7.predict_valuation(
        msrp_new=msrp,
        claimed_year=year,
        odometer_km=odometer_km,
        engine_cc=variant.engine_capacity_cc or 1500,
        fuel_type=fuel_type,
        transmission=transmission,
        tax_status=tax_status,
        has_bpkb=has_bpkb,
        is_flood_free=is_flood_free,
        is_accident_free=is_accident_free,
        current_year=2026
    )

    regional_eval = apply_regional_pricing(eval_result["predicted_fmv"], region)
    eval_result["regional_valuation"] = regional_eval

    return eval_result

@app.get("/api/v1/arbitrage-deals")
def get_arbitrage_deals(
    min_discount_pct: float = 10.0,
    limit: int = 30,
    db: Session = Depends(get_db)
):
    engine = PricingAnalyticsEngine(db)
    return engine.get_top_arbitrage_deals(min_discount_pct=min_discount_pct, limit=limit)
