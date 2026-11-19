"""
AI Body Defect & Reconditioning Cost Estimator (Computer Vision & ACV 4-Point Physical Inspector)
Menganalisis foto eksterior kendaraan (edge anomaly & surface uniformity) serta matriks kerusakan panel/mekanis
untuk menghitung Skor Inspeksi ACV (Grade A-E), Rincian Biaya Rekondisi Bengkel (Rp), dan Koreksi Valuasi.
"""

import io
from typing import Dict, Any, List, Optional
import numpy as np

try:
    from PIL import Image
except ImportError:
    Image = None

# Matriks Standar Biaya Rekondisi Bengkel Body Repair & Mekanis Indonesia (IDR)
DEFECT_CATALOG: Dict[str, Dict[str, Any]] = {
    "baret_bumper": {
        "label": "Baret / Lecet Bumper Depan atau Belakang (Cat 1 Panel Oven)",
        "category": "Exterior",
        "cost_idr": 850_000.0,
        "penalty_pts": 4,
        "est_days": 1,
    },
    "penyok_pintu_fender": {
        "label": "Penyok Pintu / Fender Samping (Body Repair + Dempul + Cat Oven)",
        "category": "Exterior",
        "cost_idr": 1_450_000.0,
        "penalty_pts": 8,
        "est_days": 2,
    },
    "cat_belang_kap": {
        "label": "Cat Kusam / Belang Kap Mesin atau Atap (Repaint Polyurethane)",
        "category": "Exterior",
        "cost_idr": 1_800_000.0,
        "penalty_pts": 7,
        "est_days": 2,
    },
    "kaca_depan_retak": {
        "label": "Kaca Depan Retak / Baret Wiper Dalam (Ganti Kaca Laminated)",
        "category": "Exterior",
        "cost_idr": 2_200_000.0,
        "penalty_pts": 9,
        "est_days": 1,
    },
    "mika_lampu_kusam": {
        "label": "Mika Headlamp Menguning / Retak Rambut (Nano Burn / Rekondisi)",
        "category": "Exterior",
        "cost_idr": 550_000.0,
        "penalty_pts": 3,
        "est_days": 1,
    },
    "interior_kotor_jok": {
        "label": "Interior Kotor / Jok Retak (Full Salon Detailing & Retrim Ringan)",
        "category": "Interior",
        "cost_idr": 1_350_000.0,
        "penalty_pts": 6,
        "est_days": 2,
    },
    "ac_kurang_dingin": {
        "label": "AC Kurang Dingin / Bau Apek (Flushing Freon, Oli Kompresor & Filter)",
        "category": "Interior",
        "cost_idr": 950_000.0,
        "penalty_pts": 5,
        "est_days": 1,
    },
    "rembes_oli_mesin": {
        "label": "Rembes Oli Tutup Klep / Seal Kruk As (Ganti Gasket & Seal)",
        "category": "Engine",
        "cost_idr": 1_250_000.0,
        "penalty_pts": 8,
        "est_days": 1,
    },
    "kaki_kaki_bunyi": {
        "label": "Kaki-Kaki Bunyi / Limbung (Tie Rod, Link Stabil, Bushing Arm)",
        "category": "Engine",
        "cost_idr": 2_100_000.0,
        "penalty_pts": 9,
        "est_days": 1,
    },
    "ban_aus_2pcs": {
        "label": "Ban Aus di Bawah 40% (Penggantian 2 Ban Baru + Spooring Balancing)",
        "category": "Engine",
        "cost_idr": 1_900_000.0,
        "penalty_pts": 5,
        "est_days": 1,
    },
    "servis_besar_fluida": {
        "label": "Perlu Servis Besar (Oli Mesin, Oli Matik/CVT, Busi, Filter, Rem)",
        "category": "Engine",
        "cost_idr": 1_750_000.0,
        "penalty_pts": 4,
        "est_days": 1,
    },
    "bekas_tabrak_apron": {
        "label": "Bekas Tabrak Apron / Bullhead Depan (Perbaikan Struktur Rangka)",
        "category": "Frame",
        "cost_idr": 6_500_000.0,
        "penalty_pts": 25,
        "est_days": 5,
    },
    "indikasi_banjir": {
        "label": "Indikasi Bekas Banjir / Karat Kolong Kabin (Overhaul Kelistrikan)",
        "category": "Frame",
        "cost_idr": 9_500_000.0,
        "penalty_pts": 35,
        "est_days": 7,
    },
}


