from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Address, Profile
from .utils import get_profile

User = get_user_model()


class SignUpForm(UserCreationForm):
    """Standard Django user creation, extended with the fields we need
    on Profile before the account is usable (phone number)."""

    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        max_length=10,
        help_text="10-digit mobile number — you'll verify it by OTP next.",
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"]
        if Profile.objects.filter(phone_number=phone_number).exists():
            raise ValidationError("This phone number is already registered.")
        return phone_number

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # Don't assume the post_save signal already created a
            # Profile row — get_profile() creates one if it's somehow
            # missing, so signup never depends on signal timing.
            profile = get_profile(user)
            profile.phone_number = self.cleaned_data["phone_number"]
            profile.save(update_fields=["phone_number"])
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["avatar", "bio", "city", "state", "pincode"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "label",
            "full_name",
            "phone",
            "line1",
            "line2",
            "city",
            "state",
            "pincode",
            "is_default",
        ]