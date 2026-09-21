from django.db import models
from django.utils import timezone

from listings.models import Listing
from users.models import Profile


class Conversation(models.Model):
    """One thread per (listing, buyer) pair — a seller's inbox is
    naturally grouped by item and by who they're talking to."""

    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="conversations"
    )
    buyer = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="conversations_as_buyer"
    )
    seller = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="conversations_as_seller"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("listing", "buyer")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.buyer} \u2194 {self.seller} on {self.listing}"

    @classmethod
    def start(cls, listing, buyer):
        """Get or create the conversation between this buyer and the
        listing's seller. Safe to call repeatedly — the same buyer
        messaging the same listing always lands in the same thread."""
        conversation, _ = cls.objects.get_or_create(
            listing=listing, buyer=buyer, defaults={"seller": listing.seller}
        )
        return conversation

    @property
    def last_message(self):
        return self.messages.order_by("-created_at").first()

    def unread_count_for(self, profile):
        return self.messages.filter(read_at__isnull=True).exclude(sender=profile).count()

    def mark_read_for(self, profile):
        """Mark everything the *other* party sent as read, now that
        `profile` has opened this thread."""
        self.messages.filter(read_at__isnull=True).exclude(sender=profile).update(
            read_at=timezone.now()
        )


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="messages_sent"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender}: {self.text[:30]}"