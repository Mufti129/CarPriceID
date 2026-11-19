# DOKUMENTASI LENGKAP & SPESIFIKASI TEKNIS
## IBID ASTRA MAP (MARKET AUCTION PRICE) — CAR VALUATION & PRICE BENCHMARK ENGINE
**Kategori:** Wholesale & Auction Market Intelligence (Mobil & Kendaraan Roda 4)  
**Sumber Portal:** [https://map.ibid.astra.co.id/](https://map.ibid.astra.co.id/)  
**Dual Backend API Hosts:**
- **Host Master & Check-Price:** `https://api.ibid.astra.co.id/backend-dc-map`
- **Host Analytics & Grade History:** `https://api.ibid.astra.co.id/map-be`  
**Lokasi Direktori:** `scrapers/mobil/` & `scrapers/ibid_map_scraper.py`

---

## 1. Pendahuluan & Ringkasan Sistem
Portal **IBID MAP (Market Auction Price)** adalah platform analitik harga kendaraan lelang resmi yang dikelola oleh **PT Balai Lelang Serasi (IBID - Astra Group)**. 

Sistem **MAP** ini dikhususkan untuk **kendaraan roda empat (Mobil Penumpang, SUV, MPV, Niaga, dan Truk)** dengan cakupan **26 Merek Resmi**. Modul ini menyediakan data harga pasar terbentuk (*fair auction value*), rentang harga minimum/maksimum (`hargaTerendah` & `hargaTertinggi`), valuasi berdasarkan *Grade Inspeksi ACV (Astra Car Valuation)* Grade A–E, serta tren harga per kota dan kurun waktu.

---

## 2. Spesifikasi Teknis REST API & Keamanan

Sistem backend IBID MAP dilindungi oleh Azure API Management (APIM) dan internal client signature. Setiap request wajib menyertakan header otentikasi berikut:

```http
Content-Type: application/json
Accept: application/json, text/plain, */*
Ocp-Apim-Subscription-Key: 5c425b903b2b49b48f5edf10ce95616b
secret_key_map: stf57d68ag79d8uajd081n09dasdjjin9a87gfy6098h9d78s6f756crsafygud
client_id_map: 0000000000001
Referer: https://map.ibid.astra.co.id/
Origin: https://map.ibid.astra.co.id
```

---

## 3. Kamus Endpoint & Spesifikasi Request-Response

### 3.1 Master Taksonomi Kendaraan (`backend-dc-map`)
1. **Master Merek (`master-data-merk`)**:
   - `GET https://api.ibid.astra.co.id/backend-dc-map/services/stock/master-data-merk`
2. **Master Seri (`master-data-seri`)**:
   - `GET https://api.ibid.astra.co.id/backend-dc-map/services/stock/master-data-seri?merk=TOYOTA`
3. **Master Tipe (`master-data-tipe`)**:
   - `GET https://api.ibid.astra.co.id/backend-dc-map/services/stock/master-data-tipe?merk=TOYOTA&seri=AVANZA`
4. **Master Silinder (`master-data-silinder`)**:
   - `GET https://api.ibid.astra.co.id/backend-dc-map/services/stock/master-data-silinder?merk=TOYOTA&seri=AVANZA&tipe=G`
5. **Master Tahun (`master-data-tahun`)**:
   - `GET https://api.ibid.astra.co.id/backend-dc-map/services/stock/master-data-tahun?merk=TOYOTA&seri=AVANZA&tipe=G&silinder=1.3`
6. **Master Transmisi (`master-data-transmisi`)**:
   - `GET https://api.ibid.astra.co.id/backend-dc-map/services/stock/master-data-transmisi?merk=TOYOTA&seri=AVANZA&tipe=G&silinder=1.3&tahun=2019`

### 3.2 Analitik Harga Multi-Tahun & Grade ACV (`map-be`)
1. **Multi-Year & Multi-Grade Batch Valuation (`type-of-year/get`)**:
   - `GET https://api.ibid.astra.co.id/map-be/services/price/type-of-year/get`
   - **Query Parameters:** `brand`, `merk`, `series`, `seri`, `cylinder`, `silinder`, `type`, `tipe`, `transmisi`, `startYear`, `endYear`, `city`, `period`
   - **Catatan Penting Parsing:**
     - Gunakan `hargaTerendah` dan `hargaTertinggi` (atau nilai tengahnya `(hargaTerendah + hargaTertinggi) / 2`) sebagai harga valuasi per 1 unit mobil.
     - Jangan gunakan `totalHarga` sebagai harga unit, karena `totalHarga` adalah akumulasi nilai transaksi seluruh lot yang terjual pada bucket grade tersebut.
2. **Single-Year Grade Breakdown (`unit-condition/get`)**:
   - `GET https://api.ibid.astra.co.id/map-be/services/price/unit-condition/get`
3. **Distribusi Harga per Kota (`area-city/get`)**:
   - `GET https://api.ibid.astra.co.id/map-be/services/price/area-city/get`
4. **Tren Pergerakan Waktu (`time/get`)**:
   - `GET https://api.ibid.astra.co.id/map-be/services/price/time/get`
5. **Cek Estimasi Harga Cepat (`check-price`)**:
   - `POST https://api.ibid.astra.co.id/backend-dc-map/services/map/check-price`
