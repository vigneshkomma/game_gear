"""
Project-level URL configuration.

This is the urls.py inside your SETTINGS package (the folder that also
holds settings.py — e.g. gamebazaar/urls.py, not the repo root).
Replace whatever is already there with this.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # Everything account-related — login/logout/password-reset (Django's
    # built-in views) alongside signup/profile/addresses (ours) — lives
    # under one prefix. Order matters here: users.urls must come first
    # so its "signup/" etc. are tried before auth's catch-all patterns
    # under the same "users/" prefix don't accidentally shadow them.
    path("users/", include("users.urls")),
    path("users/", include("django.contrib.auth.urls")),

    path("orders/", include("orders.urls")),
    path("contact/", include("contact.urls")),

    # Listings owns the site root ("" prefix) — this MUST be last.
    # listings.urls contains <slug:slug>/, a single-segment catch-all
    # (the listing detail route). If this were listed earlier, Django
    # would try matching inside listings.urls before ever reaching
    # "orders/" or "contact/" below, and bare paths like "/orders/" or
    # "/contact/" would get swallowed as if "orders"/"contact" were a
    # listing slug — a 404 from the WRONG view, which is exactly what
    # happened before this reorder. Multi-segment paths like
    # "/orders/5/" were never affected, only single-segment ones.
    path("", include("listings.urls")),
]

# Serve user-uploaded media (avatars, listing photos) in development.
# In production this is handled by your web server / storage backend
# instead — never serve media this way with DEBUG=False.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)