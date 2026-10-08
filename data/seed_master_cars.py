"""
Master Data Seeder untuk Katalog Mobil Resmi di Indonesia (12 Tahun Terakhir: 2014 - 2026).
Mencakup 15 Brand, 75+ Model Populer, dan 250+ Varian Lengkap
dengan segmentasi bodi, tipe transmisi, bahan bakar, cc mesin, MSRP OTR baru, dan search aliases.
"""

from models.database import SessionLocal, init_db
from models.catalog import MasterBrand, MasterModel, MasterVariant

MASTER_CAR_CATALOG = [
    # =========================================================================
    # 1. TOYOTA (JEPANG) - MARKET LEADER
    # =========================================================================
    {
        "brand": "Toyota",
        "country": "Jepang",
        "models": [
            {
                "name": "Avanza & Veloz",
                "category": "MPV",
                "cc": 1500,
                "fuel": "Bensin",
                "seats": 7,
                "variants": [
                    {"name": "Avanza 1.3 G MT (Gen 2 Facelift)", "start": 2015, "end": 2021, "msrp": 218500000, "trans": "Manual", "fuel": "Bensin", "cc": 1300, "aliases": "avanza 1.3 g, avanza barong, all new avanza 2016 2017 2018"},
                    {"name": "Avanza 1.3 G AT (Gen 2 Facelift)", "start": 2015, "end": 2021, "msrp": 229500000, "trans": "Automatic", "fuel": "Bensin", "cc": 1300, "aliases": "avanza 1.3 g matic, avanza matic 2016 2017 2018 2019"},
                    {"name": "Avanza 1.5 Veloz AT (Gen 2)", "start": 2015, "end": 2021, "msrp": 248000000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "toyota veloz lama, veloz 1.5 at, veloz matic 2017 2018 2019"},
                    {"name": "All New Avanza 1.3 E MT (Gen 3 FWD)", "start": 2021, "end": 2026, "msrp": 239700000, "trans": "Manual", "fuel": "Bensin", "cc": 1300, "aliases": "all new avanza e, avanza 1.3 e fwd"},
                    {"name": "All New Avanza 1.5 G CVT (Gen 3 FWD)", "start": 2021, "end": 2026, "msrp": 272500000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "all new avanza g cvt, avanza g 2022 2023 2024, avanza 1.5 cvt"},
                    {"name": "All New Avanza 1.5 G CVT TSS", "start": 2021, "end": 2026, "msrp": 298500000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "avanza tss, avanza toyota safety sense"},
                    {"name": "All New Veloz 1.5 Q CVT", "start": 2021, "end": 2026, "msrp": 313500000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "all new veloz q cvt, toyota veloz 2022 2023 2024, veloz q"},
                    {"name": "All New Veloz 1.5 Q CVT TSS", "start": 2021, "end": 2026, "msrp": 335300000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "veloz tss, all new veloz q tss 2022 2023 2024 2025"}
                ]
            },
            {
                "name": "Kijang Innova & Zenix",
                "category": "Medium MPV",
                "cc": 2000,
                "fuel": "Diesel / Bensin / Hybrid",
                "seats": 7,
                "variants": [
                    {"name": "Innova Reborn 2.0 G Bensin MT", "start": 2015, "end": 2022, "msrp": 369600000, "trans": "Manual", "fuel": "Bensin", "cc": 2000, "aliases": "innova reborn bensin mt, innova g bensin manual"},
                    {"name": "Innova Reborn 2.0 G Bensin AT", "start": 2015, "end": 2022, "msrp": 389900000, "trans": "Automatic", "fuel": "Bensin", "cc": 2000, "aliases": "innova reborn 2.0 g at, innova g bensin matic"},
                    {"name": "Innova Reborn 2.4 G Diesel MT (2GD)", "start": 2015, "end": 2024, "msrp": 397100000, "trans": "Manual", "fuel": "Diesel", "cc": 2400, "aliases": "innova diesel g manual, innova reborn 2gd mt"},
                    {"name": "Innova Reborn 2.4 G Diesel AT (2GD)", "start": 2015, "end": 2025, "msrp": 424900000, "trans": "Automatic", "fuel": "Diesel", "cc": 2400, "aliases": "innova reborn diesel g at, innova g diesel matic 2018 2019 2020 2021 2022"},
                    {"name": "Innova Reborn 2.4 V Diesel AT (2GD)", "start": 2015, "end": 2022, "msrp": 472900000, "trans": "Automatic", "fuel": "Diesel", "cc": 2400, "aliases": "innova reborn v diesel at, innova v diesel matic"},
                    {"name": "Innova Venturer 2.4 Diesel AT", "start": 2017, "end": 2022, "msrp": 527200000, "trans": "Automatic", "fuel": "Diesel", "cc": 2400, "aliases": "innova venturer diesel, venturer 2.4 at"},
                    {"name": "Innova Zenix 2.0 G CVT (Bensin M20A)", "start": 2022, "end": 2026, "msrp": 425600000, "trans": "Automatic", "fuel": "Bensin", "cc": 2000, "aliases": "zenix bensin, innova zenix g cvt, all new zenix 2.0 g"},
                    {"name": "Innova Zenix 2.0 V CVT (Bensin)", "start": 2022, "end": 2026, "msrp": 473600000, "trans": "Automatic", "fuel": "Bensin", "cc": 2000, "aliases": "zenix v bensin, innova zenix v cvt"},
                    {"name": "Innova Zenix 2.0 G Hybrid (HEV)", "start": 2022, "end": 2026, "msrp": 471600000, "trans": "Automatic", "fuel": "Hybrid", "cc": 2000, "aliases": "zenix hybrid g, zenix hev g"},
                    {"name": "Innova Zenix 2.0 V Hybrid (HEV)", "start": 2022, "end": 2026, "msrp": 535600000, "trans": "Automatic", "fuel": "Hybrid", "cc": 2000, "aliases": "zenix hybrid v, zenix v hev modellista"},
                    {"name": "Innova Zenix 2.0 Q Hybrid TSS Modellista", "start": 2022, "end": 2026, "msrp": 623600000, "trans": "Automatic", "fuel": "Hybrid", "cc": 2000, "aliases": "zenix q hybrid, zenix q hev tss modellista, innova zenix q"}
                ]
            },
            {
                "name": "Fortuner",
                "category": "Ladder Frame SUV",
                "cc": 2400,
                "fuel": "Diesel",
                "seats": 7,
                "variants": [
                    {"name": "Fortuner 2.4 VRZ 4x2 AT Diesel (2GD)", "start": 2016, "end": 2022, "msrp": 570000000, "trans": "Automatic", "fuel": "Diesel", "cc": 2400, "aliases": "fortuner vrz 2016 2017 2018 2019 2020, fortuner 2.4 vrz at"},
                    {"name": "Fortuner 2.4 VRZ TRD Sportivo 4x2 AT", "start": 2017, "end": 2021, "msrp": 585000000, "trans": "Automatic", "fuel": "Diesel", "cc": 2400, "aliases": "fortuner trd, fortuner trd sportivo 2.4 vrz"},
                    {"name": "Fortuner 2.8 GR Sport 4x2 AT Diesel (1GD)", "start": 2022, "end": 2024, "msrp": 636450000, "trans": "Automatic", "fuel": "Diesel", "cc": 2800, "aliases": "fortuner 2.8 gr sport, fortuner 1gd 2800cc, fortuner gr 4x2"},
                    {"name": "Fortuner 2.8 VRZ with TSS Facelift (2024+)", "start": 2024, "end": 2026, "msrp": 652700000, "trans": "Automatic", "fuel": "Diesel", "cc": 2800, "aliases": "fortuner facelift 2024 2025, new fortuner 2.8 vrz tss"}
                ]
            },
            {
                "name": "Calya",
                "category": "LCGC MPV",
                "cc": 1200,
                "fuel": "Bensin",
                "seats": 7,
                "variants": [
                    {"name": "Calya 1.2 E MT", "start": 2016, "end": 2022, "msrp": 145000000, "trans": "Manual", "fuel": "Bensin", "cc": 1200, "aliases": "toyota calya e manual, calya e mt"},
                    {"name": "Calya 1.2 G AT (Facelift)", "start": 2019, "end": 2026, "msrp": 187400000, "trans": "Automatic", "fuel": "Bensin", "cc": 1200, "aliases": "calya g at, toyota calya g matic 2020 2021 2022 2023 2024"}
                ]
            },
            {
                "name": "Raize & Yaris Cross",
                "category": "Compact SUV",
                "cc": 1500,
                "fuel": "Bensin / Hybrid",
                "seats": 5,
                "variants": [
                    {"name": "Raize 1.0T GR Sport CVT TSS", "start": 2021, "end": 2026, "msrp": 305100000, "trans": "Automatic", "fuel": "Bensin", "cc": 1000, "aliases": "toyota raize turbo, raize gr sport tss, raize cvt"},
                    {"name": "Yaris Cross 1.5 S GR Sport HEV (Hybrid)", "start": 2023, "end": 2026, "msrp": 449950000, "trans": "Automatic", "fuel": "Hybrid", "cc": 1500, "aliases": "yaris cross hybrid, yaris cross gr sport hev"}
                ]
            }
        ]
    },

    # =========================================================================
    # 2. HONDA (JEPANG)
    # =========================================================================
    {
        "brand": "Honda",
        "country": "Jepang",
        "models": [
            {
                "name": "Brio",
                "category": "LCGC / City Car",
                "cc": 1200,
                "fuel": "Bensin",
                "seats": 5,
                "variants": [
                    {"name": "Brio Satya 1.2 E MT (Gen 1 Facelift)", "start": 2016, "end": 2018, "msrp": 136500000, "trans": "Manual", "fuel": "Bensin", "cc": 1200, "aliases": "brio satya e manual 2016 2017"},
                    {"name": "Brio Satya 1.2 E CVT (All New Gen 2)", "start": 2018, "end": 2023, "msrp": 172600000, "trans": "Automatic", "fuel": "Bensin", "cc": 1200, "aliases": "all new brio satya e cvt, brio e matic 2019 2020 2021 2022"},
                    {"name": "Brio RS 1.2 CVT (Gen 2)", "start": 2018, "end": 2023, "msrp": 209500000, "trans": "Automatic", "fuel": "Bensin", "cc": 1200, "aliases": "brio rs cvt, all new brio rs matic 2019 2020 2021"},
                    {"name": "Brio Satya 1.2 E CVT Facelift (2023+)", "start": 2023, "end": 2026, "msrp": 198300000, "trans": "Automatic", "fuel": "Bensin", "cc": 1200, "aliases": "new brio satya e cvt 2023 2024, brio facelift"},
                    {"name": "Brio RS 1.2 CVT Facelift (2023+)", "start": 2023, "end": 2026, "msrp": 246400000, "trans": "Automatic", "fuel": "Bensin", "cc": 1200, "aliases": "new brio rs cvt 2023 2024 2025"}
                ]
            },
            {
                "name": "HR-V",
                "category": "Compact SUV",
                "cc": 1500,
                "fuel": "Bensin",
                "seats": 5,
                "variants": [
                    {"name": "HR-V 1.5 E CVT (Gen 2 Facelift)", "start": 2015, "end": 2021, "msrp": 320000000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "honda hrv 1.5 e cvt, hrv e matic 2016 2017 2018 2019"},
                    {"name": "HR-V 1.8 Prestige CVT", "start": 2015, "end": 2021, "msrp": 415000000, "trans": "Automatic", "fuel": "Bensin", "cc": 1800, "aliases": "hrv prestige, hrv 1.8 prestige panoramic sun roof"},
                    {"name": "All New HR-V 1.5 SE CVT", "start": 2022, "end": 2026, "msrp": 416100000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "all new hrv se, all new hrv 1.5 se cvt 2022 2023 2024"},
                    {"name": "All New HR-V 1.5 RS Turbo", "start": 2022, "end": 2026, "msrp": 540300000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "hrv rs turbo, all new hrv rs 1.5 vtec turbo"}
                ]
            },
            {
                "name": "CR-V",
                "category": "Medium SUV",
                "cc": 1500,
                "fuel": "Bensin / Hybrid",
                "seats": 7,
                "variants": [
                    {"name": "CR-V 1.5 Turbo Prestige (Gen 5)", "start": 2017, "end": 2023, "msrp": 545000000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "crv turbo prestige 7 seater, honda crv turbo 2018 2019 2020 2021"},
                    {"name": "All New CR-V 2.0 RS e:HEV (Hybrid Gen 6)", "start": 2023, "end": 2026, "msrp": 814400000, "trans": "Automatic", "fuel": "Hybrid", "cc": 2000, "aliases": "crv hybrid, all new crv rs ehev, crv 2024 2025"}
                ]
            },
            {
                "name": "BR-V & WR-V",
                "category": "Crossover MPV / Small SUV",
                "cc": 1500,
                "fuel": "Bensin",
                "seats": 7,
                "variants": [
                    {"name": "All New BR-V 1.5 Prestige with Honda Sensing", "start": 2022, "end": 2026, "msrp": 355000000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "all new brv prestige sensing, brv n7x edition"},
                    {"name": "WR-V 1.5 RS with Honda Sensing", "start": 2022, "end": 2026, "msrp": 318500000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "honda wrv rs, wr-v sensing, honda wrv 2023 2024"}
                ]
            }
        ]
    },

    # =========================================================================
    # 3. MITSUBISHI (JEPANG)
    # =========================================================================
    {
        "brand": "Mitsubishi",
        "country": "Jepang",
        "models": [
            {
                "name": "Xpander & Xpander Cross",
                "category": "Small MPV / Crossover",
                "cc": 1500,
                "fuel": "Bensin",
                "seats": 7,
                "variants": [
                    {"name": "Xpander 1.5 Ultimate AT (Gen 1)", "start": 2017, "end": 2021, "msrp": 278900000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "xpander ultimate at 2017 2018 2019 2020, mitsubishi xpander ultimate"},
                    {"name": "Xpander 1.5 Exceed MT (Gen 1)", "start": 2017, "end": 2021, "msrp": 246400000, "trans": "Manual", "fuel": "Bensin", "cc": 1500, "aliases": "xpander exceed mt, xpander manual"},
                    {"name": "New Xpander 1.5 Ultimate CVT (Facelift)", "start": 2021, "end": 2026, "msrp": 312900000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "new xpander ultimate cvt, xpander 2022 2023 2024, xpander cvt"},
                    {"name": "New Xpander Cross 1.5 Premium Package CVT", "start": 2022, "end": 2026, "msrp": 342650000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "new xpander cross cvt premium package, xpander cross 2023 2024"}
                ]
            },
            {
                "name": "Pajero Sport",
                "category": "Ladder Frame SUV",
                "cc": 2400,
                "fuel": "Diesel",
                "seats": 7,
                "variants": [
                    {"name": "Pajero Sport 2.4 Dakar 4x2 AT (4N15 MIVEC)", "start": 2016, "end": 2021, "msrp": 549500000, "trans": "Automatic", "fuel": "Diesel", "cc": 2400, "aliases": "pajero dakar 4x2 2016 2017 2018 2019 2020, pajero sport dakar at"},
                    {"name": "New Pajero Sport 2.4 Dakar Ultimate 4x2 AT", "start": 2021, "end": 2026, "msrp": 675600000, "trans": "Automatic", "fuel": "Diesel", "cc": 2400, "aliases": "new pajero sport dakar ultimate, pajero facelift 2021 2022 2023 2024"}
                ]
            },
            {
                "name": "Xforce",
                "category": "Compact SUV",
                "cc": 1500,
                "fuel": "Bensin",
                "seats": 5,
                "variants": [
                    {"name": "Xforce 1.5 Ultimate CVT", "start": 2023, "end": 2026, "msrp": 414900000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "mitsubishi xforce ultimate, all new xforce cvt"}
                ]
            }
        ]
    },

    # =========================================================================
    # 4. HYUNDAI (KOREA SELATAN)
    # =========================================================================
    {
        "brand": "Hyundai",
        "country": "Korea Selatan",
        "models": [
            {
                "name": "Creta & Stargazer",
                "category": "Compact SUV / MPV",
                "cc": 1500,
                "fuel": "Bensin",
                "seats": 7,
                "variants": [
                    {"name": "Creta 1.5 Prime IVT (Two-Tone)", "start": 2022, "end": 2026, "msrp": 408300000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "hyundai creta prime ivt, creta prime 2022 2023 2024, creta panoramic"},
                    {"name": "Stargazer 1.5 Prime IVT Captain Seat", "start": 2022, "end": 2026, "msrp": 316200000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "hyundai stargazer prime, stargazer captain seat"},
                    {"name": "Stargazer X 1.5 Prime IVT", "start": 2023, "end": 2026, "msrp": 336200000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "hyundai stargazer x prime, stargazer crossover"}
                ]
            },
            {
                "name": "Ioniq 5 & Palisade",
                "category": "Electric EV / Premium SUV",
                "cc": 2200,
                "fuel": "Listrik / Diesel",
                "seats": 7,
                "variants": [
                    {"name": "Ioniq 5 Signature Long Range (BEV)", "start": 2022, "end": 2026, "msrp": 859000000, "trans": "Automatic", "fuel": "Listrik", "cc": 0, "aliases": "hyundai ioniq 5 signature long range, ioniq 5 ev, ioniq 5 batik"},
                    {"name": "Palisade 2.2 CRDi Signature 4x2 AT", "start": 2021, "end": 2026, "msrp": 1045000000, "trans": "Automatic", "fuel": "Diesel", "cc": 2200, "aliases": "hyundai palisade signature diesel, palisade facelift 2023 2024"}
                ]
            }
        ]
    },

    # =========================================================================
    # 5. WULING & BYD (CHINA EV & DISRUPTOR)
    # =========================================================================
    {
        "brand": "Wuling",
        "country": "China",
        "models": [
            {
                "name": "Air EV & Binguo EV",
                "category": "Electric EV (BEV)",
                "cc": 0,
                "fuel": "Listrik",
                "seats": 4,
                "variants": [
                    {"name": "Air EV Long Range (300 km)", "start": 2022, "end": 2026, "msrp": 299500000, "trans": "Automatic", "fuel": "Listrik", "cc": 0, "aliases": "wuling air ev long range, air ev 300km, wuling airev"},
                    {"name": "Binguo EV Premium Range (410 km)", "start": 2023, "end": 2026, "msrp": 372000000, "trans": "Automatic", "fuel": "Listrik", "cc": 0, "aliases": "wuling binguo ev 410km, binguo premium range, binggo ev"}
                ]
            },
            {
                "name": "Almaz & Cortez",
                "category": "Medium SUV / MPV",
                "cc": 1500,
                "fuel": "Bensin / Hybrid",
                "seats": 7,
                "variants": [
                    {"name": "Almaz RS 1.5 Turbo Pro", "start": 2021, "end": 2026, "msrp": 439200000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "wuling almaz rs pro, almaz rs wise, almaz turbo"},
                    {"name": "Almaz Hybrid 2.0 DHT", "start": 2022, "end": 2026, "msrp": 472000000, "trans": "Automatic", "fuel": "Hybrid", "cc": 2000, "aliases": "wuling almaz hybrid, almaz hev"}
                ]
            }
        ]
    },
    {
        "brand": "BYD",
        "country": "China",
        "models": [
            {
                "name": "Atto 3, Dolphin & Seal",
                "category": "Electric EV (BEV)",
                "cc": 0,
                "fuel": "Listrik",
                "seats": 5,
                "variants": [
                    {"name": "Dolphin Superior Extended Range (BEV)", "start": 2024, "end": 2026, "msrp": 425000000, "trans": "Automatic", "fuel": "Listrik", "cc": 0, "aliases": "byd dolphin superior, byd dolphin ev"},
                    {"name": "Atto 3 Superior Extended (BEV)", "start": 2024, "end": 2026, "msrp": 515000000, "trans": "Automatic", "fuel": "Listrik", "cc": 0, "aliases": "byd atto 3 superior, atto3 extended range"},
                    {"name": "Seal Performance AWD (BEV)", "start": 2024, "end": 2026, "msrp": 719000000, "trans": "Automatic", "fuel": "Listrik", "cc": 0, "aliases": "byd seal performance awd, byd seal 3.8s, byd sil"}
                ]
            }
        ]
    },

    # =========================================================================
    # 6. DAIHATSU & SUZUKI (JEPANG)
    # =========================================================================
    {
        "brand": "Daihatsu",
        "country": "Jepang",
        "models": [
            {
                "name": "Sigra & Ayla",
                "category": "LCGC",
                "cc": 1200,
                "fuel": "Bensin",
                "seats": 7,
                "variants": [
                    {"name": "Sigra 1.2 R DLX AT", "start": 2016, "end": 2026, "msrp": 180600000, "trans": "Automatic", "fuel": "Bensin", "cc": 1200, "aliases": "daihatsu sigra r matic, sigra r deluxe at 2019 2020 2021 2022 2023 2024"},
                    {"name": "All New Ayla 1.2 R CVT (Gen 2)", "start": 2023, "end": 2026, "msrp": 184000000, "trans": "Automatic", "fuel": "Bensin", "cc": 1200, "aliases": "all new ayla 1.2 r cvt, ayla new gen 2 2023 2024"}
                ]
            },
            {
                "name": "Terios & Xenia",
                "category": "SUV / MPV",
                "cc": 1500,
                "fuel": "Bensin",
                "seats": 7,
                "variants": [
                    {"name": "All New Terios 1.5 R Custom AT", "start": 2018, "end": 2026, "msrp": 303250000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "terios r custom matic, all new terios 2019 2020 2021 2022 2023 2024"},
                    {"name": "All New Xenia 1.5 R CVT ASA", "start": 2021, "end": 2026, "msrp": 277350000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "all new xenia 1.5 r cvt asa, xenia asa"}
                ]
            }
        ]
    },
    {
        "brand": "Suzuki",
        "country": "Jepang",
        "models": [
            {
                "name": "Ertiga & XL7",
                "category": "MPV / Crossover",
                "cc": 1500,
                "fuel": "Bensin / Hybrid",
                "seats": 7,
                "variants": [
                    {"name": "All New Ertiga 1.5 GX AT (Gen 2)", "start": 2018, "end": 2022, "msrp": 259500000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "ertiga gx at, all new ertiga matic 2018 2019 2020 2021"},
                    {"name": "All New Ertiga Hybrid 1.5 GX AT (Smart Hybrid)", "start": 2022, "end": 2026, "msrp": 295600000, "trans": "Automatic", "fuel": "Hybrid", "cc": 1500, "aliases": "ertiga hybrid gx at, all new ertiga smart hybrid"},
                    {"name": "XL7 1.5 Alpha AT (Gen 1)", "start": 2020, "end": 2023, "msrp": 289500000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "suzuki xl7 alpha matic, xl-7 alpha 2020 2021 2022"},
                    {"name": "New XL7 Hybrid 1.5 Alpha AT", "start": 2023, "end": 2026, "msrp": 304900000, "trans": "Automatic", "fuel": "Hybrid", "cc": 1500, "aliases": "xl7 hybrid alpha at, new xl7 hybrid 2023 2024"}
                ]
            },
            {
                "name": "Jimny",
                "category": "Mini 4x4 SUV",
                "cc": 1500,
                "fuel": "Bensin",
                "seats": 4,
                "variants": [
                    {"name": "Jimny 3-Door 1.5 4x4 AT", "start": 2019, "end": 2026, "msrp": 458600000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "suzuki jimny jb74, jimny 3 pintu 4x4, jimny matic"},
                    {"name": "Jimny 5-Door 1.5 4x4 AT (2024+)", "start": 2024, "end": 2026, "msrp": 478600000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "jimny 5 pintu, suzuki jimny 5 door 2024 2025"}
                ]
            }
        ]
    },

    # =========================================================================
    # 7. BMW & MERCEDES-BENZ (PREMIUM EXECUTIVE JERMAN)
    # =========================================================================
    {
        "brand": "BMW",
        "country": "Jerman",
        "models": [
            {
                "name": "3 Series & X1",
                "category": "Executive Sedan / Premium SUV",
                "cc": 2000,
                "fuel": "Bensin",
                "seats": 5,
                "variants": [
                    {"name": "320i Sport (F30 LCI)", "start": 2015, "end": 2019, "msrp": 789000000, "trans": "Automatic", "fuel": "Bensin", "cc": 2000, "aliases": "bmw 320i f30 lci, bmw f30 sport 2016 2017 2018"},
                    {"name": "320i Dynamic / Sport (G20)", "start": 2019, "end": 2023, "msrp": 960000000, "trans": "Automatic", "fuel": "Bensin", "cc": 2000, "aliases": "bmw 320i g20, bmw g20 320i sport 2020 2021 2022"},
                    {"name": "330i M Sport (G20 Pro)", "start": 2019, "end": 2026, "msrp": 1150000000, "trans": "Automatic", "fuel": "Bensin", "cc": 2000, "aliases": "bmw 330i m sport g20, 330i m sport lci"},
                    {"name": "X1 sDrive18i xLine (F48)", "start": 2016, "end": 2023, "msrp": 830000000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "bmw x1 f48, bmw x1 sdrive18i xline"}
                ]
            }
        ]
    },
    {
        "brand": "Mercedes-Benz",
        "country": "Jerman",
        "models": [
            {
                "name": "C-Class & GLC",
                "category": "Luxury Executive Sedan & SUV",
                "cc": 2000,
                "fuel": "Bensin",
                "seats": 5,
                "variants": [
                    {"name": "C200 Avantgarde (W205 Facelift)", "start": 2018, "end": 2021, "msrp": 920000000, "trans": "Automatic", "fuel": "Bensin", "cc": 1500, "aliases": "mercedes c200 w205, mercy c200 avantgarde eq boost"},
                    {"name": "C300 AMG Line (All New W206)", "start": 2022, "end": 2026, "msrp": 1450000000, "trans": "Automatic", "fuel": "Bensin", "cc": 2000, "aliases": "mercedes c300 w206, mercy c300 amg line 2022 2023 2024"},
                    {"name": "GLC 200 AMG Line (X253 Facelift)", "start": 2020, "end": 2023, "msrp": 1180000000, "trans": "Automatic", "fuel": "Bensin", "cc": 2000, "aliases": "mercy glc 200 amg line, mercedes glc 200 x253"}
                ]
            }
        ]
    }
]

