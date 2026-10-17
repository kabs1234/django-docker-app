# Django URL Shortener

A URL shortener built with Django and PostgreSQL, run as a multi-container application with Docker Compose.

Each short link is stored in PostgreSQL. Following a short link reads it from the database and increments its click counter, so the backend both reads and writes data.

## Services

| Service | Image                          | Purpose                                         |
|---------|--------------------------------|-------------------------------------------------|
| `web`   | built from the local `Dockerfile` | Django + Gunicorn backend, published on port 8000 |
| `db`    | `postgres:17-alpine`           | PostgreSQL database, reachable only inside the `backend` network |

- Both services share the `backend` network; `web` connects to the database by its service name `db`.
- `web` starts only after `db` passes its `pg_isready` healthcheck, and applies migrations on start.
- Database files live in the named volume `pgdata`, so data survives `docker compose down` and container recreation.

## Quick start

```bash
cp .env.example .env
```

Edit `.env` and set real values for `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD`. `.env` is ignored by Git and must never be committed.

```bash
docker compose up --build
```

Open http://localhost:8000.

## API

| Method | Path                    | Description                                       |
|--------|-------------------------|---------------------------------------------------|
| `POST` | `/api/links/`           | Create a short link from `{"url": "...", "code": "optional"}` |
| `GET`  | `/api/links/`           | List all links, most clicked first                |
| `GET`  | `/api/links/<code>/`    | Stats for one link                                |
| `GET`  | `/s/<code>/`            | Redirect to the target URL and count the click    |
| `GET`  | `/`                     | HTML page with the top links and instance info    |
| `GET`  | `/health/`              | Liveness and database connectivity (Docker `HEALTHCHECK`) |
| `GET`  | `/api/info/`            | App info as JSON                                  |

Without `code`, a random 6-character code is generated. Invalid URLs and codes return `400`, a taken code returns `409`.

### Example

```bash
curl -X POST http://localhost:8000/api/links/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.postgresql.org/", "code": "pg"}'
```

```json
{"code": "pg", "target_url": "https://www.postgresql.org/", "short_url": "http://localhost:8000/s/pg/", "clicks": 0, "created_at": "..."}
```

```bash
curl -i http://localhost:8000/s/pg/          # 302 redirect, clicks becomes 1
curl http://localhost:8000/api/links/pg/     # stats for the link
curl http://localhost:8000/api/links/        # all links
```

## Environment variables

All variables are read from `.env` (see `.env.example`).

| Variable               | Example                    | Purpose                                     |
|------------------------|----------------------------|---------------------------------------------|
| `APP_NAME`             | `Django URL Shortener`     | Title shown on the page                     |
| `APP_ENV`              | `production`               | Environment label                           |
| `WEB_PORT`             | `8000`                     | Host port mapped to the `web` container     |
| `DJANGO_DEBUG`         | `False`                    | Django debug mode                           |
| `DJANGO_SECRET_KEY`    | —                          | Django secret key (required)                |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1`      | Comma-separated allowed hosts               |
| `POSTGRES_DB`          | `shortener`                | Database name                               |
| `POSTGRES_USER`        | `shortener`                | Database user                               |
| `POSTGRES_PASSWORD`    | —                          | Database password (required)                |

`POSTGRES_HOST` and `POSTGRES_PORT` are set by `compose.yaml` to `db` and `5432`. If a `POSTGRES_*` variable is missing, Compose refuses to start and names it. Without `DJANGO_SECRET_KEY`, the `web` container exits with `KeyError: 'DJANGO_SECRET_KEY'`.

## Persistence check

```bash
docker compose down
docker compose up -d
curl http://localhost:8000/api/links/        # links and click counts are still there
```

`docker compose down -v` also removes the `pgdata` volume and deletes all data.

## Useful commands

```bash
docker compose ps                  # status and health of both services
docker compose logs -f web         # follow backend logs
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'   # open a psql shell
docker compose down                # stop and remove containers, keep data
```

## Dockerfile optimizations

- Multi-stage build: `pip wheel` runs in a builder stage, and the runtime stage installs the wheels from a build-time mount, so they never end up in an image layer.
- `python:3.12-slim` base image keeps the image small.
- `requirements.txt` is copied before the source code, so the dependency layer stays cached until requirements change.
- `pip --no-cache-dir` and `.dockerignore` keep pip's cache, `.git`, `.env` files, virtualenvs and `__pycache__` out of the image.
- Runs as an unprivileged `appuser` instead of root.
- `HEALTHCHECK` polls `/health/`, which also checks the database connection.
- Production WSGI server (Gunicorn) instead of Django's dev server.
