from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.user import User
from models.video import Video
from models.viral_experiment import ViralExperiment
from models.viral_metric import ViralMetric
from models.viral_variant import ViralVariant


@dataclass(frozen=True)
class _Prediction:
    hook_rate: float
    watch_rate: float
    share_rate: float
    save_rate: float
    score: float


def _clamp01(value: float) -> float:
    return max(0.0, min(value, 1.0))


def _normalize_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return _clamp01(numerator / denominator)


def _score_from_metrics(
    *,
    hook_rate: float,
    watch_rate: float,
    share_rate: float,
    save_rate: float,
    conversion_rate: float,
) -> float:
    return round(
        _clamp01(
            (hook_rate * 0.28)
            + (watch_rate * 0.30)
            + (share_rate * 0.17)
            + (save_rate * 0.15)
            + (conversion_rate * 0.10)
        ),
        4,
    )


def _predict_variant(
    *,
    objective: str,
    tone: str,
    hook: str,
    cta: str,
    seed: int,
) -> _Prediction:
    objective_low = objective.lower()
    tone_low = tone.lower()
    hook_low = hook.lower()
    cta_low = cta.lower()

    hook_rate = 0.32 + (0.03 * (seed % 3))
    if any(token in hook_low for token in ("cara", "how", "rahasia", "secret", "mistake", "error")):
        hook_rate += 0.08
    if any(token in hook_low for token in ("3", "5", "7", "langkah", "step")):
        hook_rate += 0.05
    if tone_low in {"direct", "bold"}:
        hook_rate += 0.03

    watch_rate = 0.24 + (0.02 * (seed % 4))
    if "education" in objective_low or "awareness" in objective_low:
        watch_rate += 0.08
    if "lead" in objective_low or "sales" in objective_low:
        watch_rate += 0.04

    share_rate = 0.05 + (0.01 * (seed % 5))
    if any(token in hook_low for token in ("template", "framework", "checklist")):
        share_rate += 0.04
    if "share" in cta_low:
        share_rate += 0.03

    save_rate = 0.04 + (0.012 * (seed % 4))
    if any(token in hook_low for token in ("checklist", "formula", "script")):
        save_rate += 0.05
    if "save" in cta_low:
        save_rate += 0.03

    score = _score_from_metrics(
        hook_rate=_clamp01(hook_rate),
        watch_rate=_clamp01(watch_rate),
        share_rate=_clamp01(share_rate),
        save_rate=_clamp01(save_rate),
        conversion_rate=0.03 + (0.01 * (seed % 3)),
    )
    return _Prediction(
        hook_rate=round(_clamp01(hook_rate), 4),
        watch_rate=round(_clamp01(watch_rate), 4),
        share_rate=round(_clamp01(share_rate), 4),
        save_rate=round(_clamp01(save_rate), 4),
        score=score,
    )


def _default_hook_bank(niche: str, objective: str, problem_angle: str) -> list[str]:
    return [
        f"3 kesalahan {niche} yang bikin {objective} gagal",
        f"Cara cepat selesaikan {problem_angle} tanpa buang budget",
        f"Framework 30 detik untuk naikkan {objective} di {niche}",
    ]


def _default_cta_bank(objective: str) -> list[str]:
    return [
        f"Ketik 'PLAN' untuk template {objective}",
        "Save video ini untuk dipraktikkan hari ini",
        "Share ke tim kamu yang pegang konten",
    ]


def _build_script(*, hook: str, problem_angle: str, offer: str | None, cta: str) -> str:
    offer_line = offer or "audit mini 15 menit tanpa biaya"
    return (
        f"Hook: {hook}\n"
        f"Problem: Banyak tim stuck karena {problem_angle}.\n"
        "Insight: Fokus ke retention 3 detik pertama + CTA tunggal.\n"
        f"Offer: {offer_line}.\n"
        f"CTA: {cta}."
    )


def _build_caption(*, niche: str, objective: str, hook: str) -> str:
    return f"{hook} | Niche: {niche}. Fokus hari ini: {objective}."


