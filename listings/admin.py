from django.contrib import admin

from .models import (
    Category,
    CategoryAttribute,
    Listing,
    ListingImage,
    ListingSpec,
    Wishlist,
)


class CategoryAttributeInline(admin.TabularInline):
    model = CategoryAttribute
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "is_leaf_display")
    list_filter = ("is_active", "parent")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CategoryAttributeInline]

    @admin.display(boolean=True, description="Leaf")
    def is_leaf_display(self, obj):
        return obj.is_leaf


@admin.register(CategoryAttribute)
class CategoryAttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "data_type", "is_required", "display_order")
    list_filter = ("data_type", "is_required", "category")
    search_fields = ("name", "category__name")


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1


class ListingSpecInline(admin.TabularInline):
    model = ListingSpec
    extra = 0
    autocomplete_fields = ["attribute"]


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "seller",
        "category",
        "price",
        "condition",
        "status",
        "city",
        "views_count",
        "created_at",
    )
    list_filter = ("status", "condition", "category", "state")
    search_fields = ("title", "description", "seller__user__username", "city")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("views_count", "created_at", "updated_at", "purchased_at")
    list_select_related = ("seller", "category")
    inlines = [ListingImageInline, ListingSpecInline]


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("profile", "listing", "created_at")
    search_fields = ("profile__user__username", "listing__title")
    list_select_related = ("profile", "listing")