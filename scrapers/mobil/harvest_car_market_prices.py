"""
Harvesting Engine: Penarikan Data Harga Pasar Mobil IBID MAP
Menyimpan data master varian, estimasi harga lelang, dan data per grade ke mobil_bekas.db.
"""

from data.sync_ibid_map_data import sync_ibid_map_data

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Harvest Car Market Auction Price from IBID Astra MAP")
    parser.add_argument("--brands", type=int, default=5, help="Limit number of brands to harvest (default: 5)")
    parser.add_argument("--delay", type=float, default=0.05, help="Delay between requests in seconds")
    args = parser.parse_args()

    res = sync_ibid_map_data(limit_brands=args.brands, delay_sec=args.delay)
    print(f"✅ Harvesting selesai: {res}")
