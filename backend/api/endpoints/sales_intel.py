from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from models.sales_lead import SalesLead
from services.sales_intel_service import create_outreach_draft, discover_leads, list_leads, score_lead

router = APIRouter()


def _extract_company_size(notes: str | None) -> str:
    if not notes or "company_size=" not in notes:
        return "unknown"
    return notes.split("company_size=")[-1].split(";")[0].strip()


def _lead_to_payload(lead: SalesLead) -> dict:
    created_at = lead.created_at if isinstance(lead.created_at, datetime) else None
    return {
        "id": lead.id,
        "source": lead.source,
        "company_name": lead.company_name,
        "company_domain": lead.domain,
        "contact_name": lead.contact_name or "",
        "contact_title": lead.contact_role or "",
        "contact_email": lead.email or "",
        "company_size": _extract_company_size(lead.notes),
        "geography": lead.region,
        "industry": lead.industry,
        "pain_points_json": "[]",
        "raw_signals_json": "{}",
        "icp_score": lead.icp_fit_score,
        "intent_score": lead.intent_score,
        "priority_score": lead.lead_score,
        "outreach_status": lead.status,
        "outreach_draft": lead.outreach_draft,
        "created_at": created_at.isoformat() if created_at else None,
    }


@router.post("/discover", status_code=status.HTTP_201_CREATED)
@router.post("/leads/discover", status_code=status.HTTP_201_CREATED)
def discover_leads_endpoint(
    industry: str,
    region: str = "ID",
    company_size: str = "mid-market",
    count: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict:
    seed = f"{industry} {company_size}"
    rows = discover_leads(
        db=db,
        seed_text=seed,
        region=region,
        industry=industry,
        limit=count,
    )
    items = [_lead_to_payload(row) for row in rows]
    return {"count": len(items), "items": items}


@router.get("/leads")
def list_leads_endpoint(
    min_score: float | None = Query(default=None, ge=0, le=1),
    db: Session = Depends(get_db),
) -> dict:
    rows = list_leads(db=db, min_score=min_score)
    items = [_lead_to_payload(row) for row in rows]
    return {"count": len(items), "items": items}


@router.post("/score/{lead_id}")
@router.post("/leads/{lead_id}/score")
def score_lead_endpoint(
    lead_id: int,
    icp_industry: str,
    icp_region: str = "ID",
    db: Session = Depends(get_db),
) -> dict:
    try:
        lead = score_lead(
            db=db,
            lead_id=lead_id,
            icp_industry=icp_industry,
            icp_region=icp_region,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return _lead_to_payload(lead)


@router.post("/outreach/{lead_id}")
@router.post("/leads/{lead_id}/outreach-draft")
def outreach_draft_endpoint(
    lead_id: int,
    product_name: str = "Autoviral",
    offer_text: str = "Bisa bantu naikkan lead-to-close conversion",
    channel: str = "email",
    db: Session = Depends(get_db),
) -> dict:
    try:
        lead = create_outreach_draft(
            db=db,
            lead_id=lead_id,
            product_name=product_name,
            offer_text=offer_text,
            channel=channel,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return _lead_to_payload(lead)
