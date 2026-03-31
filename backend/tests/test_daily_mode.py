def _create_user_and_video(client):
    user_resp = client.post(
        "/api/v1/users/",
        json={
            "email": "dailymode@example.com",
            "password": "password123",
            "name": "Daily Mode User",
        },
    )
    assert user_resp.status_code == 201
    user = user_resp.json()

    human_resp = client.post(
        "/api/v1/synthetic-humans/",
        json={
            "name": "Daily Human",
            "age": 25,
            "gender": "female",
            "style": "cinematic",
            "user_id": user["id"],
        },
    )
    assert human_resp.status_code == 201
    human = human_resp.json()

    video_resp = client.post(
        "/api/v1/videos/",
        json={
            "title": "Daily baseline",
            "status": "completed",
            "file_path": "/tmp/daily.mp4",
            "human_id": human["id"],
            "user_id": user["id"],
        },
    )
    assert video_resp.status_code == 201
    return user, video_resp.json()


def test_daily_mode_bootstrap_and_run(client):
    user, video = _create_user_and_video(client)

    response = client.post(
        "/api/v1/autonomous/daily-mode",
        json={
            "user_id": user["id"],
            "video_id": video["id"],
            "niche": "beauty",
            "audience": "women 20-35",
            "objective": "increase sales leads",
            "problem_angle": "watch rate bagus tapi leads lambat",
            "offer": "free mini audit",
            "platform": "tiktok",
            "region": "ID",
            "interval_minutes": 1440,
            "plan_name": "Daily Autonomous Mode",
            "run_now": True,
            "leads_count": 4,
            "variants_count": 3,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["plan"]["id"] > 0
    assert payload["plan"]["is_active"] is True
    assert payload["run"] is not None
    assert payload["run"]["status"] in {"completed", "failed"}
    assert payload["scheduler_enabled"] in {True, False}
    assert payload["ml_status"] in {"trained", "insufficient_samples"}

    # Ensure idempotency by calling daily-mode again with the same plan name.
    second = client.post(
        "/api/v1/autonomous/daily-mode",
        json={
            "user_id": user["id"],
            "video_id": video["id"],
            "niche": "beauty",
            "audience": "women 20-35",
            "objective": "increase sales leads",
            "problem_angle": "watch rate bagus tapi leads lambat",
            "offer": "free mini audit",
            "platform": "tiktok",
            "region": "ID",
            "interval_minutes": 1440,
            "plan_name": "Daily Autonomous Mode",
            "run_now": False,
        },
    )
    assert second.status_code == 201
    second_payload = second.json()
    assert second_payload["plan"]["id"] == payload["plan"]["id"]
    assert second_payload["run"] is None