def analyze_vehicle_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
    """
    Menganalisis citra foto mobil menggunakan ekstraksi fitur komputer vision
    (Sobel/gradient edge density, luminance contrast, dan color channel variance)
    untuk mendeteksi indikasi anomali permukaan bodi.
    """
    if not Image or not image_bytes:
        return {
            "image_analyzed": False,
            "surface_smoothness_score": 88.0,
            "paint_uniformity_score": 86.0,
            "edge_anomaly_index": 0.12,
            "suggested_defects": ["baret_bumper"],
            "vision_summary": "Mode standar matriks teknis (tanpa foto).",
        }

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_resized = img.resize((256, 256))
        arr = np.asarray(img_resized, dtype=np.float32)

        # Hitung luminansi & gradien tepi (edge roughness)
        gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        gx = np.abs(np.diff(gray, axis=1))
        gy = np.abs(np.diff(gray, axis=0))
        edge_mean = float((np.mean(gx) + np.mean(gy)) / 2.0)
        edge_anomaly = round(min(1.0, max(0.05, edge_mean / 35.0)), 3)

        # Hitung keseragaman warna cat pada ROI tengah (bodi kendaraan)
        center_roi = arr[64:192, 64:192, :]
        color_std = float(np.mean(np.std(center_roi, axis=(0, 1))))
        paint_uniformity = round(max(55.0, min(98.0, 100.0 - (color_std * 0.45))), 1)
        smoothness = round(max(50.0, min(98.0, 100.0 - (edge_anomaly * 42.0))), 1)

        suggested = []
        if smoothness < 78.0:
            suggested.append("baret_bumper")
        if smoothness < 68.0:
            suggested.append("penyok_pintu_fender")
        if paint_uniformity < 74.0:
            suggested.append("cat_belang_kap")

        return {
            "image_analyzed": True,
            "resolution": f"{img.width}x{img.height}",
            "surface_smoothness_score": smoothness,
            "paint_uniformity_score": paint_uniformity,
            "edge_anomaly_index": edge_anomaly,
            "suggested_defects": suggested,
            "vision_summary": (
                f"Skor Kehalusan Panel: {smoothness}/100 | "
                f"Keseragaman Cat: {paint_uniformity}/100 | "
                f"Indeks Anomali Tepi: {edge_anomaly}"
            ),
        }
    except Exception as e:
        return {
            "image_analyzed": False,
            "surface_smoothness_score": 85.0,
            "paint_uniformity_score": 85.0,
            "edge_anomaly_index": 0.15,
            "suggested_defects": [],
            "vision_summary": f"Fallback analisis citra: {str(e)}",
        }


def _score_to_letter_grade(score: float) -> str:
    if score >= 88:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 45:
        return "D"
    return "E"


