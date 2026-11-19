"""
Simulator Kredit Multifinance, Leasing & Asuransi Kendaraan Bermotor Indonesia
Mengacu pada Surat Edaran OJK (SEOJK Tarif Asuransi Kendaraan Bermotor Wilayah 1, 2, 3)
serta standar pembiayaan APPI (BCA Finance, Mandiri Utama Finance, ACC Astra, Adira Finance).
"""

from typing import Dict, Any, List

# Tarif Asuransi OJK Berdasarkan Kategori Harga & Wilayah (Persentase per Tahun)
OJK_ALL_RISK_RATES = {
    "Wilayah 1 (Sumatera & Kepulauan)": [3.82, 2.67, 2.18, 1.20, 1.05],
    "Wilayah 2 (DKI Jakarta, Jawa Barat, Banten)": [3.26, 2.47, 2.08, 1.20, 1.05],
    "Wilayah 3 (Jawa Tengah, Jatim, Bali, Kalimantan, Sulawesi)": [2.53, 2.69, 1.79, 1.14, 1.05],
}

OJK_TLO_RATES = {
    "Wilayah 1 (Sumatera & Kepulauan)": [0.47, 0.63, 0.41, 0.25, 0.20],
    "Wilayah 2 (DKI Jakarta, Jawa Barat, Banten)": [0.44, 0.56, 0.38, 0.25, 0.20],
    "Wilayah 3 (Jawa Tengah, Jatim, Bali, Kalimantan, Sulawesi)": [0.51, 0.44, 0.29, 0.23, 0.20],
}

# Suku Bunga Flat Tahunan Standar Multifinance Mobil Bekas per Tenor (Tahun 1 s/d 5)
DEFAULT_MULTIFINANCE_FLAT_RATES = {
    1: 7.75,
    2: 8.25,
    3: 8.75,
    4: 9.35,
    5: 9.95,
}


def get_ojk_price_category_index(car_price: float) -> int:
    """Menentukan indeks kategori harga OJK (0 s/d 4)."""
    if car_price <= 125_000_000:
        return 0
    elif car_price <= 200_000_000:
        return 1
    elif car_price <= 400_000_000:
        return 2
    elif car_price <= 800_000_000:
        return 3
    return 4


def calculate_insurance_premium(
    car_price: float,
    tenor_years: int,
    insurance_type: str = "Kombinasi (Thn 1 All-Risk + TLO)",
    ojk_region: str = "Wilayah 2 (DKI Jakarta, Jawa Barat, Banten)",
) -> float:
    """
    Menghitung total premi asuransi selama masa tenor kredit dengan memperhitungkan
    depresiasi nilai pertanggungan tahunan (100%, 90%, 80%, 75%, 70%).
    """
    cat_idx = get_ojk_price_category_index(car_price)
    ar_rate = OJK_ALL_RISK_RATES.get(
        ojk_region, OJK_ALL_RISK_RATES["Wilayah 2 (DKI Jakarta, Jawa Barat, Banten)"]
    )[cat_idx] / 100.0
    tlo_rate = OJK_TLO_RATES.get(
        ojk_region, OJK_TLO_RATES["Wilayah 2 (DKI Jakarta, Jawa Barat, Banten)"]
    )[cat_idx] / 100.0

    depreciation_factors = [1.00, 0.90, 0.80, 0.75, 0.70, 0.65]
    total_premium = 0.0

    for yr in range(tenor_years):
        insured_val = car_price * depreciation_factors[min(yr, len(depreciation_factors) - 1)]
        if "All-Risk" in insurance_type and "Kombinasi" not in insurance_type:
            total_premium += insured_val * ar_rate
        elif "TLO" in insurance_type and "Kombinasi" not in insurance_type:
            total_premium += insured_val * tlo_rate
        else:
            # Kombinasi: Tahun 1 All-Risk, Tahun 2+ TLO
            rate = ar_rate if yr == 0 else tlo_rate
            total_premium += insured_val * rate

    return round(total_premium, 0)


