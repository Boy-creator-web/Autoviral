from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.schemas import (
    ViralExperimentCreateRequest,
    ViralExperimentCreateResponse,
    ViralExperimentListResponse,
    ViralExperimentRead,
    ViralMetricIngestRequest,
    ViralMetricRead,
    ViralRecommendationRead,
    ViralVariantListResponse,
    ViralVariantRead,
)
from core.database import get_db
from services.viral_engine_service import (
    create_viral_experiment,
    get_experiment_recommendation,
    ingest_variant_metric,
    list_experiments,
    list_variants,
)

router = APIRouter()


@router.post(
    "/experiments",
    response_model=ViralExperimentCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_experiment_endpoint(
    payload: ViralExperimentCreateRequest,
    db: Session = Depends(get_db),
) -> ViralExperimentCreateResponse:
    try:
        experiment, variants = create_viral_experiment(
            db=db,
            user_id=payload.user_id,
            video_id=payload.video_id,
            niche=payload.niche,
            audience=payload.audience,
            objective=payload.objective,
            problem_angle=payload.problem_angle,
            offer=payload.offer,
            tone=payload.tone,
            platform=payload.platform,
            trend_context=payload.trend_context,
            variants_count=payload.variants_count,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return ViralExperimentCreateResponse(
        experiment=ViralExperimentRead.model_validate(experiment),
        variants=[ViralVariantRead.model_validate(row) for row in variants],
    )


@router.get("/experiments", response_model=ViralExperimentListResponse)
def list_experiments_endpoint(
    user_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> ViralExperimentListResponse:
    rows = list_experiments(db=db, user_id=user_id, status=status_filter)
    return ViralExperimentListResponse(
        count=len(rows),
        experiments=[ViralExperimentRead.model_validate(row) for row in rows],
    )


@router.get("/experiments/{experiment_id}/variants", response_model=ViralVariantListResponse)
def list_variants_endpoint(
    experiment_id: int,
    db: Session = Depends(get_db),
) -> ViralVariantListResponse:
    try:
        rows = list_variants(db=db, experiment_id=experiment_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return ViralVariantListResponse(
        count=len(rows),
        variants=[ViralVariantRead.model_validate(row) for row in rows],
    )


@router.post("/variants/{variant_id}/metrics", response_model=ViralMetricRead, status_code=status.HTTP_201_CREATED)
def ingest_metric_endpoint(
    variant_id: int,
    payload: ViralMetricIngestRequest,
    db: Session = Depends(get_db),
) -> ViralMetricRead:
    try:
        row = ingest_variant_metric(
            db=db,
            variant_id=variant_id,
            impressions=payload.impressions,
            views_3s=payload.views_3s,
            views_10s=payload.views_10s,
            completions=payload.completions,
            likes=payload.likes,
            comments=payload.comments,
            shares=payload.shares,
            saves=payload.saves,
            profile_visits=payload.profile_visits,
            link_clicks=payload.link_clicks,
            watch_time_avg_sec=payload.watch_time_avg_sec,
            conversion_events=payload.conversion_events,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return ViralMetricRead.model_validate(row)


@router.get("/experiments/{experiment_id}/recommendation", response_model=ViralRecommendationRead)
def recommendation_endpoint(
    experiment_id: int,
    db: Session = Depends(get_db),
) -> ViralRecommendationRead:
    try:
        recommendation = get_experiment_recommendation(db=db, experiment_id=experiment_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return ViralRecommendationRead.model_validate(recommendation)
