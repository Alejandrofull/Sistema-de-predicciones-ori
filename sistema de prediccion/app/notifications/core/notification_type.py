from enum import StrEnum


class NotificationCategory(StrEnum):
    MODEL = "model"
    TRAINING = "training"
    RETRAINING = "retraining"
    DEMAND = "demand"
    INVENTORY = "inventory"
    MONITORING = "monitoring"
    SYSTEM = "system"


class NotificationPriority(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(StrEnum):
    TRAINING_COMPLETED = "training_completed"
    TRAINING_FAILED = "training_failed"
    MODEL_ACTIVATED = "model_activated"
    MODEL_EVALUATED = "model_evaluated"
    DRIFT_DETECTED = "drift_detected"
    ANOMALY_DETECTED = "anomaly_detected"
    RETRAINING_STARTED = "retraining_started"
    RETRAINING_COMPLETED = "retraining_completed"
    RETRAINING_FAILED = "retraining_failed"
    DEMAND_ALERT = "demand_alert"
    STOCK_ALERT = "stock_alert"
    REPLENISHMENT_ALERT = "replenishment_alert"
    OVERSTOCK_ALERT = "overstock_alert"
    PURCHASE_RECOMMENDATION = "purchase_recommendation"
