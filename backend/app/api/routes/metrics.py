from fastapi import APIRouter, Depends
from sqlmodel import col, func, select

from app.api.deps import SessionDep, require_permission
from app.core.permissions import Permission, Role
from app.models import Item, Metrics, User

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    dependencies=[Depends(require_permission(Permission.METRICS_READ))],
)


@router.get("/")
def read_metrics(session: SessionDep) -> Metrics:
    """
    Aggregated usage metrics.
    """
    role_counts = session.exec(
        select(User.role, func.count()).group_by(col(User.role))
    ).all()
    users_by_role = dict.fromkeys(Role, 0) | {
        Role(role): count for role, count in role_counts
    }

    return Metrics(
        total_users=sum(users_by_role.values()),
        active_users=session.exec(
            select(func.count()).select_from(User).where(col(User.is_active))
        ).one(),
        users_by_role=users_by_role,
        total_items=session.exec(select(func.count()).select_from(Item)).one(),
    )
