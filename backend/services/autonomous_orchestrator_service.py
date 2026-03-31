from __future__ import annotations

import json

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.autonomous_run import AutonomousRun
from models.user import User
from models.video import Video
from models.viral_variant import ViralVariant
from services.sales_intel_service import create_outreach_draft, discover_leads, score_lead
from services.scraper.engine import generate_and_store_insights
from services.viral_engine_service import create_viral_experiment, get_experiment_recommendation


def _extract_trend_context(raw_data: str) -> str:
    try:
        payload = json.loads(raw_data)
    except json.JSONDecodeError:
        return ""
    summary = payload.get("summary", {})
    trends = payload.get("trends", {})
    audience = payload.get("audience", {})
    compact = {
        "summary": summary,
        "trends": trends,
        "audience": audience,
    }
    return json.dumps(compact, ensure_ascii=False)


def run_autonomous_cycle(
    db: Session,
    *,
    user_id: int,
    video_id: int | None,
    seed_text: str,
    niche: str,
    audience: str,
    objective: str,
    problem_angle: str,
    offer: str | None,
    tone: str,
    platform: str,
    region: str,
    leads_count: int,
    variants_count: int,
) -> AutonomousRun:
    if db.get(User, user_id) is None:
        raise ValueError("User not found")
    if video_id is not None and db.get(Video, video_id) is None:
        raise ValueError("Video not found")

    run = AutonomousRun(
        user_id=user_id,
        video_id=video_id,
        seed_text=seed_text,
        niche=niche,
        audience=audience,
        objective=objective,
        region=region,
        platform=platform,
        status="running",
        discovered_leads_count=0,
        qualified_leads_count=0,
        drafted_outreach_count=0,
        summary_json="{}",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        insights = generate_and_store_insights(
            db=db,
            seed_text=seed_text,
            product_data={"niche": niche, "audience": audience, "objective": objective},
        )
        run.insight_topic = insights.get("topic")
        trend_context = _extract_trend_context(str(insights.get("raw_data", "{}")))

        experiment, variants = create_viral_experiment(
            db=db,
            user_id=user_id,
            video_id=video_id,
            niche=niche,
            audience=audience,
            objective=objective,
            problem_angle=problem_angle,
            offer=offer,
            tone=tone,
            platform=platform,
            trend_context=trend_context,
            variants_count=variants_count,
        )
        run.experiment_id = experiment.id

        recommendation = get_experiment_recommendation(db=db, experiment_id=experiment.id)
        selected_variant_id = recommendation.get("winner_variant_id")
        run.selected_variant_id = selected_variant_id

        leads = discover_leads(
            db=db,
            seed_text=seed_text,
            region=region,
            industry=niche,
            limit=leads_count,
        )
        run.discovered_leads_count = len(leads)

        qualified = 0
        drafted = 0
        for lead in leads:
            scored = score_lead(
                db=db,
                lead_id=lead.id,
                icp_industry=niche,
                icp_region=region,
                min_company_size=10,
                max_company_size=20_000,
            )
            if scored.status == "qualified":
                qualified += 1
            drafted_lead = create_outreach_draft(
                db=db,
                lead_id=lead.id,
                product_name="Autoviral",
                offer_text=offer or "growth sprint + conversion uplift",
                channel="email",
            )
            if drafted_lead.status == "drafted":
                drafted += 1

        run.qualified_leads_count = qualified
        run.drafted_outreach_count = drafted

        chosen_variant: ViralVariant | None = None
        if selected_variant_id is not None:
            chosen_variant = db.get(ViralVariant, selected_variant_id)

        summary = {
            "insight": insights,
            "experiment": {
                "id": experiment.id,
                "baseline_score": experiment.baseline_score,
                "variants_count": len(variants),
            },
            "selected_variant": {
                "id": chosen_variant.id if chosen_variant else None,
                "variant_key": chosen_variant.variant_key if chosen_variant else None,
                "hook": chosen_variant.hook if chosen_variant else None,
                "script": chosen_variant.script if chosen_variant else None,
                "cta": chosen_variant.cta if chosen_variant else None,
                "caption": chosen_variant.caption if chosen_variant else None,
                "hashtags": chosen_variant.hashtags if chosen_variant else None,
            },
            "recommendation": recommendation,
            "sales": {
                "discovered": run.discovered_leads_count,
                "qualified": run.qualified_leads_count,
                "drafted_outreach": run.drafted_outreach_count,
            },
        }
        run.summary_json = json.dumps(summary, ensure_ascii=False)
        run.status = "completed"
        run.error_message = None
        db.commit()
        db.refresh(run)
        return run
    except Exception as err:
        run.status = "failed"
        run.error_message = str(err)
        db.commit()
        db.refresh(run)
        return run


def list_autonomous_runs(db: Session, *, user_id: int | None = None) -> list[AutonomousRun]:
    statement: Select[tuple[AutonomousRun]] = select(AutonomousRun).order_by(AutonomousRun.id.desc())
    if user_id is not None:
        statement = statement.where(AutonomousRun.user_id == user_id)
    return list(db.scalars(statement).all())


def get_autonomous_run(db: Session, *, run_id: int) -> AutonomousRun:
    row = db.get(AutonomousRun, run_id)
    if row is None:
        raise ValueError("Autonomous run not found")
    return row


def get_autonomous_dashboard(db: Session, *, user_id: int | None = None) -> dict:
    runs = list_autonomous_runs(db, user_id=user_id)
    if not runs:
        return {
            "total_runs": 0,
            "completed_runs": 0,
            "failed_runs": 0,
            "success_rate": 0.0,
            "avg_discovered_leads": 0.0,
            "avg_qualified_leads": 0.0,
            "avg_drafted_outreach": 0.0,
            "latest_experiment_ids": [],
        }

    completed = [row for row in runs if row.status == "completed"]
    failed = [row for row in runs if row.status == "failed"]
    success_rate = round((len(completed) / len(runs)) * 100, 2)
    avg_discovered = round(sum(row.discovered_leads_count for row in runs) / len(runs), 2)
    avg_qualified = round(sum(row.qualified_leads_count for row in runs) / len(runs), 2)
    avg_drafted = round(sum(row.drafted_outreach_count for row in runs) / len(runs), 2)
    latest_experiment_ids = [row.experiment_id for row in runs[:5] if row.experiment_id is not None]

    return {
        "total_runs": len(runs),
        "completed_runs": len(completed),
        "failed_runs": len(failed),
        "success_rate": success_rate,
        "avg_discovered_leads": avg_discovered,
        "avg_qualified_leads": avg_qualified,
        "avg_drafted_outreach": avg_drafted,
        "latest_experiment_ids": latest_experiment_ids,
    }

