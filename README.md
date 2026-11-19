# CarPrice ID — Used Car Intelligence & Valuation Platform

**CarPrice ID** adalah platform kecerdasan pasar dan valuasi harga wajar mobil bekas Indonesia (*End-to-End Used Car Intelligence & Hedonic Valuation Engine*) yang dirancang khusus untuk ekosistem pasar kendaraan roda empat di Indonesia.

---

## Fitur Utama Sistem

1. **Market Overview & Macro Analytics:** Distribusi volume pasar per brand, bahan bakar (Bensin, Diesel, Hybrid, EV), transmisi, histogram harga, dan sebaran regional.
2. **Fair Market Value (FMV) Calculator:** Mesin valuasi berbasis Machine Learning Hedonic Regression Versi 7 ($R^2 = 0.9542$, $\text{MAPE} = 3.94\%$) dilengkapi kurva proyeksi nilai sisa 10 tahun dan ekspor **Sertifikat Valuasi PDF Resmi**.
3. **3-Tier Price Corridors & Monitoring:** Visualisasi 3 tingkatan harga (Tier 1 Floor Lelang -> Tier 2 Hammer Lelang -> Tier 3 FMV Retail) serta analisis gross margin & net profit showroom dealer.
4. **Bargain & Arbitrage Scanner:** Algoritma pemindai listing retail murah dengan potensi selisih keuntungan perputaran unit cepat.
5. **Wholesale & Auction Intelligence (JBA & IBID Astra MAP):** Integrasi langsung ke dual-host REST API resmi **IBID Astra MAP (`map.ibid.astra.co.id`)** mencakup 26 merek mobil, valuasi multi-tahun, dan rincian harga per unit berdasarkan inspeksi teknis 4-titik ACV (Grade A, B, C, D) yang disinkronkan berkala ke database lokal `mobil_bekas.db` (`ibid_map_valuations`).
6. **AI NLP & Scam Filter:** Pembersih harga DP/uang muka palsu dan pemetaan varian fuzzy (*Entity Resolution*).
7. **Enterprise B2B FastAPI REST Endpoints (13 Endpoints):** Siap diintegrasikan ke mobile app, sistem multifinance, atau CRM dealer.

---

## Panduan Memulai

### 1. Instalasi Dependensi
```bash
pip install -r requirements.txt
```

### 2. Inisialisasi Database & Sinkronisasi IBID Astra MAP
```bash
python main.py --seed
python -m data.sync_ibid_map_data --brands 26 --delay 0.05
```

### 3. Menjalankan Dashboard Streamlit & REST API
```bash
streamlit run app.py
uvicorn api.main:app --reload --port 8000
```

### 4. Menjalankan Seluruh Unit Tests (21 Test Cases)
```bash
PYTHONPATH=. python -m unittest discover tests
```

---

## Struktur Repositori

```text
├── models/               # SQLAlchemy Models (Master Brands, Models, Variants, Listings, Lots)
├── pipeline/             # NLP Normalizer, Slang Dictionary, Scam Detector, Entity Matcher
├── analytics/            # ML Valuation V7, 3-Tier Pricing Engine, Regional Index, PDF Certificate
├── scrapers/             # OLX Mobil Scraper (Cat ID 198), Car Auction Harvester, Batch Ingestion
├── data/                 # Seeder Master Catalog (2014-2026), Auction Lots, Market Generator
├── api/                  # FastAPI REST API Endpoints
├── tests/                # Automated Unit Test Suite
├── app.py                # Enterprise Streamlit UI Platform
├── main.py               # CLI Orchestrator
├── requirements.txt      # Dependency Requirements
└── DOKUMENTASI_SISTEM_LENGKAP.md # Spesifikasi Teknis Lengkap
```
