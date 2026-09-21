from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "text", "created_at", "read_at")
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("listing", "buyer", "seller", "created_at", "updated_at")
    search_fields = (
        "listing__title",
        "buyer__user__username",
        "seller__user__username",
    )
    list_select_related = ("listing", "buyer", "seller")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "short_text", "created_at", "read_at")
    search_fields = ("text", "sender__user__username")
    readonly_fields = ("created_at",)

    @admin.display(description="Message")
    def short_text(self, obj):
        return obj.text[:50]