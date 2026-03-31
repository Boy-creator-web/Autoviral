"""Campaign reports endpoint."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from core.audit import audit_log
from core.database import get_db
from core.rate_limit import apply_rate_limit_headers, enforce_ip_rate_limit, enforce_user_rate_limit
from core.security import get_current_user
from models.campaign_report import CampaignReport
from models.user import User
from schemas.operations import CampaignReportCreate, CampaignReportRead

router = APIRouter()


@router.get("/", response_model=list[CampaignReportRead])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CampaignReportRead]:
    rows = list(db.scalars(select(CampaignReport).order_by(CampaignReport.id.desc())).all())
    if current_user.role != "admin":
        rows = [row for row in rows if row.user_id == current_user.id]
    return [
        CampaignReportRead(
            id=row.id,
            user_id=row.user_id,
            period=row.period,
            report_data=row.report_data,
            status=row.status,
        )
        for row in rows
    ]


@router.post("/", response_model=CampaignReportRead, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: CampaignReportCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignReportRead:
    ip_limit = enforce_ip_rate_limit(request)
    user_limit = enforce_user_rate_limit(current_user.id)
    apply_rate_limit_headers(response, ip_limit, user_limit)
    if current_user.role != "admin" and current_user.id != payload.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this user")

    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    row = CampaignReport(
        user_id=payload.user_id,
        period=payload.period,
        report_data=payload.report_data,
        status="ready",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    audit_log(
        "campaign_report_created",
        actor=f"user:{current_user.id}",
        target=f"report:{row.id}",
        metadata={"owner_user_id": row.user_id, "period": row.period},
        db=db,
    )
    return CampaignReportRead(
        id=row.id,
        user_id=row.user_id,
        period=row.period,
        report_data=row.report_data,
        status=row.status,
    )
