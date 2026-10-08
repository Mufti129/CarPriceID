# CarPrice ID — Used Car Intelligence & Valuation Platform

**CarPrice ID** adalah platform kecerdasan pasar dan valuasi harga wajar mobil bekas Indonesia (*End-to-End Used Car Intelligence & Hedonic Valuation Engine*) yang dirancang khusus untuk ekosistem pasar kendaraan roda empat di Indonesia.

---

## Fitur Utama Sistem

1. **Market Overview & Macro Analytics:** Distribusi volume pasar per brand, bahan bakar (Bensin, Diesel, Hybrid, EV), transmisi, histogram harga, dan sebaran regional.
2. **Fair Market Value (FMV) Calculator:** Mesin valuasi berbasis Machine Learning Hedonic Regression Versi 7 ($R^2 = 0.9542$, $\text{MAPE} = 3.94\%$) dilengkapi kurva proyeksi nilai sisa 10 tahun dan ekspor **Sertifikat Valuasi PDF Resmi**.
3. **3-Tier Price Corridors & Monitoring:** Visualisasi 3 tingkatan harga (Tier 1 Floor Lelang -> Tier 2 Hammer Lelang -> Tier 3 FMV Retail) serta analisis gross margin & net profit showroom dealer.
4. **Bargain & Arbitrage Scanner:** Algoritma pemindai listing retail murah dengan potensi selisih keuntungan perputaran unit cepat.
5. **Wholesale & Auction Intelligence:** Integrasi data balai lelang resmi (JBA Indonesia & IBID Astra) lengkap dengan inspeksi teknis 4-titik (Eksterior, Interior, Mesin, Sasis).
6. **AI NLP & Scam Filter:** Pembersih harga DP/uang muka palsu dan pemetaan varian fuzzy (*Entity Resolution*).
7. **FastAPI REST Endpoints:** Siap diintegrasikan ke mobile app atau sistem CRM dealer.

---

## Panduan Memulai

### 1. Instalasi Dependensi
```bash
pip install -r requirements.txt
```

### 2. Inisialisasi Database & Seeding
```bash
python main.py --seed
```

### 3. Menjalankan Dashboard Streamlit
```bash
streamlit run app.py
```

### 4. Menjalankan Unit Tests
```bash
python -m unittest tests/test_car_pipeline.py
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
