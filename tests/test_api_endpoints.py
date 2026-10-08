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

if __name__ == "__main__":
    unittest.main()
