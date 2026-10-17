from django.urls import path

from web import views

urlpatterns = [
    path("", views.index, name="index"),
    path("health/", views.health, name="health"),
    path("api/info/", views.info, name="info"),
    path("api/links/", views.links, name="links"),
    path("api/links/<slug:code>/", views.link_detail, name="link-detail"),
    path("s/<slug:code>/", views.follow_link, name="follow-link"),
]