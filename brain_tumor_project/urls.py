from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from django.views.static import serve


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("detector.urls")),
]


# Serve uploaded media files
# This is needed because Render runs Django with DEBUG=False.
urlpatterns += [
    path(
        "media/<path:path>",
        serve,
        {
            "document_root": settings.MEDIA_ROOT,
        },
    ),
]