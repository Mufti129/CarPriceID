# DOKUMENTASI LENGKAP & SPESIFIKASI TEKNIS SISTEM
## CARPRICE ID — USED CAR MARKET INTELLIGENCE & VALUATION ENGINE
**Penulis & Pengembang:** AI & Automotive Software Engineering Team  
**Versi Sistem:** v7.4 (Enterprise Automotive Edition)  
**Waktu Rilis:** Oktober 2026  
**Platform Deploy:** Streamlit Community Cloud & FastAPI (Python 3.13 Runtime)  

---

# DAFTAR ISI
1. [BAB I: Pendahuluan & Latar Belakang Masalah](#bab-i-pendahuluan--latar-belakang-masalah)
2. [BAB II: Arsitektur Sistem End-to-End](#bab-ii-arsitektur-sistem-end-to-end)
3. [BAB III: Definisi Kamus Data & Parameter Lengkap](#bab-iii-definisi-kamus-data--parameter-lengkap)
4. [BAB IV: Logika Ekonometrika, Model Analitik & Landasan Teori Ahli](#bab-iv-logika-ekonometrika-model-analitik--landasan-teori-ahli)
5. [BAB V: Taksonomi Master Katalog Mobil (2014–2026)](#bab-v-taksonomi-master-katalog-mobil-20142026)
6. [BAB VI: Panduan Operasional & API Service](#bab-vi-panduan-operasional--api-service)

---

# BAB I: Pendahuluan & Latar Belakang Masalah

### 1.1 Dinamika Pasar Mobil Bekas Indonesia
Pasar mobil bekas di Indonesia memiliki volume transaksi multi-triliun rupiah dengan karakter pasar sekunder yang unik:
1. **Asimetri Informasi Kualitas & Riwayat (*Information Asymmetry*):** Pembeli sering kali kesulitan memvalidasi apakah unit pernah mengalami tabrakan struktur sasis besar, riwayat terendam banjir (*flood damaged*), atau manipulasi jarak tempuh odometer.
2. **Jebakan Uang Muka (*DP / Clickbait Scam Trap*):** Banyak pedagang di marketplace mencantumkan nominal DP rendah (contoh: Rp 20.000.000 untuk Toyota Innova seharga Rp 350.000.000) pada kolom harga jual, sehingga mengacaukan perhitungan rata-rata statistik jika tidak dibersihkan dengan AI.
3. **Disparitas Nilai Berdasarkan Bahan Bakar (*Fuel Retention*):** Mobil Diesel Turbo (misal Toyota 2GD/1GD, Mitsubishi Pajero 4N15) dan Hybrid HEV (Innova Zenix HEV, Yaris Cross) memiliki daya tahan retensi harga yang jauh lebih kuat dibandingkan segmen bensin biasa di Indonesia.
4. **Faktor Beban Pajak (PKB):** Pajak mobil tahunan bernilai signifikan (Rp 2.500.000 – Rp 20.000.000+), sehingga status pajak mati memerlukan perhitungan penalti ekonometrika yang presisi.

### 1.2 Tujuan Pembangunan CarPrice ID
CarPrice ID hadir sebagai platform enterprise terintegrasi yang:
- Mengumpulkan data dari marketplace retail (OLX Mobil Bekas, Mobil123, Carmudi, Facebook, Carsome) dan balai lelang resmi (JBA Indonesia & IBID Astra).
- Mengimplementasikan NLP Normalizer dengan kamus istilah mobil Indonesia.
- Melakukan pemetaan varian fuzzy (*Entity Resolution*) ke katalog master 10+ Brand, 23+ Model, dan 76+ Varian resmi (2014–2026).
- Menerapkan ML Valuation Model V7 (Hedonic Residual Ensemble) berakurasi R² = 0.9542 dan MAPE = 3.94%.
- Menyediakan visualisasi Koridor Harga 3-Tier (Floor Lelang -> Wholesale Hammer -> Retail FMV) serta detektor arbitrase showroom.

---

# BAB II: Arsitektur Sistem End-to-End

```text
+-----------------------------------------------------------------------------------+
|                        1. DATA HARVESTING & INGESTION                             |
|  - RETAIL LAYER: OLX Mobil Bekas (Cat ID 198), Mobil123, Carmudi, Carsome, Carro   |
|  - WHOLESALE LAYER: JBA Indonesia & IBID Astra Lelang Resmi (5,000+ Auction Lots) |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                   2. AI & NLP DATA REFINEMENT PIPELINE                            |
|  - Automotive Slang Dictionary    - DP / Clickbait Scam Filter                    |
|  - Fuel & Transmission Extractor  - RapidFuzz Entity Resolution (Master Catalog)  |
|  - 4-Point Technical Normalizer   - Flood & Accident Free Condition Verifier      |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                     3. RELATIONAL DATABASE LAYER (SQLite)                         |
|  - master_brands (10)      - master_models (23)    - master_variants (76)         |
|  - scraped_listings (15K)  - auction_listings (5K)                                |
|  - market_price_stats (FMV)- wholesale_price_stats (Clearance & Wholesale Limits) |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                 4. ECONOMETRIC & PRICING ANALYTICS ENGINE                         |
|  - 3-Tier Price Corridor (Floor Limit -> Wholesale Hammer -> Retail FMV)          |
|  - ML Valuation Engine V7 (Multi-Stage Residual Gradient Boosting & Random Forest)|
|  - Tukey Interquartile Range (P25, FMV, P75) - Fama Arbitrage Opportunity Scanner |
|  - Regional Price Disparity Multiplier (BBN-KB & Inter-Island Freight Logistics)  |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|             5. ENTERPRISE STREAMLIT USER INTERFACE & REST API                     |
|  - 3-Tier Price Corridor Charts              - Dealer Gross & Net Margin Radar    |
|  - Interactive 4-Point Inspection Lots       - PDF Car Valuation Appraisal Report |
|  - Residual Value Forecast Curve (10 Years)  - FastAPI Endpoints (/api/v1/...)    |
+-----------------------------------------------------------------------------------+
```

---

# BAB III: Definisi Kamus Data & Parameter Lengkap

### 3.1 Tabel Listing Retail Pasar (`scraped_listings`)

| Nama Kolom | Tipe Data | Definisi & Fungsi Bisnis |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Primary key unik database |
| `source_platform` | String (50) | Marketplace sumber ekstraksi (`olx`, `mobil123`, `carmudi`, `carsome`) |
| `title` | String (300) | Judul listing setelah dibersihkan dari karakter noise |
| `price` | Numeric (15,2) | Harga transaksi tunai tervalidasi (IDR) |
| `is_dp_price` | Boolean | True jika terdeteksi sebagai DP/uang muka kredit semu |
| `transmission` | String (30) | `Automatic` (CVT, AT, e-CVT, DCT) vs `Manual` |
| `fuel_type` | String (30) | `Bensin`, `Diesel`, `Hybrid`, `Listrik` |
| `odometer_km` | Integer | Total jarak tempuh kendaraan (km) |
| `flood_free` | Boolean | Klaim jaminan bebas banjir 100% |
| `accident_free` | Boolean | Klaim jaminan bebas benturan rangka sasis |
| `service_record` | Boolean | Catatan servis berkala di bengkel resmi |
| `tax_status` | String (50) | `Hidup / Panjang` vs `Mati / Off` |
| `has_bpkb` | Boolean | Legalitas kepemilikan mutlak BPKB |

### 3.2 Tabel Lot Lelang Resmi (`auction_listings`)

| Nama Kolom | Tipe Data | Definisi & Fungsi Bisnis |
| :--- | :--- | :--- |
| `source_platform` | String (50) | `jba_indonesia` atau `ibid_astra` |
| `lot_number` | String (50) | Nomor lot resmi sesi lelang |
| `pool_city` | String (100) | Lokasi pool fisik kendaraan (Daan Mogot, Tipar Cakung, Surabaya, dsb) |
| `grade_exterior` | String (10) | Grade inspeksi fisik eksterior bodi (A/B/C/D) |
| `grade_interior` | String (10) | Grade inspeksi kebersihan & kelengkapan kabin (A/B/C/D) |
| `grade_engine` | String (10) | Grade kesehatan mekanikal & kebocoran oli mesin (A/B/C/D) |
| `grade_frame_body` | String (10) | Grade integritas struktur sasis (A = Bebas Potong Sambung) |
| `base_limit_price` | Numeric (15,2) | Harga dasar pembukaan lelang (Clearance Floor) |
| `hammer_price` | Numeric (15,2) | Harga ketok palu final terbentuk |
| `admin_fee` | Numeric (15,2) | Biaya administrasi lelang mobil (standar Rp 2.500.000) |

---

# BAB IV: Logika Ekonometrika, Model Analitik & Landasan Teori Ahli

### 4.1 Teori Pasar Barang Bekas & Model Depresiasi (George Akerlof 1970)
Kendaraan mengalami penurunan nilai terbesar di tahun pertama akibat *information asymmetry discount*. Formulasi depresiasi mobil di CarPrice ID:

$$\text{Depresiasi Kumulatif } D(t) = 1.0 - \left[0.165 \times (1 - e^{-0.40 t}) + 0.058 t\right]$$

### 4.2 Model Penyesuaian Kualitas Hedonik (Lancaster 1966 & Rosen 1974)
Harga sebuah mobil bekas diuraikan atas nilai utilitas marjinal dari tiap fitur:

$$\text{FMV}_{\text{Mobil}} = \left(\text{Base}_{\text{MSRP}} \times D(t) \times F_{\text{BBM}} \times F_{\text{Trans}} \times F_{\text{Bodi}}\right) + \Delta_{\text{KM}} + \Delta_{\text{Pajak}} - \Delta_{\text{Banjir/Tabrak}} - \Delta_{\text{Legalitas}}$$

1. **Multiplier Bahan Bakar ($F_{\text{BBM}}$):**
   - Diesel Turbo (Innova 2GD/1GD, Pajero 4N15): $+4.5\%$ (Retensi nilai tertinggi)
   - Hybrid HEV: $+3.5\%$
   - Bensin Konvensional: $1.00$
   - Listrik Murni (EV): $-6.0\%$ (Penyesuaian siklus teknologi baterai)
2. **Multiplier Transmisi ($F_{\text{Trans}}$):**
   - Automatic / CVT: $1.00$ (Baseline likuiditas perkotaan)
   - Manual (MT): $-5.5\%$ (Disparitas minat pembeli)
3. **Penalti Kerusakan Sasis & Banjir:**
   - Riwayat Banjir: $-40\%$ penalti
   - Riwayat Tabrak Sasis: $-35\%$ penalti
4. **Penalti Non-BPKB:** $-40\%$ penalti

---

# BAB V: Taksonomi Master Katalog Mobil (2014–2026)

Katalog master mencakup 10 brand otomotif papan atas Indonesia:
1. **Toyota:** Avanza, Veloz, Kijang Innova Reborn, Innova Zenix (Gas & HEV), Fortuner (VRZ 2.4 & GR 2.8), Calya, Raize, Yaris Cross HEV.
2. **Honda:** Brio Satya & RS, HR-V (SE & RS Turbo), CR-V Turbo & e:HEV, BR-V Sensing, WR-V RS.
3. **Mitsubishi:** Xpander, Xpander Cross, Pajero Sport Dakar, Xforce Ultimate.
4. **Hyundai:** Creta Prime, Stargazer, Stargazer X, Ioniq 5 EV, Palisade Diesel.
5. **Wuling:** Air EV Long Range, Binguo EV, Almaz RS Pro & Hybrid.
6. **BYD:** Dolphin Superior, Atto 3, Seal AWD Performance.
7. **Daihatsu:** Sigra, All New Ayla, All New Terios, All New Xenia.
8. **Suzuki:** All New Ertiga Hybrid, XL7 Hybrid, Jimny 3-Door & 5-Door.
9. **BMW:** 320i Sport, 330i M Sport, X1 xLine.
10. **Mercedes-Benz:** C200 Avantgarde, C300 AMG Line, GLC 200 AMG Line.

---

# BAB VI: Panduan Operasional & API Service

### Menjalankan Streamlit Dashboard:
```bash
streamlit run app.py
```

### Menjalankan FastAPI REST Service:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
