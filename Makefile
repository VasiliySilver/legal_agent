SHELL := /bin/bash

.PHONY: help db-up db-init db-drop db-reset db-load build-vector-faiss build-vector-postgres run-api test

help:
	@echo "Makefile targets: db-up db-init db-drop db-reset db-load build-vector-faiss build-vector-postgres run-api test"

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

test:
	@pytest