def simulate_car_credit(
    otr_price: float,
    dp_pct: float = 25.0,
    tenor_years: int = 4,
    interest_rate_flat_pct: float = 0.0,
    insurance_type: str = "Kombinasi (Thn 1 All-Risk + TLO)",
    ojk_region: str = "Wilayah 2 (DKI Jakarta, Jawa Barat, Banten)",
    payment_scheme: str = "ADDM (Angsuran Dibayar di Muka)",
) -> Dict[str, Any]:
    """
    Menghitung simulasi pembiayaan kredit mobil bekas secara komprehensif:
      - Uang Muka Murni (Pure DP)
      - Pokok Hutang (Principal Loan)
      - Premi Asuransi OJK, Biaya Admin & Fidusia, Biaya Provisi (1%)
      - Total Down Payment (TDP) & Angsuran Bulanan
      - Tabel Perbandingan Multi-Tenor (1 s/d 5 Tahun)
    """
    tenor_years = max(1, min(6, int(tenor_years)))
    dp_pct = max(10.0, min(80.0, float(dp_pct)))
    tenor_months = tenor_years * 12

    if interest_rate_flat_pct <= 0:
        interest_rate_flat_pct = DEFAULT_MULTIFINANCE_FLAT_RATES.get(tenor_years, 9.35)

    pure_dp = round(otr_price * (dp_pct / 100.0), 0)
    principal_loan = round(otr_price - pure_dp, 0)

    # Bunga total selama masa tenor
    total_interest = round(principal_loan * (interest_rate_flat_pct / 100.0) * tenor_years, 0)
    total_loan_with_interest = principal_loan + total_interest
    monthly_installment = round(total_loan_with_interest / tenor_months, -3)

    # Biaya-biaya multifinance standar Indonesia
    admin_fidusia_fee = 2_750_000.0 + (tenor_years * 250_000.0)
    provision_fee = round(principal_loan * 0.01, 0)  # 1% provisi
    insurance_premium = calculate_insurance_premium(
        car_price=otr_price,
        tenor_years=tenor_years,
        insurance_type=insurance_type,
        ojk_region=ojk_region,
    )

    is_addm = "ADDM" in payment_scheme.upper()
    if is_addm:
        total_tdp = pure_dp + admin_fidusia_fee + provision_fee + insurance_premium + monthly_installment
        effective_installments_count = tenor_months - 1
    else:
        total_tdp = pure_dp + admin_fidusia_fee + provision_fee + insurance_premium
        effective_installments_count = tenor_months

    # Tabel perbandingan seluruh tenor 1 - 5 tahun
    multi_tenor_schedule: List[Dict[str, Any]] = []
    for t_yr in range(1, 6):
        t_months = t_yr * 12
        t_rate = (
            interest_rate_flat_pct
            if t_yr == tenor_years
            else DEFAULT_MULTIFINANCE_FLAT_RATES.get(t_yr, 9.0)
        )
        t_interest = round(principal_loan * (t_rate / 100.0) * t_yr, 0)
        t_inst = round((principal_loan + t_interest) / t_months, -3)
        t_ins = calculate_insurance_premium(otr_price, t_yr, insurance_type, ojk_region)
        t_adm = 2_750_000.0 + (t_yr * 250_000.0)
        t_tdp = pure_dp + t_adm + provision_fee + t_ins + (t_inst if is_addm else 0.0)
        multi_tenor_schedule.append({
            "tenor_years": t_yr,
            "tenor_months": t_months,
            "flat_interest_pct": t_rate,
            "monthly_installment": t_inst,
            "insurance_premium": t_ins,
            "total_tdp": t_tdp,
            "min_monthly_income_dsr30": round(t_inst * 3.3, -4),
        })

    return {
        "otr_price": otr_price,
        "dp_pct": dp_pct,
        "pure_dp": pure_dp,
        "principal_loan": principal_loan,
        "tenor_years": tenor_years,
        "tenor_months": tenor_months,
        "interest_rate_flat_pct": interest_rate_flat_pct,
        "total_interest": total_interest,
        "monthly_installment": monthly_installment,
        "effective_installments_remaining": effective_installments_count,
        "admin_fidusia_fee": admin_fidusia_fee,
        "provision_fee": provision_fee,
        "insurance_type": insurance_type,
        "ojk_region": ojk_region,
        "insurance_premium": insurance_premium,
        "payment_scheme": payment_scheme,
        "total_tdp": total_tdp,
        "min_recommended_income_idr": round(monthly_installment * 3.3, -4),
        "multi_tenor_comparison": multi_tenor_schedule,
    }
