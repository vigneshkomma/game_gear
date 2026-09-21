from django.contrib import admin

from .models import Address, Profile


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "phone_number",
        "phone_verified",
        "city",
        "state",
        "rating_avg",
        "rating_count",
        "is_seller_verified",
        "created_at",
    )
    list_filter = ("phone_verified", "is_seller_verified", "state")
    search_fields = ("user__username", "user__email", "phone_number", "city")
    readonly_fields = ("rating_avg", "rating_count", "created_at")
    inlines = [AddressInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "label",
        "full_name",
        "city",
        "state",
        "pincode",
        "is_default",
    )
    list_filter = ("state", "is_default")
    search_fields = ("full_name", "profile__user__username", "pincode")