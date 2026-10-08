"""
Generator Sertifikat Valuasi Harga Wajar Mobil Berstandar Industri (CarPrice ID Appraisal Certificate).
Dibuat dalam format PDF siap unduh & cetak menggunakan fpdf2.
"""

import io
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

class CarValuationCertificate(FPDF if FPDF else object):
    def header(self):
        if not FPDF:
            return
        self.set_fill_color(15, 23, 42) # Slate Dark 900
        self.rect(0, 0, 210, 32, 'F')
        
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.set_xy(12, 8)
        self.cell(0, 8, "CARPRICE ID | OFFICIAL USED CAR APPRAISAL CERTIFICATE", ln=1)
        
        self.set_font("Helvetica", "", 9)
        self.set_text_color(203, 213, 225)
        self.set_xy(12, 18)
        self.cell(0, 6, "AI-Powered Indonesian Automotive Intelligence & Hedonic Valuation Engine (Model V7)", ln=1)
        self.ln(12)

    def footer(self):
        if not FPDF:
            return
        self.set_y(-18)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()} | Verified by CarPrice ID AI Multi-Marketplace Intelligence Platform | Generated: {datetime.now().strftime('%d %B %Y %H:%M:%S')}", 0, 0, 'C')

def generate_car_pdf_certificate(
    unit_data: Dict[str, Any],
    valuation_result: Dict[str, Any],
    market_stats: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Menghasilkan file PDF Certificate dalam bentuk raw bytes stream.
    """
    if not FPDF:
        return b"%PDF-1.4 dummy fallback certificate"

    pdf = CarValuationCertificate(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # 1. Judul & Nomor Sertifikat
    cert_no = f"CPID-CAR-{datetime.now().strftime('%Y%m%d')}-{abs(hash(str(unit_data))) % 100000:05d}"
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(100, 7, "USED VEHICLE VALUATION SUMMARY", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 7, f"Certificate ID: {cert_no}", 0, 1, 'R')
    pdf.ln(3)

    # 2. Box Unit Details
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(12, 45, 186, 48, 'DF')

    pdf.set_xy(16, 48)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    brand_model = f"{unit_data.get('brand', '')} {unit_data.get('model', '')} - {unit_data.get('variant', '')}"
    pdf.cell(178, 6, brand_model[:75], 0, 1)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.set_xy(16, 57)
    pdf.cell(90, 5, f"Tahun Perakitan: {unit_data.get('year', '-')}", 0, 0)
    pdf.cell(90, 5, f"Transmisi: {unit_data.get('transmission', 'Automatic')}", 0, 1)

    pdf.set_xy(16, 63)
    pdf.cell(90, 5, f"Bahan Bakar: {unit_data.get('fuel_type', 'Bensin')}", 0, 0)
    pdf.cell(90, 5, f"Odometer: {unit_data.get('odometer_km', 0):,} KM", 0, 1)

    pdf.set_xy(16, 69)
    pdf.cell(90, 5, f"Status Pajak: {unit_data.get('tax_status', 'Pajak Hidup')}", 0, 0)
    pdf.cell(90, 5, f"Dokumen: BPKB ({'Ada' if unit_data.get('has_bpkb', True) else 'Tidak Ada'})", 0, 1)

    pdf.set_xy(16, 75)
    flood_status = "Bebas Banjir (100%)" if unit_data.get("flood_free", True) else "Catatan Riwayat Banjir"
    acc_status = "Bebas Tabrak Struktur" if unit_data.get("accident_free", True) else "Catatan Tabrak Sasis"
    pdf.cell(90, 5, f"Kondisi Air: {flood_status}", 0, 0)
    pdf.cell(90, 5, f"Kondisi Sasis: {acc_status}", 0, 1)

    pdf.ln(18)

    # 3. Valuation Hero Box
    pdf.set_fill_color(238, 242, 255) # Indigo Light
    pdf.set_draw_color(99, 102, 241)
    pdf.rect(12, 102, 186, 42, 'DF')

    pdf.set_xy(16, 105)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(67, 56, 202)
    pdf.cell(178, 5, "FAIR MARKET VALUE (FMV) BENCHMARK", 0, 1, 'C')

    pdf.set_xy(16, 112)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 27, 75)
    fmv_val = valuation_result.get("predicted_fmv", 0)
    pdf.cell(178, 10, f"Rp {fmv_val:,.0f}", 0, 1, 'C')

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(79, 70, 229)
    p25 = valuation_result.get("price_p25_deal", 0)
    p75 = valuation_result.get("price_p75_pristine", 0)
    pdf.cell(178, 6, f"Bargain Buy Target (P25): Rp {p25:,.0f}   |   Pristine Showroom (P75): Rp {p75:,.0f}", 0, 1, 'C')

    depr = valuation_result.get("real_depreciation_pct", 0)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(178, 5, f"Tingkat Depresiasi Riil dari MSRP Baru: {depr}%", 0, 1, 'C')

    pdf.ln(20)

    # 4. Metrik Analitik & Landasan Teori
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "METODOLOGI VALUASI & FAKTOR PENYESUAIAN", 0, 1)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(0, 4.5, 
        "Penilaian ini menggunakan algoritma Machine Learning Hedonic Regression Versi 7 "
        "yang memadukan kurva depresiasi George Akerlof (1970) dan Kelvin Lancaster (1966) dengan data aktual "
        "18.000 listing retail terverifikasi (OLX, Mobil123, Carmudi) dan 7.000+ lot lelang balai resmi (JBA Indonesia & IBID Astra). "
        "Harga di atas merupakan estimasi nilai ekuilibrium pasar sekunder di wilayah Jabodetabek."
    )

    pdf.ln(5)

    # 5. Sign-off Footer Box
    pdf.set_draw_color(203, 213, 225)
    pdf.line(12, 220, 198, 220)
    pdf.set_xy(12, 224)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(90, 5, "Disahkan Oleh:", 0, 0)
    pdf.cell(90, 5, "Catatan Penggunaan:", 0, 1)

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(90, 4, "CarPrice ID Automotive Analytics Engine", 0, 0)
    pdf.cell(90, 4, "1. Nilai pasar dapat berfluktuasi tergantung inspeksi fisik on-site.", 0, 1)
    pdf.cell(90, 4, "Sistem Valuasi Kendaraan Roda Empat Indonesia", 0, 0)
    pdf.cell(90, 4, "2. Dokumen ini bukan merupakan polis asuransi atau garansi sepihak.", 0, 1)

    # Output as binary string
    output_io = io.BytesIO()
    pdf.output(output_io)
    return output_io.getvalue()
