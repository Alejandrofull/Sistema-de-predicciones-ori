from __future__ import annotations

from sqlalchemy import (
    select,
)

from sqlalchemy.orm import Session

from app.database.session import (
    SessionLocal,
)

from app.models.permission import (
    Permission,
)

from app.models.role import (
    Role,
)

from app.models.role_permission import (
    RolePermission,
)


# ==========================================
# PERMISSIONS
# ==========================================

PERMISSIONS = [

    # ======================================
    # USERS
    # ======================================

    (
        "Gestionar usuarios",
        "users.manage",
        "users",
        (
            "Crear, modificar, activar, "
            "desactivar y administrar usuarios."
        ),
    ),

    (
        "Ver usuarios",
        "users.view",
        "users",
        (
            "Consultar información de usuarios."
        ),
    ),

    # ======================================
    # ROLES
    # ======================================

    (
        "Asignar roles",
        "roles.assign",
        "roles",
        (
            "Asignar y administrar roles "
            "de usuarios."
        ),
    ),

    # ======================================
    # DATASETS
    # ======================================

    (
        "Importar datasets",
        "datasets.import",
        "datasets",
        (
            "Importar archivos y fuentes "
            "de datos."
        ),
    ),

    (
        "Ver datasets",
        "datasets.view",
        "datasets",
        (
            "Consultar datasets y "
            "su información."
        ),
    ),

    (
        "Procesar datasets",
        "datasets.process",
        "datasets",
        (
            "Validar, limpiar, transformar, "
            "extraer series y generar features."
        ),
    ),

    (
        "Eliminar datasets",
        "datasets.delete",
        "datasets",
        (
            "Eliminar datasets registrados."
        ),
    ),

    # ======================================
    # BUSINESS SERIES
    # ======================================

    (
        "Ver series de negocio",
        "business_series.view",
        "business_series",
        (
            "Consultar productos, platos "
            "y otras series de negocio."
        ),
    ),

    (
        "Gestionar series de negocio",
        "business_series.manage",
        "business_series",
        (
            "Crear, modificar, activar, "
            "desactivar y eliminar series "
            "de negocio."
        ),
    ),

    # ======================================
    # MODELS
    # ======================================

    (
        "Ver modelos",
        "models.view",
        "models",
        (
            "Consultar modelos y versiones."
        ),
    ),

    (
        "Entrenar modelos",
        "models.train",
        "models",
        (
            "Ejecutar entrenamiento "
            "de modelos predictivos."
        ),
    ),

    (
        "Evaluar modelos",
        "models.evaluate",
        "models",
        (
            "Evaluar el desempeño "
            "de modelos predictivos."
        ),
    ),

    (
        "Comparar modelos",
        "models.compare",
        "models",
        (
            "Comparar métricas entre "
            "modelos predictivos."
        ),
    ),

    (
        "Activar modelos",
        "models.activate",
        "models",
        (
            "Activar versiones de modelos "
            "para uso en producción."
        ),
    ),

    # ======================================
    # RETRAINING
    # ======================================

    (
        "Ver reentrenamiento",
        "retraining.view",
        "retraining",
        (
            "Consultar políticas y ejecuciones "
            "de reentrenamiento."
        ),
    ),

    (
        "Gestionar reentrenamiento",
        "retraining.manage",
        "retraining",
        (
            "Crear políticas y ejecutar "
            "reentrenamientos."
        ),
    ),

    # ======================================
    # PREDICTIONS
    # ======================================

    (
        "Ejecutar predicciones",
        "predictions.run",
        "predictions",
        (
            "Generar predicciones "
            "de demanda."
        ),
    ),

    (
        "Ver predicciones",
        "predictions.view",
        "predictions",
        (
            "Consultar predicciones "
            "y sus resultados."
        ),
    ),

    # ======================================
    # INVENTORY
    # ======================================

    (
        "Ver inventario",
        "inventory.view",
        "inventory",
        (
            "Consultar observaciones y "
            "registros de inventario."
        ),
    ),

    (
        "Gestionar inventario",
        "inventory.manage",
        "inventory",
        (
            "Crear, modificar y eliminar "
            "observaciones de inventario."
        ),
    ),

    (
        "Importar inventario",
        "inventory.import",
        "inventory",
        (
            "Importar registros de inventario "
            "desde archivos."
        ),
    ),

    # ======================================
    # STATISTICS
    # ======================================

    (
        "Ver análisis estadísticos",
        "statistics.view",
        "statistics",
        (
            "Consultar resultados de "
            "análisis estadísticos."
        ),
    ),

    (
        "Ejecutar análisis estadísticos",
        "statistics.run",
        "statistics",
        (
            "Ejecutar análisis estadísticos "
            "sobre indicadores del sistema."
        ),
    ),

    # ======================================
    # KPIS
    # ======================================

    (
        "Ver KPIs técnicos",
        "kpis.technical.view",
        "kpis",
        (
            "Consultar indicadores técnicos "
            "del sistema predictivo."
        ),
    ),

    (
        "Ver KPIs operacionales",
        "kpis.operational.view",
        "kpis",
        (
            "Consultar indicadores operativos "
            "de demanda e inventario."
        ),
    ),

    # ======================================
    # REPORTS
    # ======================================

    (
        "Ver reportes",
        "reports.view",
        "reports",
        (
            "Consultar reportes generados."
        ),
    ),

    (
        "Generar reportes",
        "reports.generate",
        "reports",
        (
            "Generar y administrar reportes."
        ),
    ),

    # ======================================
    # EXPORTS
    # ======================================

    (
        "Ver exportaciones",
        "exports.view",
        "exports",
        (
            "Consultar y descargar "
            "exportaciones generadas."
        ),
    ),

    (
        "Generar exportaciones",
        "exports.generate",
        "exports",
        (
            "Generar y administrar "
            "exportaciones del sistema."
        ),
    ),

    # ======================================
    # NOTIFICATIONS
    # ======================================

    (
        "Ver notificaciones",
        "notifications.view",
        "notifications",
        (
            "Consultar notificaciones "
            "del sistema."
        ),
    ),

    (
        "Reconocer notificaciones",
        "notifications.acknowledge",
        "notifications",
        (
            "Reconocer alertas y "
            "notificaciones importantes."
        ),
    ),

    # ======================================
    # EXTERNAL VARIABLES
    # ======================================

    (
        "Ver variables externas",
        "external_variables.view",
        "external_variables",
        (
            "Consultar variables externas "
            "y sus valores."
        ),
    ),

    (
        "Gestionar variables externas",
        "external_variables.manage",
        "external_variables",
        (
            "Crear, modificar y administrar "
            "variables externas."
        ),
    ),

    # ======================================
    # DRIFT
    # ======================================

    (
        "Ver monitoreo y drift",
        "drift.view",
        "monitoring",
        (
            "Consultar desempeño productivo, "
            "degradación y drift de modelos."
        ),
    ),

    # ======================================
    # ANOMALIES
    # ======================================

    (
        "Ver anomalías",
        "anomalies.view",
        "anomalies",
        (
            "Consultar anomalías detectadas."
        ),
    ),

    (
        "Ejecutar detección de anomalías",
        "anomalies.scan",
        "anomalies",
        (
            "Analizar predicciones y generar "
            "anomalías y alertas."
        ),
    ),

    (
        "Resolver anomalías",
        "anomalies.resolve",
        "anomalies",
        (
            "Marcar anomalías detectadas "
            "como resueltas."
        ),
    ),

    # ======================================
    # AUDIT
    # ======================================

    (
        "Ver auditoría",
        "audit.view",
        "audit",
        (
            "Consultar registros "
            "de auditoría."
        ),
    ),
]


