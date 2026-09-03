from app.notifications.templates.anomaly_detected import anomaly_detected
from app.notifications.templates.demand_alert import demand_alert
from app.notifications.templates.drift_detected import drift_detected
from app.notifications.templates.model_activated import model_activated
from app.notifications.templates.model_evaluated import model_evaluated
from app.notifications.templates.overstock_alert import overstock_alert
from app.notifications.templates.purchase_recommendation import purchase_recommendation
from app.notifications.templates.replenishment_alert import replenishment_alert
from app.notifications.templates.retraining_completed import retraining_completed
from app.notifications.templates.retraining_failed import retraining_failed
from app.notifications.templates.retraining_started import retraining_started
from app.notifications.templates.stock_alert import stock_alert
from app.notifications.templates.training_completed import training_completed
from app.notifications.templates.training_failed import training_failed

__all__ = [
    "anomaly_detected", "demand_alert", "drift_detected", "model_activated",
    "model_evaluated", "overstock_alert", "purchase_recommendation",
    "replenishment_alert", "retraining_completed", "retraining_failed",
    "retraining_started", "stock_alert", "training_completed", "training_failed",
]
