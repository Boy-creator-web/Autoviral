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
