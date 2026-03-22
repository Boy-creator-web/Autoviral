.PHONY: help up down restart logs ps build backend-logs test test-local postiz-up postiz-down postiz-logs clean

help:
	@echo "Perintah yang tersedia:"
	@echo "  make up            - Jalankan stack utama (backend + postgres + redis)"
	@echo "  make down          - Hentikan stack utama"
	@echo "  make restart       - Restart stack utama"
	@echo "  make build         - Build image backend"
	@echo "  make logs          - Lihat logs stack utama"
	@echo "  make backend-logs  - Lihat logs service backend"
	@echo "  make ps            - Lihat status container"
	@echo "  make test          - Jalankan pytest via docker compose"
	@echo "  make test-local    - Jalankan pytest lokal (python3)"
	@echo "  make postiz-up     - Jalankan stack Postiz (profile postiz)"
	@echo "  make postiz-down   - Hentikan stack Postiz"
	@echo "  make postiz-logs   - Lihat logs Postiz"
	@echo "  make clean         - Hapus volume stack utama"

up:
	docker compose up --build -d

down:
	docker compose down

restart: down up

build:
	docker compose build backend

logs:
	docker compose logs -f

backend-logs:
	docker compose logs -f backend

ps:
	docker compose ps

test:
	docker compose run --rm backend python -m pytest -q tests

test-local:
	python3 -m pytest -q backend/tests

postiz-up:
	docker compose --profile postiz up -d postiz postiz-postgres postiz-redis temporal-postgresql temporal-elasticsearch temporal temporal-ui

postiz-down:
	docker compose --profile postiz down

postiz-logs:
	docker compose --profile postiz logs -f postiz

clean:
	docker compose down -v
