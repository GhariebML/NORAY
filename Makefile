.PHONY: setup update dev-db dev-backend dev-frontend test lint clean

# Setup the entire environment (OS agnostic-ish)
setup:
	@echo "Running environment bootstrap..."
	@if [ "$$(uname -s)" = "Linux" ] || [ "$$(uname -s)" = "Darwin" ]; then \
		bash setup.sh; \
	else \
		powershell.exe -ExecutionPolicy Bypass -File setup.ps1; \
	fi

update:
	@echo "Updating dependencies..."
	@pip install -e .
	@cd frontend && npm install

dev-db:
	@echo "Starting local databases via Docker Compose..."
	@docker-compose up -d

dev-backend:
	@echo "Starting FastAPI backend..."
	@uvicorn api.main:app --reload --port 8000

dev-frontend:
	@echo "Starting Next.js frontend..."
	@cd frontend && npm run dev

# Start all development services together
dev: dev-db
	@make -j 2 dev-backend dev-frontend

test:
	@echo "Running Python tests..."
	@pytest tests/
	@echo "Running Frontend tests..."
	@cd frontend && npm run test

lint:
	@echo "Linting Python code..."
	@ruff check .
	@echo "Linting Frontend code..."
	@cd frontend && npm run lint

clean:
	@echo "Cleaning up..."
	@rm -rf .venv
	@rm -rf frontend/node_modules
	@rm -rf __pycache__
	@rm -rf .pytest_cache
	@docker-compose down -v
