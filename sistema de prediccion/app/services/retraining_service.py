from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.dataset_repository import (
    DatasetRepository,
)

from app.repositories.model_repository import (
    ModelRepository,
)

from app.repositories.model_version_repository import (
    ModelVersionRepository,
)

from app.repositories.retraining_policy_repository import (
    RetrainingPolicyRepository,
)

from app.repositories.retraining_run_repository import (
    RetrainingRunRepository,
)

from app.services.performance_monitoring_service import (
    PerformanceMonitoringService,
)

from app.services.training_service import (
    TrainingService,
)


class RetrainingService:

    def __init__(self):

        self.performance_service = (
            PerformanceMonitoringService()
        )

        self.training_service = (
            TrainingService()
        )

    def check_model(
        self,
        db: Session,
        model_id: int,
        limit: int = 100,
        minimum_observations: int = 5
    ) -> dict:

        model = (
            ModelRepository.get_by_id(
                db,
                model_id
            )
        )

        if not model:

            raise HTTPException(
                status_code=404,
                detail="Modelo no encontrado"
            )

        policies = (
            RetrainingPolicyRepository
            .get_by_model(
                db=db,
                model_id=model_id,
                active_only=True
            )
        )

        if not policies:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El modelo no tiene políticas "
                    "de reentrenamiento activas"
                )
            )

        performance = (
            self.performance_service
            .get_model_performance(
                db=db,
                model_id=model_id,
                limit=limit,
                minimum_observations=(
                    minimum_observations
                ),
                rmse_degradation_threshold=(
                    999999.0
                ),
                mape_threshold=(
                    999999.0
                )
            )
        )

        checks = []

        triggered_policy_ids = []

        for policy in policies:

            check = (
                self._evaluate_policy(
                    policy=policy,
                    performance=performance
                )
            )

            checks.append(
                check
            )

            if check[
                "triggered"
            ]:

                triggered_policy_ids.append(
                    policy.id
                )

        should_retrain = (
            len(
                triggered_policy_ids
            )
            > 0
        )

        return {
            "model_id": model.id,
            "business_series_id": (
                model.business_series_id
            ),
            "sufficient_data": (
                performance[
                    "sufficient_data"
                ]
            ),
            "should_retrain": (
                should_retrain
            ),
            "triggered_policy_ids": (
                triggered_policy_ids
            ),
            "checks": checks,
            "performance": performance
        }

    def execute_retraining(
        self,
        db: Session,
        model_id: int,
        user_id: int,
        trigger_type: str,
        reason: str | None = None,
        dataset_id: int | None = None
    ) -> dict:

        model = (
            ModelRepository.get_by_id(
                db,
                model_id
            )
        )

        if not model:

            raise HTTPException(
                status_code=404,
                detail="Modelo no encontrado"
            )

        existing_run = (
            RetrainingRunRepository
            .get_running_by_model(
                db=db,
                model_id=model.id
            )
        )

        if existing_run:

            raise HTTPException(
                status_code=409,
                detail=(
                    "Ya existe un reentrenamiento "
                    "pendiente o en ejecución "
                    "para este modelo"
                )
            )

        previous_version = (
            ModelVersionRepository
            .get_active_by_model(
                db=db,
                model_id=model.id
            )
        )

        if not previous_version:

            previous_version = (
                ModelVersionRepository
                .get_latest(
                    db=db,
                    model_id=model.id
                )
            )

        dataset = (
            self._resolve_dataset(
                db=db,
                model=model,
                previous_version=(
                    previous_version
                ),
                requested_dataset_id=(
                    dataset_id
                ),
                user_id=user_id
            )
        )

        if (
            dataset.processing_stage
            != "features"
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset de reentrenamiento "
                    "debe tener "
                    "processing_stage='features'"
                )
            )

        if (
            model.business_series_id
            is not None
            and dataset.business_series_id
            != model.business_series_id
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "El dataset no pertenece "
                    "a la misma serie de negocio "
                    "del modelo"
                )
            )

        feature_config = (
            previous_version.feature_config
            if previous_version
            else {}
        ) or {}

        date_column = (
            feature_config.get(
                "date_column"
            )
            or (
                dataset.dataset_metadata
                or {}
            ).get(
                "date_column"
            )
        )

        target_column = (
            feature_config.get(
                "target_column"
            )
            or (
                dataset.dataset_metadata
                or {}
            ).get(
                "target_column"
            )
        )

        test_ratio = float(
            feature_config.get(
                "test_ratio",
                0.20
            )
        )

        if not date_column:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No se pudo determinar "
                    "date_column para "
                    "el reentrenamiento"
                )
            )

        if not target_column:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No se pudo determinar "
                    "target_column para "
                    "el reentrenamiento"
                )
            )

        run = (
            RetrainingRunRepository.create(
                db=db,
                model_id=model.id,
                previous_version_id=(
                    previous_version.id
                    if previous_version
                    else None
                ),
                new_version_id=None,
                dataset_id=dataset.id,
                trigger_type=trigger_type,
                reason=reason,
                status="pending"
            )
        )

        RetrainingRunRepository.mark_running(
            db=db,
            run=run
        )

        try:

            training_result = (
                self.training_service
                .train_models(
                    db=db,
                    dataset_id=dataset.id,
                    user_id=user_id,
                    date_column=(
                        date_column
                    ),
                    target_column=(
                        target_column
                    ),
                    model_names=[
                        model.model_type
                    ],
                    test_ratio=(
                        test_ratio
                    )
                )
            )

            trained_results = (
                training_result.get(
                    "results",
                    []
                )
            )

            if not trained_results:

                raise RuntimeError(
                    "El entrenamiento no generó "
                    "ninguna nueva versión"
                )

            trained_result = (
                trained_results[
                    0
                ]
            )

            generated_model_id = int(
                trained_result[
                    "model_id"
                ]
            )

            if generated_model_id != model.id:

                raise RuntimeError(
                    "El reentrenamiento creó "
                    "un modelo lógico diferente. "
                    "Se esperaba reutilizar "
                    f"model_id={model.id}."
                )

            new_version_id = int(
                trained_result[
                    "model_version_id"
                ]
            )

            run = (
                RetrainingRunRepository
                .mark_completed(
                    db=db,
                    run=run,
                    new_version_id=(
                        new_version_id
                    )
                )
            )

            return {
                "run": run,
                "model_id": model.id,
                "previous_version_id": (
                    previous_version.id
                    if previous_version
                    else None
                ),
                "new_version_id": (
                    new_version_id
                ),
                "model_type": (
                    model.model_type
                ),
                "dataset_id": (
                    dataset.id
                ),
                "business_series_id": (
                    model.business_series_id
                ),
                "metrics": (
                    trained_result[
                        "metrics"
                    ]
                ),
                "activation_required": (
                    True
                ),
                "message": (
                    "Reentrenamiento completado. "
                    "La nueva versión fue creada, "
                    "pero todavía no ha sido "
                    "activada."
                )
            }

        except HTTPException as error:

            RetrainingRunRepository.mark_failed(
                db=db,
                run=run,
                reason=(
                    self._error_message(
                        error
                    )
                )
            )

            raise

        except Exception as error:

            RetrainingRunRepository.mark_failed(
                db=db,
                run=run,
                reason=str(
                    error
                )
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Error durante el "
                    "reentrenamiento: "
                    f"{error}"
                )
            )

    def check_and_run(
        self,
        db: Session,
        model_id: int,
        user_id: int,
        dataset_id: int | None = None,
        limit: int = 100,
        minimum_observations: int = 5
    ) -> dict:

        check = (
            self.check_model(
                db=db,
                model_id=model_id,
                limit=limit,
                minimum_observations=(
                    minimum_observations
                )
            )
        )

        if not check[
            "should_retrain"
        ]:

            return {
                "checked": True,
                "triggered": False,
                "check": check,
                "execution": None
            }

        triggered_checks = [
            item
            for item
            in check[
                "checks"
            ]
            if item[
                "triggered"
            ]
        ]

        reasons = [
            item[
                "reason"
            ]
            for item
            in triggered_checks
        ]

        reason = (
            " | ".join(
                reasons
            )
        )

        trigger_types = {
            item[
                "trigger_type"
            ]
            for item
            in triggered_checks
        }

        if len(
            trigger_types
        ) == 1:

            trigger_type = next(
                iter(
                    trigger_types
                )
            )

        else:

            trigger_type = (
                "multiple_policies"
            )

        execution = (
            self.execute_retraining(
                db=db,
                model_id=model_id,
                user_id=user_id,
                trigger_type=(
                    trigger_type
                ),
                reason=reason,
                dataset_id=(
                    dataset_id
                )
            )
        )

        return {
            "checked": True,
            "triggered": True,
            "check": check,
            "execution": execution
        }

    @staticmethod
    def _evaluate_policy(
        policy,
        performance: dict
    ) -> dict:

        if not performance[
            "sufficient_data"
        ]:

            return {
                "policy_id": policy.id,
                "trigger_type": (
                    policy.trigger_type
                ),
                "metric_name": (
                    policy.metric_name
                ),
                "threshold": (
                    policy.threshold
                ),
                "current_value": None,
                "triggered": False,
                "reason": (
                    "No existen suficientes "
                    "observaciones reales "
                    "para evaluar la política."
                )
            }

        metrics = (
            performance.get(
                "metrics"
            )
            or {}
        )

        trigger_type = (
            policy.trigger_type
            .strip()
            .lower()
        )

        threshold = (
            float(
                policy.threshold
            )
            if policy.threshold
            is not None
            else None
        )

        current_value = None
        triggered = False

        if (
            trigger_type
            == "metric_threshold"
        ):

            metric_name = (
                policy.metric_name
            )

            if not metric_name:

                return {
                    "policy_id": (
                        policy.id
                    ),
                    "trigger_type": (
                        trigger_type
                    ),
                    "metric_name": None,
                    "threshold": threshold,
                    "current_value": None,
                    "triggered": False,
                    "reason": (
                        "La política no tiene "
                        "metric_name configurado."
                    )
                }

            current_value = (
                metrics.get(
                    metric_name
                )
            )

            if (
                current_value is not None
                and threshold is not None
            ):

                if metric_name == "r2":

                    triggered = (
                        float(
                            current_value
                        )
                        < threshold
                    )

                else:

                    triggered = (
                        float(
                            current_value
                        )
                        > threshold
                    )

        elif (
            trigger_type
            == "mape_threshold"
        ):

            current_value = (
                metrics.get(
                    "mape"
                )
            )

            if (
                current_value is not None
                and threshold is not None
            ):

                triggered = (
                    float(
                        current_value
                    )
                    > threshold
                )

        elif (
            trigger_type
            == "rmse_degradation"
        ):

            baseline = (
                performance.get(
                    "baseline_metrics"
                )
                or {}
            )

            baseline_rmse = (
                baseline.get(
                    "rmse"
                )
            )

            current_rmse = (
                metrics.get(
                    "rmse"
                )
            )

            if (
                baseline_rmse is not None
                and current_rmse is not None
                and float(
                    baseline_rmse
                ) > 0
            ):

                current_value = (
                    (
                        float(
                            current_rmse
                        )
                        -
                        float(
                            baseline_rmse
                        )
                    )
                    /
                    float(
                        baseline_rmse
                    )
                )

                if threshold is not None:

                    triggered = (
                        current_value
                        > threshold
                    )

        else:

            return {
                "policy_id": policy.id,
                "trigger_type": (
                    trigger_type
                ),
                "metric_name": (
                    policy.metric_name
                ),
                "threshold": threshold,
                "current_value": None,
                "triggered": False,
                "reason": (
                    "Tipo de disparador "
                    "no soportado."
                )
            }

        if current_value is None:

            reason = (
                "No existe información "
                "suficiente para calcular "
                "la métrica de la política."
            )

        elif triggered:

            if (
                trigger_type
                == "rmse_degradation"
            ):

                reason = (
                    "La degradación del RMSE "
                    f"alcanzó "
                    f"{current_value * 100:.2f}% "
                    "y superó el umbral de "
                    f"{threshold * 100:.2f}%."
                )

            else:

                reason = (
                    f"{policy.metric_name}="
                    f"{float(current_value):.4f} "
                    "superó el umbral "
                    f"{threshold}."
                )

        else:

            reason = (
                "La política fue evaluada "
                "y su umbral no fue superado."
            )

        return {
            "policy_id": policy.id,
            "trigger_type": (
                trigger_type
            ),
            "metric_name": (
                policy.metric_name
            ),
            "threshold": threshold,
            "current_value": (
                float(
                    current_value
                )
                if current_value
                is not None
                else None
            ),
            "triggered": (
                triggered
            ),
            "reason": reason
        }

    @staticmethod
    def _resolve_dataset(
        db: Session,
        model,
        previous_version,
        requested_dataset_id: int | None,
        user_id: int
    ):

        if requested_dataset_id:

            dataset = (
                DatasetRepository.get_by_id(
                    db,
                    requested_dataset_id
                )
            )

            if not dataset:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Dataset de "
                        "reentrenamiento "
                        "no encontrado"
                    )
                )

        elif (
            model.business_series_id
            is not None
        ):

            dataset = (
                DatasetRepository
                .get_latest_by_business_series(
                    db=db,
                    business_series_id=(
                        model.business_series_id
                    ),
                    processing_stage=(
                        "features"
                    )
                )
            )

            if not dataset:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "No existe un dataset "
                        "FEATURES para la serie "
                        "de negocio."
                    )
                )

        else:

            feature_config = (
                previous_version.feature_config
                if previous_version
                else {}
            ) or {}

            previous_dataset_id = (
                feature_config.get(
                    "dataset_id"
                )
            )

            if not previous_dataset_id:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "No se pudo determinar "
                        "el dataset para "
                        "reentrenamiento."
                    )
                )

            dataset = (
                DatasetRepository.get_by_id(
                    db,
                    int(
                        previous_dataset_id
                    )
                )
            )

            if not dataset:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        "El dataset del modelo "
                        "ya no existe."
                    )
                )

        if dataset.user_id != user_id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "No tiene acceso al dataset "
                    "de reentrenamiento."
                )
            )

        return dataset

    @staticmethod
    def _error_message(
        error: HTTPException
    ) -> str:

        detail = (
            error.detail
        )

        if isinstance(
            detail,
            str
        ):

            return detail

        return str(
            detail
        )