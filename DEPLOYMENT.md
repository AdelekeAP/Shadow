# Shadow - Deployment Guide

## Prerequisites

- **Docker** v20.10+ and **Docker Compose** v2.0+
- An **OpenAI API key** (required for SmartStudy AI features)
- Git (to clone the repository)

## Quick Start with Docker Compose

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/shadow-final-year.git
   cd shadow-final-year
   ```

2. **Configure environment variables**
   ```bash
   cp backend/.env.example backend/.env
   ```
   Edit `backend/.env` and set at minimum:
   - `SECRET_KEY` -- a strong random string for JWT signing
   - `OPENAI_API_KEY` -- your OpenAI API key

   You can also pass these via the shell when running Docker Compose:
   ```bash
   export SECRET_KEY="your-strong-secret-key"
   export OPENAI_API_KEY="sk-your-key"
   ```

3. **Start all services**
   ```bash
   docker compose up -d
   ```
   This starts four containers:
   | Service    | URL                          |
   |------------|------------------------------|
   | Frontend   | http://localhost:3000         |
   | Backend    | http://localhost:8000         |
   | API Docs   | http://localhost:8000/api/docs|
   | PostgreSQL | localhost:5432               |
   | Redis      | localhost:6379               |

   To view logs:
   ```bash
   docker compose logs -f
   ```

   To stop:
   ```bash
   docker compose down
   ```

## Manual Deployment

### Backend (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`) and then run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Requires a running PostgreSQL instance. Set `DATABASE_URL` in `.env` accordingly.

### Frontend (React + Vite)

```bash
cd frontend
npm ci
npm run build
```

The production build is output to `frontend/dist/`. Serve it with any static file server (Nginx, Apache, Caddy, etc.). The included `nginx.conf` can be used directly:

```bash
# Example with a local nginx
cp nginx.conf /etc/nginx/conf.d/default.conf
cp -r dist/ /usr/share/nginx/html/
nginx -s reload
```

Ensure the Nginx config proxies `/api/` requests to the backend host and port.

### Database Setup

```bash
psql -U postgres -c "CREATE DATABASE shadow_db;"
psql -U postgres -d shadow_db -f database/schema.sql
```

## Production Considerations

### Secrets Management
- **Never** commit `.env` files or real credentials to version control.
- Use a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.) or environment variables injected at runtime.
- Generate a strong `SECRET_KEY` (at least 32 random characters).

### HTTPS
- Place a reverse proxy (Nginx, Caddy, or a cloud load balancer) in front of the application with TLS termination.
- Obtain certificates via Let's Encrypt or your cloud provider.
- Redirect all HTTP traffic to HTTPS.

### Scaling
- The backend is stateless and can be horizontally scaled behind a load balancer.
- Use `docker compose up --scale backend=3` to run multiple backend instances.
- For production PostgreSQL, consider a managed database service (AWS RDS, Cloud SQL, etc.) with connection pooling.
- Enable Redis (`REDIS_ENABLED=true`) for caching and session management at scale.

### Logging and Monitoring
- Set `LOG_LEVEL` to `WARNING` or `ERROR` in production to reduce noise.
- Integrate with a centralized logging service (ELK, CloudWatch, Datadog).
- Add health check endpoints for container orchestration readiness probes.
