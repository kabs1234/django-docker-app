from django.db import models

CODE_MAX_LENGTH = 32
TARGET_URL_MAX_LENGTH = 2048


class ShortLink(models.Model):
    """A short code that redirects to a target URL and counts its visits."""

    code = models.SlugField(max_length=CODE_MAX_LENGTH, unique=True)
    target_url = models.URLField(max_length=TARGET_URL_MAX_LENGTH)
    clicks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-clicks", "-created_at")

    def __str__(self) -> str:
        return f"{self.code} -> {self.target_url}"