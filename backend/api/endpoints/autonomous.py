import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.schemas import (
    AutonomousDashboardRead,
    AutonomousRunListResponse,
    AutonomousRunRead,
    AutonomousRunRequest,
)
from core.database import get_db
from models.autonomous_run import AutonomousRun
from services.autonomous_orchestrator_service import (
    get_autonomous_dashboard,
    get_autonomous_run,
    list_autonomous_runs,
    run_autonomous_cycle,
)

router = APIRouter()


def _run_to_payload(row: AutonomousRun) -> AutonomousRunRead:
    summary: dict = {}
    if row.summary_json:
        try:
            summary = json.loads(row.summary_json)
        except json.JSONDecodeError:
            summary = {}
    return AutonomousRunRead(
        id=row.id,
        user_id=row.user_id,
        video_id=row.video_id,
        seed_text=row.seed_text,
        niche=row.niche,
        audience=row.audience,
        objective=row.objective,
        region=row.region,
        platform=row.platform,
        status=row.status,
        insight_topic=row.insight_topic,
        experiment_id=row.experiment_id,
        selected_variant_id=row.selected_variant_id,
        discovered_leads_count=row.discovered_leads_count,
        qualified_leads_count=row.qualified_leads_count,
        drafted_outreach_count=row.drafted_outreach_count,
        summary=summary,
        error_message=row.error_message,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post("/run", response_model=AutonomousRunRead, status_code=status.HTTP_201_CREATED)
def run_cycle_endpoint(
    payload: AutonomousRunRequest,
    db: Session = Depends(get_db),
) -> AutonomousRunRead:
    try:
        row = run_autonomous_cycle(
            db=db,
            user_id=payload.user_id,
            video_id=payload.video_id,
            seed_text=payload.seed_text,
            niche=payload.niche,
            audience=payload.audience,
            objective=payload.objective,
            problem_angle=payload.problem_angle,
            offer=payload.offer,
            tone=payload.tone,
            platform=payload.platform,
            region=payload.region,
            leads_count=payload.leads_count,
            variants_count=payload.variants_count,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return _run_to_payload(row)


@router.get("/runs", response_model=AutonomousRunListResponse)
def list_runs_endpoint(
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AutonomousRunListResponse:
    rows = list_autonomous_runs(db=db, user_id=user_id)
    payload = [_run_to_payload(row) for row in rows]
    return AutonomousRunListResponse(count=len(payload), runs=payload)


@router.get("/runs/{run_id}", response_model=AutonomousRunRead)
def get_run_endpoint(run_id: int, db: Session = Depends(get_db)) -> AutonomousRunRead:
    try:
        row = get_autonomous_run(db=db, run_id=run_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return _run_to_payload(row)


@router.get("/dashboard", response_model=AutonomousDashboardRead)
def dashboard_endpoint(
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AutonomousDashboardRead:
    dashboard = get_autonomous_dashboard(db=db, user_id=user_id)
    return AutonomousDashboardRead.model_validate(dashboard)
