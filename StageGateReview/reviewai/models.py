from django.db import models

class FileUpload(models.Model):
    file = models.FileField(upload_to='uploads/')
    extracted_text = models.TextField(blank=True, null=True)  # Store extracted text

class ChatMessage(models.Model):
    session_id = models.CharField(max_length=255)
    content = models.TextField()
    is_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
