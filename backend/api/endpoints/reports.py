"""Campaign reports endpoint."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from models.campaign_report import CampaignReport
from models.user import User
from schemas.operations import CampaignReportCreate, CampaignReportRead

router = APIRouter()


@router.get("/", response_model=list[CampaignReportRead])
def list_reports(db: Session = Depends(get_db)) -> list[CampaignReportRead]:
    rows = list(db.scalars(select(CampaignReport).order_by(CampaignReport.id.desc())).all())
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
def create_report(payload: CampaignReportCreate, db: Session = Depends(get_db)) -> CampaignReportRead:
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
    return CampaignReportRead(
        id=row.id,
        user_id=row.user_id,
        period=row.period,
        report_data=row.report_data,
        status=row.status,
    )
