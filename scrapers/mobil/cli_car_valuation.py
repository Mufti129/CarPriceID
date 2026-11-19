"""
Interactive CLI Tool: IBID Astra MAP Car Valuation Engine
Memungkinkan pengecekan nilai lelang mobil langsung dari terminal.
"""

from scrapers.ibid_map_scraper import IbidMapClient, _extract_unit_grade_prices


def format_rupiah(val):
    if val is None:
        return "N/A"
    try:
        return f"Rp {float(val):,.0f}".replace(",", ".")
    except Exception:
        return str(val)


def main():
    client = IbidMapClient()
    print("=" * 65)
    print("  IBID ASTRA MAP (MARKET AUCTION PRICE) - CAR VALUATION ENGINE")
    print("=" * 65)

    brands_data = client.get_brands()
    if not brands_data:
        print("[!] Gagal mengambil data merek. Periksa koneksi internet.")
        return

    brands = [b.get("label") for b in brands_data if b.get("label")]
    print("\n[+] Merek Tersedia:", ", ".join(brands[:15]) + " ...")

    brand_input = input("\nMasukkan Nama Merek (contoh: TOYOTA): ").strip().upper()
    if brand_input not in brands:
        print(f"[!] Merek '{brand_input}' tidak ditemukan di katalog.")
        return

    print(f"\n[*] Mengambil daftar model/seri untuk {brand_input}...")
    series_objs = client.get_series(merk=brand_input)
    if not series_objs:
        print(f"[!] Tidak ada data seri untuk {brand_input}.")
        return

    series_list = sorted(list(set([s.get("value") for s in series_objs if s.get("value")])))
    print(f"[+] Seri/Model Tersedia ({len(series_list)}):", ", ".join(series_list))

    seri_input = input("\nMasukkan Nama Seri (contoh: AVANZA): ").strip().upper()
    if seri_input not in series_list:
        print(f"[!] Seri '{seri_input}' tidak ditemukan.")
        return

    types_objs = client.get_types(merk=brand_input, seri=seri_input)
    types = [t.get("value") for t in types_objs if t.get("value")]
    print("[+] Pilihan Tipe:", ", ".join(types))
    tipe_input = input("\nMasukkan Tipe (contoh: G): ").strip().upper()

    cyl_objs = client.get_cylinders(merk=brand_input, seri=seri_input, tipe=tipe_input)
    cylinders = [str(c.get("value")) for c in cyl_objs if c.get("value")]
    print("[+] Pilihan Silinder (CC/Liter):", ", ".join(cylinders))
    silinder_input = input("Masukkan Silinder (contoh: 1.3): ").strip()

    yr_objs = client.get_years(merk=brand_input, seri=seri_input, tipe=tipe_input, silinder=silinder_input)
    years = [str(y.get("value")) for y in yr_objs if y.get("value")]
    print("[+] Pilihan Tahun:", ", ".join(years))
    tahun_input = input("Masukkan Tahun (contoh: 2019): ").strip()
    trans_input = input("Masukkan Transmisi (MT / AT, default MT): ").strip().upper() or "MT"

    print("\n" + "-" * 65)
    print(f"[*] Melakukan valuasi lelang untuk: {brand_input} {seri_input} {tipe_input} {silinder_input} ({tahun_input} {trans_input})...")
    print("-" * 65)

    # 1. Price Check
    price_res = client.check_price(
        merk=brand_input,
        seri=seri_input,
        silinder=silinder_input,
        tipe=tipe_input,
        tahun=tahun_input,
        transmisi=trans_input,
    )

    min_p = price_res.get("min_harga")
    max_p = price_res.get("max_harga")

    # 2. Grade Analysis (Host: MAP_BE)
    grade_res = client.get_price_by_grade(
        brand=brand_input,
        series=seri_input,
        cylinder=silinder_input,
        tipe=tipe_input,
        year=tahun_input,
        transmission=trans_input,
    )

    grade_items = grade_res.get("item", []) if isinstance(grade_res, dict) else []
    print("\n📊 HASIL ESTIMASI HARGA PASAR LELANG (MAP):")
    print(f"  • Harga Minimum Lelang : {format_rupiah(min_p)}")
    print(f"  • Harga Maksimum Lelang: {format_rupiah(max_p)}")

    if grade_items:
        print("\n🔍 ESTIMASI HARGA PER UNIT BERDASARKAN GRADE INSPEKSI ACV:")
        for item in grade_items:
            g = item.get("grade")
            parsed = _extract_unit_grade_prices(item)
            if parsed["mid"]:
                print(
                    f"  • Grade {g} : {format_rupiah(parsed['mid'])} "
                    f"(Rentang: {format_rupiah(parsed['low'])} - {format_rupiah(parsed['high'])})"
                )

    print("\n" + "=" * 65)


if __name__ == "__main__":
    main()
