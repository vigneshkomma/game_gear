from django.urls import path

from . import views

app_name = "contact"

urlpatterns = [
    path("", views.conversation_list_view, name="list"),
    path("start/<slug:listing_slug>/", views.conversation_start_view, name="start"),
    path("<int:pk>/", views.conversation_detail_view, name="detail"),
]