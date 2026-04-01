from celery import shared_task
from sqlalchemy.orm import Session

from core.database import SessionLocal
from services.autonomous_orchestrator_service import run_autonomous_cycle


@shared_task(name="autoviral.tasks.run_autonomous_cycle")
def run_autonomous_cycle_task(payload: dict) -> dict:
    db: Session = SessionLocal()
    try:
        row = run_autonomous_cycle(
            db=db,
            user_id=int(payload["user_id"]),
            video_id=payload.get("video_id"),
            seed_text=str(payload["seed_text"]),
            niche=str(payload["niche"]),
            audience=str(payload["audience"]),
            objective=str(payload["objective"]),
            problem_angle=str(payload["problem_angle"]),
            offer=payload.get("offer"),
            tone=str(payload.get("tone", "direct")),
            platform=str(payload.get("platform", "tiktok")),
            region=str(payload.get("region", "ID")),
            leads_count=int(payload.get("leads_count", 5)),
            variants_count=int(payload.get("variants_count", 3)),
        )
        return {
            "id": row.id,
            "status": row.status,
            "experiment_id": row.experiment_id,
            "selected_variant_id": row.selected_variant_id,
            "discovered_leads_count": row.discovered_leads_count,
            "qualified_leads_count": row.qualified_leads_count,
            "drafted_outreach_count": row.drafted_outreach_count,
        }
    finally:
        db.close()


@shared_task(name="autoviral.tasks.healthcheck")
def celery_healthcheck_task() -> dict:
    return {"ok": True, "service": "celery"}
