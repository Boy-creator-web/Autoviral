from pathlib import Path


def test_human_compat_create_list_and_train(client):
    create_budi = client.post(
        "/api/v1/human/create",
        json={
            "name": "Budi Santoso",
            "age": 28,
            "gender": "male",
            "style": "professional",
        },
    )
    assert create_budi.status_code == 201
    budi = create_budi.json()
    assert budi["name"] == "Budi Santoso"

    create_siti = client.post(
        "/api/v1/human/create",
        json={
            "name": "Siti Aisyah",
            "age": 25,
            "gender": "female",
            "style": "casual",
        },
    )
    assert create_siti.status_code == 201
    siti = create_siti.json()
    assert siti["name"] == "Siti Aisyah"

    list_resp = client.get("/api/v1/human/list")
    assert list_resp.status_code == 200
    listing = list_resp.json()
    assert listing["count"] >= 2
    names = {item["name"] for item in listing["items"]}
    assert {"Budi Santoso", "Siti Aisyah"}.issubset(names)

    train_budi = client.post(
        "/api/v1/human/train",
        json={
            "text": "Halo, saya Budi Santoso, siap membantu kebutuhan marketing Anda dengan konten viral.",
            "human_id": budi["id"],
        },
    )
    assert train_budi.status_code == 200
    budi_payload = train_budi.json()
    assert budi_payload["ok"] is True
    assert budi_payload["audio_file"].endswith(".mp3")
    assert Path(budi_payload["audio_file"]).exists()

    train_siti = client.post(
        "/api/v1/human/train",
        json={
            "text": "Assalamualaikum, saya Siti Aisyah. Mari kita buat konten yang menarik dan efektif.",
            "human_id": siti["id"],
        },
    )
    assert train_siti.status_code == 200
    siti_payload = train_siti.json()
    assert siti_payload["ok"] is True
    assert siti_payload["audio_file"].endswith(".mp3")
    assert Path(siti_payload["audio_file"]).exists()
