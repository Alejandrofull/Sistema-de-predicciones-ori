from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.schemas.notification import (
    NotificationResponse,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.notification_service import (
    NotificationService,
)


router = APIRouter(
    prefix="/notifications",
    tags=["notifications"]
)


@router.get(
    "",
    response_model=list[
        NotificationResponse
    ]
)
def get_notifications(
    unread_only: bool = Query(
        default=False
    ),

    limit: int = Query(
        default=100,
        ge=1,
        le=1000
    ),

    current_user=Depends(
        require_permission(
            Permissions.NOTIFICATIONS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        NotificationService
        .get_user_notifications(
            db=db,
            user_id=current_user.id,
            unread_only=(
                unread_only
            ),
            limit=limit
        )
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse
)
def mark_notification_read(
    notification_id: int,

    current_user=Depends(
        require_permission(
            Permissions.NOTIFICATIONS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        NotificationService.mark_read(
            db=db,
            notification_id=(
                notification_id
            ),
            user_id=current_user.id
        )
    )


@router.patch(
    "/{notification_id}/acknowledge",
    response_model=NotificationResponse
)
def acknowledge_notification(
    notification_id: int,

    current_user=Depends(
        require_permission(
            Permissions.NOTIFICATIONS_ACKNOWLEDGE
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    return (
        NotificationService.acknowledge(
            db=db,
            notification_id=(
                notification_id
            ),
            user_id=current_user.id
        )
    )