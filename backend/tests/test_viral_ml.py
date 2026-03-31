def _create_user_video_experiment_and_variants(client):
    user_resp = client.post(
        "/api/v1/users/",
        json={
            "email": "ml@example.com",
            "password": "password123",
            "name": "ML User",
        },
    )
    assert user_resp.status_code == 201
    user = user_resp.json()

    human_resp = client.post(
        "/api/v1/synthetic-humans/",
        json={
            "name": "ML Human",
            "age": 29,
            "gender": "female",
            "style": "modern",
            "user_id": user["id"],
        },
    )
    assert human_resp.status_code == 201
    human = human_resp.json()

    video_resp = client.post(
        "/api/v1/videos/",
        json={
            "title": "ML baseline",
            "status": "completed",
            "file_path": "/tmp/ml.mp4",
            "human_id": human["id"],
            "user_id": user["id"],
        },
    )
    assert video_resp.status_code == 201
    video = video_resp.json()

    exp_resp = client.post(
        "/api/v1/viral-engine/experiments",
        json={
            "user_id": user["id"],
            "video_id": video["id"],
            "niche": "fitness",
            "audience": "men 20-35",
            "objective": "increase sales leads",
            "problem_angle": "views bagus tapi leads kecil",
            "offer": "free program consult",
            "tone": "direct",
            "platform": "tiktok",
            "variants_count": 3,
        },
    )
    assert exp_resp.status_code == 201
    payload = exp_resp.json()
    return user, payload["variants"]


def test_train_and_predict_viral_ml_model(client):
    _, variants = _create_user_video_experiment_and_variants(client)

    # Build enough training samples (>=5) across variants.
    for idx in range(6):
        variant = variants[idx % len(variants)]
        resp = client.post(
            f"/api/v1/viral-engine/variants/{variant['id']}/metrics",
            json={
                "impressions": 10000 + (idx * 500),
                "views_3s": 4200 + (idx * 120),
                "views_10s": 2500 + (idx * 90),
                "completions": 1600 + (idx * 70),
                "likes": 500 + (idx * 20),
                "comments": 60 + (idx * 4),
                "shares": 180 + (idx * 10),
                "saves": 150 + (idx * 8),
                "profile_visits": 300 + (idx * 15),
                "link_clicks": 80 + (idx * 5),
                "watch_time_avg_sec": 12.5 + (idx * 0.3),
                "conversion_events": 20 + (idx * 2),
            },
        )
        assert resp.status_code == 201

    train_resp = client.post("/api/v1/viral-engine/model/train")
    assert train_resp.status_code == 201
    train_payload = train_resp.json()
    assert train_payload["snapshot_id"] > 0
    assert train_payload["sample_count"] >= 5
    assert train_payload["feature_count"] >= 5
    assert train_payload["activated"] is True

    predict_resp = client.post(
        "/api/v1/viral-engine/predict",
        json={
            "objective": "increase sales leads",
            "tone": "direct",
            "hook": "3 cara naikkan conversion tanpa bakar budget",
            "cta": "save dan share ke tim kamu",
            "niche": "fitness",
            "platform": "tiktok",
            "duration_target_sec": 30,
        },
    )
    assert predict_resp.status_code == 200
    prediction = predict_resp.json()
    assert prediction["using_model"] is True
    assert prediction["model_snapshot_id"] == train_payload["snapshot_id"]
    assert 0 <= prediction["predicted_score"] <= 1
    assert "objective_has_sales" in prediction["features"]
