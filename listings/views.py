from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ListingForm, ListingImageFormSet, ListingSearchForm, ListingSpecsForm
from .models import Category, Listing, Wishlist


def listing_list_view(request):
    listings = Listing.objects.filter(status=Listing.ACTIVE).select_related(
        "category", "seller"
    )

    search_form = ListingSearchForm(request.GET)
    if search_form.is_valid():
        data = search_form.cleaned_data
        if data["category"]:
            listings = listings.filter(category__slug=data["category"])
        if data["q"]:
            listings = listings.filter(
                Q(title__icontains=data["q"]) | Q(description__icontains=data["q"])
            )
        if data["min_price"] is not None:
            listings = listings.filter(price__gte=data["min_price"])
        if data["max_price"] is not None:
            listings = listings.filter(price__lte=data["max_price"])
        if data["city"]:
            listings = listings.filter(city__iexact=data["city"])

    return render(
        request,
        "listings/listing_list.html",
        {
            "listings": listings,
            "categories": Category.objects.filter(parent__isnull=True),
            "search_form": search_form,
        },
    )


def listing_detail_view(request, slug):
    listing = get_object_or_404(
        Listing.objects.select_related("seller", "category").prefetch_related(
            "images", "specs__attribute"
        ),
        slug=slug,
    )
    listing.views_count += 1
    listing.save(update_fields=["views_count"])

    is_wishlisted = (
        request.user.is_authenticated
        and Wishlist.objects.filter(
            profile=request.user.profile, listing=listing
        ).exists()
    )
    return render(
        request,
        "listings/listing_detail.html",
        {"listing": listing, "is_wishlisted": is_wishlisted},
    )


@login_required
def listing_create_view(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user.profile
            listing.status = Listing.DRAFT
            listing.save()

            specs_form = ListingSpecsForm(request.POST, category=listing.category)
            if specs_form.is_valid():
                specs_form.save(listing)

            image_formset = ListingImageFormSet(
                request.POST, request.FILES, instance=listing
            )
            if image_formset.is_valid():
                image_formset.save()

            messages.success(
                request, "Listing created as a draft — publish it when ready."
            )
            return redirect("listings:detail", slug=listing.slug)
        # Invalid base form — re-render with whatever category was
        # posted so the specs fields don't vanish on a validation error.
        category = form.data.get("category")
        specs_form = ListingSpecsForm(
            request.POST,
            category=Category.objects.filter(pk=category).first() if category else None,
        )
        image_formset = ListingImageFormSet(
            request.POST, request.FILES, instance=Listing()
        )
    else:
        form = ListingForm()
        specs_form = ListingSpecsForm()  # no category chosen yet — no fields
        image_formset = ListingImageFormSet(instance=Listing())
    return render(
        request,
        "listings/listing_form.html",
        {"form": form, "specs_form": specs_form, "image_formset": image_formset},
    )


@login_required
def listing_edit_view(request, slug):
    listing = get_object_or_404(Listing, slug=slug, seller=request.user.profile)
    if request.method == "POST":
        form = ListingForm(request.POST, instance=listing)
        if form.is_valid():
            listing = form.save()

            specs_form = ListingSpecsForm(request.POST, category=listing.category)
            if specs_form.is_valid():
                specs_form.save(listing)

            image_formset = ListingImageFormSet(
                request.POST, request.FILES, instance=listing
            )
            if image_formset.is_valid():
                image_formset.save()

            messages.success(request, "Listing updated.")
            return redirect("listings:detail", slug=listing.slug)
        category = form.data.get("category")
        specs_form = ListingSpecsForm(
            request.POST,
            category=Category.objects.filter(pk=category).first() if category else None,
        )
        image_formset = ListingImageFormSet(
            request.POST, request.FILES, instance=listing
        )
    else:
        form = ListingForm(instance=listing)
        # Pre-fill with whatever specs already exist for this listing.
        initial = {
            f"attr_{spec.attribute_id}": spec.value
            for spec in listing.specs.select_related("attribute")
        }
        specs_form = ListingSpecsForm(category=listing.category, initial=initial)
        image_formset = ListingImageFormSet(instance=listing)
    return render(
        request,
        "listings/listing_form.html",
        {"form": form, "specs_form": specs_form, "image_formset": image_formset},
    )



def listing_specs_fields_view(request):
    """HTMX endpoint: given ?category=<id>, returns just the spec
    input fields for that category, to be swapped into #specs-fields
    on the create/edit listing page when the category dropdown changes.
    """
    category_id = request.GET.get("category")
    category = Category.objects.filter(pk=category_id).first() if category_id else None
    specs_form = ListingSpecsForm(category=category)
    return render(
        request, "listings/partials/specs_fields.html", {"specs_form": specs_form}
    )


@login_required
def listing_publish_view(request, slug):
    listing = get_object_or_404(Listing, slug=slug, seller=request.user.profile)
    if request.method == "POST":
        listing.status = Listing.ACTIVE
        listing.save(update_fields=["status"])
        messages.success(request, "Listing is now live.")
    return redirect("listings:detail", slug=listing.slug)


@login_required
def listing_delete_view(request, slug):
    listing = get_object_or_404(Listing, slug=slug, seller=request.user.profile)
    if request.method == "POST":
        # Soft delete — keeps history for orders/reviews that reference it.
        listing.status = Listing.REMOVED
        listing.save(update_fields=["status"])
        messages.success(request, "Listing removed.")
        return redirect("listings:my_listings")
    return render(
        request, "listings/listing_confirm_delete.html", {"listing": listing}
    )


@login_required
def my_listings_view(request):
    listings = Listing.objects.filter(seller=request.user.profile).exclude(
        status=Listing.REMOVED
    )
    return render(request, "listings/my_listings.html", {"listings": listings})


@login_required
def wishlist_toggle_view(request, slug):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    listing = get_object_or_404(Listing, slug=slug)
    wishlist_item, created = Wishlist.objects.get_or_create(
        profile=request.user.profile, listing=listing
    )
    is_wishlisted = True
    if not created:
        wishlist_item.delete()
        is_wishlisted = False

    if request.headers.get("HX-Request"):
        # Swap just the button in place — no page reload.
        return render(
            request,
            "listings/partials/wishlist_button.html",
            {"listing": listing, "is_wishlisted": is_wishlisted},
        )

    # Non-HTMX fallback (JS disabled, or a plain <form method="post"> submit):
    # same effect, just a full redirect back to the listing.
    messages.success(
        request, "Added to wishlist." if is_wishlisted else "Removed from wishlist."
    )
    return redirect("listings:detail", slug=listing.slug)


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(profile=request.user.profile).select_related(
        "listing"
    )
    return render(request, "listings/wishlist.html", {"items": items})