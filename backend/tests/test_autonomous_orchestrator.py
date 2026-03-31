def _create_user_and_video(client):
    user_resp = client.post(
        "/api/v1/users/",
        json={
            "email": "auto@example.com",
            "password": "password123",
            "name": "Auto User",
        },
    )
    assert user_resp.status_code == 201
    user = user_resp.json()

    human_resp = client.post(
        "/api/v1/synthetic-humans/",
        json={
            "name": "Auto Human",
            "age": 26,
            "gender": "female",
            "style": "business",
            "user_id": user["id"],
        },
    )
    assert human_resp.status_code == 201
    human = human_resp.json()

    video_resp = client.post(
        "/api/v1/videos/",
        json={
            "title": "Auto baseline",
            "status": "completed",
            "file_path": "/tmp/auto.mp4",
            "human_id": human["id"],
            "user_id": user["id"],
        },
    )
    assert video_resp.status_code == 201
    video = video_resp.json()
    return user, video


def test_autonomous_cycle_end_to_end(client):
    user, video = _create_user_and_video(client)

    run_resp = client.post(
        "/api/v1/autonomous/run",
        json={
            "user_id": user["id"],
            "video_id": video["id"],
            "seed_text": "konten skincare untuk meningkatkan lead",
            "niche": "skincare",
            "audience": "women 20-35",
            "objective": "increase sales leads",
            "problem_angle": "views bagus tapi conversion rendah",
            "offer": "free audit funnel",
            "tone": "direct",
            "platform": "tiktok",
            "region": "ID",
            "leads_count": 4,
            "variants_count": 3,
        },
    )
    assert run_resp.status_code == 201
    run = run_resp.json()
    assert run["status"] == "completed"
    assert run["experiment_id"] is not None
    assert run["selected_variant_id"] is not None
    assert run["discovered_leads_count"] == 4
    assert run["qualified_leads_count"] == 4
    assert run["drafted_outreach_count"] == 4
    assert "selected_variant" in run["summary"]

    run_id = run["id"]
    get_resp = client.get(f"/api/v1/autonomous/runs/{run_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == run_id
    assert fetched["status"] == "completed"

    list_resp = client.get(f"/api/v1/autonomous/runs?user_id={user['id']}")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert listed["count"] >= 1

    dashboard_resp = client.get(f"/api/v1/autonomous/dashboard?user_id={user['id']}")
    assert dashboard_resp.status_code == 200
    dashboard = dashboard_resp.json()
    assert dashboard["total_runs"] >= 1
    assert dashboard["completed_runs"] >= 1
    assert dashboard["success_rate"] >= 0
