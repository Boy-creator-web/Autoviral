def test_customer_intake_create_and_list(client):
    create_resp = client.post(
        "/api/v1/customer-intake/",
        json={
            "full_name": "Budi Santoso",
            "email": "budi@bisnis.id",
            "phone": "+628123456789",
            "business_name": "PT Bisnis Maju",
            "niche": "retail",
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

    list_resp = client.get("/api/v1/customer-intake/")
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert payload["count"] >= 1
    assert payload["items"][0]["email"] == "budi@bisnis.id"
