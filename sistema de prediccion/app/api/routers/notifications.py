from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.concurrency import run_in_threadpool

from sqlalchemy.orm import Session

from app.database.session import (
    get_db,
)

from app.config.push_config import VAPID_PUBLIC_KEY_RAW

from app.repositories.push_subscription_repository import (
    PushSubscriptionRepository,
)

from app.schemas.notification import (
    NotificationResponse,
)

from app.schemas.push_subscription import (
    PushSubscriptionCreate,
    VapidPublicKeyResponse,
)

from app.security.dependencies import (
    authenticate_token,
)

from app.security.permissions import (
    Permissions,
    require_permission,
)

from app.services.notification_service import (
    NotificationService,
)

from app.websockets.connection_manager import (
    manager,
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


@router.get(
    "/push/vapid-public-key",
    response_model=VapidPublicKeyResponse
)
def get_vapid_public_key():
    return VapidPublicKeyResponse(
        public_key=VAPID_PUBLIC_KEY_RAW
    )


@router.post(
    "/push/subscribe",
    status_code=status.HTTP_204_NO_CONTENT
)
def subscribe_push(
    subscription: PushSubscriptionCreate,

    current_user=Depends(
        require_permission(
            Permissions.NOTIFICATIONS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    PushSubscriptionRepository.upsert(
        db=db,
        user_id=current_user.id,
        endpoint=subscription.endpoint,
        p256dh=subscription.keys.p256dh,
        auth=subscription.keys.auth,
        user_agent=subscription.user_agent,
    )


@router.delete(
    "/push/subscribe",
    status_code=status.HTTP_204_NO_CONTENT
)
def unsubscribe_push(
    endpoint: str,

    current_user=Depends(
        require_permission(
            Permissions.NOTIFICATIONS_VIEW
        )
    ),

    db: Session = Depends(
        get_db
    )
):
    PushSubscriptionRepository.delete(
        db,
        current_user.id,
        endpoint
    )


@router.websocket("/ws")
async def notifications_websocket(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(
        get_db
    ),
):
    try:
        # authenticate_token es síncrona (usa SQLAlchemy sync);
        # se ejecuta en threadpool para no bloquear el loop.
        current_user = await run_in_threadpool(
            authenticate_token, token, db
        )
    except HTTPException:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION
        )
        return

    await manager.connect(current_user.id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(current_user.id, websocket)