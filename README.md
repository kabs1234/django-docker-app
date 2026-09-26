# Django Docker App

A simple Django web application containerized with Docker and served by Gunicorn.

## Endpoints

| Path          | Description                                  |
|---------------|----------------------------------------------|
| `/`           | HTML page showing app config and container info |
| `/health/`    | JSON health check (used by Docker `HEALTHCHECK`) |
| `/api/info/`  | App info as JSON                             |

## Environment variables

Defaults below are the ones set in the image. Without Docker, `APP_ENV` falls back to `development` and `DJANGO_ALLOWED_HOSTS` to `localhost,127.0.0.1`.

| Variable               | Default                  | Purpose                              |
|------------------------|--------------------------|--------------------------------------|
| `PORT`                 | `8000`                   | Port Gunicorn listens on             |
| `APP_NAME`             | `Django Docker App`      | Title shown on the page              |
| `APP_ENV`              | `production`             | Environment label                    |
| `DJANGO_DEBUG`         | `False`                  | Django debug mode                    |
| `DJANGO_SECRET_KEY`    | insecure dev key         | Django secret key (set in production)|
| `DJANGO_ALLOWED_HOSTS` | `*`                      | Comma-separated allowed hosts        |

## Build and run with Docker

```bash
docker build -t django-docker-app .
docker run -d --name django-app -p 8000:8000 django-docker-app
```

Open http://localhost:8000.

Override environment variables and the port:

```bash
docker run -d --name django-app \
  -p 9000:9000 \
  -e PORT=9000 \
  -e APP_NAME="My Container App" \
  -e APP_ENV=staging \
  -e DJANGO_SECRET_KEY=change-me \
  django-docker-app
```

Open http://localhost:9000.

```bash
docker ps                    # container status, including health
docker logs -f django-app    # follow logs
docker stop django-app && docker rm django-app
```

## Run locally without Docker

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

## Dockerfile optimizations

- Multi-stage build: `pip wheel` runs in a builder stage, and the runtime stage installs them from a build-time mount, so the wheel files never end up in an image layer.
- `python:3.12-slim` base image keeps the image small.
- `requirements.txt` is copied before the source code, so the dependency layer stays cached until requirements change.
- `pip --no-cache-dir` and `.dockerignore` keep pip's cache, `.git`, virtualenvs and `__pycache__` out of the image.
- Runs as an unprivileged `appuser` instead of root.
- `HEALTHCHECK` polls `/health/` every 30 seconds, so `docker ps` shows `healthy` or `unhealthy`.
- Production WSGI server (Gunicorn) instead of Django's dev server.
