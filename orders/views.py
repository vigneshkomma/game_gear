from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from listings.models import Listing
from users.utils import get_profile

from .forms import OrderCreateForm, OrderStatusUpdateForm, ReviewForm
from .models import Order


@login_required
def order_create_view(request, listing_slug):
    """Entry point from a listing's 'Buy now' button."""
    listing = get_object_or_404(Listing, slug=listing_slug, status=Listing.ACTIVE)
    buyer = get_profile(request.user)
    if buyer == listing.seller:
        messages.error(request, "You can't buy your own listing.")
        return redirect("listings:detail", slug=listing.slug)

    if request.method == "POST":
        form = OrderCreateForm(request.POST, buyer=buyer)
        if form.is_valid():
            order = form.save(commit=False)
            order.listing = listing
            order.buyer = buyer
            order.seller = listing.seller
            order.price = listing.price  # snapshot — listing.price may change later
            order.save()
            # Take the listing off the active market while this order
            # is worked out; it only becomes "purchased" on completion.
            listing.status = Listing.RESERVED
            listing.save(update_fields=["status"])
            messages.success(
                request, "Order placed — coordinate payment/delivery with the seller."
            )
            return redirect("orders:detail", pk=order.pk)
    else:
        form = OrderCreateForm(buyer=buyer)

    return render(
        request, "orders/order_create.html", {"form": form, "listing": listing}
    )


@login_required
def order_list_view(request):
    profile = get_profile(request.user)
    orders = Order.objects.filter(Q(buyer=profile) | Q(seller=profile)).select_related(
        "listing"
    )
    return render(
        request, "orders/order_list.html", {"orders": orders, "profile": profile}
    )


@login_required
def order_detail_view(request, pk):
    profile = get_profile(request.user)
    order = get_object_or_404(
        Order.objects.filter(Q(buyer=profile) | Q(seller=profile)), pk=pk
    )
    can_review = order.status == Order.COMPLETED and not order.reviews.filter(
        reviewer=profile
    ).exists()
    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
            "profile": profile,
            "can_review": can_review,
            # Only the seller gets the editable inline status control;
            # the buyer sees status as plain text (status_control.html
            # checks this to decide which to render).
            "can_update_status": profile == order.seller,
            "status_choices": Order.STATUS_CHOICES,
        },
    )


@login_required
def order_status_update_view(request, pk):
    # Only the seller drives fulfillment status (paid/shipped/etc.).
    order = get_object_or_404(Order, pk=pk, seller=get_profile(request.user))
    if request.method == "POST":
        form = OrderStatusUpdateForm(request.POST, instance=order)
        if form.is_valid():
            new_status = form.cleaned_data["status"]
            if new_status == Order.COMPLETED:
                order.mark_completed()  # also flips listing to purchased
            else:
                order = form.save()

            if request.headers.get("HX-Request"):
                # Same URL serves both the inline control on
                # order_detail.html (this branch) and the standalone
                # fallback page below (non-HTMX POST) — one view,
                # two response shapes depending on how it was called.
                return render(
                    request,
                    "orders/partials/status_control.html",
                    {
                        "order": order,
                        "can_update_status": True,
                        "status_choices": Order.STATUS_CHOICES,
                    },
                )
            messages.success(request, "Order status updated.")
            return redirect("orders:detail", pk=order.pk)
    else:
        form = OrderStatusUpdateForm(instance=order)
    return render(
        request, "orders/order_status_form.html", {"form": form, "order": order}
    )


@login_required
def order_cancel_view(request, pk):
    profile = get_profile(request.user)
    order = get_object_or_404(
        Order.objects.filter(Q(buyer=profile) | Q(seller=profile)), pk=pk
    )
    if request.method == "POST":
        order.cancel()
        # Put the listing back on the market.
        order.listing.status = Listing.ACTIVE
        order.listing.save(update_fields=["status"])
        messages.info(request, "Order cancelled.")
        return redirect("orders:detail", pk=order.pk)
    return render(request, "orders/order_confirm_cancel.html", {"order": order})


@login_required
def review_create_view(request, pk):
    profile = get_profile(request.user)
    order = get_object_or_404(
        Order.objects.filter(Q(buyer=profile) | Q(seller=profile)),
        pk=pk,
        status=Order.COMPLETED,
    )
    reviewee = order.seller if profile == order.buyer else order.buyer

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.order = order
            review.reviewer = profile
            review.reviewee = reviewee
            review.full_clean()  # runs Review.clean() before saving
            review.save()
            messages.success(request, "Review submitted.")
            return redirect("orders:detail", pk=order.pk)
    else:
        form = ReviewForm()

    return render(
        request, "orders/review_form.html", {"form": form, "order": order}
    )