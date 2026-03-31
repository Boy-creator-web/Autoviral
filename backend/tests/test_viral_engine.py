def _create_user_and_video(client):
    user_resp = client.post(
        "/api/v1/users/",
        json={
            "email": "viral@example.com",
            "password": "password123",
            "name": "Viral User",
        },
    )
    assert user_resp.status_code == 201
    user = user_resp.json()

    human_resp = client.post(
        "/api/v1/synthetic-humans/",
        json={
            "name": "Viral Human",
            "age": 23,
            "gender": "female",
            "style": "trendy",
            "user_id": user["id"],
        },
    )
    assert human_resp.status_code == 201
    human = human_resp.json()

    video_resp = client.post(
        "/api/v1/videos/",
        json={
            "title": "Viral baseline video",
            "status": "completed",
            "file_path": "/tmp/viral.mp4",
            "human_id": human["id"],
            "user_id": user["id"],
        },
    )
    assert video_resp.status_code == 201
    video = video_resp.json()
    return user, video


def test_viral_engine_end_to_end(client):
    user, video = _create_user_and_video(client)

    create_resp = client.post(
        "/api/v1/viral-engine/experiments",
        json={
            "user_id": user["id"],
            "video_id": video["id"],
            "niche": "skincare",
            "audience": "women 20-35",
            "objective": "increase leads",
            "problem_angle": "konten views tinggi tapi DM sepi",
            "offer": "free funnel audit",
            "tone": "direct",
            "platform": "tiktok",
            "variants_count": 3,
        },
    )
    assert create_resp.status_code == 201
    create_payload = create_resp.json()
    assert create_payload["experiment"]["id"] > 0
    assert len(create_payload["variants"]) == 3

    experiment_id = create_payload["experiment"]["id"]
    first_variant_id = create_payload["variants"][0]["id"]

    variant_resp = client.get(f"/api/v1/viral-engine/experiments/{experiment_id}/variants")
    assert variant_resp.status_code == 200
    variant_payload = variant_resp.json()
    assert variant_payload["count"] == 3

    metric_resp = client.post(
        f"/api/v1/viral-engine/variants/{first_variant_id}/metrics",
        json={
            "impressions": 10000,
            "views_3s": 4200,
            "views_10s": 2400,
            "completions": 1700,
            "likes": 500,
            "comments": 63,
            "shares": 210,
            "saves": 180,
            "profile_visits": 340,
            "link_clicks": 85,
            "watch_time_avg_sec": 13.5,
            "conversion_events": 25,
        },
    )
    assert metric_resp.status_code == 201
    metric_payload = metric_resp.json()
    assert metric_payload["variant_id"] == first_variant_id

    recommendation_resp = client.get(
        f"/api/v1/viral-engine/experiments/{experiment_id}/recommendation"
    )
    assert recommendation_resp.status_code == 200
    recommendation = recommendation_resp.json()
    assert recommendation["experiment_id"] == experiment_id
    assert recommendation["winner_variant_id"] is not None
    assert recommendation["summary"]
    assert len(recommendation["actions"]) >= 2

    list_resp = client.get(f"/api/v1/viral-engine/experiments?user_id={user['id']}")
    assert list_resp.status_code == 200
    list_payload = list_resp.json()
    assert list_payload["count"] >= 1
