from django.core.exceptions import ValidationError
from django.db import models

from listings.models import Listing
from users.models import Address, Profile


class Order(models.Model):
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"
    REFUNDED = "refunded"
    STATUS_CHOICES = [
        (PENDING_PAYMENT, "Pending Payment"),
        (PAID, "Paid"),
        (SHIPPED, "Shipped"),
        (DELIVERED, "Delivered"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
        (DISPUTED, "Disputed"),
        (REFUNDED, "Refunded"),
    ]

    COURIER = "courier"
    LOCAL_PICKUP = "local_pickup"
    DELIVERY_METHOD_CHOICES = [
        (COURIER, "Courier"),
        (LOCAL_PICKUP, "Local Pickup"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("upi", "UPI"),
        ("card", "Card"),
        ("netbanking", "Net Banking"),
        ("cod", "Cash on Delivery"),
    ]

    listing = models.ForeignKey(
        Listing, on_delete=models.PROTECT, related_name="orders"
    )
    buyer = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="orders_as_buyer"
    )
    seller = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="orders_as_seller"
    )
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Null for local pickup.",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Snapshot of the agreed price at order time — may "
                  "differ from the listing's current price if it was negotiated.",
    )
    delivery_method = models.CharField(
        max_length=20, choices=DELIVERY_METHOD_CHOICES, default=LOCAL_PICKUP
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=PENDING_PAYMENT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — {self.listing.title}"

    def mark_completed(self):
        """The one path that should flip an order to completed — also
        flips the underlying listing to 'purchased' so the two never
        drift out of sync."""
        self.status = self.COMPLETED
        self.save(update_fields=["status"])
        self.listing.mark_purchased()

    def cancel(self):
        self.status = self.CANCELLED
        self.save(update_fields=["status"])


class Review(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="reviews_given"
    )
    reviewee = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="reviews_received"
    )
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("order", "reviewer")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reviewer} \u2192 {self.reviewee}: {self.rating}\u2605"

    def clean(self):
        parties = (self.order.buyer_id, self.order.seller_id)
        if self.reviewer_id not in parties:
            raise ValidationError("Reviewer must be the buyer or seller on this order.")
        if self.reviewee_id not in parties:
            raise ValidationError("Reviewee must be the buyer or seller on this order.")
        if self.reviewer_id == self.reviewee_id:
            raise ValidationError("You can't review yourself.")
        if self.order.status != Order.COMPLETED:
            raise ValidationError("You can only review a completed order.")

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating:
            # Keep Profile.rating_avg/rating_count in sync — see
            # Profile.record_review() in the users app.
            self.reviewee.record_review(self.rating)


from django.db import models

# Create your models here.
