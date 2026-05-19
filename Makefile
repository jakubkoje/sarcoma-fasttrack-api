.PHONY: help tidy test build run run-local push compose-up compose-down compose-config

IMAGE_NAME ?= $(DOCKERHUB_USERNAME)/sarcomfasttrack-be
TAG ?= latest
PORT ?= 8000
COMPOSE ?= docker compose

help:
	@echo "Common targets:"
	@echo "  make build        Build Docker image (IMAGE_NAME/TAG configurable)."
	@echo "  make run          Run container on port $(PORT)."
	@echo "  make run-local    Run Go API locally on localhost:$(PORT)."
	@echo "  make test         Run Go tests."
	@echo "  make tidy         Resolve Go module files."
	@echo "  make push         Push built image to registry."
	@echo "  make compose-up   Start services with docker-compose."
	@echo "  make compose-down Stop services and remove compose resources."
	@echo "  make compose-config Validate compose configuration."

tidy:
	go mod tidy

test:
	go test ./...

build:
	docker build -t $(IMAGE_NAME):$(TAG) .

run:
	docker run --rm -p $(PORT):8000 $(IMAGE_NAME):$(TAG)

run-local:
	SARCOMA_API_PORT=$(PORT) go run ./cmd/sarcoma-api-service

push:
	docker push $(IMAGE_NAME):$(TAG)

compose-up:
	$(COMPOSE) up -d

compose-down:
	$(COMPOSE) down

compose-config:
	$(COMPOSE) config
