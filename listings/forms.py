from django import forms
from django.forms import inlineformset_factory
from django.urls import reverse_lazy

from .models import Category, CategoryAttribute, Listing, ListingImage, ListingSpec


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            "category",
            "title",
            "description",
            "condition",
            "price",
            "is_negotiable",
            "quantity",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only leaf categories are selectable — sellers shouldn't post
        # directly under an organizational parent like "PC Components".
        self.fields["category"].queryset = Category.objects.filter(
            is_active=True, children__isnull=True
        )
        # HTMX: whenever the category changes, fetch that category's
        # spec fields (VRAM, switch type, etc.) and swap them into
        # #specs-fields, without a full page reload. hx-include="this"
        # ensures only the category value itself is sent, not the
        # whole form (which may have partially-filled required fields
        # elsewhere that would otherwise fail validation on this
        # side-request).
        self.fields["category"].widget.attrs.update(
            {
                "hx-get": reverse_lazy("listings:specs_fields"),
                "hx-target": "#specs-fields",
                "hx-trigger": "change",
                "hx-include": "this",
            }
        )


ListingImageFormSet = inlineformset_factory(
    Listing,
    ListingImage,
    fields=["image", "is_primary", "order"],
    extra=3,
    can_delete=True,
)


class ListingSpecsForm(forms.Form):
    """Builds one form field per CategoryAttribute belonging to the
    listing's chosen category — this is what turns 'VRAM' and
    'Wattage' into actual input boxes on the listing form.

    Usage:
        form = ListingSpecsForm(request.POST, category=some_category)
        if form.is_valid():
            form.save(listing)
    """

    def __init__(self, *args, category=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category
        if not category:
            return
        for attribute in category.attributes.all():
            field_name = f"attr_{attribute.id}"
            required = attribute.is_required
            if attribute.data_type == CategoryAttribute.NUMBER:
                field = forms.DecimalField(required=required, label=attribute.name)
            elif attribute.data_type == CategoryAttribute.CHOICE:
                choices = [(c, c) for c in (attribute.choices or [])]
                field = forms.ChoiceField(
                    choices=choices, required=required, label=attribute.name
                )
            elif attribute.data_type == CategoryAttribute.BOOLEAN:
                field = forms.BooleanField(required=False, label=attribute.name)
            else:
                field = forms.CharField(required=required, label=attribute.name)
            self.fields[field_name] = field

    def save(self, listing):
        for attribute in self.category.attributes.all():
            value = self.cleaned_data.get(f"attr_{attribute.id}")
            if value in (None, ""):
                continue
            ListingSpec.objects.update_or_create(
                listing=listing, attribute=attribute, defaults={"value": str(value)}
            )


class ListingSearchForm(forms.Form):
    q = forms.CharField(required=False, label="Search")
    category = forms.CharField(required=False)
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    city = forms.CharField(required=False)