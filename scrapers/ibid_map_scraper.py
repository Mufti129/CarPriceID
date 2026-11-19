"""
IBID Astra MAP (Market Auction Price) API Client SDK & Wholesale Scraper
Platform Resmi Balai Lelang Serasi (Astra Group) untuk Valuasi Mobil Bekas Indonesia
Portal: https://map.ibid.astra.co.id/
"""

import logging
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IbidMapScraper")


def _extract_unit_grade_prices(item_dict: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Mengekstrak harga unit (hargaTerendah, hargaTertinggi, dan nilai tengah/midpoint)
    dari objek item grade IBID MAP.
    Catatan Penting: Field 'totalHarga' pada API IBID MAP adalah akumulasi nilai seluruh transaksi
    lot pada grade tersebut (bukan harga per 1 unit mobil), sehingga harga per unit yang akurat
    dihitung dari hargaTerendah dan hargaTertinggi.
    """
    low_raw = item_dict.get("hargaTerendah")
    high_raw = item_dict.get("hargaTertinggi")

    low_val: Optional[float] = None
    high_val: Optional[float] = None

    try:
        if low_raw is not None and str(low_raw).strip() not in ("", "-", "null", "None"):
            v = float(low_raw)
            if v > 1_000_000:
                low_val = v
    except (ValueError, TypeError):
        pass

    try:
        if high_raw is not None and str(high_raw).strip() not in ("", "-", "null", "None"):
            v = float(high_raw)
            if v > 1_000_000:
                high_val = v
    except (ValueError, TypeError):
        pass

    if low_val and high_val:
        mid_val = round((low_val + high_val) / 2.0, 2)
    elif high_val:
        mid_val = high_val
        low_val = high_val
    elif low_val:
        mid_val = low_val
        high_val = low_val
    else:
        mid_val = None

    return {
        "low": low_val,
        "high": high_val,
        "mid": mid_val,
    }


class IbidMapClient:
    """
    Client SDK resmi untuk berinteraksi dengan REST API backend IBID Astra MAP.
    Arsitektur Dual-Host IBID MAP:
      - BASE_URL (backend-dc-map): Master taksonomi (merk, seri, tipe, silinder, tahun, transmisi, location) & check-price
      - MAP_BE_URL (map-be): Analitik harga historis per grade (unit-condition, type-of-year, area-city, time, popular)
    """

    BASE_URL = "https://api.ibid.astra.co.id/backend-dc-map"
    MAP_BE_URL = "https://api.ibid.astra.co.id/map-be"

    def __init__(self, timeout: int = 12):
        self.timeout = timeout
        self.session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=0.4,
            status_forcelist=[429, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": "5c425b903b2b49b48f5edf10ce95616b",
            "secret_key_map": "stf57d68ag79d8uajd081n09dasdjjin9a87gfy6098h9d78s6f756crsafygud",
            "client_id_map": "0000000000001",
            "Referer": "https://map.ibid.astra.co.id/",
            "Origin": "https://map.ibid.astra.co.id",
        })

    # ==========================================================================
    # 1. MASTER TAXONOMY ENDPOINTS (HOST: backend-dc-map)
    # ==========================================================================
    def get_brands(self) -> List[Dict[str, Any]]:
        """Mengambil daftar seluruh 26 merek mobil di database IBID MAP."""
        url = f"{self.BASE_URL}/services/stock/master-data-merk"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", []) if isinstance(data, dict) else data
        except Exception as e:
            logger.error(f"Gagal mengambil master merek IBID MAP: {e}")
            return []

    def get_series(self, merk: str) -> List[Dict[str, Any]]:
        """Mengambil seluruh daftar seri/model untuk merek tertentu (contoh: TOYOTA -> 34 seri)."""
        url = f"{self.BASE_URL}/services/stock/master-data-seri"
        try:
            resp = self.session.get(url, params={"merk": str(merk).upper()}, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", []) if isinstance(data, dict) else data
            return [x for x in items if x.get("value")]
        except Exception as e:
            logger.error(f"Gagal mengambil master seri untuk {merk}: {e}")
            return []

    def get_types(self, merk: str, seri: str) -> List[Dict[str, Any]]:
        """Mengambil seluruh daftar tipe/trim untuk merek dan seri tertentu (contoh: TOYOTA AVANZA -> E, G, VELOZ)."""
        url = f"{self.BASE_URL}/services/stock/master-data-tipe"
        try:
            resp = self.session.get(
                url,
                params={"merk": str(merk).upper(), "seri": str(seri).upper()},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", []) if isinstance(data, dict) else data
            return [x for x in items if x.get("value")]
        except Exception as e:
            logger.error(f"Gagal mengambil master tipe untuk {merk} {seri}: {e}")
            return []

    def get_cylinders(self, merk: str, seri: str, tipe: str) -> List[Dict[str, Any]]:
        """Mengambil daftar kapasitas silinder (contoh: 1.3, 1.5, 2.0, 2.4)."""
        url = f"{self.BASE_URL}/services/stock/master-data-silinder"
        try:
            resp = self.session.get(
                url,
                params={
                    "merk": str(merk).upper(),
                    "seri": str(seri).upper(),
                    "tipe": str(tipe).upper(),
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", []) if isinstance(data, dict) else data
            return [x for x in items if x.get("value")]
        except Exception as e:
            logger.error(f"Gagal mengambil silinder untuk {merk} {seri} {tipe}: {e}")
            return []

    def get_years(self, merk: str, seri: str, tipe: str, silinder: str) -> List[Dict[str, Any]]:
        """Mengambil daftar tahun produksi yang tersedia di database lelang IBID."""
        url = f"{self.BASE_URL}/services/stock/master-data-tahun"
        try:
            resp = self.session.get(
                url,
                params={
                    "merk": str(merk).upper(),
                    "seri": str(seri).upper(),
                    "tipe": str(tipe).upper(),
                    "silinder": str(silinder),
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", []) if isinstance(data, dict) else data
            return [x for x in items if x.get("value")]
        except Exception as e:
            logger.error(f"Gagal mengambil tahun untuk {merk} {seri} {tipe}: {e}")
            return []

    def get_transmissions(
        self,
        merk: str,
        seri: str,
        tipe: Optional[str] = None,
        silinder: Optional[str] = None,
        tahun: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Mengambil daftar transmisi (AT / MT) yang tersedia."""
        url = f"{self.BASE_URL}/services/stock/master-data-transmisi"
        params: Dict[str, str] = {"merk": str(merk).upper(), "seri": str(seri).upper()}
        if tipe:
            params["tipe"] = str(tipe).upper()
        if silinder:
            params["silinder"] = str(silinder)
        if tahun:
            params["tahun"] = str(tahun)
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", []) if isinstance(data, dict) else data
            return [x for x in items if x.get("value") and x.get("value") != "label"]
        except Exception as e:
            logger.error(f"Gagal mengambil transmisi untuk {merk} {seri}: {e}")
            return []

    def get_variants(self, merk: str, seri: Optional[str] = None) -> List[Dict[str, Any]]:
        """Mengambil daftar sampel stok varian dari endpoint stock/get/variant."""
        url = f"{self.BASE_URL}/services/map/stock/get/variant"
        params = {"merk": str(merk).upper()}
        if seri:
            params["seri"] = str(seri).upper()
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get("data", [])
        except Exception as e:
            logger.error(f"Gagal mengambil varian {merk} {seri}: {e}")
            return []

    # ==========================================================================
    # 2. VALUATION & GRADE ANALYTICS ENDPOINTS (HOST: map-be & backend-dc-map)
    # ==========================================================================
    def _build_analytics_params(
        self,
        brand: str,
        series: str,
        cylinder: str,
        tipe: str,
        year: str,
        transmission: str = "MT",
        city: str = "JAKARTA",
        start_year: Optional[str] = None,
        end_year: Optional[str] = None,
        period: str = "12",
    ) -> Dict[str, str]:
        s_yr = str(start_year or year)
        e_yr = str(end_year or year)
        return {
            "city": str(city).upper(),
            "transmisi": str(transmission).upper(),
            "transmission": str(transmission).upper(),
            "startYear": s_yr,
            "endYear": e_yr,
            "period": str(period),
            "brand": str(brand).upper(),
            "merk": str(brand).upper(),
            "series": str(series).upper(),
            "seri": str(series).upper(),
            "cylinder": str(cylinder),
            "silinder": str(cylinder),
            "type": str(tipe).upper(),
            "tipe": str(tipe).upper(),
            "year": str(year),
        }

    def check_price(
        self,
        merk: str,
        seri: str,
        silinder: str,
        tipe: str,
        tahun: str,
        transmisi: str = "MT",
    ) -> Dict[str, Any]:
        """Mengecek estimasi harga pasar lelang wholesale (min_harga & max_harga)."""
        url = f"{self.BASE_URL}/services/map/check-price"
        payload = {
            "merk": str(merk).upper(),
            "seri": str(seri).upper(),
            "silinder": str(silinder),
            "tipe": str(tipe).upper(),
            "tahun": str(tahun),
            "transmisi": str(transmisi).upper(),
        }
        try:
            resp = self.session.post(url, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                return {}
            data = resp.json()
            return data.get("data", {}) if data.get("status") else {}
        except Exception as e:
            logger.debug(f"check_price fallback untuk {merk} {seri} {tahun}: {e}")
            return {}

    def get_price_by_grade(
        self,
        brand: str,
        series: str,
        cylinder: str,
        tipe: str,
        year: str,
        transmission: str = "MT",
        city: str = "JAKARTA",
    ) -> Dict[str, Any]:
        """
        Mengambil harga terbentuk per unit berdasarkan Grade Inspeksi ACV (Grade A, B, C, D, E)
        dari host resmi MAP_BE_URL (/map-be/services/price/unit-condition/get).
        """
        url = f"{self.MAP_BE_URL}/services/price/unit-condition/get"
        params = self._build_analytics_params(
            brand=brand,
            series=series,
            cylinder=cylinder,
            tipe=tipe,
            year=year,
            transmission=transmission,
            city=city,
        )
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            raw_data = data.get("data", {}) if isinstance(data, dict) else {}
            # Normalisasi setiap item agar memiliki harga per unit yang akurat
            items = raw_data.get("item", []) if isinstance(raw_data, dict) else []
            for item in items:
                parsed = _extract_unit_grade_prices(item)
                item["unit_price_low"] = parsed["low"]
                item["unit_price_high"] = parsed["high"]
                item["unit_price_mid"] = parsed["mid"]
            return raw_data
        except Exception as e:
            logger.error(f"Gagal mengambil harga grade {brand} {series} ({year}): {e}")
            return {}

    def get_price_by_type_of_year(
        self,
        brand: str,
        series: str,
        cylinder: str,
        tipe: str,
        transmission: str = "MT",
        start_year: int = 2014,
        end_year: int = 2026,
        city: str = "JAKARTA",
        period: str = "12",
    ) -> List[Dict[str, Any]]:
        """
        Batch Multi-Year Grade Valuation Endpoint (/map-be/services/price/type-of-year/get).
        Mengambil seluruh rentang tahun (start_year s/d end_year) beserta rincian Grade A, B, C, D, E
        hanya dalam 1 panggilan HTTP!
        """
        url = f"{self.MAP_BE_URL}/services/price/type-of-year/get"
        params = self._build_analytics_params(
            brand=brand,
            series=series,
            cylinder=cylinder,
            tipe=tipe,
            year=str(start_year),
            transmission=transmission,
            city=city,
            start_year=str(start_year),
            end_year=str(end_year),
            period=period,
        )
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            raw_data = data.get("data", {}) if isinstance(data, dict) else {}
            year_items = raw_data.get("item", []) if isinstance(raw_data, dict) else []

            results = []
            for y_obj in year_items:
                yr = y_obj.get("year")
                price_list = y_obj.get("price", [])
                if not yr or not price_list:
                    continue

                grades_map: Dict[str, float] = {}
                all_lows: List[float] = []
                all_highs: List[float] = []

                for p_item in price_list:
                    g_code = (p_item.get("grade") or "").strip().upper()
                    parsed = _extract_unit_grade_prices(p_item)
                    if g_code and parsed["mid"]:
                        grades_map[g_code] = parsed["mid"]
                    if parsed["low"]:
                        all_lows.append(parsed["low"])
                    if parsed["high"]:
                        all_highs.append(parsed["high"])

                if not grades_map and not all_lows:
                    continue

                results.append({
                    "year": int(yr),
                    "min_price": min(all_lows) if all_lows else None,
                    "max_price": max(all_highs) if all_highs else None,
                    "grade_a": grades_map.get("A"),
                    "grade_b": grades_map.get("B"),
                    "grade_c": grades_map.get("C"),
                    "grade_d": grades_map.get("D"),
                    "grade_e": grades_map.get("E"),
                })
            return results
        except Exception as e:
            logger.error(f"Gagal mengambil multi-year grade {brand} {series} {tipe}: {e}")
            return []

    def get_price_by_city(
        self,
        brand: str,
        series: str,
        cylinder: str,
        tipe: str,
        year: str,
        transmission: str = "MT",
    ) -> Dict[str, Any]:
        """Mengambil distribusi harga lelang per kota/cabang IBID dari MAP_BE_URL."""
        url = f"{self.MAP_BE_URL}/services/price/area-city/get"
        params = self._build_analytics_params(
            brand=brand,
            series=series,
            cylinder=cylinder,
            tipe=tipe,
            year=year,
            transmission=transmission,
        )
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {}) if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"Gagal mengambil harga per kota {brand} {series}: {e}")
            return {}

    def get_price_trend_by_time(
        self,
        brand: str,
        series: str,
        cylinder: str,
        tipe: str,
        year: str,
        transmission: str = "MT",
    ) -> Dict[str, Any]:
        """Mengambil histori grafik tren pergerakan harga lelang dari MAP_BE_URL."""
        url = f"{self.MAP_BE_URL}/services/price/time/get"
        params = self._build_analytics_params(
            brand=brand,
            series=series,
            cylinder=cylinder,
            tipe=tipe,
            year=year,
            transmission=transmission,
        )
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {}) if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"Gagal mengambil tren waktu {brand} {series}: {e}")
            return {}

    def get_popular_vehicles(self) -> List[Dict[str, Any]]:
        """Mengambil unit mobil yang paling banyak dicari pembeli di portal IBID MAP."""
        url = f"{self.MAP_BE_URL}/services/popular"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", []) if isinstance(data, dict) else []
        except Exception as e:
            logger.error(f"Gagal mengambil data mobil populer: {e}")
            return []
