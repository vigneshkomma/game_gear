from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path("addresses/", views.address_list_view, name="address_list"),
    path("addresses/add/", views.address_create_view, name="address_create"),
    path("addresses/<int:pk>/edit/", views.address_edit_view, name="address_edit"),
    path(
        "addresses/<int:pk>/delete/",
        views.address_delete_view,
        name="address_delete",
    ),
]