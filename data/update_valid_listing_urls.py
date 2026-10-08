import os
import re
import urllib.parse
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.catalog import (
    ScrapedListing, AuctionLot, MasterBrand, MasterModel, MasterVariant
)

def extract_clean_vehicle_name(brand: str, model: str, variant: str = None) -> str:
    brand = (brand or '').strip()
    if variant:
        v_clean = re.sub(r'\(.*?\)', '', variant).strip()
        v_clean = re.sub(r'^(All\s+New|New)\s+', '', v_clean, flags=re.IGNORECASE).strip()
        v_tokens = v_clean.split()
        if len(v_tokens) >= 2 and v_tokens[1].lower() in ['zenix', 'reborn', 'cross', 'satya', 'ev', 'sport', 'prime', 'signature', 'dakar', 'hybrid', 'venturer', 'urbanite']:
            car_sub = f'{v_tokens[0]} {v_tokens[1]}'
        elif len(v_tokens) >= 1:
            car_sub = v_tokens[0]
        else:
            car_sub = model.split('&')[0].strip()
    else:
        m_first = model.split('&')[0].split(',')[0].strip()
        car_sub = re.sub(r'^(All\s+New|New)\s+', '', m_first, flags=re.IGNORECASE).strip()
    return f'{brand} {car_sub}'.strip()

def build_retail_listing_url(platform: str, brand: str, model: str, year: int = None, variant: str = None) -> str:
    clean_car = extract_clean_vehicle_name(brand, model, variant)
    query_str = f'{clean_car} {year}' if year else clean_car
    q_encoded = urllib.parse.quote(query_str)
    
    p = (platform or '').lower()
    if 'olx' in p:
        return f'https://www.olx.co.id/mobil-bekas_c198?q={q_encoded}'
    elif 'carsome' in p:
        return f'https://www.carsome.id/beli-mobil-bekas?q={q_encoded}'
    elif 'carmudi' in p:
        return f'https://www.carmudi.co.id/mobil-dijual/indonesia?q={q_encoded}'
    elif 'mobil123' in p:
        return f'https://www.mobil123.com/mobil-dijual/indonesia?q={q_encoded}'
    elif 'facebook' in p or 'fb' in p:
        return f'https://www.facebook.com/marketplace/search/?query={q_encoded}'
    else:
        return f'https://www.olx.co.id/mobil-bekas_c198?q={q_encoded}'

def build_auction_lot_url(platform: str, brand: str, model: str, year: int = None, variant: str = None) -> str:
    clean_car = extract_clean_vehicle_name(brand, model, variant)
    q_plus = urllib.parse.quote_plus(clean_car)
    
    p = (platform or '').lower()
    if 'jba' in p:
        return f'https://www.jba.co.id/id/lelang-mobil?keyword={q_plus}'
    elif 'ibid' in p:
        return f'https://www.ibid.astra.co.id/cari-otomotif?keyword={q_plus}&kategori=mobil'
    else:
        return f'https://www.jba.co.id/id/lelang-mobil?keyword={q_plus}'

def update_all_urls():
    db: Session = SessionLocal()
    try:
        print('Mulai memperbarui URL listing retail...')
        listings = db.query(
            ScrapedListing,
            MasterBrand.name.label('brand_name'),
            MasterModel.name.label('model_name'),
            MasterVariant.variant_name
        ).outerjoin(
            MasterVariant, ScrapedListing.matched_variant_id == MasterVariant.id
        ).outerjoin(
            MasterModel, MasterVariant.model_id == MasterModel.id
        ).outerjoin(
            MasterBrand, MasterModel.brand_id == MasterBrand.id
        ).all()

        updated_listings_count = 0
        for listing, b_name, m_name, v_name in listings:
            brand = b_name or 'Toyota'
            model = m_name or 'Avanza'
            new_url = build_retail_listing_url(
                platform=listing.source_platform,
                brand=brand,
                model=model,
                year=listing.claimed_year,
                variant=v_name
            )
            listing.url = new_url
            updated_listings_count += 1

        db.commit()
        print(f'Berhasil memperbarui {updated_listings_count} URL ScrapedListing.')

        print('Mulai memperbarui URL lot lelang...')
        auction_lots = db.query(
            AuctionLot,
            MasterBrand.name.label('brand_name'),
            MasterModel.name.label('model_name'),
            MasterVariant.variant_name
        ).outerjoin(
            MasterVariant, AuctionLot.matched_variant_id == MasterVariant.id
        ).outerjoin(
            MasterModel, MasterVariant.model_id == MasterModel.id
        ).outerjoin(
            MasterBrand, MasterModel.brand_id == MasterBrand.id
        ).all()

        updated_auction_count = 0
        for lot, b_name, m_name, v_name in auction_lots:
            brand = b_name or 'Toyota'
            model = m_name or 'Avanza'
            new_url = build_auction_lot_url(
                platform=lot.source_platform,
                brand=brand,
                model=model,
                year=lot.claimed_year,
                variant=v_name
            )
            lot.url = new_url
            updated_auction_count += 1

        db.commit()
        print(f'Berhasil memperbarui {updated_auction_count} URL AuctionLot.')

    finally:
        db.close()

if __name__ == '__main__':
    update_all_urls()
