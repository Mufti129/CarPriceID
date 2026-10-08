from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.database import get_db, init_db
from models.catalog import (
    MasterBrand, MasterModel, MasterVariant, ScrapedListing, 
    MarketPriceStats, AuctionLot, WholesalePriceStats
)
from analytics.ml_car_valuation import ml_car_model_v7
from analytics.pricing_engine import PricingAnalyticsEngine
from analytics.regional_index import REGIONAL_PRICE_INDEX, apply_regional_pricing, get_all_regions

app = FastAPI(
    title="CarPrice ID B2B Enterprise API",
    description="Automotive Valuation & Market Intelligence REST API for Indonesian Used Cars",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==============================================================================
# PYDANTIC SCHEMAS
# ==============================================================================
class ValuationRequest(BaseModel):
    variant_id: int = Field(..., description="ID Master Variant Mobil")
    year: int = Field(..., ge=2000, le=2026, description="Tahun pembuatan kendaraan")
    odometer_km: int = Field(..., ge=0, le=600000, description="Jarak tempuh odometer dalam KM")
    fuel_type: str = Field(default="Bensin", description="Tipe bahan bakar (Bensin, Diesel, Hybrid, Listrik)")
    transmission: str = Field(default="Automatic", description="Tipe transmisi (Automatic, Manual, CVT)")
    tax_status: str = Field(default="Pajak Hidup / Panjang", description="Status legalitas pajak tahunan PKB")
    has_bpkb: bool = Field(default=True, description="Kelengkapan dokumen BPKB")
    is_flood_free: bool = Field(default=True, description="Jaminan bebas banjir")
    is_accident_free: bool = Field(default=True, description="Jaminan bebas tabrak sasis")
    region: str = Field(default="Jabodetabek (DKI Jakarta, Bogor, Depok, Tangerang, Bekasi)", description="Wilayah geografis")

# ==============================================================================
# 1. HEALTH CHECK & STATUS
# ==============================================================================
@app.get("/", tags=["System"])
@app.get("/api/v1/health", tags=["System"])
def health_check():
    return {
        "service": "CarPrice ID Automotive Valuation Engine",
        "version": "1.0.0",
        "ml_model_version": ml_car_model_v7.version,
        "status": "OPERATIONAL",
        "database": "CONNECTED"
    }

# ==============================================================================
# 2. CATALOG & TAXONOMY ENDPOINTS
# ==============================================================================
@app.get("/api/v1/catalog/brands", tags=["Catalog"])
@app.get("/api/v1/brands", tags=["Catalog"])
def get_brands(db: Session = Depends(get_db)):
    brands = db.query(MasterBrand).order_by(MasterBrand.name).all()
    return [{
        "id": b.id,
        "name": b.name,
        "country_origin": b.country_origin,
        "is_active": getattr(b, "is_active", True)
    } for b in brands]

@app.get("/api/v1/catalog/models", tags=["Catalog"])
def get_catalog_models(brand_id: Optional[int] = Query(None, description="Filter berdasarkan ID Brand"), db: Session = Depends(get_db)):
    query = db.query(MasterModel)
    if brand_id:
        query = query.filter(MasterModel.brand_id == brand_id)
    models = query.order_by(MasterModel.name).all()
    return [{
        "id": m.id,
        "brand_id": m.brand_id,
        "brand_name": m.brand.name if m.brand else None,
        "name": m.name,
        "category": m.category,
        "engine_cc": m.engine_capacity_cc,
        "fuel_default": m.fuel_type_default,
        "seats": m.seat_capacity,
        "image_url": m.image_url
    } for m in models]

@app.get("/api/v1/models/{brand_id}", tags=["Catalog"])
def get_models_by_brand(brand_id: int, db: Session = Depends(get_db)):
    models = db.query(MasterModel).filter(MasterModel.brand_id == brand_id).all()
    return [{
        "id": m.id,
        "name": m.name,
        "category": m.category,
        "engine_cc": m.engine_capacity_cc,
        "fuel_default": m.fuel_type_default,
        "seats": m.seat_capacity,
        "image_url": m.image_url
    } for m in models]

@app.get("/api/v1/catalog/variants", tags=["Catalog"])
def get_catalog_variants(model_id: Optional[int] = Query(None, description="Filter berdasarkan ID Model"), db: Session = Depends(get_db)):
    query = db.query(MasterVariant)
    if model_id:
        query = query.filter(MasterVariant.model_id == model_id)
    variants = query.order_by(MasterVariant.variant_name).all()
    return [{
        "id": v.id,
        "model_id": v.model_id,
        "model_name": v.model.name if v.model else None,
        "brand_name": v.model.brand.name if (v.model and v.model.brand) else None,
        "variant_name": v.variant_name,
        "release_year_start": v.release_year_start,
        "release_year_end": v.release_year_end,
        "official_msrp_new": float(v.official_msrp_new) if v.official_msrp_new else None,
        "transmission_type": v.transmission_type,
        "fuel_type": v.fuel_type,
        "engine_capacity_cc": v.engine_capacity_cc,
        "image_url": v.image_url
    } for v in variants]

@app.get("/api/v1/variants/{model_id}", tags=["Catalog"])
def get_variants_by_model(model_id: int, db: Session = Depends(get_db)):
    variants = db.query(MasterVariant).filter(MasterVariant.model_id == model_id).all()
    return [{
        "id": v.id,
        "variant_name": v.variant_name,
        "release_year_start": v.release_year_start,
        "release_year_end": v.release_year_end,
        "official_msrp_new": float(v.official_msrp_new) if v.official_msrp_new else None,
        "transmission_type": v.transmission_type,
        "fuel_type": v.fuel_type,
        "engine_capacity_cc": v.engine_capacity_cc,
        "image_url": v.image_url
    } for v in variants]

# ==============================================================================
# 3. VALUATION & PRICING ENGINE (POST & GET)
# ==============================================================================
@app.post("/api/v1/valuation/calculate", tags=["Valuation"])
def post_calculate_car_valuation(payload: ValuationRequest, db: Session = Depends(get_db)):
    variant = db.query(MasterVariant).filter(MasterVariant.id == payload.variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Master Variant ID mobil tidak ditemukan")

    msrp = float(variant.official_msrp_new) if variant.official_msrp_new else 280000000.0
    model = variant.model
    brand = model.brand if model else None

    eval_result = ml_car_model_v7.predict_valuation(
        msrp_new=msrp,
        claimed_year=payload.year,
        odometer_km=payload.odometer_km,
        engine_cc=variant.engine_capacity_cc or (model.engine_capacity_cc if model else 1500),
        fuel_type=payload.fuel_type,
        transmission=payload.transmission,
        body_category=model.category if model else "MPV",
        tax_status=payload.tax_status,
        has_bpkb=payload.has_bpkb,
        is_flood_free=payload.is_flood_free,
        is_accident_free=payload.is_accident_free,
        current_year=2026
    )

    regional_eval = apply_regional_pricing(eval_result["predicted_fmv"], payload.region)

    forecast_curve = ml_car_model_v7.generate_residual_forecast_curve(
        current_fmv=regional_eval["regional_fmv"],
        fuel_type=payload.fuel_type,
        body_category=model.category if model else "MPV",
        current_year=2026,
        car_production_year=payload.year
    )

    return {
        "vehicle": {
            "brand": brand.name if brand else "",
            "model": model.name if model else "",
            "variant": variant.variant_name,
            "year": payload.year,
            "odometer_km": payload.odometer_km,
            "fuel_type": payload.fuel_type,
            "transmission": payload.transmission,
            "official_msrp_new": msrp,
            "image_url": variant.image_url or (model.image_url if model else "")
        },
        "valuation": {
            "fair_market_value": regional_eval["regional_fmv"],
            "base_predicted_fmv": eval_result["predicted_fmv"],
            "bargain_p25": eval_result["price_p25_deal"] * regional_eval["multiplier"],
            "premium_p75": eval_result["price_p75_pristine"] * regional_eval["multiplier"],
            "real_depreciation_pct": eval_result["real_depreciation_pct"],
            "methodology": "Hedonic Gradient Boosted Trees & Random Forest Ensemble V7"
        },
        "hedonic_factors": eval_result.get("factors", {}),
        "regional_adjustment": {
            "region_selected": payload.region,
            "region_code": REGIONAL_PRICE_INDEX.get(payload.region, {}).get("region_code", "NASIONAL"),
            "multiplier": regional_eval["multiplier"],
            "regional_adjusted_price": regional_eval["regional_fmv"]
        },
        "residual_forecast_10y": forecast_curve
    }

@app.get("/api/v1/valuation", tags=["Valuation"])
def get_calculate_car_valuation(
    variant_id: int = Query(..., description="ID Master Variant"),
    year: int = Query(..., ge=2000, le=2026, description="Tahun pembuatan"),
    odometer_km: int = Query(..., ge=0, le=600000, description="Odometer KM"),
    transmission: str = Query("Automatic", description="Transmisi"),
    fuel_type: str = Query("Bensin", description="Bahan bakar"),
    tax_status: str = Query("Pajak Hidup / Panjang", description="Status Pajak"),
    has_bpkb: bool = Query(True, description="Ada BPKB"),
    is_flood_free: bool = Query(True, description="Bebas Banjir"),
    is_accident_free: bool = Query(True, description="Bebas Tabrak"),
    region: str = Query("Jabodetabek (DKI Jakarta, Bogor, Depok, Tangerang, Bekasi)", description="Wilayah"),
    db: Session = Depends(get_db)
):
    req = ValuationRequest(
        variant_id=variant_id,
        year=year,
        odometer_km=odometer_km,
        transmission=transmission,
        fuel_type=fuel_type,
        tax_status=tax_status,
        has_bpkb=has_bpkb,
        is_flood_free=is_flood_free,
        is_accident_free=is_accident_free,
        region=region
    )
    return post_calculate_car_valuation(req, db)

# ==============================================================================
# 4. WHOLESALE & AUCTION 3-TIER CORRIDORS
# ==============================================================================
@app.get("/api/v1/wholesale/corridor/{variant_id}/{year}", tags=["Wholesale & Auctions"])
def get_wholesale_corridor(variant_id: int, year: int, db: Session = Depends(get_db)):
    engine = PricingAnalyticsEngine(db)
    corridor = engine.calculate_3tier_price_corridor(variant_id, year)
    if not corridor:
        raise HTTPException(status_code=404, detail="Data koridor 3-tier wholesale untuk varian dan tahun tersebut tidak ditemukan")
    return corridor

# ==============================================================================
# 5. ARBITRAGE & HOT DEALS
# ==============================================================================
@app.get("/api/v1/arbitrage/deals", tags=["Arbitrage Intelligence"])
@app.get("/api/v1/arbitrage-deals", tags=["Arbitrage Intelligence"])
def get_arbitrage_deals(
    min_discount_pct: float = Query(10.0, description="Diskon minimum terhadap FMV pasar (%)"),
    limit: int = Query(30, ge=1, le=100, description="Jumlah maksimal deals yang ditampilkan"),
    db: Session = Depends(get_db)
):
    engine = PricingAnalyticsEngine(db)
    return engine.get_top_arbitrage_deals(min_discount_pct=min_discount_pct, limit=limit)

# ==============================================================================
# 6. REGIONAL DISPARITY INDEX
# ==============================================================================
@app.get("/api/v1/regions", tags=["Regional Economics"])
def get_regions():
    res = []
    for r_name, r_info in REGIONAL_PRICE_INDEX.items():
        res.append({
            "region_name": r_name,
            "region_code": r_info["region_code"],
            "multiplier": r_info["multiplier"],
            "disparity_pct": round((r_info["multiplier"] - 1.0) * 100.0, 1),
            "bbn_rate": r_info["bbn_rate"],
            "description": r_info["description"],
            "provinces": r_info["provinces"]
        })
    return res
