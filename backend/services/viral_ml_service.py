from __future__ import annotations

import json
import math
from dataclasses import dataclass

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.viral_model_snapshot import ViralModelSnapshot
from models.viral_metric import ViralMetric
from models.viral_variant import ViralVariant


FEATURE_NAMES = [
    "bias_token",
    "objective_has_sales",
    "objective_has_education",
    "tone_direct_or_bold",
    "hook_has_how_or_secret",
    "hook_has_number",
    "hook_has_framework",
    "cta_has_save",
    "cta_has_share",
    "duration_norm",
    "niche_token_len_norm",
    "platform_is_short_video",
]


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
    return _clamp01(
        (hook_rate * 0.28)
        + (watch_rate * 0.30)
        + (share_rate * 0.17)
        + (save_rate * 0.15)
        + (conversion_rate * 0.10)
    )


def _contains_any(text: str, tokens: tuple[str, ...]) -> float:
    low = text.lower()
    return 1.0 if any(token in low for token in tokens) else 0.0


def extract_features(
    *,
    objective: str,
    tone: str,
    hook: str,
    cta: str,
    niche: str,
    platform: str,
    duration_target_sec: int,
) -> dict[str, float]:
    return {
        "bias_token": 1.0,
        "objective_has_sales": _contains_any(objective, ("sales", "lead", "conversion", "closing")),
        "objective_has_education": _contains_any(objective, ("education", "awareness", "teach", "learn")),
        "tone_direct_or_bold": 1.0 if tone.lower() in {"direct", "bold"} else 0.0,
        "hook_has_how_or_secret": _contains_any(hook, ("cara", "how", "secret", "rahasia", "mistake", "error")),
        "hook_has_number": 1.0 if any(ch.isdigit() for ch in hook) else 0.0,
        "hook_has_framework": _contains_any(hook, ("framework", "checklist", "template", "formula")),
        "cta_has_save": _contains_any(cta, ("save", "simpan")),
        "cta_has_share": _contains_any(cta, ("share", "bagikan")),
        "duration_norm": min(max(duration_target_sec, 5), 180) / 180.0,
        "niche_token_len_norm": min(len(niche.strip()), 40) / 40.0,
        "platform_is_short_video": 1.0 if platform.lower() in {"tiktok", "instagram", "reels", "shorts"} else 0.0,
    }


@dataclass(frozen=True)
class ModelBundle:
    snapshot_id: int
    feature_names: list[str]
    weights: list[float]
    bias: float
    means: list[float]
    stds: list[float]


def _build_training_dataset(db: Session) -> tuple[list[list[float]], list[float]]:
    statement: Select[tuple[ViralMetric]] = (
        select(ViralMetric)
        .join(ViralVariant, ViralVariant.id == ViralMetric.variant_id)
        .where(ViralMetric.impressions > 0)
    )
    rows = list(db.scalars(statement).all())
    x_data: list[list[float]] = []
    y_data: list[float] = []
    for metric in rows:
        variant = metric.variant
        impressions = metric.impressions
        views_3s = metric.views_3s
        completions = metric.completions
        shares = metric.shares
        saves = metric.saves
        conversions = metric.conversion_events
        label = _score_from_metrics(
            hook_rate=_normalize_rate(views_3s, impressions),
            watch_rate=_normalize_rate(completions, views_3s),
            share_rate=_normalize_rate(shares, views_3s),
            save_rate=_normalize_rate(saves, views_3s),
            conversion_rate=_normalize_rate(conversions, impressions),
        )
        objective = variant.experiment.objective if variant.experiment else "general"
        tone = variant.experiment.tone if variant.experiment else "direct"
        niche = variant.experiment.niche if variant.experiment else "general"
        platform = variant.experiment.platform if variant.experiment else "tiktok"
        feats = extract_features(
            objective=objective,
            tone=tone,
            hook=variant.hook,
            cta=variant.cta,
            niche=niche,
            platform=platform,
            duration_target_sec=variant.duration_target_sec,
        )
        x_data.append([feats[name] for name in FEATURE_NAMES])
        y_data.append(label)
    return x_data, y_data


def _standardize(x_data: list[list[float]]) -> tuple[list[list[float]], list[float], list[float]]:
    if not x_data:
        return [], [], []
    feature_count = len(x_data[0])
    means = [0.0] * feature_count
    stds = [1.0] * feature_count
    for col in range(feature_count):
        vals = [row[col] for row in x_data]
        mean = sum(vals) / len(vals)
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        std = math.sqrt(variance) or 1.0
        means[col] = mean
        stds[col] = std
    standardized = []
    for row in x_data:
        standardized.append([(row[i] - means[i]) / stds[i] for i in range(feature_count)])
    return standardized, means, stds


