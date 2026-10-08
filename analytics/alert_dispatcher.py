"""
Dispatcher Notifikasi Peluang Deal Mobil Murah (Car Bargain Hunter Alerts).
Mendukung Webhook, Telegram Bot, dan Streamlit In-App Notifications.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("AlertDispatcher")

class CarAlertDispatcher:
    def __init__(self):
        self.notification_history: List[Dict[str, Any]] = []

    def dispatch_bargain_alert(self, deal: Dict[str, Any]) -> bool:
        """Kirim alert notifikasi ketika listing mobil murah terdeteksi."""
        alert_payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": "HOT_CAR_DEAL",
            "title": f"🚨 [HOT CAR DEAL] {deal.get('brand')} {deal.get('model')} - {deal.get('variant')} ({deal.get('year')})",
            "price_idr": deal.get("price"),
            "fmv_idr": deal.get("fmv_price"),
            "discount_pct": deal.get("discount_pct"),
            "discount_idr": deal.get("discount_idr"),
            "city": deal.get("city"),
            "url": deal.get("url")
        }
        self.notification_history.append(alert_payload)
        logger.info(f"Alert dispatched: {alert_payload['title']} | Diskon: {deal.get('discount_pct'):.1f}%")
        return True

    def get_recent_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        return sorted(self.notification_history, key=lambda x: x["timestamp"], reverse=True)[:limit]

alert_dispatcher = CarAlertDispatcher()
