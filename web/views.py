import json
import platform
import secrets
import socket
import string
import time
from dataclasses import asdict, dataclass

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_slug
from django.db import DatabaseError, connection
from django.db.models import F
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_http_methods

from web.models import CODE_MAX_LENGTH, ShortLink

STARTED_AT: float = time.monotonic()
UPTIME_PRECISION = 1
GENERATED_CODE_LENGTH = 6
CODE_ALPHABET: str = string.ascii_letters + string.digits
RECENT_LINKS_LIMIT = 10
HTTP_BAD_REQUEST = 400
HTTP_CREATED = 201
HTTP_CONFLICT = 409
HTTP_SERVICE_UNAVAILABLE = 503

validate_url = URLValidator(schemes=("http", "https"))


@dataclass(frozen=True)
class AppInfo:
    """Runtime details about the running application instance."""

    name: str
    env: str
    port: str
    debug: bool
    hostname: str
    python: str


@dataclass(frozen=True)
class LinkRequest:
    """Validated payload for creating a short link."""

    target_url: str
    code: str | None


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


def is_database_reachable() -> bool:
    """Return True when a trivial query against the database succeeds."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return False
    return True


def generate_code() -> str:
    """Return a random code that is not used by any existing link."""
    while True:
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(GENERATED_CODE_LENGTH))
        if not ShortLink.objects.filter(code=code).exists():
            return code


def serialize_link(request: HttpRequest, link: ShortLink) -> dict[str, str | int]:
    """Convert a link into its public JSON representation."""
    return {
        "code": link.code,
        "target_url": link.target_url,
        "short_url": request.build_absolute_uri(f"/s/{link.code}/"),
        "clicks": link.clicks,
        "created_at": link.created_at.isoformat(),
    }


def parse_link_request(body: bytes) -> LinkRequest:
    """Parse and validate the JSON body of a create-link request."""
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as error:
        raise ValidationError("Request body must be valid JSON.") from error
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object.")
    target_url = str(payload.get("url", "")).strip()
    validate_url(target_url)
    code = payload.get("code")
    if code is not None:
        code = str(code).strip()
        validate_slug(code)
        if len(code) > CODE_MAX_LENGTH:
            raise ValidationError(f"Code must be at most {CODE_MAX_LENGTH} characters.")
    return LinkRequest(target_url=target_url, code=code)


def index(request: HttpRequest) -> HttpResponse:
    """Render the landing page with the app info and the most clicked links."""
    links = ShortLink.objects.all()[:RECENT_LINKS_LIMIT]
    return render(request, "web/index.html", {"info": current_app_info(), "links": links})


def health(request: HttpRequest) -> JsonResponse:
    """Report liveness and database connectivity for Docker's HEALTHCHECK."""
    uptime_seconds = round(time.monotonic() - STARTED_AT, UPTIME_PRECISION)
    if not is_database_reachable():
        return JsonResponse(
            {"status": "degraded", "database": "unreachable", "uptime_seconds": uptime_seconds},
            status=HTTP_SERVICE_UNAVAILABLE,
        )
    return JsonResponse({"status": "ok", "database": "ok", "uptime_seconds": uptime_seconds})


def info(request: HttpRequest) -> JsonResponse:
    """Return the current app info as JSON."""
    return JsonResponse(asdict(current_app_info()))


def list_links(request: HttpRequest) -> JsonResponse:
    """Return every short link, most clicked first."""
    return JsonResponse({"links": [serialize_link(request, link) for link in ShortLink.objects.all()]})


def create_link(request: HttpRequest) -> JsonResponse:
    """Create a short link from a JSON body with a url and an optional custom code."""
    try:
        link_request = parse_link_request(request.body)
    except ValidationError as error:
        return JsonResponse({"error": " ".join(error.messages)}, status=HTTP_BAD_REQUEST)
    if link_request.code and ShortLink.objects.filter(code=link_request.code).exists():
        return JsonResponse({"error": f"Code '{link_request.code}' is already taken."}, status=HTTP_CONFLICT)
    link = ShortLink.objects.create(code=link_request.code or generate_code(), target_url=link_request.target_url)
    return JsonResponse(serialize_link(request, link), status=HTTP_CREATED)


@require_http_methods(["GET", "POST"])
def links(request: HttpRequest) -> JsonResponse:
    """Dispatch the links collection endpoint to list or create."""
    if request.method == "POST":
        return create_link(request)
    return list_links(request)


@require_GET
def link_detail(request: HttpRequest, code: str) -> JsonResponse:
    """Return the stats of a single short link."""
    link = get_object_or_404(ShortLink, code=code)
    return JsonResponse(serialize_link(request, link))


@require_GET
def follow_link(request: HttpRequest, code: str) -> HttpResponseRedirect:
    """Count a visit atomically and redirect to the link's target URL."""
    link = get_object_or_404(ShortLink, code=code)
    ShortLink.objects.filter(pk=link.pk).update(clicks=F("clicks") + 1)
    return HttpResponseRedirect(link.target_url)