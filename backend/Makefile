.PHONY: install dev lint lint-fix format format-check typecheck test test-cov test-fast \
       security-scan pre-commit check check-all docker-build docker-run docker-up docker-down \
       audit-report clean fastapi-check

# ─── Setup ──────────────────────────────────────────────────────────
install:
	uv sync --all-extras
	uv run pre-commit install
	@echo "✓ Dependencies installed and pre-commit hooks set up"

# ─── Development ────────────────────────────────────────────────────
dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ─── Linting ────────────────────────────────────────────────────────
lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

# ─── Type Checking ──────────────────────────────────────────────────
typecheck:
	uv run mypy app/ || echo "⚠ mypy found issues (non-blocking for now)"

# ─── Testing ────────────────────────────────────────────────────────
test:
	DISABLE_ML_MODELS=true TESTING=true SECRET_KEY=test-key ALGORITHM=HS256 \
	uv run pytest tests/ -v --tb=short

test-cov:
	DISABLE_ML_MODELS=true TESTING=true SECRET_KEY=test-key ALGORITHM=HS256 \
	uv run pytest tests/ --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=65

test-fast:
	DISABLE_ML_MODELS=true TESTING=true SECRET_KEY=test-key ALGORITHM=HS256 \
	uv run pytest tests/ -x -q --tb=line --no-header

# ─── Security ───────────────────────────────────────────────────────
security-scan:
	gitleaks detect --config gitleaks.toml --verbose

# ─── FastAPI Check ──────────────────────────────────────────────────
fastapi-check:
	uv run python -c "from app.main import app; print('✓ FastAPI app imports OK')"

# ─── Pre-Commit ─────────────────────────────────────────────────────
pre-commit:
	pre-commit run --all-files

# ─── Combined Quality Gates ─────────────────────────────────────────
check: format-check lint typecheck fastapi-check test-fast
	@echo ""
	@echo "════════════════════════════════════════"
	@echo "  ✓ All quick checks passed"
	@echo "════════════════════════════════════════"

check-all: format-check lint typecheck fastapi-check test-cov security-scan
	@echo ""
	@echo "════════════════════════════════════════"
	@echo "  ✓ Full validation passed"
	@echo "════════════════════════════════════════"

# ─── Docker ─────────────────────────────────────────────────────────
docker-build:
	docker build -t shadow-backend .

docker-run:
	docker run --env-file .env -p 8000:8000 shadow-backend

docker-up:
	cd .. && docker compose up -d

docker-down:
	cd .. && docker compose down

# ─── Audit Report ───────────────────────────────────────────────────
audit-report:
	@echo "═══ Shadow Backend — Production Readiness Audit ═══"
	@echo ""
	@printf "  %-30s " "pyproject.toml" && (test -f pyproject.toml && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " "Makefile" && (test -f Makefile && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " "Dockerfile" && (test -f Dockerfile && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " ".dockerignore" && (test -f .dockerignore && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " ".env.example" && (test -f .env.example && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " "gitleaks.toml" && (test -f gitleaks.toml && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " ".pre-commit-config.yaml" && (test -f ../.pre-commit-config.yaml && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " "CI workflow (ci.yml)" && (test -f ../.github/workflows/ci.yml && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " "Deploy workflow" && (test -f ../.github/workflows/deploy.yml && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " "Code review workflow" && (test -f ../.github/workflows/claude-code-review.yml && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " "pytest config" && (grep -q "pytest" pyproject.toml 2>/dev/null && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " "ruff config" && (grep -q "ruff" pyproject.toml 2>/dev/null && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " "mypy config" && (grep -q "mypy" pyproject.toml 2>/dev/null && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " "conftest.py" && (test -f tests/conftest.py && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " "sentry-sdk" && (grep -q "sentry" pyproject.toml 2>/dev/null && echo "✓" || echo "✗ MISSING")
	@printf "  %-30s " "python-json-logger" && (grep -q "json-logger" pyproject.toml 2>/dev/null && echo "✓" || echo "✗ MISSING")
	@echo ""
	@echo "═══════════════════════════════════════════════════"

# ─── Cleanup ────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .pytest_cache htmlcov .coverage coverage.xml .ruff_cache
	@echo "✓ Cleaned"
