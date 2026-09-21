from django.contrib import admin

from .models import Order, Review


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ("reviewer", "reviewee", "rating", "comment", "created_at")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "listing",
        "buyer",
        "seller",
        "price",
        "status",
        "delivery_method",
        "created_at",
    )
    list_filter = ("status", "delivery_method", "payment_method")
    search_fields = (
        "listing__title",
        "buyer__user__username",
        "seller__user__username",
    )
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("listing", "buyer", "seller")
    inlines = [ReviewInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("order", "reviewer", "reviewee", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = (
        "reviewer__user__username",
        "reviewee__user__username",
        "comment",
    )
    readonly_fields = ("created_at",)