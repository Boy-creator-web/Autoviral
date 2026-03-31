import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.schemas import (
    AutonomousDashboardRead,
    AutonomousDailyModeRequest,
    AutonomousDailyModeResponse,
    AutonomousPlanCreateRequest,
    AutonomousPlanListResponse,
    AutonomousPlanRead,
    AutonomousPlanSetActiveRequest,
    AutonomousRunListResponse,
    AutonomousRunRead,
    AutonomousRunRequest,
    AutonomousSchedulerTickResponse,
    DailyOpsBootstrapRequest,
    DailyOpsBootstrapResponse,
)
from core.config import settings
from core.database import get_db
from models.autonomous_plan import AutonomousPlan
from models.autonomous_run import AutonomousRun
from services.autonomous_orchestrator_service import (
    bootstrap_daily_mode,
    bootstrap_daily_operations,
    create_autonomous_plan,
    get_autonomous_dashboard,
    get_autonomous_plan,
    get_autonomous_run,
    list_autonomous_plans,
    list_autonomous_runs,
    run_due_autonomous_plans,
    run_autonomous_cycle,
    set_autonomous_plan_active,
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


def _plan_to_payload(row: AutonomousPlan) -> AutonomousPlanRead:
    return AutonomousPlanRead(
        id=row.id,
        user_id=row.user_id,
        video_id=row.video_id,
        name=row.name,
        seed_text=row.seed_text,
        niche=row.niche,
        audience=row.audience,
        objective=row.objective,
        problem_angle=row.problem_angle,
        offer=row.offer,
        tone=row.tone,
        platform=row.platform,
        region=row.region,
        leads_count=row.leads_count,
        variants_count=row.variants_count,
        interval_minutes=row.interval_minutes,
        is_active=row.is_active,
        next_run_at=row.next_run_at,
        last_run_at=row.last_run_at,
        last_status=row.last_status,
        last_error=row.last_error,
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


@router.post("/plans", response_model=AutonomousPlanRead, status_code=status.HTTP_201_CREATED)
def create_plan_endpoint(
    payload: AutonomousPlanCreateRequest,
    db: Session = Depends(get_db),
) -> AutonomousPlanRead:
    try:
        row = create_autonomous_plan(
            db=db,
            user_id=payload.user_id,
            video_id=payload.video_id,
            name=payload.name,
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
            interval_minutes=payload.interval_minutes,
            is_active=payload.is_active,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return _plan_to_payload(row)


@router.get("/plans", response_model=AutonomousPlanListResponse)
def list_plans_endpoint(
    user_id: int | None = Query(default=None),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> AutonomousPlanListResponse:
    rows = list_autonomous_plans(db=db, user_id=user_id, active_only=active_only)
    payload = [_plan_to_payload(row) for row in rows]
    return AutonomousPlanListResponse(count=len(payload), plans=payload)


@router.get("/plans/{plan_id}", response_model=AutonomousPlanRead)
def get_plan_endpoint(plan_id: int, db: Session = Depends(get_db)) -> AutonomousPlanRead:
    try:
        row = get_autonomous_plan(db=db, plan_id=plan_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return _plan_to_payload(row)


@router.post("/plans/{plan_id}/active", response_model=AutonomousPlanRead)
def set_plan_active_endpoint(
    plan_id: int,
    payload: AutonomousPlanSetActiveRequest,
    db: Session = Depends(get_db),
) -> AutonomousPlanRead:
    try:
        row = set_autonomous_plan_active(db=db, plan_id=plan_id, is_active=payload.is_active)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return _plan_to_payload(row)


@router.post("/scheduler/tick", response_model=AutonomousSchedulerTickResponse)
def scheduler_tick_endpoint(db: Session = Depends(get_db)) -> AutonomousSchedulerTickResponse:
    rows = run_due_autonomous_plans(db=db)
    return AutonomousSchedulerTickResponse(
        executed_runs=len(rows),
        run_ids=[row.id for row in rows],
    )


@router.post("/bootstrap", response_model=DailyOpsBootstrapResponse, status_code=status.HTTP_201_CREATED)
def bootstrap_endpoint(
    payload: DailyOpsBootstrapRequest,
    db: Session = Depends(get_db),
) -> DailyOpsBootstrapResponse:
    try:
        result = bootstrap_daily_operations(
            db=db,
            user_id=payload.user_id,
            video_id=payload.video_id,
            niche=payload.niche,
            audience=payload.audience,
            objective=payload.objective,
            region=payload.region,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return DailyOpsBootstrapResponse.model_validate(result)


@router.post("/daily-mode", response_model=AutonomousDailyModeResponse, status_code=status.HTTP_201_CREATED)
def daily_mode_endpoint(
    payload: AutonomousDailyModeRequest,
    db: Session = Depends(get_db),
) -> AutonomousDailyModeResponse:
    try:
        plan, run, ml_status = bootstrap_daily_mode(
            db=db,
            user_id=payload.user_id,
            video_id=payload.video_id,
            niche=payload.niche,
            audience=payload.audience,
            objective=payload.objective,
            problem_angle=payload.problem_angle,
            offer=payload.offer,
            platform=payload.platform,
            region=payload.region,
            interval_minutes=payload.interval_minutes,
            plan_name=payload.plan_name,
            seed_text=payload.seed_text,
            leads_count=payload.leads_count,
            variants_count=payload.variants_count,
            run_now=payload.run_now,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    return AutonomousDailyModeResponse(
        plan=_plan_to_payload(plan),
        run=_run_to_payload(run) if run else None,
        scheduler_enabled=settings.autonomous_scheduler_enabled,
        ml_status=ml_status,
    )

