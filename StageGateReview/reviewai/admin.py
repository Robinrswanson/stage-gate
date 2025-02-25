from django.contrib import admin
from .models import Chat, Message, UserMessage, AiMessage, FileMessage

class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'role', 'created_at', 'get_message_preview')  # Show key info
    list_filter = ('chat', 'role')  # Group messages by chat
    search_fields = ('chat__title', 'role', 'usermessage__content', 'aimessage__content1', 'filemessage__file_name')  # Search messages
    ordering = ('chat', 'created_at')  # Sort by chat and timestamp
    list_per_page = 20  # Paginate messages

    def get_message_preview(self, obj):
        """ Show a short preview of the message content """
        if hasattr(obj, 'usermessage'):
            return obj.usermessage.content[:50] + "..." if obj.usermessage.content else "(No Content)"
        elif hasattr(obj, 'aimessage'):
            return obj.aimessage.content1[:50] + "..." if obj.aimessage.content1 else "(No Content)"
        elif hasattr(obj, 'filemessage'):
            return f"File: {obj.filemessage.file_name}"
        return "(Unknown Type)"

    get_message_preview.short_description = "Message Preview"

admin.site.register(Chat)  # Register Chat for reference
admin.site.register(Message, MessageAdmin)  # Register base Message model
admin.site.register(UserMessage, MessageAdmin)  # Register UserMessage
admin.site.register(AiMessage, MessageAdmin)  # Register AiMessage
admin.site.register(FileMessage, MessageAdmin)  # Register FileMessage