def _fit_linear_regression_gd(
    x_data: list[list[float]],
    y_data: list[float],
    *,
    lr: float = 0.08,
    epochs: int = 450,
) -> tuple[list[float], float]:
    feature_count = len(x_data[0])
    weights = [0.0] * feature_count
    bias = 0.0
    n = len(x_data)
    for _ in range(epochs):
        grad_w = [0.0] * feature_count
        grad_b = 0.0
        for i in range(n):
            prediction = sum(weights[j] * x_data[i][j] for j in range(feature_count)) + bias
            error = prediction - y_data[i]
            for j in range(feature_count):
                grad_w[j] += (2.0 / n) * error * x_data[i][j]
            grad_b += (2.0 / n) * error
        for j in range(feature_count):
            weights[j] -= lr * grad_w[j]
        bias -= lr * grad_b / n
    return weights, bias


def _mae(x_data: list[list[float]], y_data: list[float], weights: list[float], bias: float) -> float:
    errors = []
    for i in range(len(x_data)):
        pred = sum(weights[j] * x_data[i][j] for j in range(len(weights))) + bias
        errors.append(abs(pred - y_data[i]))
    return round(sum(errors) / len(errors), 6) if errors else 0.0


def train_viral_model(db: Session, *, activate: bool = True) -> ViralModelSnapshot:
    x_data, y_data = _build_training_dataset(db)
    if len(x_data) < 5:
        raise ValueError("Not enough training samples. Need at least 5 metric rows.")

    x_std, means, stds = _standardize(x_data)
    weights, bias = _fit_linear_regression_gd(x_std, y_data)
    mae = _mae(x_std, y_data, weights, bias)

    if activate:
        for row in db.scalars(select(ViralModelSnapshot).where(ViralModelSnapshot.is_active.is_(True))).all():
            row.is_active = False
        db.flush()

    snapshot = ViralModelSnapshot(
        model_type="linear_regression_gd",
        sample_count=len(x_data),
        mae=mae,
        feature_names_json=json.dumps(FEATURE_NAMES),
        weights_json=json.dumps(weights),
        normalization_json=json.dumps({"means": means, "stds": stds}),
        bias=bias,
        metadata_json=json.dumps({"epochs": 450, "learning_rate": 0.08}),
        is_active=activate,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_active_model_bundle(db: Session) -> ModelBundle | None:
    snapshot = db.scalar(
        select(ViralModelSnapshot)
        .where(ViralModelSnapshot.is_active.is_(True))
        .order_by(ViralModelSnapshot.id.desc())
    )
    if snapshot is None:
        return None
    feature_names = json.loads(snapshot.feature_names_json or "[]")
    weights = json.loads(snapshot.weights_json or "[]")
    normalization = json.loads(snapshot.normalization_json or "{}")
    means = normalization.get("means", [])
    stds = normalization.get("stds", [])
    if not feature_names or not weights or len(feature_names) != len(weights):
        return None
    if len(means) != len(weights) or len(stds) != len(weights):
        means = [0.0] * len(weights)
        stds = [1.0] * len(weights)
    return ModelBundle(
        snapshot_id=snapshot.id,
        feature_names=feature_names,
        weights=weights,
        bias=snapshot.bias,
        means=means,
        stds=[val if val != 0 else 1.0 for val in stds],
    )


def predict_with_active_model(
    db: Session,
    *,
    objective: str,
    tone: str,
    hook: str,
    cta: str,
    niche: str,
    platform: str,
    duration_target_sec: int,
) -> tuple[float, bool, int | None, dict[str, float]]:
    features = extract_features(
        objective=objective,
        tone=tone,
        hook=hook,
        cta=cta,
        niche=niche,
        platform=platform,
        duration_target_sec=duration_target_sec,
    )
    bundle = get_active_model_bundle(db)
    if bundle is None:
        # No model available yet; caller can fallback.
        return 0.0, False, None, features

    values = [features.get(name, 0.0) for name in bundle.feature_names]
    standardized = [(values[i] - bundle.means[i]) / bundle.stds[i] for i in range(len(values))]
    prediction = sum(bundle.weights[i] * standardized[i] for i in range(len(values))) + bundle.bias
    return _clamp01(prediction), True, bundle.snapshot_id, features
