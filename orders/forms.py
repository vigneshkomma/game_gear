from django import forms

from .models import Order, Review


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["shipping_address", "delivery_method", "payment_method"]

    def __init__(self, *args, buyer=None, **kwargs):
        super().__init__(*args, **kwargs)
        if buyer is not None:
            # Only let the buyer pick from their own saved addresses.
            self.fields["shipping_address"].queryset = buyer.addresses.all()
        self.fields["shipping_address"].required = False


class OrderStatusUpdateForm(forms.ModelForm):
    """Used by the seller to move an order through pending_payment →
    paid → shipped → delivered → completed (or cancelled/disputed)."""

    class Meta:
        model = Order
        fields = ["status"]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3}),
        }