# ==========================================
# ROLES
# ==========================================

ROLES = [

    (
        "Administrador general",
        "general_admin",
        (
            "Administrador con acceso completo "
            "a la plataforma."
        ),
    ),

    (
        "Administrador de operaciones",
        "operation_admin",
        (
            "Responsable de operaciones, "
            "datos, modelos, predicciones, "
            "inventario y seguimiento."
        ),
    ),

    (
        "Operador",
        "operator",
        (
            "Usuario encargado de la operación "
            "diaria, inventario, predicciones, "
            "reportes y alertas."
        ),
    ),
]


# ==========================================
# ROLE PERMISSIONS
# ==========================================

ROLE_PERMISSIONS = {

    # ======================================
    # GENERAL ADMIN
    # ======================================

    "general_admin": {
        permission_code
        for (
            _name,
            permission_code,
            _module,
            _description,
        )
        in PERMISSIONS
    },

    # ======================================
    # OPERATION ADMIN
    # ======================================

    "operation_admin": {

        # DATASETS
        "datasets.import",
        "datasets.view",
        "datasets.process",
        "datasets.delete",

        # BUSINESS SERIES
        "business_series.view",
        "business_series.manage",

        # MODELS
        "models.view",
        "models.train",
        "models.evaluate",
        "models.compare",
        "models.activate",

        # RETRAINING
        "retraining.view",
        "retraining.manage",

        # PREDICTIONS
        "predictions.run",
        "predictions.view",

        # INVENTORY
        "inventory.view",
        "inventory.manage",
        "inventory.import",

        # STATISTICS
        "statistics.view",
        "statistics.run",

        # KPIS
        "kpis.technical.view",
        "kpis.operational.view",

        # REPORTS
        "reports.view",
        "reports.generate",

        # EXPORTS
        "exports.view",
        "exports.generate",

        # NOTIFICATIONS
        "notifications.view",
        "notifications.acknowledge",

        # EXTERNAL VARIABLES
        "external_variables.view",
        "external_variables.manage",

        # MONITORING
        "drift.view",

        # ANOMALIES
        "anomalies.view",
        "anomalies.scan",
        "anomalies.resolve",
    },

    # ======================================
    # OPERATOR
    # ======================================

    "operator": {

        # DATASETS
        "datasets.view",

        # BUSINESS SERIES
        "business_series.view",

        # MODELS
        "models.view",

        # RETRAINING
        "retraining.view",

        # PREDICTIONS
        "predictions.run",
        "predictions.view",

        # INVENTORY
        "inventory.view",
        "inventory.manage",
        "inventory.import",

        # STATISTICS
        "statistics.view",

        # KPIS
        "kpis.operational.view",

        # REPORTS
        "reports.view",

        # EXPORTS
        "exports.view",

        # NOTIFICATIONS
        "notifications.view",
        "notifications.acknowledge",

        # EXTERNAL VARIABLES
        "external_variables.view",

        # ANOMALIES
        "anomalies.view",
        "anomalies.resolve",
    },
}


