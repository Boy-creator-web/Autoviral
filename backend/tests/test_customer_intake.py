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


def test_midtrans_webhook_confirms_payment(client, monkeypatch):
    monkeypatch.setattr(
        "services.customer_intake_service.settings.midtrans_server_key",
        "test-server-key",
    )

    create_resp = client.post(
        "/api/v1/customer-intake/",
        json={
            "full_name": "Rina Maharani",
            "email": "rina@bisnis.id",
            "phone": "+6281222233344",
            "business_name": "Rina Digital",
            "niche": "fashion",
            "product_name": "Kelas Branding Fashion",
            "product_category": "Edukasi",
            "product_price_range": "Rp500.000 - Rp2.000.000",
            "business_model": "b2c",
            "target_customer_profile": "Owner brand fashion lokal",
            "target_region": "Indonesia",
            "main_platforms": "TikTok, Instagram",
            "primary_kpi": "sales_conversion",
            "current_monthly_leads": 60,
            "current_conversion_rate_percent": 2.8,
            "sales_cycle_days": 12,
            "monthly_marketing_budget": 10000000,
            "preferred_contact_time": "Senin-Jumat 09.00-18.00",
            "monthly_revenue_target": 120000000,
            "preferred_plan": "growth",
            "pain_point": "Leads lumayan tapi conversion rendah.",
            "desired_outcome": "Conversion rate naik signifikan.",
            "source": "synapsetech.my.id",
        },
    )
    assert create_resp.status_code == 201
    intake_id = create_resp.json()["id"]

    order_id = f"INTAKE-{intake_id}"
    status_code = "200"
    gross_amount = "2500000.00"
    import hashlib

    signature = hashlib.sha512(
        f"{order_id}{status_code}{gross_amount}test-server-key".encode("utf-8")
    ).hexdigest()

    webhook_resp = client.post(
        "/api/v1/customer-intake/midtrans/webhook",
        json={
            "order_id": order_id,
            "status_code": status_code,
            "gross_amount": gross_amount,
            "signature_key": signature,
            "transaction_status": "settlement",
            "fraud_status": "accept",
            "payment_type": "qris",
        },
    )
    assert webhook_resp.status_code == 200
    payload = webhook_resp.json()
    assert payload["ok"] is True
    assert payload["updated"] is True
    assert payload["intake_id"] == intake_id

    rows_resp = client.get("/api/v1/customer-intake/")
    assert rows_resp.status_code == 200
    rows = rows_resp.json()["items"]
    row = next(item for item in rows if item["id"] == intake_id)
    assert row["payment_status"] == "paid"
    assert row["payment_reference"] == order_id


def test_ai_cs_chat_endpoint(client):
    resp = client.post(
        "/api/v1/customer-intake/ai-cs/chat",
        json={
            "message": "Bagaimana alur dari pembayaran sampai engine jalan otomatis?",
            "customer_name": "Raka",
            "business_name": "Raka Retail",
            "email": "raka@retail.id",
            "source": "synapsetech.my.id",
        },
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert "AI CS SynapseTech" in payload["reply"]
    assert "klik 'Kerjakan'" in payload["reply"]
    assert payload["handoff_required"] is False
    assert payload["suggested_plan"] in {"starter", "growth", "pro", "enterprise"}
    assert len(payload["suggested_actions"]) >= 1


def test_checkout_stores_social_credentials(client):
    create_resp = client.post(
        "/api/v1/customer-intake/",
        json={
            "full_name": "Sari Putri",
            "email": "sari@brand.id",
            "phone": "+6281333344455",
            "business_name": "Sari Brand",
            "niche": "beauty",
            "product_name": "Serum Glow",
            "product_category": "Skincare",
            "product_price_range": "Rp150.000 - Rp350.000",
            "business_model": "b2c",
            "target_customer_profile": "Wanita 20-35, aktif belanja online",
            "target_region": "Indonesia",
            "main_platforms": "Instagram, TikTok",
            "primary_kpi": "sales_conversion",
            "current_monthly_leads": 100,
            "current_conversion_rate_percent": 3.2,
            "sales_cycle_days": 7,
            "monthly_marketing_budget": 12000000,
            "preferred_contact_time": "Senin-Jumat 09.00-18.00",
            "monthly_revenue_target": 100000000,
            "preferred_plan": "growth",
            "pain_point": "Akun sosial aktif tapi closing kurang stabil.",
            "desired_outcome": "Leads dan conversion naik konsisten.",
            "source": "synapsetech.my.id",
        },
    )
    assert create_resp.status_code == 201
    intake_id = create_resp.json()["id"]

    checkout_resp = client.post(
        "/api/v1/customer-intake/checkout",
        json={
            "intake_id": intake_id,
            "payment_method": "midtrans",
            "preferred_plan": "pro",
            "social_accounts": [
                {
                    "platform": "instagram",
                    "username": "@saribrand",
                    "password": "ig-secret-pass",
                    "autopost_enabled": True,
                },
                {
                    "platform": "tiktok",
                    "username": "@saribrand.id",
                    "password": "tt-secret-pass",
                    "autopost_enabled": True,
                },
            ],
        },
    )
    assert checkout_resp.status_code == 200
    payload = checkout_resp.json()
    assert payload["intake"]["id"] == intake_id
    assert payload["intake"]["preferred_plan"] == "pro"
    assert payload["social_accounts_count"] == 2
    assert {item["platform"] for item in payload["social_accounts"]} == {"instagram", "tiktok"}

    get_resp = client.get(f"/api/v1/customer-intake/checkout/{intake_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["social_accounts_count"] >= 2