def _derive_hashtags(niche: str, objective: str, platform: str) -> str:
    tokens = [niche, objective, platform, "autoviral", "growth", "contentstrategy"]
    normalized = ["#" + item.lower().replace(" ", "") for item in tokens if item.strip()]
    return " ".join(dict.fromkeys(normalized))


def create_experiment(
    db: Session,
    *,
    user_id: int,
    video_id: int | None,
    niche: str,
    audience: str,
    objective: str,
    problem_angle: str,
    offer: str | None,
    tone: str,
    platform: str,
    trend_context: str | None,
    variants_count: int = 3,
) -> tuple[ViralExperiment, list[ViralVariant]]:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    if video_id is not None and db.get(Video, video_id) is None:
        raise ValueError("Video not found")
    if variants_count < 2:
        raise ValueError("variants_count must be >= 2")

    experiment = ViralExperiment(
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
        status="running",
        baseline_score=0.0,
    )
    db.add(experiment)
    db.flush()

    hooks = _default_hook_bank(niche, objective, problem_angle)
    ctas = _default_cta_bank(objective)
    rows: list[ViralVariant] = []
    score_sum = 0.0

    for idx in range(variants_count):
        key = chr(ord("A") + idx)
        hook = hooks[idx % len(hooks)]
        cta = ctas[idx % len(ctas)]
        prediction = _predict_variant(
            objective=objective,
            tone=tone,
            hook=hook,
            cta=cta,
            seed=idx + 1,
        )
        variant = ViralVariant(
            experiment_id=experiment.id,
            variant_key=key,
            hook=hook,
            script=_build_script(hook=hook, problem_angle=problem_angle, offer=offer, cta=cta),
            cta=cta,
            caption=_build_caption(niche=niche, objective=objective, hook=hook),
            hashtags=_derive_hashtags(niche=niche, objective=objective, platform=platform),
            duration_target_sec=30 if platform.lower() in {"tiktok", "instagram"} else 45,
            predicted_hook_rate=prediction.hook_rate,
            predicted_watch_rate=prediction.watch_rate,
            predicted_share_rate=prediction.share_rate,
            predicted_save_rate=prediction.save_rate,
            predicted_score=prediction.score,
        )
        db.add(variant)
        rows.append(variant)
        score_sum += prediction.score

    experiment.baseline_score = round(score_sum / len(rows), 4)
    db.commit()
    db.refresh(experiment)
    for row in rows:
        db.refresh(row)
    return experiment, rows


def create_viral_experiment(**kwargs):
    return create_experiment(**kwargs)


def list_experiments(db: Session, *, user_id: int | None = None, status: str | None = None) -> list[ViralExperiment]:
    statement: Select[tuple[ViralExperiment]] = select(ViralExperiment).order_by(ViralExperiment.id.desc())
    if user_id is not None:
        statement = statement.where(ViralExperiment.user_id == user_id)
    if status is not None:
        statement = statement.where(ViralExperiment.status == status)
    return list(db.scalars(statement).all())


def list_variants(db: Session, *, experiment_id: int) -> list[ViralVariant]:
    experiment = db.get(ViralExperiment, experiment_id)
    if experiment is None:
        raise ValueError("Experiment not found")
    statement: Select[tuple[ViralVariant]] = (
        select(ViralVariant)
        .where(ViralVariant.experiment_id == experiment_id)
        .order_by(ViralVariant.predicted_score.desc(), ViralVariant.id)
    )
    return list(db.scalars(statement).all())


