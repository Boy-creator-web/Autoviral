from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.sales_lead import SalesLead


def _company_size_to_int(company_size: str) -> int:
    value = company_size.strip().lower()
    if value.isdigit():
        return int(value)
    if value in {"enterprise"}:
        return 5000
    if value in {"mid-market", "mid market"}:
        return 500
    if value in {"smb", "small", "startup"}:
        return 50
    return 100


def _compute_icp_score(*, industry: str, region: str, company_size: int, icp_industry: str, icp_region: str) -> float:
    score = 0.3
    if industry.strip().lower() == icp_industry.strip().lower():
        score += 0.35
    if region.strip().lower() == icp_region.strip().lower():
        score += 0.2
    if 20 <= company_size <= 5000:
        score += 0.15
    return min(score, 1.0)


def _compute_intent_score(seed_text: str) -> float:
    text = seed_text.lower()
    score = 0.35
    for keyword in ("sales", "lead", "closing", "pipeline", "roi", "conversion"):
        if keyword in text:
            score += 0.1
    return min(score, 1.0)


def _compute_final_score(icp_score: float, intent_score: float) -> float:
    return round(min((icp_score * 0.55) + (intent_score * 0.45), 1.0), 4)


def discover_leads(
    db: Session,
    *,
    seed_text: str,
    region: str,
    industry: str,
    limit: int,
) -> list[SalesLead]:
    if limit < 1:
        raise ValueError("limit must be >= 1")

    rows: list[SalesLead] = []
    intent_score = _compute_intent_score(seed_text)
    for idx in range(1, limit + 1):
        domain = f"{industry.lower()}-{idx}.example.com"
        email = f"decision-maker-{idx}@{domain}"
        existing = db.scalar(select(SalesLead).where(SalesLead.email == email))
        if existing is not None:
            rows.append(existing)
            continue

        company_size = 50 + (idx * 25)
        icp_score = _compute_icp_score(
            industry=industry,
            region=region,
            company_size=company_size,
            icp_industry=industry,
            icp_region=region,
        )
        lead_score = _compute_final_score(icp_score, intent_score)
        lead = SalesLead(
            company_name=f"{industry.title()} Growth Co {idx}",
            domain=domain,
            contact_name=f"Lead Owner {idx}",
            contact_role="Head of Growth",
            email=email,
            source="sales-intel-agent",
            icp_fit_score=icp_score,
            intent_score=intent_score,
            lead_score=lead_score,
            notes=f"Seed: {seed_text}; region={region}; industry={industry}; company_size={company_size}",
            status="new",
        )
        db.add(lead)
        rows.append(lead)

    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def list_leads(db: Session, stage: str | None = None, min_score: float | None = None) -> list[SalesLead]:
    statement: Select[tuple[SalesLead]] = select(SalesLead).order_by(SalesLead.lead_score.desc(), SalesLead.id)
    if stage:
        statement = statement.where(SalesLead.status == stage)
    if min_score is not None:
        statement = statement.where(SalesLead.lead_score >= min_score)
    return list(db.scalars(statement).all())


def score_lead(
    db: Session,
    *,
    lead_id: int,
    icp_industry: str,
    icp_region: str,
    min_company_size: int = 1,
    max_company_size: int = 100_000,
) -> SalesLead:
    lead = db.get(SalesLead, lead_id)
    if lead is None:
        raise ValueError("Lead not found")

    company_size = _company_size_to_int(lead.notes.split("company_size=")[-1].split(";")[0]) if "company_size=" in (lead.notes or "") else 100
    icp = _compute_icp_score(
        industry=icp_industry if not lead.notes else lead.notes.split("industry=")[-1].split(";")[0],
        region=icp_region if not lead.notes else lead.notes.split("region=")[-1].split(";")[0],
        company_size=company_size,
        icp_industry=icp_industry,
        icp_region=icp_region,
    )
    if company_size < min_company_size or company_size > max_company_size:
        icp = max(icp - 0.2, 0.0)

    lead.icp_fit_score = round(icp, 4)
    lead.lead_score = _compute_final_score(lead.icp_fit_score, lead.intent_score)
    lead.status = "qualified"
    db.commit()
    db.refresh(lead)
    return lead


def create_outreach_draft(db: Session, *, lead_id: int, product_name: str, offer_text: str, channel: str = "email") -> SalesLead:
    lead = db.get(SalesLead, lead_id)
    if lead is None:
        raise ValueError("Lead not found")

    channel_label = channel.lower()
    draft = (
        f"Hi {lead.contact_name}, saya dari tim {product_name}. "
        f"Kami melihat peluang peningkatan sales di {lead.company_name}. "
        f"Penawaran: {offer_text}. "
        "Jika berkenan, saya kirimkan mini audit pipeline penjualan 15 menit."
    )
    if channel_label == "email":
        draft = (
            f"Subject: Ide peningkatan sales untuk {lead.company_name}\n\n"
            f"Halo {lead.contact_name},\n\n"
            f"Saya dari {product_name}. {offer_text}.\n"
            "Kami bisa bantu naikkan lead-to-close conversion dengan eksperimen konten terukur.\n\n"
            "Jika cocok, saya kirimkan mini audit singkat.\n\nTerima kasih."
        )

    lead.outreach_draft = draft
    lead.status = "drafted"
    db.commit()
    db.refresh(lead)
    return lead

