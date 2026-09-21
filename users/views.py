from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AddressForm, ProfileForm, SignUpForm
from .models import Address


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created — welcome!")
            return redirect("users:profile")
    else:
        form = SignUpForm()
    return render(request, "users/signup.html", {"form": form})


@login_required
def profile_view(request):
    return render(request, "users/profile_detail.html", {"profile": request.user.profile})


@login_required
def profile_edit_view(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("users:profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "users/profile_edit.html", {"form": form})


@login_required
def address_list_view(request):
    addresses = request.user.profile.addresses.all()
    return render(request, "users/address_list.html", {"addresses": addresses})


@login_required
def address_create_view(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.profile = request.user.profile
            address.save()
            messages.success(request, "Address added.")
            return redirect("users:address_list")
    else:
        form = AddressForm()
    return render(request, "users/address_form.html", {"form": form})


@login_required
def address_edit_view(request, pk):
    address = get_object_or_404(Address, pk=pk, profile=request.user.profile)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated.")
            return redirect("users:address_list")
    else:
        form = AddressForm(instance=address)
    return render(request, "users/address_form.html", {"form": form})


@login_required
def address_delete_view(request, pk):
    address = get_object_or_404(Address, pk=pk, profile=request.user.profile)
    if request.method == "POST":
        address.delete()
        messages.success(request, "Address removed.")
        return redirect("users:address_list")
    return render(request, "users/address_confirm_delete.html", {"address": address})