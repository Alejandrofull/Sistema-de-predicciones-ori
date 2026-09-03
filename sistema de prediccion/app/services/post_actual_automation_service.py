from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories.notification_repository import (
    NotificationRepository,
)
from app.services.anomaly_service import (
    AnomalyService,
)
from app.services.audit_service import (
    AuditService,
)
from app.services.performance_monitoring_service import (
    PerformanceMonitoringService,
)
from app.services.retraining_service import (
    RetrainingService,
)


class PostActualAutomationService:

    # ==========================================
    # CONFIGURACIÓN POR DEFECTO
    # ==========================================

    PERFORMANCE_LIMIT = 100
    MINIMUM_OBSERVATIONS = 5

    RMSE_DEGRADATION_THRESHOLD = 20.0
    MAPE_THRESHOLD = 20.0

    ANOMALY_LIMIT = 200
    Z_THRESHOLD = 3.0
    IQR_MULTIPLIER = 1.5

    def __init__(self):

        self.performance_service = (
            PerformanceMonitoringService()
        )

        self.anomaly_service = (
            AnomalyService()
        )

        self.retraining_service = (
            RetrainingService()
        )

    # ==========================================
    # PROCESAR NUEVO VALOR REAL
    # ==========================================

    def process(
        self,
        db: Session,
        prediction,
        prediction_result
    ) -> dict:

        response = {
            "processed": True,
            "prediction_id": (
                prediction.id
            ),
            "prediction_result_id": (
                prediction_result.id
            ),
            "model_id": (
                prediction.model_id
            ),
            "business_series_id": (
                prediction.business_series_id
            ),
            "performance": None,
            "anomalies": None,
            "retraining": None,
            "retraining_notification_created": (
                False
            ),
            "errors": [],
        }

        # ==========================================
        # 1. PERFORMANCE
        # ==========================================

        performance = (
            self._process_performance(
                db=db,
                model_id=(
                    prediction.model_id
                )
            )
        )

        response[
            "performance"
        ] = performance

        if not performance[
            "success"
        ]:

            response[
                "errors"
            ].append(
                {
                    "stage": (
                        "performance"
                    ),
                    "detail": (
                        performance[
                            "error"
                        ]
                    ),
                }
            )

        # ==========================================
        # 2. ANOMALÍAS
        # ==========================================

        anomalies = (
            self._process_anomalies(
                db=db,
                business_series_id=(
                    prediction
                    .business_series_id
                ),
                model_id=(
                    prediction.model_id
                )
            )
        )

        response[
            "anomalies"
        ] = anomalies

        if not anomalies[
            "success"
        ]:

            response[
                "errors"
            ].append(
                {
                    "stage": (
                        "anomalies"
                    ),
                    "detail": (
                        anomalies[
                            "error"
                        ]
                    ),
                }
            )

        # ==========================================
        # 3. REENTRENAMIENTO
        # ==========================================

        retraining = (
            self._process_retraining_check(
                db=db,
                model_id=(
                    prediction.model_id
                )
            )
        )

        response[
            "retraining"
        ] = retraining

        if not retraining[
            "success"
        ]:

            response[
                "errors"
            ].append(
                {
                    "stage": (
                        "retraining"
                    ),
                    "detail": (
                        retraining[
                            "error"
                        ]
                    ),
                }
            )

        # ==========================================
        # 4. NOTIFICAR SI REQUIERE
        # REENTRENAMIENTO
        # ==========================================

        if (
            retraining[
                "success"
            ]
            and retraining.get(
                "should_retrain",
                False
            )
        ):

            try:

                (
                    _notification,
                    notification_created,
                ) = (
                    self
                    ._create_retraining_notification(
                        db=db,
                        prediction=(
                            prediction
                        ),
                        retraining=(
                            retraining.get(
                                "data"
                            )
                            or {}
                        )
                    )
                )

                response[
                    "retraining_notification_created"
                ] = (
                    notification_created
                )

            except Exception as error:

                try:
                    db.rollback()

                except Exception:
                    pass

                response[
                    "errors"
                ].append(
                    {
                        "stage": (
                            "retraining_notification"
                        ),
                        "detail": str(
                            error
                        ),
                    }
                )

        # ==========================================
        # 5. AUDITORÍA DEL CICLO AUTOMÁTICO
        # ==========================================

        self._audit(
            db=db,
            prediction=prediction,
            prediction_result=(
                prediction_result
            ),
            response=response
        )

        return response

    # ==========================================
    # PERFORMANCE
    # ==========================================

    def _process_performance(
        self,
        db: Session,
        model_id: int
    ) -> dict:

        try:

            result = (
                self.performance_service
                .get_model_performance(
                    db=db,
                    model_id=model_id,
                    limit=(
                        self.PERFORMANCE_LIMIT
                    ),
                    minimum_observations=(
                        self.MINIMUM_OBSERVATIONS
                    ),
                    rmse_degradation_threshold=(
                        self
                        .RMSE_DEGRADATION_THRESHOLD
                    ),
                    mape_threshold=(
                        self.MAPE_THRESHOLD
                    )
                )
            )

            return {
                "success": True,
                "error": None,
                "sufficient_data": (
                    result.get(
                        "sufficient_data",
                        False
                    )
                ),
                "metrics": (
                    result.get(
                        "metrics"
                    )
                ),
                "baseline_metrics": (
                    result.get(
                        "baseline_metrics"
                    )
                ),
                "health": (
                    result.get(
                        "health"
                    )
                ),
                "data": result,
            }

        except Exception as error:

            try:
                db.rollback()

            except Exception:
                pass

            return {
                "success": False,
                "error": str(
                    error
                ),
                "sufficient_data": False,
                "metrics": None,
                "baseline_metrics": None,
                "health": None,
                "data": None,
            }

    # ==========================================
    # ANOMALÍAS
    # ==========================================

    def _process_anomalies(
        self,
        db: Session,
        business_series_id: int | None,
        model_id: int
    ) -> dict:

        try:

            result = (
                self.anomaly_service
                .scan_prediction_errors(
                    db=db,
                    business_series_id=(
                        business_series_id
                    ),
                    model_id=model_id,
                    limit=(
                        self.ANOMALY_LIMIT
                    ),
                    minimum_observations=(
                        self.MINIMUM_OBSERVATIONS
                    ),
                    z_threshold=(
                        self.Z_THRESHOLD
                    ),
                    iqr_multiplier=(
                        self.IQR_MULTIPLIER
                    )
                )
            )

            return {
                "success": True,
                "error": None,
                "observations_analyzed": (
                    result.get(
                        "observations_analyzed",
                        0
                    )
                ),
                "anomalies_detected": (
                    result.get(
                        "anomalies_detected",
                        0
                    )
                ),
                "anomalies_created": (
                    result.get(
                        "anomalies_created",
                        0
                    )
                ),
                "anomalies_existing": (
                    result.get(
                        "anomalies_existing",
                        0
                    )
                ),
                "notifications_created": (
                    result.get(
                        "notifications_created",
                        0
                    )
                ),
                "data": result,
            }

        except Exception as error:

            try:
                db.rollback()

            except Exception:
                pass

            return {
                "success": False,
                "error": str(
                    error
                ),
                "observations_analyzed": 0,
                "anomalies_detected": 0,
                "anomalies_created": 0,
                "anomalies_existing": 0,
                "notifications_created": 0,
                "data": None,
            }

    # ==========================================
    # REENTRAINING CHECK
    # ==========================================

    def _process_retraining_check(
        self,
        db: Session,
        model_id: int
    ) -> dict:

        try:

            result = (
                self.retraining_service
                .check_model(
                    db=db,
                    model_id=model_id,
                    limit=(
                        self.PERFORMANCE_LIMIT
                    ),
                    minimum_observations=(
                        self.MINIMUM_OBSERVATIONS
                    )
                )
            )

            return {
                "success": True,
                "error": None,
                "policies_available": True,
                "sufficient_data": (
                    result.get(
                        "sufficient_data",
                        False
                    )
                ),
                "should_retrain": (
                    result.get(
                        "should_retrain",
                        False
                    )
                ),
                "triggered_policy_ids": (
                    result.get(
                        "triggered_policy_ids",
                        []
                    )
                ),
                "checks": (
                    result.get(
                        "checks",
                        []
                    )
                ),
                "data": result,
            }

        except HTTPException as error:

            # No tener políticas activas no debe
            # convertir el ingreso de demanda real
            # en un error.
            if error.status_code == 400:

                return {
                    "success": True,
                    "error": None,
                    "policies_available": False,
                    "sufficient_data": False,
                    "should_retrain": False,
                    "triggered_policy_ids": [],
                    "checks": [],
                    "data": {
                        "message": (
                            error.detail
                        )
                    },
                }

            try:
                db.rollback()

            except Exception:
                pass

            return {
                "success": False,
                "error": str(
                    error.detail
                ),
                "policies_available": False,
                "sufficient_data": False,
                "should_retrain": False,
                "triggered_policy_ids": [],
                "checks": [],
                "data": None,
            }

        except Exception as error:

            try:
                db.rollback()

            except Exception:
                pass

            return {
                "success": False,
                "error": str(
                    error
                ),
                "policies_available": False,
                "sufficient_data": False,
                "should_retrain": False,
                "triggered_policy_ids": [],
                "checks": [],
                "data": None,
            }

    # ==========================================
    # NOTIFICACIÓN DE REENTRENAMIENTO
    # ==========================================

    def _create_retraining_notification(
        self,
        db: Session,
        prediction,
        retraining: dict
    ):

        model_id = (
            prediction.model_id
        )

        # ==========================================
        # EVITAR ALERTAS DUPLICADAS
        # ==========================================

        existing = db.scalar(
            select(
                Notification
            )
            .where(
                Notification.notification_type
                == "retraining_recommended",
                Notification.entity_type
                == "model",
                Notification.entity_id
                == str(
                    model_id
                ),
                Notification.acknowledged.is_(
                    False
                )
            )
            .order_by(
                Notification.created_at.desc(),
                Notification.id.desc()
            )
            .limit(1)
        )

        if existing:

            return (
                existing,
                False
            )

        checks = (
            retraining.get(
                "checks"
            )
            or []
        )

        triggered_checks = [
            check
            for check in checks
            if check.get(
                "triggered"
            )
        ]

        reasons = [
            str(
                check.get(
                    "reason"
                )
            )
            for check in triggered_checks
            if check.get(
                "reason"
            )
        ]

        if reasons:

            reason_text = (
                " ".join(
                    reasons
                )
            )

        else:

            reason_text = (
                "Una o más políticas de "
                "reentrenamiento fueron "
                "activadas."
            )

        title = (
            "Reentrenamiento recomendado"
        )

        message = (
            "El desempeño reciente del modelo "
            f"{model_id} activó una política de "
            "reentrenamiento. "
            f"{reason_text}"
        )

        notification = (
            NotificationRepository.create(
                db=db,

                # Visible para el usuario que
                # generó la predicción.
                user_id=(
                    prediction.user_id
                ),

                # También puede ser consumida
                # por administradores operativos
                # cuando get_for_user recibe roles.
                recipient_role=(
                    "operation_admin"
                ),

                category=(
                    "model_monitoring"
                ),
                notification_type=(
                    "retraining_recommended"
                ),
                title=title,
                message=message,
                priority="high",
                requires_action=True,
                suggested_action=(
                    "Revisar las métricas del "
                    "modelo y ejecutar el "
                    "reentrenamiento si la "
                    "degradación es válida."
                ),
                entity_type="model",
                entity_id=str(
                    model_id
                ),
                payload={
                    "model_id": (
                        model_id
                    ),
                    "business_series_id": (
                        prediction
                        .business_series_id
                    ),
                    "prediction_id": (
                        prediction.id
                    ),
                    "triggered_policy_ids": (
                        retraining.get(
                            "triggered_policy_ids",
                            []
                        )
                    ),
                    "reasons": (
                        reasons
                    ),
                }
            )
        )

        return (
            notification,
            True
        )

    # ==========================================
    # AUDITORÍA
    # ==========================================

    @staticmethod
    def _audit(
        db: Session,
        prediction,
        prediction_result,
        response: dict
    ) -> None:

        performance = (
            response.get(
                "performance"
            )
            or {}
        )

        anomalies = (
            response.get(
                "anomalies"
            )
            or {}
        )

        retraining = (
            response.get(
                "retraining"
            )
            or {}
        )

        health = (
            performance.get(
                "health"
            )
            or {}
        )

        AuditService.log_safe(
            db=db,
            user_id=(
                prediction.user_id
            ),
            action=(
                "prediction.actual.processed"
            ),
            entity=(
                "prediction_result"
            ),
            entity_id=(
                prediction_result.id
            ),
            details={
                "prediction_id": (
                    prediction.id
                ),
                "model_id": (
                    prediction.model_id
                ),
                "business_series_id": (
                    prediction
                    .business_series_id
                ),
                "prediction_date": (
                    prediction_result
                    .prediction_date
                ),
                "predicted_value": (
                    prediction_result
                    .predicted_value
                ),
                "actual_value": (
                    prediction_result
                    .actual_value
                ),
                "sufficient_performance_data": (
                    performance.get(
                        "sufficient_data"
                    )
                ),
                "performance_status": (
                    health.get(
                        "status"
                    )
                ),
                "anomalies_created": (
                    anomalies.get(
                        "anomalies_created",
                        0
                    )
                ),
                "should_retrain": (
                    retraining.get(
                        "should_retrain",
                        False
                    )
                ),
                "triggered_policy_ids": (
                    retraining.get(
                        "triggered_policy_ids",
                        []
                    )
                ),
                "automation_errors": (
                    response.get(
                        "errors",
                        []
                    )
                ),
            }
        )