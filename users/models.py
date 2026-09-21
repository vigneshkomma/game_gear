from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

# 28 states + 8 union territories
INDIAN_STATE_CHOICES = [
    ("AN", "Andaman and Nicobar Islands"),
    ("AP", "Andhra Pradesh"),
    ("AR", "Arunachal Pradesh"),
    ("AS", "Assam"),
    ("BR", "Bihar"),
    ("CH", "Chandigarh"),
    ("CT", "Chhattisgarh"),
    ("DN", "Dadra and Nagar Haveli and Daman and Diu"),
    ("DL", "Delhi"),
    ("GA", "Goa"),
    ("GJ", "Gujarat"),
    ("HR", "Haryana"),
    ("HP", "Himachal Pradesh"),
    ("JK", "Jammu and Kashmir"),
    ("JH", "Jharkhand"),
    ("KA", "Karnataka"),
    ("KL", "Kerala"),
    ("LA", "Ladakh"),
    ("LD", "Lakshadweep"),
    ("MP", "Madhya Pradesh"),
    ("MH", "Maharashtra"),
    ("MN", "Manipur"),
    ("ML", "Meghalaya"),
    ("MZ", "Mizoram"),
    ("NL", "Nagaland"),
    ("OR", "Odisha"),
    ("PY", "Puducherry"),
    ("PB", "Punjab"),
    ("RJ", "Rajasthan"),
    ("SK", "Sikkim"),
    ("TN", "Tamil Nadu"),
    ("TG", "Telangana"),
    ("TR", "Tripura"),
    ("UP", "Uttar Pradesh"),
    ("UT", "Uttarakhand"),
    ("WB", "West Bengal"),
]

phone_validator = RegexValidator(
    regex=r"^[6-9]\d{9}$",
    message="Enter a valid 10-digit Indian mobile number.",
)

pincode_validator = RegexValidator(
    regex=r"^\d{6}$",
    message="Enter a valid 6-digit PIN code.",
)


def avatar_upload_path(instance, filename):
    return f"avatars/{instance.user_id}/{filename}"


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone_number = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        validators=[phone_validator],
        help_text="10-digit Indian mobile number, no country code.",
    )
    phone_verified = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to=avatar_upload_path, null=True, blank=True)
    bio = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, choices=INDIAN_STATE_CHOICES, blank=True)
    pincode = models.CharField(
        max_length=6, blank=True, validators=[pincode_validator]
    )
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    is_seller_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.user.get_username()

    def record_review(self, rating):
        """Update the denormalized rating fields when a new Review lands.

        Call this from the reviews app right after a Review is created,
        e.g. profile.record_review(review.rating)
        """
        total = self.rating_avg * self.rating_count + rating
        self.rating_count += 1
        self.rating_avg = round(total / self.rating_count, 2)
        self.save(update_fields=["rating_avg", "rating_count"])


@receiver(post_save, sender=User)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    """Every User automatically gets a Profile row on creation."""
    if created:
        Profile.objects.create(user=instance)


class Address(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="addresses"
    )
    label = models.CharField(max_length=50, blank=True, help_text="e.g. Home, Office")
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=10, validators=[phone_validator])
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2, choices=INDIAN_STATE_CHOICES)
    pincode = models.CharField(max_length=6, validators=[pincode_validator])
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "id"]
        verbose_name_plural = "addresses"

    def __str__(self):
        return f"{self.label or 'Address'} — {self.full_name}"

    def save(self, *args, **kwargs):
        # Only one default address per profile — demote any existing
        # default when this one is saved as the new default.
        if self.is_default:
            Address.objects.filter(profile=self.profile, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        super().save(*args, **kwargs)