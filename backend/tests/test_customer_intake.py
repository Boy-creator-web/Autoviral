def test_customer_intake_create_and_list(client):
    create_resp = client.post(
        "/api/v1/customer-intake/",
        json={
            "full_name": "Budi Santoso",
            "email": "budi@bisnis.id",
            "phone": "+628123456789",
            "business_name": "PT Bisnis Maju",
            "niche": "retail",
            "product_name": "Paket Membership Retail Booster",
            "product_category": "Konsultan Bisnis",
            "product_price_range": "Rp1.000.000 - Rp5.000.000",
            "business_model": "b2b",
            "target_customer_profile": "Pemilik UMKM retail dengan 2-5 cabang",
            "target_region": "Jabodetabek",
            "main_platforms": "TikTok, Instagram",
            "primary_kpi": "qualified_leads",
            "current_monthly_leads": 120,
            "current_conversion_rate_percent": 4.2,
            "sales_cycle_days": 14,
            "monthly_marketing_budget": 25000000,
            "preferred_contact_time": "Senin-Jumat 09.00-17.00",
            "monthly_revenue_target": 150000000,
            "preferred_plan": "growth",
            "pain_point": "Konten banyak views tapi closing rendah.",
            "desired_outcome": "Naikkan closing rate dan stabilkan leads mingguan.",
            "source": "synapsetech.my.id",
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["id"] > 0
    assert created["status"] == "new"
    assert created["business_name"] == "PT Bisnis Maju"
    assert created["product_name"] == "Paket Membership Retail Booster"
    assert created["primary_kpi"] == "qualified_leads"

    list_resp = client.get("/api/v1/customer-intake/")
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert payload["count"] >= 1
    assert payload["items"][0]["email"] == "budi@bisnis.id"


def test_confirm_payment_and_start_engine_flow(client):
    create_resp = client.post(
        "/api/v1/customer-intake/",
        json={
            "full_name": "Andi Pratama",
            "email": "andi@bisnis.id",
            "phone": "+6282111122233",
            "business_name": "PT Andi Growth",
            "niche": "edukasi",
            "product_name": "Kelas Public Speaking",
            "product_category": "Edukasi",
            "product_price_range": "Rp250.000 - Rp1.000.000",
            "business_model": "b2c",
            "target_customer_profile": "Profesional muda usia 22-35",
            "target_region": "Indonesia",
            "main_platforms": "TikTok, Instagram",
            "primary_kpi": "qualified_leads",
            "current_monthly_leads": 80,
            "current_conversion_rate_percent": 3.5,
            "sales_cycle_days": 10,
            "monthly_marketing_budget": 15000000,
            "preferred_contact_time": "Senin-Jumat 10.00-16.00",
            "monthly_revenue_target": 90000000,
            "preferred_plan": "growth",
            "pain_point": "Leads masuk belum stabil dan follow-up lambat.",
            "desired_outcome": "Leads naik 2x dan closing lebih cepat.",
            "source": "synapsetech.my.id",
        },
    )
    assert create_resp.status_code == 201
    intake = create_resp.json()
    intake_id = intake["id"]

    fail_start = client.post(
        "/api/v1/customer-intake/start-engine",
        json={
            "intake_id": intake_id,
            "started_by": "owner",
            "interval_minutes": 1440,
            "plan_name": "Paid Client Run",
            "run_now": True,
        },
    )
    assert fail_start.status_code == 400
    assert "Payment is not confirmed" in fail_start.json()["detail"]

    pay_resp = client.post(
        "/api/v1/customer-intake/confirm-payment",
        json={
            "intake_id": intake_id,
            "payment_reference": "MID-20260401-0001",
            "payment_method": "midtrans",
            "payment_amount": 2500000,
        },
    )
    assert pay_resp.status_code == 200
    paid = pay_resp.json()
    assert paid["payment_status"] == "paid"
    assert paid["payment_reference"] == "MID-20260401-0001"

    start_resp = client.post(
        "/api/v1/customer-intake/start-engine",
        json={
            "intake_id": intake_id,
            "started_by": "owner",
            "interval_minutes": 1440,
            "plan_name": "Paid Client Run",
            "run_now": True,
        },
    )
    assert start_resp.status_code == 200
    started = start_resp.json()
    assert started["intake"]["engine_status"] == "running"
    assert started["intake"]["engine_plan_id"] is not None
    assert started["plan"]["id"] is not None
    if started["run"] is not None:
        assert started["run"]["status"] in {"completed", "failed"}