def ingest_variant_metric(
    db: Session,
    *,
    variant_id: int,
    impressions: int,
    views_3s: int,
    views_10s: int,
    completions: int,
    likes: int,
    comments: int,
    shares: int,
    saves: int,
    profile_visits: int,
    link_clicks: int,
    watch_time_avg_sec: float,
    conversion_events: int,
) -> ViralMetric:
    variant = db.get(ViralVariant, variant_id)
    if variant is None:
        raise ValueError("Variant not found")

    row = ViralMetric(
        variant_id=variant_id,
        impressions=max(impressions, 0),
        views_3s=max(views_3s, 0),
        views_10s=max(views_10s, 0),
        completions=max(completions, 0),
        likes=max(likes, 0),
        comments=max(comments, 0),
        shares=max(shares, 0),
        saves=max(saves, 0),
        profile_visits=max(profile_visits, 0),
        link_clicks=max(link_clicks, 0),
        watch_time_avg_sec=max(watch_time_avg_sec, 0.0),
        conversion_events=max(conversion_events, 0),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_experiment_recommendation(db: Session, *, experiment_id: int) -> dict:
    experiment = db.get(ViralExperiment, experiment_id)
    if experiment is None:
        raise ValueError("Experiment not found")

    variants = list_variants(db, experiment_id=experiment_id)
    if not variants:
        return {"experiment_id": experiment_id, "winner_variant_id": None, "summary": "No variants found", "actions": []}

    metrics_by_variant: dict[int, list[ViralMetric]] = defaultdict(list)
    statement: Select[tuple[ViralMetric]] = (
        select(ViralMetric)
        .join(ViralVariant, ViralVariant.id == ViralMetric.variant_id)
        .where(ViralVariant.experiment_id == experiment_id)
    )
    for row in db.scalars(statement).all():
        metrics_by_variant[row.variant_id].append(row)

    scored_rows: list[tuple[ViralVariant, float, dict[str, float]]] = []
    for variant in variants:
        rows = metrics_by_variant.get(variant.id, [])
        if not rows:
            scored_rows.append(
                (
                    variant,
                    variant.predicted_score,
                    {
                        "hook_rate": variant.predicted_hook_rate,
                        "watch_rate": variant.predicted_watch_rate,
                        "share_rate": variant.predicted_share_rate,
                        "save_rate": variant.predicted_save_rate,
                        "conversion_rate": 0.0,
                    },
                )
            )
            continue

        impressions = sum(item.impressions for item in rows)
        views_3s = sum(item.views_3s for item in rows)
        completions = sum(item.completions for item in rows)
        shares = sum(item.shares for item in rows)
        saves = sum(item.saves for item in rows)
        conversions = sum(item.conversion_events for item in rows)

        hook_rate = _normalize_rate(views_3s, impressions)
        watch_rate = _normalize_rate(completions, views_3s)
        share_rate = _normalize_rate(shares, views_3s)
        save_rate = _normalize_rate(saves, views_3s)
        conversion_rate = _normalize_rate(conversions, impressions)
        real_score = _score_from_metrics(
            hook_rate=hook_rate,
            watch_rate=watch_rate,
            share_rate=share_rate,
            save_rate=save_rate,
            conversion_rate=conversion_rate,
        )
        scored_rows.append(
            (
                variant,
                real_score,
                {
                    "hook_rate": round(hook_rate, 4),
                    "watch_rate": round(watch_rate, 4),
                    "share_rate": round(share_rate, 4),
                    "save_rate": round(save_rate, 4),
                    "conversion_rate": round(conversion_rate, 4),
                },
            )
        )

    scored_rows.sort(key=lambda item: item[1], reverse=True)
    winner, winner_score, winner_breakdown = scored_rows[0]
    runner_up_score = scored_rows[1][1] if len(scored_rows) > 1 else winner_score

    actions = [
        f"Scale variant {winner.variant_key} as default creative for next batch",
        "Keep first 2 seconds hook exactly as winner script",
    ]
    if winner_breakdown["watch_rate"] < 0.35:
        actions.append("Shorten script by 20% and move CTA to mid-roll")
    if winner_breakdown["share_rate"] < 0.08:
        actions.append("Add checklist/framework framing to encourage shares")
    if winner_breakdown["conversion_rate"] < 0.015:
        actions.append("Strengthen offer clarity and add one frictionless CTA keyword")

    confidence = round(_clamp01(0.55 + (winner_score - runner_up_score)), 4)
    return {
        "experiment_id": experiment.id,
        "winner_variant_id": winner.id,
        "winner_variant_key": winner.variant_key,
        "winner_score": round(winner_score, 4),
        "confidence": confidence,
        "metric_breakdown": winner_breakdown,
        "summary": (
            f"Variant {winner.variant_key} currently leads with score {round(winner_score, 4)} "
            f"for objective '{experiment.objective}'."
        ),
        "actions": actions,
    }
