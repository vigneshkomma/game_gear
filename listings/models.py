from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from users.models import Profile


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    icon = models.CharField(
        max_length=50, blank=True, help_text="Optional icon name/class for UI"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return f"{self.parent.name} → {self.name}" if self.parent else self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_leaf(self):
        return not self.children.exists()


class CategoryAttribute(models.Model):
    """Defines one custom spec field for a category — e.g. Category
    'Graphics Cards' might define attributes 'VRAM' (number) and
    'Wattage' (number). The actual per-listing values live in
    ListingSpec, not here.
    """

    TEXT = "text"
    NUMBER = "number"
    CHOICE = "choice"
    BOOLEAN = "boolean"
    DATA_TYPE_CHOICES = [
        (TEXT, "Text"),
        (NUMBER, "Number"),
        (CHOICE, "Choice"),
        (BOOLEAN, "Yes/No"),
    ]

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="attributes"
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True)
    data_type = models.CharField(
        max_length=10, choices=DATA_TYPE_CHOICES, default=TEXT
    )
    choices = models.JSONField(
        null=True,
        blank=True,
        help_text='Only used when data_type="choice". List of strings, e.g. ["Cherry MX Red","Cherry MX Blue"]',
    )
    is_required = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]
        unique_together = ("category", "slug")

    def __str__(self):
        return f"{self.category.name} — {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Listing(models.Model):
    DRAFT = "draft"
    ACTIVE = "active"
    RESERVED = "reserved"
    PURCHASED = "purchased"
    REMOVED = "removed"
    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (ACTIVE, "Active"),
        (RESERVED, "Reserved"),
        (PURCHASED, "Purchased"),
        (REMOVED, "Removed"),
    ]

    NEW = "new"
    LIKE_NEW = "like_new"
    USED_GOOD = "used_good"
    USED_FAIR = "used_fair"
    FOR_PARTS = "for_parts"
    CONDITION_CHOICES = [
        (NEW, "New"),
        (LIKE_NEW, "Like New"),
        (USED_GOOD, "Used — Good"),
        (USED_FAIR, "Used — Fair"),
        (FOR_PARTS, "For Parts"),
    ]

    seller = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="listings"
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="listings"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    is_negotiable = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    pincode = models.CharField(max_length=6, blank=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    purchased_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "status", "city"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}-{Listing.objects.count() + 1}"
        # Default the item's location to the seller's, unless set explicitly.
        if not self.city and self.seller_id:
            self.city = self.seller.city
            self.state = self.seller.state
            self.pincode = self.seller.pincode
        super().save(*args, **kwargs)

    def mark_purchased(self):
        self.status = self.PURCHASED
        self.purchased_at = timezone.now()
        self.save(update_fields=["status", "purchased_at"])

    @property
    def is_purchased(self):
        return self.status == self.PURCHASED

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()


def listing_image_upload_path(instance, filename):
    return f"listings/{instance.listing_id}/{filename}"


class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to=listing_image_upload_path)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Image for {self.listing.title}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            ListingImage.objects.filter(
                listing=self.listing, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class ListingSpec(models.Model):
    """One filled-in value for a listing, answering a CategoryAttribute
    question — e.g. listing #101, attribute 'VRAM', value '12'."""

    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="specs"
    )
    attribute = models.ForeignKey(
        CategoryAttribute, on_delete=models.CASCADE, related_name="values"
    )
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ("listing", "attribute")

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class Wishlist(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="wishlist"
    )
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "listing")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile} ♥ {self.listing}"