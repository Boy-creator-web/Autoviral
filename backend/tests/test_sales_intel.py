def test_sales_intel_discover_score_and_outreach(client):
    discover_resp = client.post(
        "/api/v1/sales/discover",
        params={
            "industry": "retail",
            "region": "ID",
            "company_size": "mid-market",
            "count": 3,
        },
    )
    assert discover_resp.status_code == 201
    payload = discover_resp.json()
    assert payload["count"] == 3
    items = payload["items"]
    assert len(items) == 3

    first = items[0]
    lead_id = first["id"]
    assert first["company_name"]
    assert first["contact_email"]
    assert first["outreach_status"] == "new"
    assert first["priority_score"] >= 0

    score_resp = client.post(
        f"/api/v1/sales/score/{lead_id}",
        params={"icp_industry": "retail", "icp_region": "ID"},
    )
    assert score_resp.status_code == 200
    scored = score_resp.json()
    assert scored["id"] == lead_id
    assert scored["priority_score"] >= first["priority_score"]

    outreach_resp = client.post(f"/api/v1/sales/outreach/{lead_id}")
    assert outreach_resp.status_code == 200
    drafted = outreach_resp.json()
    assert drafted["id"] == lead_id
    assert drafted["outreach_status"] == "drafted"
    assert drafted["outreach_draft"]

    list_resp = client.get("/api/v1/sales/leads")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert listed["count"] == 3
