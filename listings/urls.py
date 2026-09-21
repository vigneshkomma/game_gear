from django.urls import path

from . import views

app_name = "listings"

urlpatterns = [
    # Static paths must come before the <slug:slug>/ catch-all below,
    # or e.g. "new/" would be swallowed as a slug lookup instead.
    path("", views.listing_list_view, name="list"),
    path("new/", views.listing_create_view, name="create"),
    path("mine/", views.my_listings_view, name="my_listings"),
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("specs-fields/", views.listing_specs_fields_view, name="specs_fields"),
    path("<slug:slug>/", views.listing_detail_view, name="detail"),
    path("<slug:slug>/edit/", views.listing_edit_view, name="edit"),
    path("<slug:slug>/publish/", views.listing_publish_view, name="publish"),
    path("<slug:slug>/delete/", views.listing_delete_view, name="delete"),
    path(
        "<slug:slug>/wishlist-toggle/",
        views.wishlist_toggle_view,
        name="wishlist_toggle",
    ),
]