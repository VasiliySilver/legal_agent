SHELL := /bin/bash

.PHONY: help db-up db-init db-drop db-reset db-load build-vector-faiss build-vector-postgres run-api run-bot disable-ipv6 test

help:
	@echo "Available targets:"
	@echo "  db-up                 - Start PostgreSQL database"
	@echo "  db-init               - Initialize database schema"
	@echo "  db-drop               - Drop database"
	@echo "  db-reset              - Reset database (drop + init)"
	@echo "  db-load               - Load articles into database"
	@echo "  build-vector-faiss    - Build FAISS vector index"
	@echo "  build-vector-postgres - Build PostgreSQL vector index"
	@echo "  run-api               - Start REST API server"
	@echo "  run-bot               - Start Telegram bot (requires IPv6 disabled)"
	@echo "  disable-ipv6          - Disable IPv6 for Telegram bot compatibility"
	@echo "  test                  - Run all tests"

db-up:
	@cd docker && docker compose up -d && cd -

db-init:
	@python -m src.infrastructure.database init

db-drop:
	@python -m src.infrastructure.database drop

db-reset:
	@python -m src.infrastructure.database reset

db-load:
	@python -m src.infrastructure.database load

build-vector-faiss:
	@VECTOR_BACKEND=faiss VECTOR_INDEX_PATH=data/faiss_index python -m src.infrastructure.database load

build-vector-postgres:
	@VECTOR_BACKEND=postgres \
		VECTOR_DB_HOST=localhost VECTOR_DB_PORT=5433 VECTOR_DB_NAME=legal_agent_vectors \
		python -m src.infrastructure.database load

run-api:
	@python run_api.py

run-bot:
	@python run_bot.py

disable-ipv6:
	@echo "Disabling IPv6 for Telegram bot compatibility..."
	@sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
	@sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
	@echo "IPv6 disabled. You can now run 'make run-bot'"

test:
	@pytest
