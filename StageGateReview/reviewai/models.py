from django.db import models
from django.contrib.auth.models import User

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default="New Chat")
    last_used = models.DateTimeField(auto_now=True)  # Updates on every save

    class Meta:
        indexes = [
            models.Index(fields=['user', 'last_used'])  # Speeds up user-specific queries
        ]

class Message(models.Model):
    ROLE_CHOICES = [
        ('user', 'user'),    # First value is stored in DB, second is human-readable
        ('model', 'model')
    ]

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
    
class FileUpload(models.Model):
    file = models.FileField(upload_to='uploads/')
    extracted_text = models.TextField(blank=True, null=True)  # Store extracted text