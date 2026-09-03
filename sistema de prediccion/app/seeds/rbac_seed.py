from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import (
    RolePermission
)


ROLES = [
    {
        "name": "Administrador general",
        "code": "general_admin",
        "description": (
            "Control total del sistema"
        )
    },
    {
        "name": "Administrador de operación",
        "code": "operation_admin",
        "description": (
            "Gestiona la operación del negocio"
        )
    },
    {
        "name": "Operador",
        "code": "operator",
        "description": (
            "Consulta predicciones y alertas "
            "operativas"
        )
    }
]


PERMISSIONS = [
    ("Gestionar usuarios", "users.manage", "users"),
    ("Ver usuarios", "users.view", "users"),
    ("Asignar roles", "roles.assign", "security"),

    ("Importar datasets", "datasets.import", "datasets"),
    ("Ver datasets", "datasets.view", "datasets"),
    ("Eliminar datasets", "datasets.delete", "datasets"),

    ("Ver modelos", "models.view", "models"),
    ("Entrenar modelos", "models.train", "models"),
    ("Evaluar modelos", "models.evaluate", "models"),
    ("Comparar modelos", "models.compare", "models"),
    ("Activar modelos", "models.activate", "models"),

    ("Ver reentrenamientos", "retraining.view", "models"),
    (
        "Gestionar reentrenamientos",
        "retraining.manage",
        "models"
    ),

    (
        "Ejecutar predicciones",
        "predictions.run",
        "predictions"
    ),
    (
        "Ver predicciones",
        "predictions.view",
        "predictions"
    ),

    (
        "Ver KPIs técnicos",
        "kpis.technical.view",
        "kpis"
    ),
    (
        "Ver KPIs operativos",
        "kpis.operational.view",
        "kpis"
    ),

    (
        "Ver reportes",
        "reports.view",
        "reports"
    ),
    (
        "Generar reportes",
        "reports.generate",
        "reports"
    ),

    (
        "Generar exportaciones",
        "exports.generate",
        "exports"
    ),

    (
        "Ver notificaciones",
        "notifications.view",
        "notifications"
    ),
    (
        "Confirmar notificaciones",
        "notifications.acknowledge",
        "notifications"
    ),

    (
        "Ver variables externas",
        "external_variables.view",
        "external_variables"
    ),
    (
        "Gestionar variables externas",
        "external_variables.manage",
        "external_variables"
    ),

    ("Ver drift", "drift.view", "monitoring"),
    (
        "Ver anomalías",
        "anomalies.view",
        "monitoring"
    ),

    (
        "Ver auditoría",
        "audit.view",
        "audit"
    ),
]


ROLE_PERMISSION_CODES = {
    "general_admin": {
        permission[1]
        for permission in PERMISSIONS
    },

    "operation_admin": {
        "datasets.import",
        "datasets.view",

        "models.view",

        "predictions.run",
        "predictions.view",

        "kpis.operational.view",

        "reports.view",
        "reports.generate",

        "exports.generate",

        "notifications.view",
        "notifications.acknowledge",

        "external_variables.view",

        "anomalies.view",
    },

    "operator": {
        "datasets.view",

        "models.view",

        "predictions.run",
        "predictions.view",

        "kpis.operational.view",

        "reports.view",

        "notifications.view",
        "notifications.acknowledge",

        "external_variables.view",
    }
}


def seed_rbac():
    db = SessionLocal()

    try:
        role_objects = {}

        for role_data in ROLES:
            role = db.scalar(
                select(Role).where(
                    Role.code
                    == role_data["code"]
                )
            )

            if not role:
                role = Role(**role_data)
                db.add(role)
                db.flush()

            role_objects[
                role.code
            ] = role

        permission_objects = {}

        for name, code, module in PERMISSIONS:

            permission = db.scalar(
                select(Permission).where(
                    Permission.code == code
                )
            )

            if not permission:
                permission = Permission(
                    name=name,
                    code=code,
                    module=module
                )

                db.add(permission)
                db.flush()

            permission_objects[
                code
            ] = permission

        for (
            role_code,
            permission_codes
        ) in ROLE_PERMISSION_CODES.items():

            role = role_objects[
                role_code
            ]

            for permission_code in (
                permission_codes
            ):
                permission = (
                    permission_objects[
                        permission_code
                    ]
                )

                existing = db.scalar(
                    select(
                        RolePermission
                    ).where(
                        RolePermission.role_id
                        == role.id,

                        RolePermission
                        .permission_id
                        == permission.id
                    )
                )

                if not existing:
                    db.add(
                        RolePermission(
                            role_id=role.id,
                            permission_id=(
                                permission.id
                            )
                        )
                    )

        db.commit()

        print(
            "✅ Roles y permisos "
            "creados correctamente"
        )

    finally:
        db.close()


if __name__ == "__main__":
    seed_rbac()