from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from listings.models import Listing
from users.utils import get_profile

from .forms import MessageForm
from .models import Conversation


@login_required
def conversation_start_view(request, listing_slug):
    """Entry point from a listing's 'Message seller' button."""
    listing = get_object_or_404(Listing, slug=listing_slug)
    buyer = get_profile(request.user)
    if buyer == listing.seller:
        return HttpResponseForbidden("You can't message yourself about your own listing.")
    conversation = Conversation.start(listing, buyer)
    return redirect("contact:detail", pk=conversation.pk)


@login_required
def conversation_list_view(request):
    profile = get_profile(request.user)
    conversations = list(
        Conversation.objects.filter(Q(buyer=profile) | Q(seller=profile)).select_related(
            "listing", "buyer", "seller"
        )
    )
    # Templates can't call a method with arguments (unread_count_for
    # needs `profile`), so compute it here and stash it as a plain
    # attribute the template can read directly.
    for conversation in conversations:
        conversation.unread_count = conversation.unread_count_for(profile)

    return render(
        request,
        "contact/conversation_list.html",
        {"conversations": conversations, "profile": profile},
    )


@login_required
def conversation_detail_view(request, pk):
    profile = get_profile(request.user)
    conversation = get_object_or_404(
        Conversation.objects.filter(Q(buyer=profile) | Q(seller=profile)), pk=pk
    )
    # Opening the thread marks whatever the other party sent as read.
    conversation.mark_read_for(profile)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = conversation
            msg.sender = profile
            msg.save()
            conversation.save()  # bumps updated_at (auto_now) so the
            # thread re-sorts to the top of conversation_list_view

            if request.headers.get("HX-Request"):
                # Two things ride in this one response:
                # 1. the new message bubble — hx-swap="beforeend" on
                #    the form appends it to #message-list.
                # 2. a fresh, empty MessageForm marked hx-swap-oob="true"
                #    — htmx pulls this out of the response and swaps it
                #    into #message-form separately, which is what
                #    clears the textarea after sending.
                return render(
                    request,
                    "contact/partials/message_sent.html",
                    {
                        "msg": msg,
                        "profile": profile,
                        "conversation": conversation,
                        "form": MessageForm(),
                    },
                )
            return redirect("contact:detail", pk=conversation.pk)

        if request.headers.get("HX-Request"):
            # Invalid submission (e.g. empty message) — OOB-swap just
            # the form back in with its error shown, no page reload.
            return render(
                request,
                "contact/partials/message_form.html",
                {"conversation": conversation, "form": form},
            )
    else:
        form = MessageForm()

    return render(
        request,
        "contact/conversation_detail.html",
        {
            "conversation": conversation,
            "thread_messages": conversation.messages.select_related("sender"),
            "form": form,
            "profile": profile,
        },
    )