.PHONY: up down restart logs build migrate test clean

# Start all services
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

# Restart all services
restart:
	docker compose down
	docker compose up -d

# View logs
logs:
	docker compose logs -f --tail=100

# Build images
build:
	docker compose build

# Run database migrations
migrate:
	docker compose exec backend alembic upgrade head

# Create a new migration
migration:
	docker compose exec backend alembic revision --autogenerate -m "$(name)"

# Run backend tests
test:
	docker compose exec backend pytest -v

# Clean up volumes (WARNING: deletes all data)
clean:
	docker compose down -v
	rm -rf data/

# Initialize Milvus collection
init-milvus:
	docker compose run --rm milvus-init

# Dev mode with hot reload
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
