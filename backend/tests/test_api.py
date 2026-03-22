def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_user_and_related_resource_flow(client):
    user_response = client.post(
        "/api/v1/users/",
        json={
            "email": "qa@example.com",
            "password": "password123",
            "name": "QA User",
        },
    )
    assert user_response.status_code == 201
    user = user_response.json()
    user_id = user["id"]

    human_response = client.post(
        "/api/v1/synthetic-humans/",
        json={
            "name": "Ava",
            "age": 24,
            "gender": "female",
            "style": "casual",
            "user_id": user_id,
        },
    )
    assert human_response.status_code == 201
    human = human_response.json()

    video_response = client.post(
        "/api/v1/videos/",
        json={
            "title": "Campaign Teaser",
            "status": "pending",
            "file_path": "/tmp/teaser.mp4",
            "human_id": human["id"],
            "user_id": user_id,
        },
    )
    assert video_response.status_code == 201

    scrape_response = client.post(
        "/api/v1/scraper-data/",
        json={
            "source": "youtube",
            "topic": "growth hacks",
            "intent_score": 0.85,
            "raw_data": '{"keyword":"viral shorts"}',
        },
    )
    assert scrape_response.status_code == 201

    list_users = client.get("/api/v1/users/")
    list_humans = client.get("/api/v1/synthetic-humans/")
    list_videos = client.get("/api/v1/videos/")
    list_scraper = client.get("/api/v1/scraper-data/")

    assert list_users.status_code == 200 and len(list_users.json()) == 1
    assert list_humans.status_code == 200 and len(list_humans.json()) == 1
    assert list_videos.status_code == 200 and len(list_videos.json()) == 1
    assert list_scraper.status_code == 200 and len(list_scraper.json()) == 1


def test_duplicate_user_email_returns_400(client):
    payload = {
        "email": "dupe@example.com",
        "password": "password123",
        "name": "User One",
    }
    first = client.post("/api/v1/users/", json=payload)
    second = client.post("/api/v1/users/", json=payload)

    assert first.status_code == 201
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"


def test_video_user_human_mismatch_returns_400(client):
    user_one = client.post(
        "/api/v1/users/",
        json={
            "email": "owner@example.com",
            "password": "password123",
            "name": "Owner",
        },
    ).json()
    user_two = client.post(
        "/api/v1/users/",
        json={
            "email": "other@example.com",
            "password": "password123",
            "name": "Other",
        },
    ).json()
    human = client.post(
        "/api/v1/synthetic-humans/",
        json={
            "name": "Model",
            "age": 30,
            "gender": "male",
            "style": "sport",
            "user_id": user_one["id"],
        },
    ).json()

    response = client.post(
        "/api/v1/videos/",
        json={
            "title": "Mismatch",
            "status": "pending",
            "file_path": None,
            "human_id": human["id"],
            "user_id": user_two["id"],
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Synthetic human does not belong to the selected user"