# ==========================================
# ROLE
# ==========================================

def get_or_create_role(
    db: Session,
    name: str,
    code: str,
    description: str
) -> Role:

    role = db.scalar(
        select(Role)
        .where(
            Role.code == code
        )
    )

    if role:

        changed = False

        if role.name != name:
            role.name = name
            changed = True

        if role.description != description:
            role.description = description
            changed = True

        if not role.is_active:
            role.is_active = True
            changed = True

        if changed:
            db.flush()

        return role

    role = Role(
        name=name,
        code=code,
        description=description,
        is_active=True
    )

    db.add(
        role
    )

    db.flush()

    return role


# ==========================================
# PERMISSION
# ==========================================

def get_or_create_permission(
    db: Session,
    name: str,
    code: str,
    module: str,
    description: str
) -> Permission:

    permission = db.scalar(
        select(Permission)
        .where(
            Permission.code == code
        )
    )

    if permission:

        changed = False

        if permission.name != name:
            permission.name = name
            changed = True

        if permission.module != module:
            permission.module = module
            changed = True

        if (
            permission.description
            != description
        ):
            permission.description = (
                description
            )

            changed = True

        if not permission.is_active:
            permission.is_active = True
            changed = True

        if changed:
            db.flush()

        return permission

    permission = Permission(
        name=name,
        code=code,
        module=module,
        description=description,
        is_active=True
    )

    db.add(
        permission
    )

    db.flush()

    return permission


# ==========================================
# SINCRONIZAR PERMISOS DE ROL
# ==========================================

