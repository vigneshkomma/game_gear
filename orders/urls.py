from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list_view, name="list"),
    path("buy/<slug:listing_slug>/", views.order_create_view, name="create"),
    path("<int:pk>/", views.order_detail_view, name="detail"),
    path("<int:pk>/status/", views.order_status_update_view, name="status_update"),
    path("<int:pk>/cancel/", views.order_cancel_view, name="cancel"),
    path("<int:pk>/review/", views.review_create_view, name="review_create"),
]