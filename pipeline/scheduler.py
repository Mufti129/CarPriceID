"""
Enterprise Background Task Scheduler & Automated Sync Daemon
Mengelola jadwal penarikan data berkala IBID Astra MAP, kalkulasi ulang kuantil harga pasar (FMV),
dan pencatatan riwayat eksekusi ke tabel sync_job_logs.
"""

import time
import threading
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from models.database import SessionLocal, init_db
from models.catalog import SyncJobLog
from data.sync_ibid_map_data import sync_ibid_map_data
from analytics.pricing_engine import PricingAnalyticsEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CarPriceScheduler")


def record_sync_job(
    job_name: str,
    trigger_source: str,
    status: str,
    records_processed: int,
    duration_seconds: float,
    notes: str,
    started_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Menyimpan log audit eksekusi job ke tabel sync_job_logs."""
    init_db()
    db = SessionLocal()
    try:
        now = datetime.now()
        job = SyncJobLog(
            job_name=job_name,
            trigger_source=trigger_source,
            status=status,
            records_processed=records_processed,
            duration_seconds=round(duration_seconds, 2),
            notes=notes,
            started_at=started_at or now,
            finished_at=now,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return {
            "id": job.id,
            "job_name": job.job_name,
            "trigger_source": job.trigger_source,
            "status": job.status,
            "records_processed": job.records_processed,
            "duration_seconds": float(job.duration_seconds or 0.0),
            "notes": job.notes,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        }
    finally:
        db.close()


def run_scheduled_sync_cycle(
    trigger_source: str = "SCHEDULED_DAEMON",
    target_brands: Optional[List[str]] = None,
    limit_brands: Optional[int] = None,
    delay_sec: float = 0.04,
    refresh_only: bool = False,
) -> Dict[str, Any]:
    """
    Menjalankan 1 siklus penuh sinkronisasi data:
      1. Auto-Sync IBID Astra MAP (jika refresh_only=False)
      2. Refresh Daily Retail Market Quantiles (P25, Median FMV, P75)
      3. Refresh Daily Wholesale Auction Corridors
      4. Catat audit trail ke tabel sync_job_logs
    """
    init_db()
    t0 = time.time()
    started_dt = datetime.now()
    total_records = 0
    notes_parts = []

    try:
        if not refresh_only:
            ibid_stats = sync_ibid_map_data(
                limit_brands=limit_brands,
                target_brand_names=target_brands,
                delay_sec=delay_sec,
            )
            upserted = ibid_stats.get("records_upserted", 0)
            total_records += upserted
            notes_parts.append(f"IBID MAP Upserted: {upserted} varian")

        db = SessionLocal()
        try:
            engine = PricingAnalyticsEngine(db)
            retail_cnt = engine.refresh_daily_market_stats()
            wh_cnt = engine.refresh_daily_wholesale_stats()
            total_records += retail_cnt + wh_cnt
            notes_parts.append(f"Retail Quantiles: {retail_cnt} grup")
            notes_parts.append(f"Wholesale Corridors: {wh_cnt} grup")
        finally:
            db.close()

        duration = time.time() - t0
        job_name = (
            "Daily Market & Wholesale Quantile Refresh"
            if refresh_only
            else "Full IBID Astra MAP & Market Intelligence Sync"
        )
        return record_sync_job(
            job_name=job_name,
            trigger_source=trigger_source,
            status="SUCCESS",
            records_processed=total_records,
            duration_seconds=duration,
            notes=" | ".join(notes_parts),
            started_at=started_dt,
        )

    except Exception as e:
        duration = time.time() - t0
        record_sync_job(
            job_name="Scheduled Data Sync Cycle",
            trigger_source=trigger_source,
            status="FAILED",
            records_processed=total_records,
            duration_seconds=duration,
            notes=f"Error: {str(e)}",
            started_at=started_dt,
        )
        raise


def get_recent_job_logs(limit: int = 15) -> List[Dict[str, Any]]:
    """Mengambil daftar riwayat eksekusi background job terbaru."""
    init_db()
    db = SessionLocal()
    try:
        logs = (
            db.query(SyncJobLog)
            .order_by(SyncJobLog.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": l.id,
                "job_name": l.job_name,
                "trigger_source": l.trigger_source,
                "status": l.status,
                "records_processed": l.records_processed,
                "duration_seconds": float(l.duration_seconds or 0.0),
                "notes": l.notes,
                "started_at": l.started_at.strftime("%Y-%m-%d %H:%M:%S") if l.started_at else "-",
                "finished_at": l.finished_at.strftime("%Y-%m-%d %H:%M:%S") if l.finished_at else "-",
            }
            for l in logs
        ]
    finally:
        db.close()


class BackgroundSyncDaemon:
    """Daemon worker thread untuk penjadwalan sinkronisasi berkala non-blocking."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self, interval_hours: float = 24.0):
        self.interval_hours = interval_hours
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    @classmethod
    def get_instance(cls, interval_hours: float = 24.0) -> "BackgroundSyncDaemon":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(interval_hours=interval_hours)
            return cls._instance

    def start_background_daemon(self):
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info(f"BackgroundSyncDaemon aktif (Interval: setiap {self.interval_hours} jam)")

    def _loop(self):
        while self.is_running:
            time.sleep(self.interval_hours * 3600.0)
            if not self.is_running:
                break
            try:
                run_scheduled_sync_cycle(
                    trigger_source="BACKGROUND_DAEMON",
                    target_brands=["TOYOTA", "HONDA", "DAIHATSU", "MITSUBISHI", "SUZUKI"],
                )
            except Exception as e:
                logger.error(f"Daemon sync error: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CarPrice ID Background Sync Scheduler")
    parser.add_argument("--run-once", action="store_true", help="Jalankan 1 siklus sync sekarang")
    parser.add_argument("--refresh-only", action="store_true", help="Hanya refresh statistik kuantil lokal")
    parser.add_argument("--interval-hours", type=float, default=24.0, help="Interval jam daemon berkala")
    args = parser.parse_args()

    if args.run_once or args.refresh_only:
        res = run_scheduled_sync_cycle(
            trigger_source="CLI_SCHEDULER",
            target_brands=["TOYOTA", "DAIHATSU", "HONDA"],
            refresh_only=args.refresh_only,
        )
        print(f"✅ Siklus Scheduler Selesai: {res}")
    else:
        print(f"⏰ Menjalankan Scheduler Daemon setiap {args.interval_hours} jam...")
        run_scheduled_sync_cycle(
            trigger_source="CLI_DAEMON_INIT",
            target_brands=["TOYOTA", "DAIHATSU", "HONDA"],
        )
        while True:
            time.sleep(args.interval_hours * 3600.0)
            run_scheduled_sync_cycle(trigger_source="CLI_DAEMON_LOOP")
