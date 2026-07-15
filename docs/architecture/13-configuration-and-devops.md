# 13. Configuration & DevOps (Changes 10, 11, 12)

## 13.1 Configuration management

`core/config.py` defines a single `Settings(BaseSettings)` (Pydantic v2 `pydantic-settings`), grouped into nested settings models for readability, loaded once as a cached singleton (`@lru_cache` `get_settings()`), injected via `Depends(get_settings)` — never imported as a bare module-level global, so tests can override it cleanly.

```python
# app/core/config.py (shape, not full implementation)
class DatabaseSettings(BaseSettings):
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str: ...   # assembled async DSN

class RedisSettings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str: ...

class JWTSettings(BaseSettings):
    jwt_secret_key: SecretStr
    jwt_refresh_secret: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

class LLMSettings(BaseSettings):
    llm_provider: Literal["ollama", "vllm"] = "ollama"
    gemma_model_name: str = "gemma3n"
    ollama_base_url: str = "http://localhost:11434"
    vllm_base_url: str = "http://localhost:8001"
    embedding_model: str = "nomic-embed-text"

class VectorDBSettings(BaseSettings):
    vector_db: Literal["chroma", "pgvector", "qdrant"] = "chroma"

class ObservabilitySettings(BaseSettings):
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "nyayaos"
    log_level: str = "INFO"

class I18nSettings(BaseSettings):
    default_language: SupportedLanguage = SupportedLanguage.EN
    supported_languages: list[SupportedLanguage] = list(SupportedLanguage)

class Settings(BaseSettings):
    environment: Literal["dev", "staging", "prod"] = "dev"
    cors_origins: list[str] = ["http://localhost:3000"]
    max_upload_size_mb: int = 20
    upload_directory: str = "./uploads"
    ocr_provider: Literal["tesseract", "gemma_vision"] = "tesseract"
    google_maps_api_key: SecretStr | None = None

    database: DatabaseSettings
    redis: RedisSettings
    jwt: JWTSettings
    llm: LLMSettings
    vector_db: VectorDBSettings
    observability: ObservabilitySettings
    i18n: I18nSettings

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

`env_nested_delimiter="__"` lets flat env vars (`POSTGRES_USER`) map onto the nested model — the exact env var names below match Change 10's list exactly, no renaming.

## 13.2 `.env.example`

```dotenv
# --- Application ---
ENVIRONMENT=dev
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# --- Database ---
DATABASE_URL=postgresql+asyncpg://nyaya:nyaya@localhost:5432/nyayaos
POSTGRES_USER=nyaya
POSTGRES_PASSWORD=change_me
POSTGRES_DB=nyayaos
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# --- Redis ---
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# --- JWT / Auth ---
JWT_SECRET_KEY=change_me_access_secret
JWT_REFRESH_SECRET=change_me_refresh_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# --- LLM / Gemma ---
LLM_PROVIDER=ollama                 # ollama | vllm
GEMMA_MODEL_NAME=gemma3n
OLLAMA_BASE_URL=http://localhost:11434
VLLM_BASE_URL=http://localhost:8001
EMBEDDING_MODEL=nomic-embed-text

# --- Vector DB / RAG ---
VECTOR_DB=chroma                    # chroma | pgvector | qdrant

# --- Observability ---
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=nyayaos

# --- External APIs ---
GOOGLE_MAPS_API_KEY=

# --- Uploads / OCR ---
MAX_UPLOAD_SIZE=20971520            # bytes (20 MB)
UPLOAD_DIRECTORY=./uploads
OCR_PROVIDER=tesseract               # tesseract | gemma_vision

# --- Multilingual (Change 9) ---
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,hi,bn,ta,te,mr,gu,pa,kn,ml,ur
```

## 13.3 `.gitignore`

```gitignore
# --- Python ---
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.eggs/

# --- Virtual environments ---
venv/
.venv/
env/
ENV/

# --- Environment / secrets ---
.env
.env.*
!.env.example

# --- FastAPI / uploads ---
uploads/
*.db
*.sqlite3

# --- Testing / coverage ---
.pytest_cache/
.coverage
.coverage.*
htmlcov/
coverage.xml
.tox/

# --- Type checking / linting ---
.mypy_cache/
.ruff_cache/
.dmypy.json

# --- Logs ---
logs/
*.log

# --- Database dumps ---
*.sql.gz
*.dump
pgdata/

# --- LangSmith / LangChain cache ---
.langchain/
.langsmith/

# --- Docker ---
docker-compose.override.yml

# --- IDEs ---
.idea/
.vscode/
*.iml
.DS_Store

# --- Alembic (keep versions, ignore local db state if any) ---
# alembic/versions/ is intentionally NOT ignored

# --- Frontend (future) ---
node_modules/
.next/
dist/

# --- OS ---
Thumbs.db
desktop.ini

# --- Misc ---
*.tmp
*.bak
.cache/
```

## 13.4 Docker / Docker Compose (Change 12)

```yaml
# docker-compose.yml (shape)
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck: {test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"], interval: 5s, retries: 5}

  redis:
    image: redis:7-alpine
    healthcheck: {test: ["CMD", "redis-cli", "ping"], interval: 5s, retries: 5}

  ollama:                              # swapped for vllm service when LLM_PROVIDER=vllm
    image: ollama/ollama:latest
    volumes: [ollama_models:/root/.ollama]
    deploy:
      resources:
        reservations:
          devices: [{driver: nvidia, count: 1, capabilities: [gpu]}]

  api:
    build: {context: ., dockerfile: docker/api.Dockerfile}
    depends_on: [postgres, redis]
    env_file: .env
    ports: ["8000:8000"]
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

  worker:
    build: {context: ., dockerfile: docker/worker.Dockerfile}
    depends_on: [postgres, redis]
    env_file: .env
    command: celery -A app.background.worker worker --loglevel=info

  prometheus:
    image: prom/prometheus:latest
    volumes: ["./docker/prometheus.yml:/etc/prometheus/prometheus.yml"]
    ports: ["9090:9090"]

  grafana:
    image: grafana/grafana:latest
    depends_on: [prometheus]
    ports: ["3001:3000"]
    volumes: [grafana_data:/var/lib/grafana]

volumes:
  pgdata:
  ollama_models:
  grafana_data:
```

Notes:
- `ollama` vs `vllm` is a **profile switch**, not two always-running services — Compose profiles (`--profile ollama` / `--profile vllm`) select one, matching `LLM_PROVIDER` in `.env`. Running both simultaneously would double GPU memory reservation for no benefit.
- `api.Dockerfile` and `worker.Dockerfile` share a base layer (same `pyproject.toml`/dependency install) but differ in `CMD` — kept as two Dockerfiles rather than one with a runtime `if`, so each image only contains what it needs (the worker doesn't need uvicorn's ASGI stack exposed, the API doesn't need Celery's beat scheduler).
- `prometheus.yml` scrapes `api:8000/metrics` and `worker` (via a Celery Prometheus exporter) — metrics come from `core/telemetry.py` (doc 1, §1.5), which is wired regardless of whether Prometheus/Grafana are actually running, so local dev without the observability stack still works.
- Production hardening beyond this shape (non-root container user, multi-stage builds to shrink image size, secrets via a secrets manager rather than `.env`, resource limits) is called out explicitly here so it isn't silently skipped: those are Module 26 (Docker) implementation details, not architecture decisions to defer indefinitely.

Continue to [14-testing-and-implementation-plan.md](14-testing-and-implementation-plan.md).