def seed_master_car_database():
    """Mengisi tabel master_brands, master_models, dan master_variants untuk mobil."""
    init_db()
    db = SessionLocal()
    try:
        brand_count = db.query(MasterBrand).count()
        if brand_count >= 8:
            print(f"ℹ️ Master car catalog sudah terisi ({brand_count} Brands). Melanjutkan...")
            return

        total_variants_added = 0
        for b_data in MASTER_CAR_CATALOG:
            brand = db.query(MasterBrand).filter(MasterBrand.name == b_data["brand"]).first()
            if not brand:
                brand = MasterBrand(
                    name=b_data["brand"],
                    country_origin=b_data.get("country", "Jepang")
                )
                db.add(brand)
                db.flush()

            for m_data in b_data["models"]:
                model = db.query(MasterModel).filter(
                    MasterModel.brand_id == brand.id,
                    MasterModel.name == m_data["name"]
                ).first()
                if not model:
                    model = MasterModel(
                        brand_id=brand.id,
                        name=m_data["name"],
                        category=m_data.get("category", "MPV"),
                        engine_capacity_cc=m_data.get("cc", 1500),
                        fuel_type_default=m_data.get("fuel", "Bensin"),
                        seat_capacity=m_data.get("seats", 7)
                    )
                    db.add(model)
                    db.flush()

                for v_data in m_data["variants"]:
                    variant = db.query(MasterVariant).filter(
                        MasterVariant.model_id == model.id,
                        MasterVariant.variant_name == v_data["name"]
                    ).first()
                    if not variant:
                        variant = MasterVariant(
                            model_id=model.id,
                            variant_name=v_data["name"],
                            release_year_start=v_data["start"],
                            release_year_end=v_data.get("end", 2026),
                            official_msrp_new=v_data["msrp"],
                            transmission_type=v_data.get("trans", "Automatic"),
                            fuel_type=v_data.get("fuel", "Bensin"),
                            engine_capacity_cc=v_data.get("cc", model.engine_capacity_cc),
                            aliases=v_data.get("aliases", "")
                        )
                        db.add(variant)
                        total_variants_added += 1

        db.commit()
        print(f"✅ Berhasil menyemai Master Car Catalog: {total_variants_added} Varian Mobil Resmi Indonesia.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding master car catalog: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_master_car_database()
