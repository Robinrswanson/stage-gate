from .models import Message

def build_history(chat_id):
    messages = Message.objects.filter(chat_id=chat_id).order_by('created_at')
    history = []
    for message in messages:
        history.append({
            "role" : "user" if message.role == "user" else "model",
            "parts" : [message.content]
        })
    return history