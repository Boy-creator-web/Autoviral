.PHONY: up down logs-backend logs-worker logs-scraper ps check health smoke smoke-import smoke-scraper

TAIL ?= 50
SERVICE ?= backend

COMPOSE := $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; elif docker-compose version >/dev/null 2>&1; then echo "docker-compose"; fi)

define ensure_compose
	@if [ -z "$(COMPOSE)" ]; then \
		echo "Docker Compose tidak ditemukan. Install Docker Compose v2 (docker compose) atau v1 (docker-compose)."; \
		exit 1; \
	fi
endef

up:
	$(call ensure_compose)
	$(COMPOSE) up --build -d

down:
	$(call ensure_compose)
	$(COMPOSE) down

ps:
	$(call ensure_compose)
	$(COMPOSE) ps

logs-backend:
	$(call ensure_compose)
	$(COMPOSE) logs --tail=$(TAIL) $(SERVICE)

logs-worker:
	$(call ensure_compose)
	$(COMPOSE) logs --tail=$(TAIL) celery-worker

logs-scraper:
	$(call ensure_compose)
	$(COMPOSE) logs --tail=$(TAIL) backend

check:
	python3 -m compileall backend

health:
	curl -s http://localhost:8000/api/v1/health/dependencies

smoke:
	python3 scripts/smoke_test_backend.py --url=http://localhost:8000

smoke-import:
	python3 scripts/smoke_test_backend.py --skip-http

smoke-scraper:
	python3 scripts/smoke_test_backend.py --url=http://localhost:8000 --check-scraper-async
