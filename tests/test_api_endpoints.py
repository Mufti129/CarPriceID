import unittest
from fastapi.testclient import TestClient
from api.main import app

class TestCarPriceAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "OPERATIONAL")
        self.assertIn("ml_model_version", data)

    def test_catalog_brands(self):
        res = self.client.get("/api/v1/catalog/brands")
        self.assertEqual(res.status_code, 200)
        brands = res.json()
        self.assertGreater(len(brands), 0)
        self.assertIn("name", brands[0])

    def test_catalog_models(self):
        res = self.client.get("/api/v1/catalog/models")
        self.assertEqual(res.status_code, 200)
        models = res.json()
        self.assertGreater(len(models), 0)
        self.assertIn("name", models[0])

    def test_catalog_variants(self):
        res = self.client.get("/api/v1/catalog/variants")
        self.assertEqual(res.status_code, 200)
        variants = res.json()
        self.assertGreater(len(variants), 0)
        self.assertIn("variant_name", variants[0])

    def test_post_valuation_calculate(self):
        payload = {
            "variant_id": 1,
            "year": 2022,
            "odometer_km": 30000,
            "fuel_type": "Bensin",
            "transmission": "Automatic",
            "tax_status": "Pajak Hidup / Panjang",
            "has_bpkb": True,
            "is_flood_free": True,
            "is_accident_free": True,
            "region": "Jabodetabek (DKI Jakarta, Bogor, Depok, Tangerang, Bekasi)"
        }
        res = self.client.post("/api/v1/valuation/calculate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("valuation", data)
        self.assertIn("fair_market_value", data["valuation"])
        self.assertGreater(data["valuation"]["fair_market_value"], 0)
        self.assertIn("hedonic_factors", data)
        self.assertIn("residual_forecast_10y", data)

    def test_get_valuation(self):
        res = self.client.get("/api/v1/valuation?variant_id=1&year=2022&odometer_km=30000")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("valuation", data)

    def test_wholesale_corridor(self):
        res = self.client.get("/api/v1/wholesale/corridor/1/2022")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("base_limit_floor", data)
        self.assertIn("wholesale_hammer_price", data)
        self.assertIn("retail_fmv_median", data)

    def test_arbitrage_deals(self):
        res = self.client.get("/api/v1/arbitrage/deals?min_discount_pct=5&limit=10")
        self.assertEqual(res.status_code, 200)
        deals = res.json()
        self.assertIsInstance(deals, list)

    def test_regional_index(self):
        res = self.client.get("/api/v1/regions")
        self.assertEqual(res.status_code, 200)
        regions = res.json()
        self.assertEqual(len(regions), 8)

    def test_ibid_map_summary(self):
        res = self.client.get("/api/v1/wholesale/ibid-map/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "OPERATIONAL")
        self.assertIn("total_records", data)
        self.assertGreaterEqual(data["total_records"], 400)
        self.assertIn("synced_brands", data)

    def test_ibid_map_valuations(self):
        res = self.client.get("/api/v1/wholesale/ibid-map/valuations?brand=TOYOTA&limit=10")
        self.assertEqual(res.status_code, 200)
        items = res.json()
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)
        for item in items:
            if item.get("grade_a_price"):
                self.assertNotEqual(item["grade_a_price"], 592500000.0)

    def test_extract_unit_grade_prices_ignores_total_harga(self):
        from scrapers.ibid_map_scraper import _extract_unit_grade_prices
        sample_api_item = {
            "totalHarga": 869520000,
            "hargaTertinggi": "148500000",
            "hargaTerendah": "142700000",
            "grade": "A"
        }
        parsed = _extract_unit_grade_prices(sample_api_item)
        self.assertEqual(parsed["low"], 142700000.0)
        self.assertEqual(parsed["high"], 148500000.0)
        self.assertEqual(parsed["mid"], 145600000.0)

    def test_credit_simulation_endpoint(self):
        payload = {
            "otr_price": 300000000.0,
            "dp_pct": 25.0,
            "tenor_years": 4,
            "interest_rate_flat_pct": 9.35,
            "insurance_type": "Kombinasi (Thn 1 All-Risk + TLO)",
            "ojk_region": "Wilayah 2 (DKI Jakarta, Jawa Barat, Banten)",
            "payment_scheme": "ADDM (Angsuran Dibayar di Muka)"
        }
        res = self.client.post("/api/v1/valuation/credit-simulation", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["otr_price"], 300000000.0)
        self.assertEqual(data["pure_dp"], 75000000.0)
        self.assertEqual(data["principal_loan"], 225000000.0)
        self.assertGreater(data["monthly_installment"], 0)
        self.assertGreater(data["total_tdp"], data["pure_dp"])
        self.assertEqual(len(data["multi_tenor_comparison"]), 5)

    def test_reconditioning_estimate_endpoint(self):
        payload = {
            "base_fmv": 250000000.0,
            "selected_defect_keys": ["baret_bumper", "penyok_pintu_fender", "ac_kurang_dingin"]
        }
        res = self.client.post("/api/v1/valuation/reconditioning-estimate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["base_fmv"], 250000000.0)
        self.assertGreater(data["total_reconditioning_cost_idr"], 0)
        self.assertIn(data["overall_grade"], ["A", "B", "C", "D", "E"])
        self.assertLess(data["net_fmv_after_reconditioning"], 250000000.0)
        self.assertEqual(len(data["selected_defects"]), 3)

    def test_enterprise_auth_status_endpoint(self):
        res = self.client.get("/api/v1/enterprise/auth-status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("authenticated", data)
        self.assertIn("tier", data)
        self.assertIn("rate_limit_per_minute", data)

    def test_system_jobs_endpoint(self):
        res = self.client.get("/api/v1/system/jobs?limit=5")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("jobs", data)
        self.assertIsInstance(data["jobs"], list)

    def test_credit_simulator_logic(self):
        from analytics.credit_simulator import simulate_car_credit
        sim = simulate_car_credit(
            otr_price=200000000.0,
            dp_pct=20.0,
            tenor_years=3,
            payment_scheme="ADDB (Angsuran Dibayar di Belakang)"
        )
        self.assertEqual(sim["pure_dp"], 40000000.0)
        self.assertEqual(sim["principal_loan"], 160000000.0)
        self.assertEqual(len(sim["multi_tenor_comparison"]), 5)
        self.assertGreater(sim["total_tdp"], 40000000.0)

    def test_damage_vision_and_acv_scoring(self):
        from analytics.damage_vision import calculate_reconditioning_and_acv_grade
        eval_res = calculate_reconditioning_and_acv_grade(
            base_fmv=350000000.0,
            selected_defect_keys=["baret_bumper", "mika_lampu_kusam"]
        )
        self.assertEqual(eval_res["total_reconditioning_cost_idr"], 1400000.0)
        self.assertEqual(eval_res["overall_grade"], "A")
        self.assertEqual(eval_res["net_fmv_after_reconditioning"], 350000000.0 - 1400000.0)

    def test_scheduler_log_recording(self):
        from pipeline.scheduler import record_sync_job, get_recent_job_logs
        log_entry = record_sync_job(
            job_name="Automated Unit Test Job",
            trigger_source="PYTEST_RUNNER",
            status="SUCCESS",
            records_processed=99,
            duration_seconds=0.15,
            notes="Scheduler unit test verification"
        )
        self.assertEqual(log_entry["status"], "SUCCESS")
        self.assertEqual(log_entry["records_processed"], 99)

        recent = get_recent_job_logs(limit=5)
        self.assertGreater(len(recent), 0)
        self.assertEqual(recent[0]["trigger_source"], "PYTEST_RUNNER")

    def test_olx_scraper_feed_valid_urls(self):
        from scrapers.olx_car_scraper import OLXCarScraper
        scraper = OLXCarScraper()
        feed = scraper._generate_realistic_feed("Innova", "indonesia", 0)
        self.assertGreater(len(feed), 0)
        for item in feed:
            self.assertIn("https://www.olx.co.id/mobil-bekas_c198?q=", item["url"])

if __name__ == "__main__":
    unittest.main()

