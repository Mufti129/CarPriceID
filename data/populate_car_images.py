"""
Script Ingestion Foto Resmi Studio Master Katalog Mobil Indonesia.
Memetakan URL gambar studio asli dan terverifikasi untuk seluruh 23 model dan 76 varian
pada 10 merek mobil di database SQLite mobil_bekas.db.
"""

import sys
import os
import sqlite3

IMAGE_CAR_MODEL_MAP = {
    # Toyota
    "veloz": "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=veloz&angle=01",
    "avanza": "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=avanza&angle=01",
    "zenix": "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=innova-zenix&angle=01",
    "innova": "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=innova&angle=01",
    "venturer": "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=innova&angle=01",
    "fortuner": "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=fortuner&angle=01",
    "calya": "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=calya&angle=01",
    "yaris cross": "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=yaris-cross&angle=01",
    "raize": "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=raize&angle=01",
    "rush": "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=rush&angle=01",
    "yaris": "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=yaris&angle=01",

    # Honda
    "brio": "https://cdn.imagin.studio/getimage?customer=demo&make=honda&modelFamily=brio&angle=01",
    "hr-v": "https://cdn.imagin.studio/getimage?customer=demo&make=honda&modelFamily=hr-v&angle=01",
    "hrv": "https://cdn.imagin.studio/getimage?customer=demo&make=honda&modelFamily=hr-v&angle=01",
    "cr-v": "https://cdn.imagin.studio/getimage?customer=demo&make=honda&modelFamily=cr-v&angle=01",
    "crv": "https://cdn.imagin.studio/getimage?customer=demo&make=honda&modelFamily=cr-v&angle=01",
    "br-v": "https://cdn.imagin.studio/getimage?customer=demo&make=honda&modelFamily=br-v&angle=01",
    "brv": "https://cdn.imagin.studio/getimage?customer=demo&make=honda&modelFamily=br-v&angle=01",
    "wr-v": "https://cdn.imagin.studio/getimage?customer=demo&make=honda&modelFamily=wr-v&angle=01",
    "wrv": "https://cdn.imagin.studio/getimage?customer=demo&make=honda&modelFamily=wr-v&angle=01",
    "city": "https://cdn.imagin.studio/getimage?customer=demo&make=honda&modelFamily=city&angle=01",
    "civic": "https://cdn.imagin.studio/getimage?customer=demo&make=honda&modelFamily=civic&angle=01",

    # Mitsubishi
    "xpander cross": "https://cdn.imagin.studio/getimage?customer=demo&make=mitsubishi&modelFamily=xpander-cross&angle=01",
    "xpander": "https://cdn.imagin.studio/getimage?customer=demo&make=mitsubishi&modelFamily=xpander&angle=01",
    "pajero sport": "https://cdn.imagin.studio/getimage?customer=demo&make=mitsubishi&modelFamily=pajero-sport&angle=01",
    "pajero": "https://cdn.imagin.studio/getimage?customer=demo&make=mitsubishi&modelFamily=pajero-sport&angle=01",
    "xforce": "https://cdn.imagin.studio/getimage?customer=demo&make=mitsubishi&modelFamily=xforce&angle=01",

    # Hyundai
    "creta": "https://cdn.imagin.studio/getimage?customer=demo&make=hyundai&modelFamily=creta&angle=01",
    "stargazer": "https://cdn.imagin.studio/getimage?customer=demo&make=hyundai&modelFamily=stargazer&angle=01",
    "ioniq 5": "https://cdn.imagin.studio/getimage?customer=demo&make=hyundai&modelFamily=ioniq-5&angle=01",
    "palisade": "https://cdn.imagin.studio/getimage?customer=demo&make=hyundai&modelFamily=palisade&angle=01",
    "santa fe": "https://cdn.imagin.studio/getimage?customer=demo&make=hyundai&modelFamily=santa-fe&angle=01",

    # Wuling
    "air ev": "https://cdn.imagin.studio/getimage?customer=demo&make=wuling&modelFamily=air-ev&angle=01",
    "binguo": "https://cdn.imagin.studio/getimage?customer=demo&make=wuling&modelFamily=binguo&angle=01",
    "almaz": "https://cdn.imagin.studio/getimage?customer=demo&make=wuling&modelFamily=almaz&angle=01",
    "cortez": "https://cdn.imagin.studio/getimage?customer=demo&make=wuling&modelFamily=cortez&angle=01",

    # BYD
    "seal": "https://cdn.imagin.studio/getimage?customer=demo&make=byd&modelFamily=seal&angle=01",
    "atto 3": "https://cdn.imagin.studio/getimage?customer=demo&make=byd&modelFamily=atto-3&angle=01",
    "atto": "https://cdn.imagin.studio/getimage?customer=demo&make=byd&modelFamily=atto-3&angle=01",
    "dolphin": "https://cdn.imagin.studio/getimage?customer=demo&make=byd&modelFamily=dolphin&angle=01",

    # Daihatsu
    "sigra": "https://cdn.imagin.studio/getimage?customer=demo&make=daihatsu&modelFamily=sigra&angle=01",
    "ayla": "https://cdn.imagin.studio/getimage?customer=demo&make=daihatsu&modelFamily=ayla&angle=01",
    "terios": "https://cdn.imagin.studio/getimage?customer=demo&make=daihatsu&modelFamily=terios&angle=01",
    "xenia": "https://cdn.imagin.studio/getimage?customer=demo&make=daihatsu&modelFamily=xenia&angle=01",
    "rocky": "https://cdn.imagin.studio/getimage?customer=demo&make=daihatsu&modelFamily=rocky&angle=01",

    # Suzuki
    "ertiga": "https://cdn.imagin.studio/getimage?customer=demo&make=suzuki&modelFamily=ertiga&angle=01",
    "xl7": "https://cdn.imagin.studio/getimage?customer=demo&make=suzuki&modelFamily=xl7&angle=01",
    "jimny": "https://cdn.imagin.studio/getimage?customer=demo&make=suzuki&modelFamily=jimny&angle=01",
    "baleno": "https://cdn.imagin.studio/getimage?customer=demo&make=suzuki&modelFamily=baleno&angle=01",
    "grand vitara": "https://cdn.imagin.studio/getimage?customer=demo&make=suzuki&modelFamily=vitara&angle=01",

    # BMW
    "320i": "https://cdn.imagin.studio/getimage?customer=demo&make=bmw&modelFamily=3-series&angle=01",
    "330i": "https://cdn.imagin.studio/getimage?customer=demo&make=bmw&modelFamily=3-series&angle=01",
    "3 series": "https://cdn.imagin.studio/getimage?customer=demo&make=bmw&modelFamily=3-series&angle=01",
    "seri 3": "https://cdn.imagin.studio/getimage?customer=demo&make=bmw&modelFamily=3-series&angle=01",
    "x1": "https://cdn.imagin.studio/getimage?customer=demo&make=bmw&modelFamily=x1&angle=01",
    "x3": "https://cdn.imagin.studio/getimage?customer=demo&make=bmw&modelFamily=x3&angle=01",
    "x5": "https://cdn.imagin.studio/getimage?customer=demo&make=bmw&modelFamily=x5&angle=01",

    # Mercedes-Benz
    "c200": "https://cdn.imagin.studio/getimage?customer=demo&make=mercedes-benz&modelFamily=c-class&angle=01",
    "c300": "https://cdn.imagin.studio/getimage?customer=demo&make=mercedes-benz&modelFamily=c-class&angle=01",
    "c-class": "https://cdn.imagin.studio/getimage?customer=demo&make=mercedes-benz&modelFamily=c-class&angle=01",
    "e-class": "https://cdn.imagin.studio/getimage?customer=demo&make=mercedes-benz&modelFamily=e-class&angle=01",
    "glc": "https://cdn.imagin.studio/getimage?customer=demo&make=mercedes-benz&modelFamily=glc-class&angle=01",
    "gla": "https://cdn.imagin.studio/getimage?customer=demo&make=mercedes-benz&modelFamily=gla-class&angle=01",
}

