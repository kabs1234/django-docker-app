import platform
import socket
import time
from dataclasses import asdict, dataclass

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

STARTED_AT: float = time.monotonic()
UPTIME_PRECISION = 1

@dataclass(frozen=True)
class AppInfo:
    """Runtime details about the running application instance."""

    name: str
    env: str
    port: str
    debug: bool
    hostname: str
    python: str


def current_app_info() -> AppInfo:
    """Collect configuration and host details for the running instance."""
    return AppInfo(
        name=settings.APP_NAME,
        env=settings.APP_ENV,
        port=settings.PORT,
        debug=settings.DEBUG,
        hostname=socket.gethostname(),
        python=platform.python_version(),
    )


def index(request: HttpRequest) -> HttpResponse:
    """Render the landing page with the current app info."""
    return render(request, "web/index.html", {"info": current_app_info()})


def health(request: HttpRequest) -> JsonResponse:
    """Report liveness for Docker's HEALTHCHECK."""
    uptime_seconds = round(time.monotonic() - STARTED_AT, UPTIME_PRECISION)
    return JsonResponse({"status": "ok", "uptime_seconds": uptime_seconds})


def info(request: HttpRequest) -> JsonResponse:
    """Return the current app info as JSON."""
    return JsonResponse(asdict(current_app_info()))