def _create_user_and_video(client):
    user_resp = client.post(
        "/api/v1/users/",
        json={
            "email": "plan@example.com",
            "password": "password123",
            "name": "Plan User",
        },
    )
    assert user_resp.status_code == 201
    user = user_resp.json()

    human_resp = client.post(
        "/api/v1/synthetic-humans/",
        json={
            "name": "Plan Human",
            "age": 28,
            "gender": "male",
            "style": "formal",
            "user_id": user["id"],
        },
    )
    assert human_resp.status_code == 201
    human = human_resp.json()

    video_resp = client.post(
        "/api/v1/videos/",
        json={
            "title": "Plan baseline",
            "status": "completed",
            "file_path": "/tmp/plan.mp4",
            "human_id": human["id"],
            "user_id": user["id"],
        },
    )
    assert video_resp.status_code == 201
    return user, video_resp.json()


def test_autonomous_plan_scheduler_tick_flow(client):
    user, video = _create_user_and_video(client)

    plan_resp = client.post(
        "/api/v1/autonomous/plans",
        json={
            "user_id": user["id"],
            "video_id": video["id"],
            "name": "Daily skincare cycle",
            "seed_text": "konten skincare untuk leads",
            "niche": "skincare",
            "audience": "women 20-35",
            "objective": "increase leads",
            "problem_angle": "retention bagus tapi DM rendah",
            "offer": "free funnel audit",
            "tone": "direct",
            "platform": "tiktok",
            "region": "ID",
            "leads_count": 3,
            "variants_count": 3,
            "interval_minutes": 60,
            "is_active": True,
        },
    )
    assert plan_resp.status_code == 201
    plan = plan_resp.json()
    assert plan["is_active"] is True
    assert plan["next_run_at"] is not None

    tick_resp = client.post("/api/v1/autonomous/scheduler/tick")
    assert tick_resp.status_code == 200
    tick_payload = tick_resp.json()
    assert tick_payload["executed_runs"] >= 1
    assert len(tick_payload["run_ids"]) >= 1

    list_runs = client.get(f"/api/v1/autonomous/runs?user_id={user['id']}")
    assert list_runs.status_code == 200
    runs_payload = list_runs.json()
    assert runs_payload["count"] >= 1
    assert runs_payload["runs"][0]["status"] == "completed"

    list_plans = client.get(f"/api/v1/autonomous/plans?user_id={user['id']}&active_only=true")
    assert list_plans.status_code == 200
    plans_payload = list_plans.json()
    assert plans_payload["count"] >= 1
    returned_plan = plans_payload["plans"][0]
    assert returned_plan["last_status"] in {"completed", "failed"}
    assert returned_plan["last_run_at"] is not None

    deactivate = client.post(
        f"/api/v1/autonomous/plans/{plan['id']}/active",
        json={"is_active": False},
    )
    assert deactivate.status_code == 200
    updated_plan = deactivate.json()
    assert updated_plan["is_active"] is False
    assert updated_plan["next_run_at"] is None
