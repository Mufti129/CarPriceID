import unittest
from pipeline.normalizer import ListingNormalizer
from pipeline.scam_detector import ScamAndDPDetector
from pipeline.entity_matcher import EntityMatcher
from analytics.ml_car_valuation import ml_car_model_v7
from analytics.regional_index import apply_regional_pricing, get_region_multiplier
from models.database import SessionLocal, init_db
from data.seed_master_cars import seed_master_car_database

class TestCarPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_master_car_database()

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_listing_normalizer_price_parsing(self):
        self.assertEqual(ListingNormalizer.parse_price("Rp 235.000.000"), 235000000.0)
        self.assertEqual(ListingNormalizer.parse_price("235 jt"), 235000000.0)
        self.assertEqual(ListingNormalizer.parse_price("1.2 M"), 1200000000.0)
        self.assertEqual(ListingNormalizer.parse_price("85.5jt"), 85500000.0)
        self.assertEqual(ListingNormalizer.parse_price(185000000), 185000000.0)

    def test_listing_normalizer_year_extraction(self):
        self.assertEqual(ListingNormalizer.extract_year("Toyota Innova Reborn 2021 Diesel"), 2021)
        self.assertEqual(ListingNormalizer.extract_year("Honda Brio 2019 E CVT"), 2019)
        self.assertIsNone(ListingNormalizer.extract_year("Mobilio tanpa tahun"))

    def test_listing_normalizer_transmission_extraction(self):
        self.assertEqual(ListingNormalizer.extract_transmission("Innova Reborn 2.4 V AT Diesel"), "Automatic")
        self.assertEqual(ListingNormalizer.extract_transmission("Veloz 1.5 Q CVT TSS"), "Automatic")
        self.assertEqual(ListingNormalizer.extract_transmission("Avanza 1.3 G Manual 2018"), "Manual")

    def test_listing_normalizer_fuel_extraction(self):
        self.assertEqual(ListingNormalizer.extract_fuel_type("Innova Reborn 2.4 V AT Diesel"), "Diesel")
        self.assertEqual(ListingNormalizer.extract_fuel_type("Zenix Q Hybrid Modellista"), "Hybrid")
        self.assertEqual(ListingNormalizer.extract_fuel_type("Ioniq 5 Signature EV Long Range"), "Listrik")
        self.assertEqual(ListingNormalizer.extract_fuel_type("Avanza 1.5 G Bensin"), "Bensin")

    def test_listing_normalizer_tax_status(self):
        status_hidup, _ = ListingNormalizer.extract_tax_status("Pajak hidup panjang sampai 2027")
        self.assertEqual(status_hidup, "Hidup / Panjang")

        status_mati, years = ListingNormalizer.extract_tax_status("Pajak off 2 tahun kaleng 2026")
        self.assertEqual(status_mati, "Mati / Off")
        self.assertEqual(years, 2)

    def test_scam_and_dp_detector(self):
        # DP Scam: Innova 2022 harga 25jt
        self.assertTrue(ScamAndDPDetector.is_dp_or_scam(
            price=25000000,
            title="TDP 25jt Innova Reborn 2022",
            claimed_year=2022,
            msrp_new=420000000
        ))

        # Valid Cash Price: Avanza 2018 harga 155jt
        self.assertFalse(ScamAndDPDetector.is_dp_or_scam(
            price=155000000,
            title="Avanza 1.3 G AT 2018 Mulus",
            claimed_year=2018,
            msrp_new=229000000
        ))

    def test_entity_matcher(self):
        matcher = EntityMatcher(self.db, min_match_score=60.0)
        match, score = matcher.match_listing(
            title="Toyota Kijang Innova Reborn 2.4 V Diesel AT 2021",
            claimed_year=2021
        )
        self.assertIsNotNone(match)
        self.assertEqual(match["brand_name"], "Toyota")
        self.assertIn("Innova", match["model_name"])
        self.assertGreaterEqual(score, 60.0)

    def test_ml_car_valuation_model(self):
        eval_res = ml_car_model_v7.predict_valuation(
            msrp_new=425000000,
            claimed_year=2022,
            odometer_km=48000,
            engine_cc=2000,
            fuel_type="Diesel",
            transmission="Automatic",
            current_year=2026
        )
        self.assertIn("predicted_fmv", eval_res)
        self.assertGreater(eval_res["predicted_fmv"], 0)
        self.assertLess(eval_res["predicted_fmv"], 425000000)
        self.assertGreater(eval_res["real_depreciation_pct"], 0)

    def test_residual_forecast_curve(self):
        curve = ml_car_model_v7.generate_residual_forecast_curve(
            current_fmv=300000000.0,
            fuel_type="Bensin",
            body_category="MPV",
            current_year=2026,
            car_production_year=2022
        )
        self.assertEqual(len(curve), 11) # Baseline + 10 Years
        self.assertEqual(curve[0]["projected_fmv"], 300000000.0)
        # Verify strictly decreasing price over time
        for i in range(len(curve) - 1):
            self.assertGreater(
                curve[i]["projected_fmv"],
                curve[i+1]["projected_fmv"],
                f"Tahun {curve[i]['horizon_label']} ({curve[i]['projected_fmv']}) harus lebih besar dari {curve[i+1]['horizon_label']} ({curve[i+1]['projected_fmv']})"
            )

    def test_regional_pricing(self):
        jabo_mult = get_region_multiplier("Jabodetabek (DKI Jakarta, Bogor, Depok, Tangerang, Bekasi)")
        self.assertEqual(jabo_mult, 1.000)

        sumatera_mult = get_region_multiplier("Sumatera (Medan, Palembang, Pekanbaru, Lampung, Padang, Batam)")
        self.assertGreater(sumatera_mult, 1.000)

        reg_calc = apply_regional_pricing(200000000, "Sumatera (Medan, Palembang, Pekanbaru, Lampung, Padang, Batam)")
        self.assertGreater(reg_calc["regional_fmv"], 200000000)

if __name__ == "__main__":
    unittest.main()