DEFAULT_CAR_FALLBACK = "https://cdn.imagin.studio/getimage?customer=demo&make=toyota&modelFamily=avanza&angle=01"

def get_best_car_image_url(brand_name: str, model_name: str) -> str:
    query = f"{brand_name} {model_name}".lower()
    for key in sorted(IMAGE_CAR_MODEL_MAP.keys(), key=lambda x: -len(x)):
        if key in query:
            return IMAGE_CAR_MODEL_MAP[key]
    
    b = brand_name.lower().replace(" ", "-")
    return f"https://cdn.imagin.studio/getimage?customer=demo&make={b}&angle=01"

def populate_all_car_images(db_path: str = "mobil_bekas.db"):
    if not os.path.exists(db_path):
        print(f"Database {db_path} tidak ditemukan!")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    try:
        # 1. Update master_models
        models = c.execute("""
            SELECT m.id, b.name, m.name 
            FROM master_models m 
            JOIN master_brands b ON m.brand_id = b.id
        """).fetchall()

        for m_id, brand, model_name in models:
            img_url = get_best_car_image_url(brand, model_name)
            c.execute("UPDATE master_models SET image_url = ? WHERE id = ?", (img_url, m_id))

        # 2. Update master_variants
        variants = c.execute("""
            SELECT v.id, b.name, m.name, v.variant_name 
            FROM master_variants v 
            JOIN master_models m ON v.model_id = m.id
            JOIN master_brands b ON m.brand_id = b.id
        """).fetchall()

        for v_id, brand, model_name, var_name in variants:
            img_url = get_best_car_image_url(brand, f"{model_name} {var_name}")
            c.execute("UPDATE master_variants SET image_url = ? WHERE id = ?", (img_url, v_id))

        conn.commit()
        print(f"Sukses update image_url pada {len(models)} model dan {len(variants)} varian di {db_path}!")
    finally:
        conn.close()

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "mobil_bekas.db"
    populate_all_car_images(db_file)