def sync_role_permissions(
    db: Session,
    role: Role,
    desired_codes: set[str],
    permissions_by_code: dict[
        str,
        Permission
    ]
) -> None:

    current_links = list(
        db.scalars(
            select(
                RolePermission
            )
            .where(
                RolePermission.role_id
                == role.id
            )
        ).all()
    )

    current_by_permission_id = {
        link.permission_id: link
        for link
        in current_links
    }

    desired_permission_ids = {
        permissions_by_code[
            code
        ].id
        for code
        in desired_codes
    }

    # ======================================
    # AGREGAR FALTANTES
    # ======================================

    for permission_id in (
        desired_permission_ids
    ):

        if (
            permission_id
            in current_by_permission_id
        ):
            continue

        db.add(
            RolePermission(
                role_id=role.id,
                permission_id=(
                    permission_id
                )
            )
        )

    # ======================================
    # ELIMINAR SOBRANTES
    # ======================================

    for (
        permission_id,
        link
    ) in current_by_permission_id.items():

        if (
            permission_id
            not in desired_permission_ids
        ):

            db.delete(
                link
            )


# ==========================================
# SEED PRINCIPAL
# ==========================================

def seed_rbac(
    db: Session
) -> None:

    print(
        "🌱 Iniciando seed RBAC..."
    )

    # ======================================
    # 1. PERMISOS
    # ======================================

    permissions_by_code = {}

    for (
        name,
        code,
        module,
        description
    ) in PERMISSIONS:

        permission = (
            get_or_create_permission(
                db=db,
                name=name,
                code=code,
                module=module,
                description=description
            )
        )

        permissions_by_code[
            code
        ] = permission

    db.flush()

    print(
        f"✅ {len(permissions_by_code)} "
        "permisos sincronizados"
    )

    # ======================================
    # 2. ROLES
    # ======================================

    roles_by_code = {}

    for (
        name,
        code,
        description
    ) in ROLES:

        role = (
            get_or_create_role(
                db=db,
                name=name,
                code=code,
                description=description
            )
        )

        roles_by_code[
            code
        ] = role

    db.flush()

    print(
        f"✅ {len(roles_by_code)} "
        "roles sincronizados"
    )

    # ======================================
    # 3. VALIDAR MATRIZ
    # ======================================

    all_permission_codes = set(
        permissions_by_code.keys()
    )

    all_role_codes = set(
        roles_by_code.keys()
    )

    configured_role_codes = set(
        ROLE_PERMISSIONS.keys()
    )

    missing_role_configs = (
        all_role_codes
        -
        configured_role_codes
    )

    if missing_role_configs:

        raise RuntimeError(
            "Existen roles sin matriz "
            "de permisos: "
            f"{sorted(missing_role_configs)}"
        )

    unknown_role_configs = (
        configured_role_codes
        -
        all_role_codes
    )

    if unknown_role_configs:

        raise RuntimeError(
            "ROLE_PERMISSIONS contiene "
            "roles inexistentes: "
            f"{sorted(unknown_role_configs)}"
        )

    for (
        role_code,
        permission_codes
    ) in ROLE_PERMISSIONS.items():

        unknown_codes = (
            permission_codes
            -
            all_permission_codes
        )

        if unknown_codes:

            raise RuntimeError(
                "El rol "
                f"'{role_code}' contiene "
                "permisos inexistentes: "
                f"{sorted(unknown_codes)}"
            )

    # ======================================
    # 4. SINCRONIZAR MATRIZ
    # ======================================

    for (
        role_code,
        desired_codes
    ) in ROLE_PERMISSIONS.items():

        role = (
            roles_by_code[
                role_code
            ]
        )

        sync_role_permissions(
            db=db,
            role=role,
            desired_codes=(
                desired_codes
            ),
            permissions_by_code=(
                permissions_by_code
            )
        )

    # ======================================
    # 5. COMMIT
    # ======================================

    db.commit()

    print(
        "✅ Matriz de permisos "
        "sincronizada"
    )

    print(
        "🎉 Seed RBAC completado"
    )


# ==========================================
# EJECUCIÓN DIRECTA
# ==========================================

def main() -> None:

    db = SessionLocal()

    try:

        seed_rbac(
            db
        )

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


if __name__ == "__main__":

    main()