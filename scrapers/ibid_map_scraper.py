"""
IBID Astra MAP (Market Auction Price) API Client SDK & Wholesale Scraper
Platform Resmi Balai Lelang Serasi (Astra Group) untuk Valuasi Mobil Bekas Indonesia
Portal: https://map.ibid.astra.co.id/
"""

import time
import logging
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('IbidMapScraper')


class IbidMapClient:
    """Client SDK resmi untuk berinteraksi dengan REST API backend IBID Astra MAP."""

    BASE_URL = 'https://api.ibid.astra.co.id/backend-dc-map'
    MAP_BE_URL = 'https://api.ibid.astra.co.id/map-be'

    def __init__(self, timeout: int = 12):
        self.timeout = timeout
        self.session = requests.Session()

        # Konfigurasi retry otomatis jika terjadi timeout atau HTTP error sementara
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': '5c425b903b2b49b48f5edf10ce95616b',
            'secret_key_map': 'stf57d68ag79d8uajd081n09dasdjjin9a87gfy6098h9d78s6f756crsafygud',
            'client_id_map': '0000000000001',
            'Referer': 'https://map.ibid.astra.co.id/',
            'Origin': 'https://map.ibid.astra.co.id'
        })

    def get_brands(self) -> List[Dict[str, Any]]:
        """Mengambil daftar seluruh 26 merek mobil di database IBID MAP."""
        url = f'{self.BASE_URL}/services/stock/master-data-merk'
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get('data', []) if isinstance(data, dict) else data
        except Exception as e:
            logger.error(f'Gagal mengambil master merek IBID MAP: {e}')
            return []

    def get_variants(self, merk: str, seri: Optional[str] = None) -> List[Dict[str, Any]]:
        """Mengambil daftar varian, silinder cc, trim tipe, dan tahun untuk merek/seri tertentu."""
        url = f'{self.BASE_URL}/services/map/stock/get/variant'
        params = {'merk': str(merk).upper()}
        if seri:
            params['seri'] = str(seri).upper()
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get('data', [])
        except Exception as e:
            logger.error(f'Gagal mengambil varian {merk} {seri}: {e}')
            return []

    def check_price(
        self,
        merk: str,
        seri: str,
        silinder: str,
        tipe: str,
        tahun: str,
        transmisi: str = 'MT'
    ) -> Dict[str, Any]:
        """Mengecek estimasi harga pasar lelang wholesale (min_harga & max_harga)."""
        url = f'{self.BASE_URL}/services/map/check-price'
        payload = {
            'merk': str(merk).upper(),
            'seri': str(seri).upper(),
            'silinder': str(silinder),
            'tipe': str(tipe).upper(),
            'tahun': str(tahun),
            'transmisi': str(transmisi).upper()
        }
        try:
            resp = self.session.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get('data', {}) if data.get('status') else {}
        except Exception as e:
            logger.error(f'Gagal cek harga {merk} {seri} {tahun}: {e}')
            return {}

    def get_price_by_grade(
        self,
        brand: str,
        series: str,
        cylinder: str,
        tipe: str,
        year: str,
        transmission: str = 'MT'
    ) -> Dict[str, Any]:
        """Mengambil harga terbentuk berdasarkan Grade Inspeksi ACV (Grade A, B, C, D, E)."""
        url = f'{self.BASE_URL}/services/price/unit-condition/get'
        params = {
            'brand': str(brand).upper(),
            'series': str(series).upper(),
            'cylinder': str(cylinder),
            'type': str(tipe).upper(),
            'year': str(year),
            'transmission': str(transmission).upper()
        }
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get('data', {}) if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f'Gagal mengambil harga grade {brand} {series}: {e}')
            return {}

    def get_price_by_city(
        self,
        brand: str,
        series: str,
        cylinder: str,
        tipe: str,
        year: str,
        transmission: str = 'MT'
    ) -> Dict[str, Any]:
        """Mengambil distribusi harga lelang per kota/cabang IBID."""
        url = f'{self.BASE_URL}/services/price/area-city/get'
        params = {
            'brand': str(brand).upper(),
            'series': str(series).upper(),
            'cylinder': str(cylinder),
            'type': str(tipe).upper(),
            'year': str(year),
            'transmission': str(transmission).upper()
        }
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get('data', {}) if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f'Gagal mengambil harga per kota {brand} {series}: {e}')
            return {}

    def get_price_trend_by_time(
        self,
        brand: str,
        series: str,
        cylinder: str,
        tipe: str,
        year: str,
        transmission: str = 'MT'
    ) -> Dict[str, Any]:
        """Mengambil histori grafik tren pergerakan harga lelang."""
        url = f'{self.BASE_URL}/services/price/time/get'
        params = {
            'brand': str(brand).upper(),
            'series': str(series).upper(),
            'cylinder': str(cylinder),
            'type': str(tipe).upper(),
            'year': str(year),
            'transmission': str(transmission).upper()
        }
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get('data', {}) if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f'Gagal mengambil tren waktu {brand} {series}: {e}')
            return {}

    def get_popular_vehicles(self) -> List[Dict[str, Any]]:
        """Mengambil unit mobil yang paling banyak dicari pembeli di portal IBID MAP."""
        url = f'{self.MAP_BE_URL}/services/popular'
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get('data', []) if isinstance(data, dict) else []
        except Exception as e:
            logger.error(f'Gagal mengambil data mobil populer: {e}')
            return []
