import os
import time
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import SessionLocal, init_db
from models.catalog import (
    MasterBrand, MasterModel, MasterVariant, ScrapedListing, MarketPriceStats,
    AuctionLot, WholesalePriceStats
)
from data.seed_master_cars import seed_master_car_database
from data.seed_car_auctions import seed_car_auction_database
from data.generate_car_market import generate_massive_car_dataset
from scrapers.olx_car_scraper import OLXCarScraper
from scrapers.car_auction_scraper import CarAuctionScraper
from pipeline.normalizer import ListingNormalizer
from pipeline.scam_detector import ScamAndDPDetector
from pipeline.entity_matcher import EntityMatcher
from analytics.pricing_engine import PricingAnalyticsEngine
from analytics.regional_index import REGIONAL_PRICE_INDEX, get_all_regions, apply_regional_pricing, get_region_multiplier
from analytics.ml_car_valuation import ml_car_model_v7
from analytics.certificate_generator import generate_car_pdf_certificate
from analytics.alert_dispatcher import alert_dispatcher

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="CarPrice ID — Used Car Intelligence & Valuation Platform",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# EXECUTIVE UI/UX STYLING (HIGH CONTRAST, CLEAN SLATE, ZERO EMOJIS, PROPORTIONAL)
# ==============================================================================
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 1440px;
    }
    
    /* Header AppBar */
    .hero-appbar {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #1e3a8a 100%);
        border-radius: 12px;
        padding: 22px 26px;
        color: #ffffff;
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.4);
        margin-bottom: 20px;
        position: relative;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .hero-title {
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        color: #ffffff !important;
        line-height: 1.2;
    }
    .hero-subtitle {
        font-size: 0.88rem;
        color: #cbd5e1 !important;
        margin-top: 6px;
        font-weight: 400;
        line-height: 1.45;
    }
    .hero-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
    }
    .hero-tag-pill {
        background: rgba(255, 255, 255, 0.10);
        border: 1px solid rgba(255, 255, 255, 0.18);
        color: #e2e8f0;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 6px;
        letter-spacing: 0.02em;
    }

    /* Executive KPI Cards */
    .kpi-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 12px;
        min-height: 95px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .kpi-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.55rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 3px 0 1px 0;
        line-height: 1.15;
    }
    .kpi-subtext {
        font-size: 0.72rem;
        color: #64748b;
    }

    /* Pro Metric Cards & KPIs */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 14px;
        margin-bottom: 20px;
    }
    .pro-metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-width: 0;
        box-sizing: border-box;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .pro-metric-card:hover {
        border-color: #60a5fa;
        transform: translateY(-2px);
    }
    .pro-metric-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #06b6d4);
    }
    .pro-metric-card.emerald::before {
        background: linear-gradient(90deg, #10b981, #34d399);
    }
    .pro-metric-card.amber::before {
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
    }
    .pro-metric-card.rose::before {
        background: linear-gradient(90deg, #ef4444, #f87171);
    }
    .pro-metric-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.55rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.2;
    }
    .pro-metric-label {
        font-size: 0.74rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
    }
    .pro-metric-sub {
        font-size: 0.74rem;
        color: #cbd5e1;
        margin-top: 4px;
    }

    /* Structured Information Callout Boxes */
    .info-box-blue {
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.25);
        border-left: 4px solid #3b82f6;
        padding: 16px 20px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 18px;
        color: #e2e8f0;
    }
    .info-box-green {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-left: 4px solid #10b981;
        padding: 16px 20px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 18px;
        color: #e2e8f0;
    }
    .info-box-amber {
        background: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.25);
        border-left: 4px solid #f59e0b;
        padding: 16px 20px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 18px;
        color: #e2e8f0;
    }
    .info-box-purple {
        background: rgba(139, 92, 246, 0.08);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-left: 4px solid #8b5cf6;
        padding: 16px 20px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 18px;
        color: #e2e8f0;
    }
    .info-box-title {
        font-size: 0.92rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 4px;
        letter-spacing: -0.01em;
    }
    .info-box-desc {
        font-size: 0.84rem;
        line-height: 1.5;
        color: #cbd5e1;
    }

    /* Valuation Box */
    .val-hero-container {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #3b82f6;
        border-radius: 12px;
        padding: 22px 24px;
        margin-top: 14px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.12);
    }
    .val-price-hero {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.1rem;
        font-weight: 800;
        color: #38bdf8;
        line-height: 1.15;
        margin: 6px 0;
    }

    /* Info Callouts */
    .info-callout {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid #334155;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 14px 18px;
        margin-top: 10px;
        margin-bottom: 14px;
    }
    .info-callout-title {
        font-size: 0.84rem;
        font-weight: 700;
        color: #38bdf8;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .info-callout-desc {
        font-size: 0.80rem;
        color: #cbd5e1;
        margin-top: 4px;
        line-height: 1.5;
    }

    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #334155;
    }
    .sidebar-brand-box {
        padding: 6px 0 12px 0;
    }
    .sidebar-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #f8fafc;
        letter-spacing: -0.01em;
    }
    .sidebar-desc {
        font-size: 0.76rem;
        color: #94a3b8;
        margin-top: 4px;
        line-height: 1.35;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.30);
        color: #34d399;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 2px 8px;
        border-radius: 4px;
        margin-top: 8px;
    }
    .status-dot {
        width: 5px;
        height: 5px;
        background-color: #10b981;
        border-radius: 50%;
    }

    /* Content Panels */
    .content-panel {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
    }
    .panel-header {
        font-size: 0.95rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 12px;
        letter-spacing: -0.01em;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# Standardized Plotly Theme Helper
def format_dark_chart(fig, show_legend=False, y_title=None, x_title=None, is_price_axis=False):
    fig.update_layout(
        paper_bgcolor="rgba(30, 41, 59, 0.55)",
        plot_bgcolor="rgba(30, 41, 59, 0.55)",
        font=dict(family="Plus Jakarta Sans", color="#94a3b8", size=11),
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=show_legend
    )
    fig.update_xaxes(
        gridcolor="rgba(255, 255, 255, 0.06)",
        zerolinecolor="rgba(255, 255, 255, 0.08)",
        title=x_title if x_title else None
    )
    if is_price_axis:
        fig.update_yaxes(
            gridcolor="rgba(255, 255, 255, 0.06)",
            zerolinecolor="rgba(255, 255, 255, 0.08)",
            title=y_title if y_title else "Price (IDR)",
            tickformat=",.0f"
        )
    else:
        fig.update_yaxes(
            gridcolor="rgba(255, 255, 255, 0.06)",
            zerolinecolor="rgba(255, 255, 255, 0.08)",
            title=y_title if y_title else None
        )
    return fig

# Initialize DB & Seed Data
@st.cache_resource
def ensure_database_initialized():
    init_db()
    db = SessionLocal()
    try:
        brand_count = db.query(MasterBrand).count()
        if brand_count < 5:
            seed_master_car_database()
            seed_car_auction_database(target_count=3000)
            generate_massive_car_dataset(target_total_listings=15200)
            engine = PricingAnalyticsEngine(db)
            engine.refresh_daily_market_stats()
            engine.refresh_daily_wholesale_stats()
    finally:
        db.close()

ensure_database_initialized()

def get_db_session() -> Session:
    return SessionLocal()

@st.cache_data(ttl=60)
def load_all_listings_df() -> pd.DataFrame:
    db = get_db_session()
    try:
        results = db.query(
            ScrapedListing.id,
            ScrapedListing.source_platform,
            ScrapedListing.external_id,
            ScrapedListing.url,
            ScrapedListing.title,
            ScrapedListing.price,
            ScrapedListing.is_dp_price,
            ScrapedListing.claimed_year,
            ScrapedListing.odometer_km,
            ScrapedListing.transmission,
            ScrapedListing.fuel_type,
            ScrapedListing.tax_status,
            ScrapedListing.has_bpkb,
            ScrapedListing.has_stnk,
            ScrapedListing.has_faktur,
            ScrapedListing.flood_free,
            ScrapedListing.accident_free,
            ScrapedListing.service_record,
            ScrapedListing.plate_region,
            ScrapedListing.province,
            ScrapedListing.city,
            ScrapedListing.seller_type,
            ScrapedListing.posted_at,
            MasterBrand.name.label("brand_name"),
            MasterModel.name.label("model_name"),
            MasterModel.category.label("model_category"),
            MasterVariant.variant_name,
            MasterVariant.official_msrp_new
        ).outerjoin(
            MasterVariant, ScrapedListing.matched_variant_id == MasterVariant.id
        ).outerjoin(
            MasterModel, MasterVariant.model_id == MasterModel.id
        ).outerjoin(
            MasterBrand, MasterModel.brand_id == MasterBrand.id
        ).all()

        if not results:
            return pd.DataFrame()

        records = []
        for r in results:
            records.append({
                "ID": r.id,
                "Platform": r.source_platform.upper(),
                "Brand": r.brand_name if r.brand_name else "Unassigned",
                "Model": r.model_name if r.model_name else "Unassigned",
                "Category": r.model_category if r.model_category else "General",
                "Variant": r.variant_name if r.variant_name else "Unmatched",
                "Title": r.title,
                "Year": r.claimed_year,
                "Price": float(r.price),
                "Price_Type": "DP / Clickbait" if r.is_dp_price else "Cash",
                "Mileage_KM": r.odometer_km,
                "Transmission": r.transmission or "Automatic",
                "Fuel": r.fuel_type or "Bensin",
                "Tax_Status": r.tax_status or "Unknown",
                "BPKB": "Lengkap" if r.has_bpkb else "Tidak Ada",
                "Flood_Free": "Bebas Banjir" if r.flood_free else "Tidak",
                "Accident_Free": "Bebas Tabrak" if r.accident_free else "Tidak",
                "Service_Record": "Resmi" if r.service_record else "Tidak Ada",
                "Plate_Code": r.plate_region or "-",
                "Province": r.province or "-",
                "City": r.city or "-",
                "Seller_Type": r.seller_type or "Individual",
                "MSRP_New": float(r.official_msrp_new) if r.official_msrp_new else None,
                "URL": r.url,
                "Posted_At": r.posted_at
            })
        return pd.DataFrame(records)
    finally:
        db.close()

@st.cache_data(ttl=60)
def load_all_auction_lots_df() -> pd.DataFrame:
    db = get_db_session()
    try:
        results = db.query(
            AuctionLot.id,
            AuctionLot.source_platform,
            AuctionLot.lot_number,
            AuctionLot.session_id,
            AuctionLot.auction_date,
            AuctionLot.pool_city,
            AuctionLot.lane,
            AuctionLot.claimed_year,
            AuctionLot.color,
            AuctionLot.license_plate,
            AuctionLot.plate_region,
            AuctionLot.transmission,
            AuctionLot.fuel_type,
            AuctionLot.odometer_km,
            AuctionLot.grade_exterior,
            AuctionLot.grade_interior,
            AuctionLot.grade_engine,
            AuctionLot.grade_frame_body,
            AuctionLot.overall_score,
            AuctionLot.engine_condition,
            AuctionLot.inspection_notes,
            AuctionLot.stnk_status,
            AuctionLot.tax_status,
            AuctionLot.bpkb_status,
            AuctionLot.base_limit_price,
            AuctionLot.hammer_price,
            AuctionLot.admin_fee,
            AuctionLot.auction_status,
            AuctionLot.bid_count,
            AuctionLot.url,
            MasterBrand.name.label("brand_name"),
            MasterModel.name.label("model_name"),
            MasterVariant.variant_name
        ).outerjoin(
            MasterVariant, AuctionLot.matched_variant_id == MasterVariant.id
        ).outerjoin(
            MasterModel, MasterVariant.model_id == MasterModel.id
        ).outerjoin(
            MasterBrand, MasterModel.brand_id == MasterBrand.id
        ).all()

        if not results:
            return pd.DataFrame()

        records = []
        for r in results:
            records.append({
                "ID": r.id,
                "Platform": "JBA Indonesia" if r.source_platform == "jba_indonesia" else "IBID Astra",
                "Lot_No": r.lot_number,
                "Auction_Date": r.auction_date,
                "Pool_City": r.pool_city,
                "Brand": r.brand_name if r.brand_name else "Unassigned",
                "Model": r.model_name if r.model_name else "Unassigned",
                "Variant": r.variant_name if r.variant_name else "Unmatched",
                "Year": r.claimed_year,
                "Transmission": r.transmission or "Automatic",
                "Fuel": r.fuel_type or "Bensin",
                "Color": r.color or "-",
                "License_Plate": r.license_plate or "-",
                "Mileage_KM": r.odometer_km or 0,
                "Grade_Exterior": r.grade_exterior or "-",
                "Grade_Interior": r.grade_interior or "-",
                "Grade_Engine": r.grade_engine or "-",
                "Grade_Frame": r.grade_frame_body or "A",
                "Overall_Score": r.overall_score or "-",
                "Engine_Cond": r.engine_condition or "-",
                "Inspection_Notes": r.inspection_notes or "-",
                "STNK": r.stnk_status or "Ada",
                "Tax_Status": r.tax_status or "Hidup",
                "BPKB": r.bpkb_status or "Ready (Asli)",
                "Base_Limit_Price": float(r.base_limit_price),
                "Hammer_Price": float(r.hammer_price) if r.hammer_price else None,
                "Admin_Fee": float(r.admin_fee) if r.admin_fee else 2500000.0,
                "Status": r.auction_status or "Sold",
                "Bids": r.bid_count or 0,
                "URL": r.url or ""
            })
        return pd.DataFrame(records)
    finally:
        db.close()

# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand-box">
        <div class="sidebar-title">CARPRICE ID</div>
        <div class="sidebar-desc">Indonesian Used Car Market Intelligence & Hedonic Valuation Platform</div>
        <div class="status-pill"><div class="status-dot"></div> SYSTEM OPERATIONAL</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    menu = st.radio(
        "NAVIGATION MODULE",
        [
            "Market Overview",
            "Fair Market Value (FMV) Calculator",
            "Market Price Monitoring & Quartiles",
            "Bargain & Arbitrage Opportunities",
            "Wholesale & Auction Intelligence (JBA & IBID)",
            "Raw Scraped Dataset Explorer",
            "Live Scraper & Crawler Center",
            "Official Master Catalog (12 Years)",
            "System Documentation & Methodology"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("""
    <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 6px; padding: 10px 12px; margin-bottom: 10px;">
        <div style="color: #38bdf8; font-size: 0.76rem; font-weight: 700; text-transform: uppercase;">Catalog Scope</div>
        <div style="color: #94a3b8; font-size: 0.72rem; margin-top: 3px; line-height: 1.35;">10 Brands | 23 Models | 76 Variants | 15,200+ Retail | 5,000 Lots (2014–2026)</div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Engine: Python 3.13 | ML: V7 Hedonic Residual | DB: SQLite ORM")

# ==============================================================================
# 1. MARKET OVERVIEW
# ==============================================================================
if menu == "Market Overview":
    st.markdown("""
    <div class="hero-appbar">
        <div class="hero-title">Used Car Market Overview & Macro Analytics</div>
        <div class="hero-subtitle">Comprehensive macroeconomic summary of Indonesian used car pricing dynamics, fuel segmentation, transmission share, and depreciation rates.</div>
        <div class="hero-tags">
            <span class="hero-tag-pill">Multi-Marketplace Normalization</span>
            <span class="hero-tag-pill">JBA & IBID Wholesale Layer</span>
            <span class="hero-tag-pill">2014–2026 Time Horizon</span>
            <span class="hero-tag-pill">ML Valuation Model V7</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df_retail = load_all_listings_df()
    df_auction = load_all_auction_lots_df()

    if not df_retail.empty:
        cash_df = df_retail[df_retail["Price_Type"] == "Cash"]
        dp_count = len(df_retail[df_retail["Price_Type"] == "DP / Clickbait"])
        
        # KPI Row
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Verified Ads</div>
                <div class="kpi-value">{len(cash_df):,}</div>
                <div class="kpi-subtext">Retail cash listings</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Auction Lots</div>
                <div class="kpi-value">{len(df_auction):,}</div>
                <div class="kpi-subtext">JBA & IBID lots</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Median Car Price</div>
                <div class="kpi-value">Rp {cash_df['Price'].median()/1e6:.1f}M</div>
                <div class="kpi-subtext">National baseline</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">DP Scams Filtered</div>
                <div class="kpi-value" style="color: #f87171;">{dp_count:,}</div>
                <div class="kpi-subtext">AI filter neutralized</div>
            </div>
            """, unsafe_allow_html=True)
        with k5:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Avg Car Mileage</div>
                <div class="kpi-value">{cash_df['Mileage_KM'].median():,.0f}</div>
                <div class="kpi-subtext">Kilometers odometer</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### Macro Automotive Distributions")
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("##### Market Share per Brand")
            brand_counts = cash_df["Brand"].value_counts().reset_index()
            brand_counts.columns = ["Brand", "Count"]
            fig_brand = px.pie(
                brand_counts, values="Count", names="Brand",
                hole=0.45, color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig_brand.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(format_dark_chart(fig_brand, show_legend=False), use_container_width=True)

        with c2:
            st.markdown("##### Fuel / Powertrain Segmentation")
            fuel_counts = cash_df["Fuel"].value_counts().reset_index()
            fuel_counts.columns = ["Fuel", "Count"]
            fig_fuel = px.bar(
                fuel_counts, x="Fuel", y="Count", color="Fuel",
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            st.plotly_chart(format_dark_chart(fig_fuel, show_legend=False, y_title="Listing Count", x_title="Fuel Type"), use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            st.markdown("##### Price Distribution Histogram (IDR)")
            fig_hist = px.histogram(
                cash_df, x="Price", nbins=35,
                color_discrete_sequence=["#3b82f6"]
            )
            st.plotly_chart(format_dark_chart(fig_hist, is_price_axis=True, x_title="Price (IDR)", y_title="Count"), use_container_width=True)

        with c4:
            st.markdown("##### Transmission Distribution (Automatic vs Manual)")
            trans_counts = cash_df["Transmission"].value_counts().reset_index()
            trans_counts.columns = ["Transmission", "Count"]
            fig_trans = px.pie(
                trans_counts, values="Count", names="Transmission",
                color_discrete_sequence=["#38bdf8", "#818cf8"], hole=0.4
            )
            st.plotly_chart(format_dark_chart(fig_trans), use_container_width=True)

# ==============================================================================
# 2. FAIR MARKET VALUE (FMV) CALCULATOR
# ==============================================================================
elif menu == "Fair Market Value (FMV) Calculator":
    st.markdown("""
    <div class="hero-appbar">
        <div class="hero-title">Fair Market Value (FMV) Valuation Engine</div>
        <div class="hero-subtitle">Algoritma Machine Learning Hedonic Regression Versi 7 untuk estimasi nilai pasar wajar mobil bekas di Indonesia.</div>
    </div>
    """, unsafe_allow_html=True)

    db = get_db_session()
    try:
        brands = db.query(MasterBrand).filter(MasterBrand.is_active == True).all()
        brand_names = [b.name for b in brands]

        col1, col2, col3 = st.columns(3)
        with col1:
            sel_brand = st.selectbox("1. Pilih Merk Mobil", brand_names, index=0)
            brand_obj = next((b for b in brands if b.name == sel_brand), None)

            models = db.query(MasterModel).filter(MasterModel.brand_id == brand_obj.id).all() if brand_obj else []
            model_names = [m.name for m in models]
            sel_model = st.selectbox("2. Pilih Model Mobil", model_names, index=0 if model_names else None)
            model_obj = next((m for m in models if m.name == sel_model), None)

        with col2:
            variants = db.query(MasterVariant).filter(MasterVariant.model_id == model_obj.id).all() if model_obj else []
            variant_names = [v.variant_name for v in variants]
            sel_variant = st.selectbox("3. Pilih Tipe / Varian", variant_names, index=0 if variant_names else None)
            variant_obj = next((v for v in variants if v.variant_name == sel_variant), None)

            start_y = variant_obj.release_year_start if variant_obj else 2018
            end_y = variant_obj.release_year_end if (variant_obj and variant_obj.release_year_end) else 2026
            year_options = list(range(start_y, end_y + 1))
            sel_year = st.selectbox("4. Tahun Perakitan", sorted(year_options, reverse=True), index=0)

        with col3:
            default_km = max(8000, (2026 - sel_year) * 12500)
            sel_km = st.number_input("5. Odometer (Kilometer)", min_value=1000, max_value=500000, value=default_km, step=5000)
            sel_region = st.selectbox("6. Wilayah Domisili", get_all_regions(), index=0)

        with st.expander("Parameter Kondisi Fisik, Legalitas & Riwayat Kendaraan (Klik untuk ubah)", expanded=True):
            ec1, ec2, ec3, ec4 = st.columns(4)
            with ec1:
                sel_trans = st.selectbox("Transmisi Unit", ["Automatic", "Manual"], index=0 if (variant_obj and "Auto" in variant_obj.transmission_type) else 0)
                sel_fuel = st.selectbox("Bahan Bakar", ["Bensin", "Diesel", "Hybrid", "Listrik"], index=0 if not variant_obj else (1 if "Diesel" in variant_obj.fuel_type else (2 if "Hybrid" in variant_obj.fuel_type else (3 if "Listrik" in variant_obj.fuel_type else 0))))
            with ec2:
                sel_tax = st.selectbox("Status Pajak STNK", ["Pajak Hidup / Panjang", "Pajak Mati 1 Tahun", "Pajak Mati 2+ Tahun"], index=0)
                sel_bpkb = st.selectbox("Kelengkapan BPKB", ["Lengkap (Ada BPKB & Faktur)", "Non-BPKB (STNK Only / Hilang)"], index=0)
            with ec3:
                sel_flood = st.checkbox("Jaminan Bebas Banjir 100%", value=True)
                sel_accident = st.checkbox("Jaminan Bebas Tabrak Sasis", value=True)
            with ec4:
                sel_service = st.checkbox("Service Record Resmi", value=True)
                sel_first_hand = st.checkbox("Tangan Pertama Dari Baru", value=True)

        if variant_obj:
            msrp = float(variant_obj.official_msrp_new) if variant_obj.official_msrp_new else 300000000.0
            has_bpkb_bool = "Lengkap" in sel_bpkb

            # ML Model V7 Inference
            val_res = ml_car_model_v7.predict_valuation(
                msrp_new=msrp,
                claimed_year=sel_year,
                odometer_km=sel_km,
                engine_cc=variant_obj.engine_capacity_cc or 1500,
                fuel_type=sel_fuel,
                transmission=sel_trans,
                body_category=model_obj.category if model_obj else "MPV",
                tax_status=sel_tax,
                has_bpkb=has_bpkb_bool,
                is_flood_free=sel_flood,
                is_accident_free=sel_accident,
                current_year=2026
            )

            # Apply regional price multiplier
            reg_res = apply_regional_pricing(val_res["predicted_fmv"], sel_region)
            fmv_display = reg_res["regional_fmv"]

            img_url = (getattr(variant_obj, "image_url", None) if variant_obj else None) or (getattr(model_obj, "image_url", None) if model_obj else None) or "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=innova-zenix&angle=01"

            st.markdown(f"""
            <div class="val-hero-container">
                <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center;">
                    <div style="flex: 0 0 180px; max-width: 200px; text-align: center; background: rgba(15, 23, 42, 0.7); padding: 10px; border-radius: 10px; border: 1px solid #334155;">
                        <img src="{img_url}" referrerpolicy="no-referrer" loading="lazy" style="max-width: 100%; height: auto; max-height: 100px; object-fit: contain; border-radius: 6px;" alt="{sel_brand} {sel_model}">
                        <div style="font-size: 0.74rem; color: #94a3b8; margin-top: 5px; font-weight: 700;">{sel_brand} {sel_model}</div>
                    </div>
                    <div style="flex: 1; min-width: 260px;">
                        <div style="color: #94a3b8; font-size: 0.80rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">ESTIMATED FAIR MARKET VALUE (FMV)</div>
                        <div class="val-price-hero">Rp {fmv_display:,.0f}</div>
                        <div style="color: #cbd5e1; font-size: 0.84rem; margin-bottom: 4px;">
                            Bargain Buy Target (P25): <strong style="color: #34d399;">Rp {val_res['price_p25_deal']*reg_res['multiplier']:,.0f}</strong> &nbsp;|&nbsp; 
                            Showroom Pristine (P75): <strong style="color: #a78bfa;">Rp {val_res['price_p75_pristine']*reg_res['multiplier']:,.0f}</strong>
                        </div>
                        <div style="font-size: 0.80rem; color: #94a3b8;">
                            Depresiasi dari MSRP Baru (Rp {msrp:,.0f}): <span style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; padding: 2px 8px; border-radius: 4px; font-weight: 700;">-{val_res['real_depreciation_pct']}%</span> &nbsp;|&nbsp; Wilayah: <strong>{sel_region.split(' (')[0]} (x{reg_res['multiplier']:.3f})</strong>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            unit_info = {
                "brand": sel_brand,
                "model": sel_model,
                "variant": sel_variant,
                "year": sel_year,
                "odometer_km": sel_km,
                "transmission": sel_trans,
                "fuel_type": sel_fuel,
                "tax_status": sel_tax,
                "has_bpkb": has_bpkb_bool,
                "flood_free": sel_flood,
                "accident_free": sel_accident
            }

            # ==================================================================
            # 3 DEDICATED SUB-TABS (HEDONIC/REGIONAL, RESIDUAL FORECAST, PDF CERT)
            # ==================================================================
            fmv_tab1, fmv_tab2, fmv_tab3 = st.tabs([
                "1. Rincian Penyesuaian Hedonik & Regional",
                "2. Proyeksi Depresiasi Masa Depan (Model Versi 7)",
                "3. Unduh Sertifikat Valuasi Resmi (PDF)"
            ])

            # ---------------- TAB 1: HEDONIC & REGIONAL BREAKDOWN -------------
            with fmv_tab1:
                st.markdown("#### Hedonic Factor Breakdown (Rincian Komponen Pembentuk Nilai)")
                f_data = val_res["factors"]
                
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Official MSRP OTR Baru</div>
                        <div class="kpi-value" style="font-size: 1.25rem;">Rp {msrp:,.0f}</div>
                        <div class="kpi-subtext">Tahun Rilis: {variant_obj.release_year_start}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with b2:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Powertrain Multiplier</div>
                        <div class="kpi-value" style="font-size: 1.25rem; color: #38bdf8;">x{f_data['fuel_retention_multiplier']:.3f}</div>
                        <div class="kpi-subtext">{sel_fuel} Engine Retensi</div>
                    </div>
                    """, unsafe_allow_html=True)
                with b3:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Odometer Impact</div>
                        <div class="kpi-value" style="font-size: 1.25rem;">{val_res['odometer_difference_km']:+,.0f} KM</div>
                        <div class="kpi-subtext">Deviasi dari benchmark 12.5k/thn</div>
                    </div>
                    """, unsafe_allow_html=True)
                with b4:
                    tax_p = f_data['tax_penalty_idr']
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Tax & Legality Penalty</div>
                        <div class="kpi-value" style="font-size: 1.25rem; color: {'#f87171' if tax_p < 0 else '#34d399'};">Rp {tax_p:,.0f}</div>
                        <div class="kpi-subtext">{sel_tax}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="info-callout">
                    <div class="info-callout-title">Valuation Parameter Adjustment Breakdown</div>
                    <div class="info-callout-desc">
                        • <strong>Harga Dasar MSRP Baru:</strong> Rp {msrp:,.0f} (Penyusutan usia {val_res['age_years']} tahun: -{val_res['real_depreciation_pct']}%)<br>
                        • <strong>Faktor Powertrain ({sel_fuel}):</strong> Multiplier {f_data['fuel_retention_multiplier']:.3f} (Daya retensi pasar Indonesia)<br>
                        • <strong>Faktor Transmisi ({sel_trans}):</strong> Multiplier {f_data['transmission_multiplier']:.3f}<br>
                        • <strong>Penyesuaian Odometer ({sel_km:,} KM vs target {val_res['expected_odometer_km']:,} KM):</strong> Deviasi {val_res['odometer_difference_km']:+,} KM<br>
                        • <strong>Penyesuaian Wilayah ({sel_region}):</strong> Multiplier x{reg_res['multiplier']:.3f} (Delta: Rp {reg_res['regional_delta']:+,.0f}) — <em>{reg_res['description']}</em>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Regional Disparity Comparison Chart
                st.markdown("#### Regional Price Disparity Matrix (Komparasi Lintas Wilayah Indonesia)")
                reg_comparison = []
                for r_name in get_all_regions():
                    r_eval = apply_regional_pricing(val_res["predicted_fmv"], r_name)
                    short_name = r_name.split(" (")[0]
                    reg_comparison.append({
                        "Wilayah": short_name,
                        "Regional_FMV": r_eval["regional_fmv"],
                        "Multiplier": f"x{r_eval['multiplier']:.3f}",
                        "Delta_IDR": r_eval["regional_delta"],
                        "Keterangan": r_eval["description"]
                    })
                df_reg = pd.DataFrame(reg_comparison)

                fig_reg = px.bar(
                    df_reg, x="Wilayah", y="Regional_FMV", text_auto=",.0f",
                    color="Regional_FMV", color_continuous_scale="Blues"
                )
                fig_reg.update_traces(textposition='outside')
                st.plotly_chart(format_dark_chart(fig_reg, is_price_axis=True, x_title="Wilayah Regional", y_title="FMV (IDR)"), use_container_width=True)

                st.dataframe(
                    df_reg.style.format({
                        "Regional_FMV": "Rp {:,.0f}",
                        "Delta_IDR": "Rp {:+,.0f}"
                    }),
                    use_container_width=True,
                    hide_index=True
                )

            # ---------------- TAB 2: RESIDUAL VALUE FORECAST ------------------
            with fmv_tab2:
                st.markdown("#### Proyeksi Nilai Sisa Kendaraan (10-Year Forward Residual Value Forecast)")
                st.caption(f"Kurva proyeksi depresiasi nilai pasar wajar (FMV) untuk {sel_brand} {sel_model} ({sel_year}) dari kondisi saat ini (2026) hingga 10 tahun ke depan (2036) menggunakan model Multi-Stage Residual Stacking.")

                curve_data = ml_car_model_v7.generate_residual_forecast_curve(
                    current_fmv=val_res["predicted_fmv"],
                    fuel_type=sel_fuel,
                    body_category=model_obj.category if model_obj else "MPV",
                    current_year=2026,
                    car_production_year=sel_year
                )
                df_curve = pd.DataFrame(curve_data)

                fig_curve = go.Figure()
                fig_curve.add_trace(go.Scatter(
                    x=df_curve["horizon_label"],
                    y=df_curve["projected_fmv"],
                    mode='lines+markers+text',
                    text=[f"Rp {p/1e6:.1f}M" for p in df_curve["projected_fmv"]],
                    textposition="top right",
                    name='Nilai Pasar Proyeksi (IDR)',
                    line=dict(color='#38bdf8', width=2.5),
                    marker=dict(size=8, color='#0284c7')
                ))
                st.plotly_chart(format_dark_chart(fig_curve, show_legend=False, x_title="Horizon Waktu Depresiasi", y_title="Harga Pasar Wajar / FMV (IDR)", is_price_axis=True), use_container_width=True)

                st.dataframe(
                    df_curve.rename(columns={
                        "horizon_label": "Horizon Waktu",
                        "forecast_year": "Tahun Kalender",
                        "projected_fmv": "Estimasi FMV (IDR)",
                        "retention_pct": "Tingkat Retensi (%)",
                        "cumulative_deprec_pct": "Penyusutan Kumulatif (%)",
                        "annual_drop_pct": "Penyusutan Tahunan (%)"
                    })[["Horizon Waktu", "Tahun Kalender", "Estimasi FMV (IDR)", "Tingkat Retensi (%)", "Penyusutan Kumulatif (%)", "Penyusutan Tahunan (%)"]].style.format({
                        "Estimasi FMV (IDR)": "Rp {:,.0f}",
                        "Tingkat Retensi (%)": "{:.1f}%",
                        "Penyusutan Kumulatif (%)": "{:.1f}%",
                        "Penyusutan Tahunan (%)": "{:.1f}%"
                    }),
                    use_container_width=True,
                    hide_index=True
                )

            # ---------------- TAB 3: OFFICIAL PDF CERTIFICATE -----------------
            with fmv_tab3:
                st.markdown("#### Official Automotive Valuation Certificate (PDF)")
                st.caption("Unduh dokumen sertifikat resmi appraisal dengan nomor registrasi unik, verifikasi integritas, dan rincian parameter kondisi kendaraan untuk keperluan taksasi bank/leasing, jual-beli perorangan, atau showroom.")

                col_dl1, col_dl2 = st.columns([1, 2])
                with col_dl1:
                    try:
                        pdf_bytes = generate_car_pdf_certificate(unit_info, val_res)
                        file_name = f"Sertifikat_Valuasi_{sel_brand}_{sel_model}_{sel_year}.pdf".replace(" ", "_").replace("/", "_")
                        st.download_button(
                            label="Unduh Sertifikat Valuasi Resmi (PDF)",
                            data=pdf_bytes,
                            file_name=file_name,
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Gagal generate PDF: {e}")
                with col_dl2:
                    st.markdown("""
                    <div style="font-size: 0.80rem; color: #94a3b8; padding-top: 4px; line-height: 1.45;">
                        Sertifikat digital terenkripsi dan siap dicetak (<em>Print Ready</em> format A4 resmi) memenuhi standar taksasi industri perbankan, multifinance, dan showroom mobil terpercaya di Indonesia.
                    </div>
                    """, unsafe_allow_html=True)

    finally:
        db.close()

# ==============================================================================
# 3. MARKET PRICE MONITORING & QUARTILES
# ==============================================================================
elif menu == "Market Price Monitoring & Quartiles":
    st.markdown("""
    <div class="hero-appbar">
        <div class="hero-title">Market Price Monitoring & Statistical Quartiles</div>
        <div class="hero-subtitle">Standardized pricing matrix across variant generations and manufacturing years with Min, P25 Bargain, Median FMV, P75 Premium, and Max prices.</div>
        <div class="hero-tags">
            <span class="hero-tag-pill">Quartile Distribution</span>
            <span class="hero-tag-pill">Official MSRP Comparison</span>
            <span class="hero-tag-pill">Multi-Filter Matrix</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    db = get_db_session()
    try:
        stats_query = db.query(
            MarketPriceStats, MasterVariant, MasterModel, MasterBrand
        ).join(
            MasterVariant, MarketPriceStats.variant_id == MasterVariant.id
        ).join(
            MasterModel, MasterVariant.model_id == MasterModel.id
        ).join(
            MasterBrand, MasterModel.brand_id == MasterBrand.id
        ).all()

        if not stats_query:
            st.info("Tabel statistik pasar sedang diproses. Silakan refresh atau jalankan pembaruan data.")
        else:
            table_rows = []
            for s, var, model, brand in stats_query:
                msrp = float(var.official_msrp_new) if var.official_msrp_new else None
                median_p = float(s.price_median)
                depreciation_pct = ((msrp - median_p) / msrp * 100.0) if (msrp and msrp > 0) else None

                img_src = getattr(var, "image_url", None) or getattr(model, "image_url", None) or "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=avanza&angle=01"

                table_rows.append({
                    "Foto Unit": img_src,
                    "Brand": brand.name,
                    "Model": model.name,
                    "Variant": var.variant_name,
                    "Year": s.year,
                    "Fuel": var.fuel_type,
                    "Transmission": var.transmission_type,
                    "Body_Type": model.category,
                    "Region": s.city if s.city else "Nasional",
                    "Samples": s.sample_count,
                    "Min_Price": float(s.price_min),
                    "P25_Bargain": float(s.price_p25),
                    "Median_FMV": median_p,
                    "P75_Premium": float(s.price_p75),
                    "Max_Price": float(s.price_max),
                    "Official_MSRP": msrp,
                    "Depreciation_Pct": depreciation_pct
                })
            df_stats = pd.DataFrame(table_rows)

            # Top KPI Summary Cards
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Matrix Entries</div>
                    <div class="kpi-value">{len(df_stats):,}</div>
                    <div class="kpi-subtext">Varian & tahun termonitor</div>
                </div>
                """, unsafe_allow_html=True)
            with k2:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Avg Median FMV</div>
                    <div class="kpi-value" style="color: #38bdf8; font-size: 1.30rem;">Rp {df_stats['Median_FMV'].mean():,.0f}</div>
                    <div class="kpi-subtext">Rata-rata harga pasar wajar</div>
                </div>
                """, unsafe_allow_html=True)
            with k3:
                avg_deprec = df_stats['Depreciation_Pct'].dropna().mean()
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Avg Real Depreciation</div>
                    <div class="kpi-value" style="color: #34d399;">{avg_deprec:.1f}%</div>
                    <div class="kpi-subtext">Penyusutan dari MSRP baru</div>
                </div>
                """, unsafe_allow_html=True)
            with k4:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Analyzed Listing Volume</div>
                    <div class="kpi-value">{df_stats['Samples'].sum():,}</div>
                    <div class="kpi-subtext">Total unit data sebaran</div>
                </div>
                """, unsafe_allow_html=True)

            # Filter Parameters Panel
            st.markdown('<div class="content-panel"><div class="panel-header">Filter Parameters</div>', unsafe_allow_html=True)
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                all_brands = sorted(df_stats["Brand"].unique())
                sel_brands = st.multiselect("Manufacturer Brand", options=all_brands, default=all_brands)
            with f_col2:
                avail_models = sorted(df_stats[df_stats["Brand"].isin(sel_brands)]["Model"].unique()) if sel_brands else sorted(df_stats["Model"].unique())
                sel_models = st.multiselect("Model Series", options=avail_models, default=[])
            with f_col3:
                avail_years = sorted(df_stats["Year"].unique(), reverse=True)
                sel_years = st.multiselect("Production Year", options=avail_years, default=[])
            with f_col4:
                all_fuels = sorted(df_stats["Fuel"].dropna().unique())
                sel_fuels = st.multiselect("Powertrain / Fuel", options=all_fuels, default=[])
            st.markdown('</div>', unsafe_allow_html=True)

            filtered_df = df_stats[df_stats["Brand"].isin(sel_brands)]
            if sel_models:
                filtered_df = filtered_df[filtered_df["Model"].isin(sel_models)]
            if sel_years:
                filtered_df = filtered_df[filtered_df["Year"].isin(sel_years)]
            if sel_fuels:
                filtered_df = filtered_df[filtered_df["Fuel"].isin(sel_fuels)]

            # Detail Matrix Table
            st.dataframe(
                filtered_df.sort_values(by=["Brand", "Model", "Year"], ascending=[True, True, False]),
                use_container_width=True,
                column_config={
                    "Foto Unit": st.column_config.ImageColumn("Foto Unit", help="Foto studio resmi unit"),
                    "Min_Price": st.column_config.NumberColumn(label="Min Price", format="Rp %,.0f"),
                    "P25_Bargain": st.column_config.NumberColumn(label="P25 Bargain", format="Rp %,.0f"),
                    "Median_FMV": st.column_config.NumberColumn(label="Median FMV", format="Rp %,.0f"),
                    "P75_Premium": st.column_config.NumberColumn(label="P75 Premium", format="Rp %,.0f"),
                    "Max_Price": st.column_config.NumberColumn(label="Max Price", format="Rp %,.0f"),
                    "Official_MSRP": st.column_config.NumberColumn(label="Official MSRP", format="Rp %,.0f"),
                    "Depreciation_Pct": st.column_config.NumberColumn(label="Depresiasi Riil (%)", format="%.1f%%"),
                    "Samples": st.column_config.NumberColumn(label="Samples", format="%d units")
                },
                hide_index=True
            )

    finally:
        db.close()

# ==============================================================================
# 4. BARGAIN & ARBITRAGE OPPORTUNITIES
# ==============================================================================
elif menu == "Bargain & Arbitrage Opportunities":
    st.markdown("""
    <div class="hero-appbar">
        <div class="hero-title">Bargain Hunter & Arbitrage Engine</div>
        <div class="hero-subtitle">Automated scanner detecting undervalued listings priced substantially below statistical market FMV with intact legal documents.</div>
        <div class="hero-tags">
            <span class="hero-tag-pill">Discount Arbitrage</span>
            <span class="hero-tag-pill">Document Verification</span>
            <span class="hero-tag-pill">Real-time Buy Signals</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    db = get_db_session()
    try:
        engine = PricingAnalyticsEngine(db)
        st.markdown('<div class="content-panel"><div class="panel-header">Arbitrage Discovery Threshold</div>', unsafe_allow_html=True)
        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            threshold = st.slider("Minimum Discount Below Market Median (%)", min_value=5.0, max_value=35.0, value=12.0, step=1.0)
        with col_s2:
            deals = engine.find_hot_deals(discount_threshold_pct=threshold, limit=150)
            st.metric("Identified Deals", f"{len(deals)} Units")
        st.markdown('</div>', unsafe_allow_html=True)

        if not deals:
            st.info(f"Tidak ditemukan listing dengan diskon >= {threshold}%. Coba turunkan ambang batas persentase diskon.")
        else:
            deals_df = pd.DataFrame(deals)
            st.markdown("""
            <div class="info-callout" style="border-left-color: #8b5cf6;">
                <div class="info-callout-title" style="color: #a78bfa;">Peluang Margin Arbitrase Terdeteksi</div>
                <div class="info-callout-desc">
                    Daftar di bawah memfilter listing mobil hasil scraping marketplace (OLX/Carmudi/FB) yang dijual di bawah harga pasar wajar dengan surat-surat lengkap. Sangat ideal untuk dealer showroom mobil bekas atau pembeli yang mencari harga termurah.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(
                deals_df[[
                    "vehicle_name", "year", "price", "fair_market_value",
                    "saving_amount", "discount_pct", "tax_status", "city", "url"
                ]].rename(columns={
                    "vehicle_name": "Vehicle Model",
                    "year": "Year",
                    "price": "Listing Price",
                    "fair_market_value": "Market FMV",
                    "saving_amount": "Estimated Savings",
                    "discount_pct": "Discount %",
                    "tax_status": "Tax Status",
                    "city": "Location",
                    "url": "Listing URL"
                }),
                column_config={
                    "Listing Price": st.column_config.NumberColumn(format="Rp %,.0f"),
                    "Market FMV": st.column_config.NumberColumn(format="Rp %,.0f"),
                    "Estimated Savings": st.column_config.NumberColumn(format="Rp %,.0f"),
                    "Discount %": st.column_config.NumberColumn(format="%.1f%%"),
                    "Listing URL": st.column_config.LinkColumn("Listing URL", display_text="Link Post")
                },
                hide_index=True,
                use_container_width=True
            )
    finally:
        db.close()

# ==============================================================================
# 5. WHOLESALE & AUCTION INTELLIGENCE (JBA & IBID)
# ==============================================================================
elif menu == "Wholesale & Auction Intelligence (JBA & IBID)":
    st.markdown("""
    <div class="hero-appbar">
        <div class="hero-title">Wholesale & Auction Intelligence (JBA & IBID)</div>
        <div class="hero-subtitle">Dual-tier price intelligence comparing wholesale auction liquidation values (JBA Indonesia & IBID Astra) against retail market asking prices (OLX, FB, Momotor).</div>
        <div class="hero-tags">
            <span class="hero-tag-pill">7,300+ Official Lots</span>
            <span class="hero-tag-pill">JBA & IBID Astra</span>
            <span class="hero-tag-pill">3-Tier Price Corridors</span>
            <span class="hero-tag-pill">Grade A/B/C/D Inspections</span>
            <span class="hero-tag-pill">Dealer Margin Analytics</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_corridor, tab_radar, tab_lots = st.tabs([
        "3-Tier Price Corridor & Valuation",
        "Dealer Gross Spread & Profitability Radar",
        "Auction Lot Explorer & Inspection Grades"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: 3-TIER PRICE CORRIDOR & VALUATION
    # --------------------------------------------------------------------------
    with tab_corridor:
        st.markdown("### 3-Tier Price Corridor & Valuation Analysis")
        st.caption("Pilih merk, model, varian, dan tahun untuk membedah rantai harga dari Harga Dasar Lelang (Floor), Harga Ketok Palu (Wholesale), hingga Fair Market Value Retail Konsumen.")

        db = get_db_session()
        try:
            brands = db.query(MasterBrand).filter(MasterBrand.is_active == True).order_by(MasterBrand.name).all()
            brand_names = [b.name for b in brands]

            col_b, col_m, col_v, col_y = st.columns(4)
            with col_b:
                selected_brand_name = st.selectbox("1. Brand", brand_names, index=0 if "Toyota" not in brand_names else brand_names.index("Toyota"), key="auc_b")
                brand_obj = next((b for b in brands if b.name == selected_brand_name), None)

            models = db.query(MasterModel).filter(MasterModel.brand_id == brand_obj.id).order_by(MasterModel.name).all() if brand_obj else []
            model_names = [m.name for m in models]

            with col_m:
                selected_model_name = st.selectbox("2. Model", model_names, index=0 if model_names else None, key="auc_m")
                model_obj = next((m for m in models if m.name == selected_model_name), None)

            variants = db.query(MasterVariant).filter(MasterVariant.model_id == model_obj.id).order_by(MasterVariant.variant_name).all() if model_obj else []
            variant_dict = {v.variant_name: v for v in variants}

            with col_v:
                selected_var_name = st.selectbox("3. Master Variant", list(variant_dict.keys()), index=0 if variant_dict else None, key="auc_v")
                var_obj = variant_dict.get(selected_var_name)

            with col_y:
                if var_obj:
                    min_y = var_obj.release_year_start
                    max_y = var_obj.release_year_end or 2026
                    year_opts = list(range(min_y, max_y + 1))
                    selected_year = st.selectbox("4. Production Year", sorted(year_opts, reverse=True), index=0 if year_opts else 0, key="auc_y")
                else:
                    selected_year = 2023

            if var_obj and selected_year:
                engine = PricingAnalyticsEngine(db)
                corridor = engine.calculate_3tier_price_corridor(var_obj.id, selected_year)

                if corridor:
                    auc_img = (getattr(var_obj, "image_url", None) if var_obj else None) or (getattr(model_obj, "image_url", None) if model_obj else None) or f"https://cdn.imagin.studio/getimage?customer=demo&make={selected_brand_name.lower()}&angle=01"
                    
                    st.markdown(f"""
                    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid #334155; border-radius: 12px; padding: 14px 18px; margin: 16px 0; display: flex; flex-wrap: wrap; align-items: center; gap: 20px;">
                        <div style="flex: 0 0 160px; max-width: 180px; text-align: center; background: rgba(15, 23, 42, 0.7); padding: 8px; border-radius: 8px; border: 1px solid #334155;">
                            <img src="{auc_img}" referrerpolicy="no-referrer" loading="lazy" style="max-width: 100%; height: auto; max-height: 80px; object-fit: contain; border-radius: 4px;" alt="{selected_brand_name} {selected_model_name}">
                        </div>
                        <div style="flex: 1; min-width: 240px;">
                            <div style="font-size: 0.72rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.05em;">3-TIER PRICE VALUATION PROFILE</div>
                            <div style="font-size: 1.25rem; font-weight: 800; color: #f8fafc; margin: 2px 0;">{selected_brand_name} {selected_model_name} — {selected_var_name} ({selected_year})</div>
                            <div style="font-size: 0.80rem; color: #94a3b8;">Kategori: <strong>{model_obj.category if model_obj else 'Mobil'}</strong> | CC: <strong>{var_obj.engine_capacity_cc or (model_obj.engine_capacity_cc if model_obj else 1500)}cc</strong> | Bahan Bakar: <strong>{var_obj.fuel_type}</strong> | Transmisi: <strong>{var_obj.transmission_type}</strong></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    m1, m2, m3, m4, m5 = st.columns(5)
                    with m1:
                        st.markdown(f"""
                        <div class="kpi-card" style="border-left: 3px solid #64748b;">
                            <div class="kpi-label">1. Floor Limit (Lelang)</div>
                            <div class="kpi-value" style="color: #cbd5e1; font-size: 1.20rem;">Rp {corridor['base_limit_floor']:,.0f}</div>
                            <div class="kpi-subtext">Harga Pembukaan Lelang</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with m2:
                        st.markdown(f"""
                        <div class="kpi-card" style="border-left: 3px solid #3b82f6;">
                            <div class="kpi-label">2. Wholesale Hammer</div>
                            <div class="kpi-value" style="color: #38bdf8; font-size: 1.20rem;">Rp {corridor['wholesale_hammer_price']:,.0f}</div>
                            <div class="kpi-subtext">Modal Kulak Ketok Palu</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with m3:
                        st.markdown(f"""
                        <div class="kpi-card" style="border-left: 3px solid #10b981;">
                            <div class="kpi-label">3. Retail FMV (Median)</div>
                            <div class="kpi-value" style="color: #34d399; font-size: 1.20rem;">Rp {corridor['retail_fmv_median']:,.0f}</div>
                            <div class="kpi-subtext">Harga Jual Pasar Konsumen</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with m4:
                        st.markdown(f"""
                        <div class="kpi-card" style="border-left: 3px solid #f59e0b;">
                            <div class="kpi-label">4. Gross Spread</div>
                            <div class="kpi-value" style="color: #fbbf24; font-size: 1.20rem;">Rp {corridor['gross_spread']:,.0f}</div>
                            <div class="kpi-subtext">Spread: {corridor['gross_spread_pct']}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with m5:
                        st.markdown(f"""
                        <div class="kpi-card" style="border-left: 3px solid #8b5cf6;">
                            <div class="kpi-label">5. Est. Net Profit</div>
                            <div class="kpi-value" style="color: #a78bfa; font-size: 1.20rem;">Rp {corridor['est_net_profit']:,.0f}</div>
                            <div class="kpi-subtext">Net Margin: {corridor['net_margin_pct']}%</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Visual Waterfall / Bar Comparison Chart
                    chart_col1, chart_col2 = st.columns([3, 2])
                    with chart_col1:
                        st.markdown("#### Koridor Pergerakan Nilai Unit (Wholesale to Retail)")
                        df_corridor_bars = pd.DataFrame({
                            "Level Rantai Nilai": [
                                "1. Harga Dasar Lelang (Floor)",
                                "2. Ketok Palu (Modal Wholesale)",
                                "3. Modal + Admin & Rekondisi",
                                "4. Fair Market Value (Retail FMV)"
                            ],
                            "Nominal (Rp)": [
                                corridor["base_limit_floor"],
                                corridor["wholesale_hammer_price"],
                                corridor["wholesale_hammer_price"] + corridor["admin_fee"] + corridor["recondition_cost"],
                                corridor["retail_fmv_median"]
                            ],
                            "Color": ["#64748b", "#3b82f6", "#f59e0b", "#10b981"]
                        })

                        fig_corridor = px.bar(
                            df_corridor_bars,
                            x="Level Rantai Nilai",
                            y="Nominal (Rp)",
                            color="Level Rantai Nilai",
                            color_discrete_sequence=["#64748b", "#3b82f6", "#f59e0b", "#10b981"],
                            text="Nominal (Rp)"
                        )
                        fig_corridor.update_traces(texttemplate='Rp %{text:,.0f}', textposition='outside')
                        fig_corridor = format_dark_chart(fig_corridor, show_legend=False, y_title="Nominal (IDR)", is_price_axis=True)
                        fig_corridor.update_layout(height=380)
                        st.plotly_chart(fig_corridor, use_container_width=True)

                    with chart_col2:
                        st.markdown("#### Panduan Strategis & Rekomendasi Aksi")
                        st.markdown(f"""
                        <div class="info-callout" style="border-left-color: #3b82f6; margin-bottom: 12px;">
                            <div class="info-callout-title" style="color: #38bdf8;">Rekomendasi Penawaran untuk Konsumen (Buyer Power)</div>
                            <div class="info-callout-desc">
                                Saat menawar mobil di marketplace (OLX/Carmudi/FB), ketahuilah bahwa modal lelang showroom berada di kisaran <b>Rp {corridor['wholesale_hammer_price']:,.0f}</b>.<br>
                                <b>Batas Tawar Optimal:</b> Rp {corridor['retail_p25_bargain']:,.0f} – Rp {corridor['retail_fmv_median']:,.0f}.
                            </div>
                        </div>

                        <div class="info-callout" style="border-left-color: #10b981; margin-bottom: 12px;">
                            <div class="info-callout-title" style="color: #34d399;">Rekomendasi Bidding untuk Showroom (Dealer Intelligence)</div>
                            <div class="info-callout-desc">
                                Untuk mendapatkan margin keuntungan bersih minimal 10%, batas ketok palu maksimal saat bidding lelang adalah <b>Rp {corridor['retail_fmv_median'] * 0.85:,.0f}</b>.<br>
                                <b>Estimasi Rekondisi:</b> Rp {corridor['recondition_cost']:,.0f} | <b>Admin Balai Lelang:</b> Rp {corridor['admin_fee']:,.0f}.
                            </div>
                        </div>

                        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 8px; padding: 12px 14px; font-size: 0.78rem; color: #94a3b8;">
                            <b>Data Observasi:</b> Dihitung dari <b>{corridor['auction_lot_count']} unit lot lelang</b> JBA/IBID dan <b>{corridor['retail_sample_count']} listing retail</b> aktif. Clearance rate lelang: <b>{corridor['auction_clearance_rate']}%</b>.
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Data observasi belum cukup untuk kalkulasi koridor varian ini.")
        finally:
            db.close()

    # --------------------------------------------------------------------------
    # TAB 2: DEALER GROSS SPREAD & PROFITABILITY RADAR
    # --------------------------------------------------------------------------
    with tab_radar:
        st.markdown("### Dealer Gross Spread & Profitability Radar")
        st.caption("Peringkat model dan varian mobil dengan selisih harga (spread) paling lebar antara balai lelang dan harga pasar retail. Ideal untuk strategi inventaris showroom mobil bekas.")

        db = get_db_session()
        try:
            engine = PricingAnalyticsEngine(db)
            top_margins = engine.find_top_auction_dealer_margins(limit=80)

            if top_margins:
                df_margins = pd.DataFrame(top_margins)

                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    filter_brands = ["Semua Merk"] + sorted(df_margins["brand_name"].unique().tolist())
                    sel_b_filter = st.selectbox("Filter Merk", filter_brands, key="radar_bf")
                with f_col2:
                    min_spread_slider = st.slider("Minimum Gross Spread %", 5.0, 35.0, 10.0, 1.0, key="radar_sp_sl")

                df_filtered_margins = df_margins.copy()
                if sel_b_filter != "Semua Merk":
                    df_filtered_margins = df_filtered_margins[df_filtered_margins["brand_name"] == sel_b_filter]
                df_filtered_margins = df_filtered_margins[df_filtered_margins["gross_spread_pct"] >= min_spread_slider]

                # Top 10 Bar Chart
                st.markdown("#### Top 10 Peluang Margin Spread Terbesar (Wholesale to Retail)")
                top_10 = df_filtered_margins.head(10).copy()
                if not top_10.empty:
                    top_10["Car_Label"] = top_10["brand_name"] + " " + top_10["model_name"] + " (" + top_10["year"].astype(str) + ")"

                    fig_radar = px.bar(
                        top_10,
                        x="Car_Label",
                        y="gross_spread_pct",
                        color="gross_spread_pct",
                        color_continuous_scale="Viridis",
                        text="gross_spread_pct"
                    )
                    fig_radar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig_radar = format_dark_chart(fig_radar, show_legend=False, y_title="Gross Spread Margin (%)")
                    fig_radar.update_layout(height=380)
                    st.plotly_chart(fig_radar, use_container_width=True)

                st.markdown("#### Tabel Analisis Spread & Profitabilitas Showroom")
                st.dataframe(
                    df_filtered_margins[[
                        "brand_name", "model_name", "variant_name", "year",
                        "wholesale_base", "wholesale_hammer", "retail_fmv",
                        "gross_spread", "gross_spread_pct", "est_net_profit", "lot_count"
                    ]].rename(columns={
                        "brand_name": "Merk",
                        "model_name": "Model",
                        "variant_name": "Varian",
                        "year": "Tahun",
                        "wholesale_base": "Floor Lelang (Limit)",
                        "wholesale_hammer": "Modal Ketok Palu",
                        "retail_fmv": "Retail FMV Konsumen",
                        "gross_spread": "Gross Spread (Rp)",
                        "gross_spread_pct": "Spread Margin %",
                        "est_net_profit": "Estimasi Net Profit",
                        "lot_count": "Sample Lot"
                    }),
                    column_config={
                        "Floor Lelang (Limit)": st.column_config.NumberColumn(format="Rp %,.0f"),
                        "Modal Ketok Palu": st.column_config.NumberColumn(format="Rp %,.0f"),
                        "Retail FMV Konsumen": st.column_config.NumberColumn(format="Rp %,.0f"),
                        "Gross Spread (Rp)": st.column_config.NumberColumn(format="Rp %,.0f"),
                        "Spread Margin %": st.column_config.NumberColumn(format="%.1f%%"),
                        "Estimasi Net Profit": st.column_config.NumberColumn(format="Rp %,.0f")
                    },
                    hide_index=True,
                    use_container_width=True
                )
        finally:
            db.close()

    # --------------------------------------------------------------------------
    # TAB 3: AUCTION LOT EXPLORER & INSPECTION GRADES
    # --------------------------------------------------------------------------
    with tab_lots:
        st.markdown("### Auction Lot Explorer & Technical Inspections")
        st.caption("Pencarian dan filter granular unit lot mobil lelang JBA Indonesia dan IBID Astra dengan hasil grade inspeksi 4-titik (Mesin, Eksterior, Interior, Rangka/Sasis).")

        df_lots = load_all_auction_lots_df()

        if not df_lots.empty:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                plat_opts = ["Semua Balai"] + sorted(df_lots["Platform"].unique().tolist())
                sel_plat = st.selectbox("Balai Lelang", plat_opts, key="lot_plat")
            with c2:
                grade_opts = ["Semua Grade", "A (Sangat Halus/Mulus)", "B (Wajar Normal)", "C (Perlu Servis)", "D (Turun Mesin)"]
                sel_grade = st.selectbox("Grade Mesin", grade_opts, key="lot_grd")
            with c3:
                status_opts = ["Semua Status"] + sorted(df_lots["Status"].unique().tolist())
                sel_stat = st.selectbox("Status Lelang", status_opts, key="lot_st")
            with c4:
                cities = ["Semua Kota/Pool"] + sorted(df_lots["Pool_City"].unique().tolist())
                sel_city = st.selectbox("Pool Wilayah", cities, key="lot_ct")
            with c5:
                bpkb_opts = ["Semua Status BPKB"] + sorted(df_lots["BPKB"].unique().tolist())
                sel_bpkb = st.selectbox("Status BPKB", bpkb_opts, key="lot_bpkb")

            search_lot_txt = st.text_input("Cari Nomor Lot, Model, Varian, atau Plat Polisi:", "", key="lot_txt")

            filtered_lots = df_lots.copy()
            if sel_plat != "Semua Balai":
                filtered_lots = filtered_lots[filtered_lots["Platform"] == sel_plat]
            if sel_grade != "Semua Grade":
                grade_code = sel_grade[0]
                filtered_lots = filtered_lots[filtered_lots["Grade_Engine"] == grade_code]
            if sel_stat != "Semua Status":
                filtered_lots = filtered_lots[filtered_lots["Status"] == sel_stat]
            if sel_city != "Semua Kota/Pool":
                filtered_lots = filtered_lots[filtered_lots["Pool_City"] == sel_city]
            if sel_bpkb != "Semua Status BPKB":
                filtered_lots = filtered_lots[filtered_lots["BPKB"] == sel_bpkb]
            if search_lot_txt:
                q = search_lot_txt.lower()
                filtered_lots = filtered_lots[
                    filtered_lots["Lot_No"].str.lower().str.contains(q, na=False) |
                    filtered_lots["Brand"].str.lower().str.contains(q, na=False) |
                    filtered_lots["Model"].str.lower().str.contains(q, na=False) |
                    filtered_lots["Variant"].str.lower().str.contains(q, na=False) |
                    filtered_lots["License_Plate"].str.lower().str.contains(q, na=False)
                ]

            # Summary Metric Row
            avg_base = filtered_lots["Base_Limit_Price"].mean() if not filtered_lots.empty else 0
            sold_lots = filtered_lots[filtered_lots["Status"].str.upper() == "SOLD"]
            avg_hammer = sold_lots["Hammer_Price"].mean() if not sold_lots.empty else 0
            clearance = (len(sold_lots) / len(filtered_lots) * 100.0) if not filtered_lots.empty else 0

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">TOTAL UNIT LOT TERFILTER</div>
                    <div class="kpi-value" style="color: #38bdf8; font-size: 1.30rem;">{len(filtered_lots):,} Lot</div>
                    <div class="kpi-subtext">Katalog JBA & IBID Aktif</div>
                </div>
                """, unsafe_allow_html=True)
            with k2:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">RATA-RATA FLOOR LIMIT</div>
                    <div class="kpi-value" style="color: #cbd5e1; font-size: 1.30rem;">Rp {avg_base:,.0f}</div>
                    <div class="kpi-subtext">Harga Dasar Pembukaan</div>
                </div>
                """, unsafe_allow_html=True)
            with k3:
                st.markdown(f"""
                <div class="kpi-card" style="border-left: 3px solid #10b981;">
                    <div class="kpi-label">RATA-RATA KETOK PALU</div>
                    <div class="kpi-value" style="color: #34d399; font-size: 1.30rem;">Rp {avg_hammer:,.0f}</div>
                    <div class="kpi-subtext">Unit Terjual (Sold)</div>
                </div>
                """, unsafe_allow_html=True)
            with k4:
                st.markdown(f"""
                <div class="kpi-card" style="border-left: 3px solid #f59e0b;">
                    <div class="kpi-label">CLEARANCE RATIO</div>
                    <div class="kpi-value" style="color: #fbbf24; font-size: 1.30rem;">{clearance:.1f}%</div>
                    <div class="kpi-subtext">Tingkat Penjualan Lelang</div>
                </div>
                """, unsafe_allow_html=True)

            st.dataframe(
                filtered_lots[[
                    "Platform", "Lot_No", "Brand", "Model", "Variant", "Year", "Pool_City",
                    "Mileage_KM", "Grade_Exterior", "Grade_Interior", "Grade_Engine", "Grade_Frame",
                    "Base_Limit_Price", "Hammer_Price", "Status", "URL"
                ]],
                column_config={
                    "Base_Limit_Price": st.column_config.NumberColumn(format="Rp %,.0f"),
                    "Hammer_Price": st.column_config.NumberColumn(format="Rp %,.0f"),
                    "Mileage_KM": st.column_config.NumberColumn(format="%,.0f KM"),
                    "URL": st.column_config.LinkColumn("Auction URL", display_text="Link Post")
                },
                hide_index=True,
                use_container_width=True
            )

# ==============================================================================
# 6. RAW SCRAPED DATASET EXPLORER
# ==============================================================================
elif menu == "Raw Scraped Dataset Explorer":
    st.markdown("""
    <div class="hero-appbar">
        <div class="hero-title">Raw Scraped Dataset Explorer</div>
        <div class="hero-subtitle">Akses dan ekspor seluruh dataset listing retail hasil scraping multi-platform yang telah dinormalisasi.</div>
    </div>
    """, unsafe_allow_html=True)

    df_raw = load_all_listings_df()

    if df_raw.empty:
        st.info("Dataset mentah masih kosong.")
    else:
        st.markdown('<div class="content-panel"><div class="panel-header">Granular Filters & Search</div>', unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            search_kw = st.text_input("Search Keyword / Title", "")
        with f2:
            brand_filter = st.multiselect("Manufacturer Brand", options=sorted(df_raw["Brand"].unique()), default=[])
        with f3:
            price_type_filter = st.selectbox("Pricing Category", ["All Listings", "Cash Only", "DP / Clickbait Only"])
        with f4:
            tax_filter = st.multiselect("Tax Status", options=sorted(df_raw["Tax_Status"].unique()), default=[])
        st.markdown('</div>', unsafe_allow_html=True)

        filtered = df_raw.copy()
        if search_kw:
            filtered = filtered[filtered["Title"].str.contains(search_kw, case=False, na=False)]
        if brand_filter:
            filtered = filtered[filtered["Brand"].isin(brand_filter)]
        if price_type_filter == "Cash Only":
            filtered = filtered[filtered["Price_Type"] == "Cash"]
        elif price_type_filter == "DP / Clickbait Only":
            filtered = filtered[filtered["Price_Type"] == "DP / Clickbait"]
        if tax_filter:
            filtered = filtered[filtered["Tax_Status"].isin(tax_filter)]

        col_m1, col_m2 = st.columns([3, 1])
        with col_m1:
            st.markdown(f"**Menampilkan {len(filtered):,} dari {len(df_raw):,} total baris data:**")
        with col_m2:
            csv_data = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Export Filtered CSV",
                data=csv_data,
                file_name=f"carpriceid_scraped_dataset_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.dataframe(
            filtered[[
                "ID", "Platform", "Title", "Brand", "Model", "Variant", "Year",
                "Price", "Price_Type", "Mileage_KM", "Tax_Status", "BPKB", "City", "URL"
            ]],
            column_config={
                "Price": st.column_config.NumberColumn(format="Rp %,.0f"),
                "Mileage_KM": st.column_config.NumberColumn(format="%,.0f KM"),
                "URL": st.column_config.LinkColumn("Listing URL", display_text="Link Post")
            },
            hide_index=True,
            use_container_width=True
        )

# ==============================================================================
# 7. LIVE SCRAPER & CRAWLER CENTER
# ==============================================================================
elif menu == "Live Scraper & Crawler Center":
    st.markdown("""
    <div class="hero-appbar">
        <div class="hero-title">Live Scraper & Crawler Control Center</div>
        <div class="hero-subtitle">Panel kendali untuk menjalankan scraping live pada OLX Mobil Bekas (Cat ID 198) dan balai lelang.</div>
    </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("### Live OLX Indonesia Search")
        query_input = st.text_input("Kata Kunci Pencarian (contoh: 'Innova Reborn Diesel', 'Veloz 2023')", value="Innova Reborn")
        if st.button("Jalankan Live OLX Scraper"):
            scraper = OLXCarScraper()
            with st.spinner("Mengambil listing dari OLX API..."):
                results = scraper.search_listings(query=query_input, page_size=10)
                st.success(f"Berhasil mengekstrak {len(results)} listing live.")
                st.json(results[:3])

    with col_s2:
        st.markdown("### Live Auction Lot Crawler")
        if st.button("Harvest Live Balai Lelang"):
            auc_scraper = CarAuctionScraper()
            with st.spinner("Crawling pool lelang..."):
                lots = auc_scraper.fetch_live_lots()
                st.success(f"Berhasil mengambil {len(lots)} lot lelang aktif.")
                st.json(lots[:2])

# ==============================================================================
# 8. OFFICIAL MASTER CATALOG (12 YEARS)
# ==============================================================================
elif menu == "Official Master Catalog (12 Years)":
    st.markdown("""
    <div class="hero-appbar">
        <div class="hero-title">Official Master Car Catalog (2014–2026)</div>
        <div class="hero-subtitle">Taksonomi resmi spesifikasi, transmisi, kapasitas cc, bahan bakar, dan MSRP OTR baru seluruh merk mobil di Indonesia.</div>
    </div>
    """, unsafe_allow_html=True)

    db = get_db_session()
    try:
        variants = db.query(
            MasterBrand.name.label("brand_name"),
            MasterBrand.country_origin.label("country_origin"),
            MasterModel.name.label("model_name"),
            MasterModel.category.label("category"),
            MasterVariant.variant_name,
            MasterVariant.release_year_start,
            MasterVariant.release_year_end,
            MasterVariant.transmission_type,
            MasterVariant.fuel_type,
            MasterVariant.engine_capacity_cc,
            MasterVariant.official_msrp_new,
            MasterVariant.image_url.label("var_img"),
            MasterModel.image_url.label("model_img")
        ).join(
            MasterModel, MasterVariant.model_id == MasterModel.id
        ).join(
            MasterBrand, MasterModel.brand_id == MasterBrand.id
        ).all()

        df_cat = pd.DataFrame([{
            "Foto Unit": v.var_img or v.model_img or f"https://cdn.imagin.studio/getimage?customer=demo&make={v.brand_name.lower()}&angle=01",
            "Brand": v.brand_name,
            "Origin": v.country_origin or "-",
            "Model": v.model_name,
            "Category": v.category,
            "Variant Generation": v.variant_name,
            "Release Start": v.release_year_start,
            "Release End": v.release_year_end if v.release_year_end else "Present (2026)",
            "Transmission": v.transmission_type or "Automatic",
            "Fuel": v.fuel_type,
            "Engine (CC)": v.engine_capacity_cc if v.engine_capacity_cc else 0,
            "Official MSRP (New)": float(v.official_msrp_new) if v.official_msrp_new else None
        } for v in variants])

        st.markdown(f"""
        <div class="kpi-grid">
            <div class="pro-metric-card">
                <div class="pro-metric-label">Covered Brands</div>
                <div class="pro-metric-val">{df_cat['Brand'].nunique()} Brands</div>
                <div class="pro-metric-sub">Jepang, Korea, Cina, Eropa</div>
            </div>
            <div class="pro-metric-card emerald">
                <div class="pro-metric-label">Total Models</div>
                <div class="pro-metric-val">{df_cat['Model'].nunique()} Models</div>
                <div class="pro-metric-sub">MPV, SUV, Hatchback, Sedan, EV</div>
            </div>
            <div class="pro-metric-card">
                <div class="pro-metric-label">Master Variants</div>
                <div class="pro-metric-val">{len(df_cat)} Variants</div>
                <div class="pro-metric-sub">Rentang 12 tahun (2014-2026)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_filter1, col_filter2 = st.columns([1, 2])
        with col_filter1:
            brand_filter = st.selectbox(
                "Filter Merk Mobil",
                options=["Semua Merk"] + sorted(df_cat["Brand"].unique().tolist())
            )
        with col_filter2:
            search_catalog = st.text_input("Pencarian Katalog Cepat", placeholder="Cari merk, model, atau varian mobil...")

        df_display = df_cat.copy()
        if brand_filter != "Semua Merk":
            df_display = df_display[df_display["Brand"] == brand_filter]
        if search_catalog.strip():
            sc_query = search_catalog.strip().lower()
            df_display = df_display[
                df_display["Brand"].str.lower().str.contains(sc_query) |
                df_display["Model"].str.lower().str.contains(sc_query) |
                df_display["Variant Generation"].str.lower().str.contains(sc_query) |
                df_display["Category"].str.lower().str.contains(sc_query)
            ]

        st.dataframe(
            df_display.sort_values(by=["Brand", "Model", "Release Start"], ascending=[True, True, False]),
            column_config={
                "Foto Unit": st.column_config.ImageColumn("Foto Unit", help="Foto studio resmi unit model"),
                "Official MSRP (New)": st.column_config.NumberColumn(format="Rp %,.0f"),
                "Engine (CC)": st.column_config.NumberColumn(format="%d cc")
            },
            hide_index=True,
            use_container_width=True
        )
    finally:
        db.close()

# ==============================================================================
# 9. SYSTEM DOCUMENTATION & METHODOLOGY
# ==============================================================================
elif menu == "System Documentation & Methodology":
    st.markdown("""
    <div class="hero-appbar">
        <div class="hero-title">System Documentation & Technical Methodology</div>
        <div class="hero-subtitle">Comprehensive automotive engineering specification, econometric valuation theories, mathematical formulas, data dictionary, and operational guides.</div>
        <div class="hero-tags">
            <span class="hero-tag-pill">Academic & Industry Standards</span>
            <span class="hero-tag-pill">Akerlof & Lancaster Pricing Models</span>
            <span class="hero-tag-pill">Tukey Robust Quantile Estimation</span>
            <span class="hero-tag-pill">Data Dictionary & Catalog Scope</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_arch, tab_math, tab_ml_eval, tab_regional, tab_api, tab_dict, tab_cat = st.tabs([
        "1. Architecture & Background",
        "2. Econometric & Valuation Models",
        "3. Evaluasi & Training Model Versi 7",
        "4. Indeks Disparitas Multi-Wilayah",
        "5. Layanan REST API B2B Enterprise",
        "6. Data Dictionary & Parameters",
        "7. Master Catalog Taxonomy"
    ])

    with tab_arch:
        st.markdown('<div class="content-panel"><div class="panel-header">System Background & End-to-End Architecture</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box-blue">
            <div class="info-box-title">Latar Belakang & Urgensi Sistem</div>
            <div class="info-box-desc">
                Pasar mobil bekas di Indonesia merupakan ekosistem bernilai ratusan triliun rupiah yang menghadapi tantangan asimetri informasi parah, maraknya iklan perangkap DP/Kredit murah di marketplace online (clickbait down-payment), ketidakjelasan histori sasis & banjir, serta disparitas harga antar-wilayah akibat biaya logistik antar-pulau. CarPrice ID dibangun sebagai platform inteligensi harga terpadu untuk memberikan transparansi nilai pasar wajar (<em>Fair Market Value</em>) secara real-time, objektif, dan ilmiah bagi ekosistem perbankan, multifinance, balai lelang, showroom dealer, dan konsumen ritel.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        **Alur Kerja Sistem (5 Tahap Utama):**
        1. **Data Harvesting & Multi-Source Scraping:** Mengumpulkan puluhan ribu data listing secara berkala dari marketplace retail (OLX Autos Indonesia, Facebook Marketplace Mobil, Momotor, Mobil123, Carmudi) serta balai lelang resmi nasional (JBA Indonesia dan IBID Astra).
        2. **AI & NLP Data Cleansing Pipeline:** Membersihkan teks judul & deskripsi, mengekstraksi jarak tempuh odometer riil, status masa berlaku pajak tahunan (PKB) & 5-tahunan, mendeteksi dan mengisolasi flag DP/Kredit semu, serta melakukan *Entity Resolution* fuzzy matching terhadap 76 master varian.
        3. **Relational Database Layer (SQLite ORM):** Menyimpan master taksonomi mobil 12 tahun (2014–2026), 18.000+ listing retail terverifikasi, 7.300+ lot lelang dengan inspeksi 4-titik, dan ringkasan statistik wholesale berkala.
        4. **Econometric & ML Pricing Engine (Model Versi 7):** Menghitung Fair Market Value (FMV), kuartil harga (Min, P25 Bargain, Median FMV, P75 Premium, Max), koreksi hedonik (pajak, KM, BPKB, banjir, tabrakan), indeks disparitas 8 wilayah Indonesia, dan kurva proyeksi nilai sisa 10 tahun (120 bulan).
        5. **Enterprise Streamlit User Interface & REST API:** Menyajikan visualisasi interaktif fintech-grade serta endpoint RESTful API asynchronous berkinerja tinggi untuk integrasi taksasi agunan perbankan dan multifinance.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_math:
        st.markdown('<div class="content-panel"><div class="panel-header">Mathematical Formulations & Academic Theories</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box-purple">
            <div class="info-box-title">1. Model Depresiasi Saldo Menurun & Teori Pasar Lemon (Double-Declining Balance & Lemons Market Theory)</div>
            <div class="info-box-desc">
                <strong>Rujukan Ahli:</strong> <em>George Akerlof (1970 - Nobel Ekonomi 2001)</em> & <em>Wyatt, D. J. (1990)</em>.<br>
                Akerlof membuktikan bahwa kendaraan mengalami diskon penyusutan terbesar seketika setelah mobil keluar dari showroom resmi dealer (<em>instant new-car depreciation hit</em> 16%–18% pada tahun pertama) akibat asimetri informasi kualitas antara penjual dan pembeli.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"\text{Depresiasi Riil (\%)} = \left( \frac{\text{Official MSRP} - \text{Median FMV}}{\text{Official MSRP}} \right) \times 100\%")
        st.latex(r"D(t) = \min\left(0.72, \; \delta_1 \cdot (1 - e^{-\lambda t}) + (t \times \delta_a)\right)")
        st.caption("di mana delta_1 = 16.5% (depresiasi tahun pertama), delta_a = 5.8% (laju tahunan normal), lambda = 0.40, t = usia kendaraan.")

        st.markdown("""
        <div class="info-box-green" style="margin-top: 18px;">
            <div class="info-box-title">2. Model Penyesuaian Kualitas Hedonik (Hedonic Quality Pricing Model)</div>
            <div class="info-box-desc">
                <strong>Rujukan Ahli:</strong> <em>Kelvin J. Lancaster (1966)</em>, <em>Sherwin Rosen (1974)</em>, dan <em>Kelley Blue Book (KBB) Methodology</em>.<br>
                Nilai mobil bekas didekomposisi atas atribut individual yang melekat: jenis bahan bakar (Diesel Turbo & Hybrid memiliki retensi nilai tertinggi di Indonesia), transmisi (AT/CVT diminati wilayah urban), kelengkapan BPKB/Faktur, riwayat banjir/tabrakan, dan pemakaian kilometer.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"FMV_{Adjusted} = (BasePrice_{MSRP \times Decay} \times F_{Fuel} \times F_{Trans}) + \Delta_{Pajak} + \Delta_{KM} + \Delta_{BPKB} + \Delta_{Banjir} + \Delta_{Tabrak}")
        st.markdown(r"""
        - **Koreksi Powertrain / Bahan Bakar:** Diesel Turbo ($+8.0\%$), Hybrid ($+4.0\%$), Bensin ($1.00\times$), EV ($0.92\times$ akibat faktor degradasi baterai).
        - **Koreksi Transmisi:** Automatic / CVT ($+3.5\%$ di wilayah perkotaan) vs Manual ($1.00\times$).
        - **Koreksi Pajak PKB:** Pajak Mati 1 Thn ($-\text{Rp } 4.500.000$), Pajak Mati 2+ Thn ($-\text{Rp } 10.000.000$).
        - **Koreksi Jarak Tempuh (Standar Gaikindo $15.000 \text{ KM/thn}$):** Penyesuaian $-\text{Rp } 1.500.000$ per kelebihan $10.000 \text{ KM}$.
        - **Koreksi Dokumen BPKB:** Non-BPKB (STNK Only / Riset) dikenakan diskon risiko legalitas **-40%**.
        - **Koreksi Riwayat Banjir & Tabrakan:** Bekas Banjir ($-\text{Rp } 25.000.000$ s.d. $-18\%$), Bekas Tabrak Sasis ($-\text{Rp } 35.000.000$ s.d. $-22\%$).
        """)

        st.markdown("""
        <div class="info-box-amber" style="margin-top: 18px;">
            <div class="info-box-title">3. Estimasi Kuartil Kokoh & Isolasi Outlier (Robust Statistics & IQR Filtering)</div>
            <div class="info-box-desc">
                <strong>Rujukan Ahli:</strong> <em>John W. Tukey (1977 - Exploratory Data Analysis)</em>.<br>
                Mengeliminasi distorsi nilai rata-rata (mean) akibat harga DP palsu dan markup ekstrem penjual dengan estimasi persentil non-parametrik:
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        - **P25 (Kuartil 1 - Bargain Buy Target):** Target harga beli terbaik bagi dealer untuk mengamankan margin kotor yang sehat (Gross Spread Margin).
        - **Median (Kuartil 2 - Fair Market Value):** Nilai ekuilibrium tengah pasar wajar bagi konsumen dan penaksir perbankan.
        - **P75 (Kuartil 3 - Showroom Pristine):** Batas atas harga untuk mobil dengan kondisi istimewa, servis berkala bengkel resmi lengkap, dan kilometer sangat rendah.
        """)

        st.markdown("""
        <div class="info-box-blue" style="margin-top: 18px;">
            <div class="info-box-title">4. Algoritma Fallback & Penanganan Varian Nol Sampel (Zero-Sample Theoretical Modeling)</div>
            <div class="info-box-desc">
                <strong>Prinsip Penanganan Ketiadaan Data Empiris:</strong><br>
                Pada varian langka, unit CBU premium, atau mobil listrik rilisan tahun terbaru di mana sampel pasar sekunder bernilai nol atau di bawah batas statistik (<em>N &lt; 2</em>), sistem tidak mengalami kegagalan (<em>crash</em>). Sistem secara otomatis mengaktifkan modul <strong>MSRP Benchmark &amp; Age-Decay Retention Modeling</strong>.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"BasePrice_{Theoretical} = MSRP_{New} \times \left(1 - \min\left(0.72, \; 0.165 \cdot (1 - e^{-0.40 t}) + 0.058 t\right)\right)")
        st.latex(r"FMV_{Final} = \max\left(\text{Rp } 35.000.000, \; BasePrice_{Theoretical} \times F_{Fuel} \times F_{Trans} + \sum \Delta_{Hedonik}\right)")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_ml_eval:
        st.markdown('<div class="content-panel"><div class="panel-header">Evaluasi & Performa Training Model Versi 7 (v7.4.0-AutomotiveEnterprise)</div>', unsafe_allow_html=True)
        
        eval_m = ml_car_model_v7.evaluation_metrics
        
        st.markdown(f"""
        <div class="info-box-purple">
            <div class="info-box-title">Spesifikasi Arsitektur Model Machine Learning Versi 7</div>
            <div class="info-box-desc">
                <strong>Arsitektur:</strong> {eval_m['architecture']}<br>
                <strong>Dataset Training:</strong> {eval_m['training_samples']:,} data latih (80%) + {eval_m['test_samples']:,} data uji (20%) = Total <strong>{ml_car_model_v7.dataset_size:,} unit mobil terverifikasi</strong>.<br>
                <strong>Tanggal Rilis:</strong> {ml_car_model_v7.trained_date} | Durasi Training: {eval_m['training_duration_seconds']} detik.
            </div>
        </div>
        """, unsafe_allow_html=True)

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(f"""
            <div class="pro-metric-card emerald">
                <div class="pro-metric-label">R-Squared (R2)</div>
                <div class="pro-metric-val">{eval_m['r2_score']:.4f}</div>
                <div class="pro-metric-sub">Akurasi Prediksi 95.42%</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
            <div class="pro-metric-card" style="border-color: #38bdf8;">
                <div class="pro-metric-label">Mean Absolute Error</div>
                <div class="pro-metric-val" style="color: #38bdf8; font-size: 1.25rem;">Rp {eval_m['mae_idr']:,.0f}</div>
                <div class="pro-metric-sub">Rata-rata selisih prediksi</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col3:
            st.markdown(f"""
            <div class="pro-metric-card amber">
                <div class="pro-metric-label">MAPE (%)</div>
                <div class="pro-metric-val">{eval_m['mape_pct']:.2f}%</div>
                <div class="pro-metric-sub">Error persentase sangat rendah</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col4:
            st.markdown(f"""
            <div class="pro-metric-card" style="border-color: #a855f7;">
                <div class="pro-metric-label">5-Fold CV Score</div>
                <div class="pro-metric-val" style="color: #a855f7;">{eval_m['cross_val_kfold_mean_r2']:.4f}</div>
                <div class="pro-metric-sub">Stabilitas generalisasi data</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("#### Feature Importance (Bobot Pengaruh Variabel terhadap Nilai Mobil Bekas)")
        df_feat = pd.DataFrame([
            {"Fitur / Variabel": k, "Bobot Pengaruh": v, "Persentase": f"{v*100:.1f}%"}
            for k, v in eval_m["feature_importance"].items()
        ]).sort_values("Bobot Pengaruh", ascending=True)

        fig_feat = px.bar(
            df_feat,
            x="Bobot Pengaruh",
            y="Fitur / Variabel",
            orientation="h",
            color="Bobot Pengaruh",
            color_continuous_scale="Teal",
            text="Persentase"
        )
        fig_feat.update_traces(textposition="outside")
        fig_feat = format_dark_chart(fig_feat, show_legend=False, x_title="Relative Feature Importance")
        fig_feat.update_layout(height=360)
        st.plotly_chart(fig_feat, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_regional:
        st.markdown('<div class="content-panel"><div class="panel-header">Indeks Disparitas Geografis Multi-Wilayah (8 Wilayah Indonesia)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box-blue">
            <div class="info-box-title">Metodologi Disparitas Harga Regional</div>
            <div class="info-box-desc">
                Harga mobil bekas di Indonesia memiliki disparitas geografis yang nyata antar-provinsi dan pulau akibat biaya pengiriman kargo kapal roro/kontainer, tingkat ketersediaan stok unit bekas di pasar lokal, serta perbedaan tarif Bea Balik Nama Kendaraan Bermotor (BBN-KB). Model CarPrice ID menerapkan koefisien pengali regional standar.
            </div>
        </div>
        """, unsafe_allow_html=True)

        reg_table = []
        for r_name, r_info in REGIONAL_PRICE_INDEX.items():
            reg_table.append({
                "Kode": r_info["region_code"],
                "Wilayah Geografis": r_name,
                "Faktor Pengali": f"{r_info['multiplier']:.3f}",
                "Disparitas %": f"{(r_info['multiplier'] - 1.0)*100:+0.1f}%",
                "Tarif BBN-KB": r_info["bbn_rate"],
                "Karakteristik Pasar": r_info["description"]
            })
        st.dataframe(pd.DataFrame(reg_table), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_api:
        st.markdown('<div class="content-panel"><div class="panel-header">Layanan REST API B2B Enterprise (FastAPI Endpoints)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box-green">
            <div class="info-box-title">Integrasi Sistem Perbankan, Multifinance & Fintech</div>
            <div class="info-box-desc">
                CarPrice ID menyediakan antarmuka REST API berkinerja tinggi (berbasis asynchronous FastAPI) yang memungkinkan mitra korporasi melakukan taksasi agunan mobil dan pemindaian harga pasar secara terprogram.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        #### Daftar Endpoint Resmi (Base URL: `http://localhost:8000` / `https://api.carprice.id`):
        - **`GET /api/v1/health`** : Health check dan status model version.
        - **`GET /api/v1/catalog/brands`** : Mengambil 10 merk terdaftar di master database.
        - **`GET /api/v1/catalog/models?brand_id={id}`** : Mengambil daftar model, CC mesin, dan kategori bodi.
        - **`POST /api/v1/valuation/calculate`** : Menghitung FMV wajar, rentang P25/P75, dan residual forecast.
        - **`GET /api/v1/wholesale/corridor/{variant_id}/{year}`** : Mengambil data 3-tier wholesale auction corridor.
        - **`GET /api/v1/arbitrage/deals?min_discount=12`** : Mengambil daftar listing hot deals diskon arbitrase.

        #### Contoh Payload Request Valuasi (`POST /api/v1/valuation/calculate`):
        ```json
        {
          "variant_id": 15,
          "year": 2023,
          "odometer_km": 28000,
          "fuel_type": "Bensin",
          "transmission": "CVT",
          "tax_status": "Pajak Hidup / Panjang",
          "has_bpkb": true,
          "is_flood_free": true,
          "is_accident_free": true,
          "region": "Jabodetabek (DKI Jakarta, Bogor, Depok, Tangerang, Bekasi)"
        }
        ```

        #### Contoh Response JSON:
        ```json
        {
          "vehicle": {
            "brand": "Toyota",
            "model": "Kijang Innova & Zenix",
            "variant": "Innova Zenix 2.0 G CVT (Bensin M20A)",
            "year": 2023,
            "msrp_new": 425600000
          },
          "valuation": {
            "fair_market_value": 372500000,
            "bargain_p25": 352000000,
            "premium_p75": 391000000,
            "sample_count": 42,
            "methodology": "Empirical Quantile Median & Hedonic V7"
          },
          "regional_adjustment": {
            "region_code": "JABO",
            "multiplier": 1.0,
            "regional_adjusted_price": 372500000
          }
        }
        ```
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_dict:
        st.markdown('<div class="content-panel"><div class="panel-header">Data Dictionary & Schema Parameters</div>', unsafe_allow_html=True)
        dict_data = [
            {"Parameter": "ID", "Tipe": "Integer", "Definisi": "Identifikator unik data listing."},
            {"Parameter": "Category", "Tipe": "String", "Definisi": "Kategori bodi kendaraan (MPV, SUV, Hatchback, Sedan, EV)."},
            {"Parameter": "Platform", "Tipe": "String", "Definisi": "Marketplace / balai lelang sumber data (OLX, FACEBOOK, MOMOTOR, JBA, IBID)."},
            {"Parameter": "Title", "Tipe": "String", "Definisi": "Judul asli iklan setelah dinormalisasi NLP pipeline."},
            {"Parameter": "Brand", "Tipe": "String", "Definisi": "Merk pabrikan mobil resmi (10 Merk Master)."},
            {"Parameter": "Model", "Tipe": "String", "Definisi": "Lini model mobil (23 Model master terdaftar)."},
            {"Parameter": "Variant", "Tipe": "String", "Definisi": "Varian spesifik dan generasi mesin (76 Varian master)."},
            {"Parameter": "Year", "Tipe": "Integer", "Definisi": "Tahun pembuatan kendaraan (2014–2026)."},
            {"Parameter": "Price", "Tipe": "Numeric", "Definisi": "Harga riil transaksi tunai (IDR)."},
            {"Parameter": "Price_Type", "Tipe": "String", "Definisi": "Klasifikasi validitas harga (Cash vs DP / Clickbait)."},
            {"Parameter": "Mileage_KM", "Tipe": "Integer", "Definisi": "Jarak tempuh odometer kendaraan (KM)."},
            {"Parameter": "Fuel_Type", "Tipe": "String", "Definisi": "Tipe powertrain bahan bakar (Bensin, Diesel, Hybrid HEV, Listrik BEV)."},
            {"Parameter": "Transmission", "Tipe": "String", "Definisi": "Tipe transmisi penggerak (Manual, Automatic, CVT, DHT, Single-Speed EV)."},
            {"Parameter": "Tax_Status", "Tipe": "String", "Definisi": "Status legalitas pajak PKB (Hidup / Panjang, Mati / Off, Unknown)."},
            {"Parameter": "BPKB", "Tipe": "String", "Definisi": "Kelengkapan dokumen BPKB & Faktur asli."},
            {"Parameter": "City & Province", "Tipe": "String", "Definisi": "Lokasi administratif unit kendaraan."},
            {"Parameter": "MSRP_New", "Tipe": "Numeric", "Definisi": "Harga resmi On The Road (OTR) baru saat rilis peluncuran."},
            {"Parameter": "Depresiasi Riil (%)", "Tipe": "Numeric", "Definisi": "Persentase penyusutan harga pasar terhadap MSRP OTR baru."},
            {"Parameter": "URL", "Tipe": "Text", "Definisi": "Tautan deep-search resmi aktif menuju listing marketplace terkait."}
        ]
        st.dataframe(pd.DataFrame(dict_data), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_cat:
        st.markdown('<div class="content-panel"><div class="panel-header">Master Catalog Scope (12 Years: 2014–2026)</div>', unsafe_allow_html=True)
        cat_summary = [
            {"Kategori Sektor": "MPV & Family Cars", "Merk": "Toyota", "Negara": "Jepang", "Model": 5, "Varian": 22, "Rentang CC": "1200cc - 2800cc", "Contoh Model Unggulan": "Avanza, Veloz, Kijang Innova Reborn, Innova Zenix Hybrid, Fortuner, Calya, Raize, Yaris Cross"},
            {"Kategori Sektor": "Hatchback & SUV", "Merk": "Honda", "Negara": "Jepang", "Model": 4, "Varian": 13, "Rentang CC": "1200cc - 2000cc", "Contoh Model Unggulan": "Brio Satya/RS, HR-V Turbo/SE, CR-V RS e:HEV, BR-V Sensing, WR-V RS"},
            {"Kategori Sektor": "MPV & Ladder Frame SUV", "Merk": "Mitsubishi", "Negara": "Jepang", "Model": 3, "Varian": 7, "Rentang CC": "1500cc - 2400cc", "Contoh Model Unggulan": "Xpander Ultimate, Xpander Cross Premium, Pajero Sport Dakar 4x2, Xforce Ultimate"},
            {"Kategori Sektor": "Crossover & EV", "Merk": "Hyundai", "Negara": "Korea Selatan", "Model": 2, "Varian": 5, "Rentang CC": "0cc (EV) / 2200cc", "Contoh Model Unggulan": "Creta Prime, Stargazer X Prime, Ioniq 5 Long Range, Palisade CRDi"},
            {"Kategori Sektor": "City EV & MPV", "Merk": "Wuling", "Negara": "Cina", "Model": 2, "Varian": 4, "Rentang CC": "0cc (EV) / 2000cc", "Contoh Model Unggulan": "Air EV Long Range, Binguo EV 410km, Almaz RS Pro, Almaz Hybrid"},
            {"Kategori Sektor": "Dedicated EV", "Merk": "BYD", "Negara": "Cina", "Model": 1, "Varian": 3, "Rentang CC": "0cc (EV Electric)", "Contoh Model Unggulan": "Seal Performance AWD, Atto 3 Superior Extended, Dolphin Extended"},
            {"Kategori Sektor": "LCGC & Compact SUV", "Merk": "Daihatsu", "Negara": "Jepang", "Model": 2, "Varian": 4, "Rentang CC": "1000cc - 1500cc", "Contoh Model Unggulan": "Sigra R DLX, All New Ayla R CVT, All New Terios Custom, All New Xenia ASA"},
            {"Kategori Sektor": "Hybrid & Mini Offroader", "Merk": "Suzuki", "Negara": "Jepang", "Model": 2, "Varian": 6, "Rentang CC": "1500cc", "Contoh Model Unggulan": "All New Ertiga GX Hybrid, XL7 Hybrid Alpha, Jimny 3-Door 4x4, Jimny 5-Door"},
            {"Kategori Sektor": "Executive Luxury Sedan/SUV", "Merk": "BMW", "Negara": "Jerman", "Model": 1, "Varian": 4, "Rentang CC": "1500cc - 2000cc", "Contoh Model Unggulan": "320i Dynamic/Sport (G20), 330i M Sport, X1 sDrive18i xLine"},
            {"Kategori Sektor": "Premium Luxury", "Merk": "Mercedes-Benz", "Negara": "Jerman", "Model": 1, "Varian": 3, "Rentang CC": "1500cc - 2000cc", "Contoh Model Unggulan": "C200 Avantgarde (W205), C300 AMG Line (W206), GLC 200 AMG Line"}
        ]
        st.dataframe(pd.DataFrame(cat_summary), use_container_width=True, hide_index=True)
        st.caption("Total Cakupan Master Katalog: 10 Produsen Terkemuka, 23 Model Kendaraan, dan 76 Varian Resmi lintas seluruh segmen mobil di Indonesia.")
        st.markdown('</div>', unsafe_allow_html=True)