def calculate_reconditioning_and_acv_grade(
    base_fmv: float,
    selected_defect_keys: List[str],
    image_bytes: Optional[bytes] = None,
) -> Dict[str, Any]:
    """
    Menghitung rincian biaya perbaikan rekondisi, skor inspeksi 4-titik ACV (Eksterior, Interior, Mesin, Rangka),
    dan nilai wajar bersih setelah dikurangi biaya perbaikan serta penalti struktur.
    """
    vision_report = analyze_vehicle_image_bytes(image_bytes) if image_bytes else None

    active_keys = list(dict.fromkeys(selected_defect_keys or []))
    if vision_report and vision_report.get("image_analyzed"):
        for s_key in vision_report.get("suggested_defects", []):
            if s_key not in active_keys:
                active_keys.append(s_key)

    cat_penalties = {"Exterior": 0, "Interior": 0, "Engine": 0, "Frame": 0}
    itemized_repairs: List[Dict[str, Any]] = []
    total_repair_cost = 0.0
    total_days = 0

    for k in active_keys:
        d = DEFECT_CATALOG.get(k)
        if not d:
            continue
        cat = d["category"]
        cat_penalties[cat] = cat_penalties.get(cat, 0) + d["penalty_pts"]
        total_repair_cost += d["cost_idr"]
        total_days = max(total_days, d["est_days"]) + (1 if d["est_days"] > 1 else 0)
        itemized_repairs.append({
            "defect_key": k,
            "label": d["label"],
            "name": d["label"],
            "category": cat,
            "cost_idr": d["cost_idr"],
            "penalty_pts": d["penalty_pts"],
            "est_days": d["est_days"],
        })

    ext_score = max(35.0, 96.0 - (cat_penalties["Exterior"] * 1.8))
    int_score = max(40.0, 95.0 - (cat_penalties["Interior"] * 2.2))
    eng_score = max(35.0, 96.0 - (cat_penalties["Engine"] * 1.9))
    frm_score = max(25.0, 98.0 - (cat_penalties["Frame"] * 2.0))

    overall_score = round(
        (ext_score * 0.25) + (int_score * 0.15) + (eng_score * 0.30) + (frm_score * 0.30),
        1,
    )

    grade_ext = _score_to_letter_grade(ext_score)
    grade_int = _score_to_letter_grade(int_score)
    grade_eng = _score_to_letter_grade(eng_score)
    grade_frm = _score_to_letter_grade(frm_score)
    overall_grade = _score_to_letter_grade(overall_score)

    # Penalti depresiasi struktural jika rangka/banjir bermasalah
    structural_depreciation_idr = 0.0
    if "indikasi_banjir" in active_keys:
        structural_depreciation_idr += base_fmv * 0.18
    if "bekas_tabrak_apron" in active_keys:
        structural_depreciation_idr += base_fmv * 0.12

    adjusted_fmv = max(base_fmv * 0.40, base_fmv - total_repair_cost - structural_depreciation_idr)
    recommended_dealer_buy = round(adjusted_fmv * 0.86, -5)
    workshop_days = max(1, total_days) if itemized_repairs else 0
    decision_text = (
        "Unit Layak Beli (Kondisi Prima & Sangat Terawat)"
        if overall_score >= 85
        else (
            "Perlu Negosiasi Potongan Biaya Rekondisi Bengkel"
            if overall_score >= 65
            else "Unit Risiko Tinggi (Lakukan Inspeksi Rangka/Kolong Ulang)"
        )
    )

    return {
        "base_fmv": base_fmv,
        "overall_acv_grade": f"Grade {overall_grade}",
        "overall_acv_score": overall_score,
        "overall_grade": overall_grade,
        "overall_score": overall_score,
        "grades_4point": {
            "exterior": grade_ext,
            "interior": grade_int,
            "engine": grade_eng,
            "frame_chassis": grade_frm,
        },
        "scores_4point": {
            "exterior": round(ext_score, 1),
            "interior": round(int_score, 1),
            "engine": round(eng_score, 1),
            "frame_chassis": round(frm_score, 1),
        },
        "category_scores": {
            "Exterior": {"score": round(ext_score, 1), "grade": grade_ext},
            "Interior": {"score": round(int_score, 1), "grade": grade_int},
            "Engine": {"score": round(eng_score, 1), "grade": grade_eng},
            "Frame": {"score": round(frm_score, 1), "grade": grade_frm},
        },
        "defect_count": len(itemized_repairs),
        "itemized_repairs": itemized_repairs,
        "selected_defects": itemized_repairs,
        "total_reconditioning_cost_idr": round(total_repair_cost, 0),
        "total_workshop_days": workshop_days,
        "structural_depreciation_idr": round(structural_depreciation_idr, 0),
        "adjusted_net_fmv_idr": round(adjusted_fmv, -4),
        "net_fmv_after_reconditioning": round(adjusted_fmv, -4),
        "recommended_dealer_buy_price_idr": recommended_dealer_buy,
        "estimated_workshop_days": workshop_days,
        "decision_recommendation": decision_text,
        "action_recommendation": decision_text,
        "vision_analysis": vision_report,
    }
