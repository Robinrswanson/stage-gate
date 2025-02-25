from django.db import models
from django.contrib.auth.models import User

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default="New Chat")
    last_used = models.DateTimeField(auto_now=True)
    report = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'last_used'])
        ]

class Message(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('model', 'Model')
    ]

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

class UserMessage(Message):
    content = models.TextField(blank=True, null=True)

class FileMessage(Message):
    file_name = models.CharField(max_length=200)
    file = models.ForeignKey('FileUpload', on_delete=models.SET_NULL, null=True)

class AiMessage(Message):
    content1 = models.TextField(null=True)
    content2 = models.TextField(blank=True, null=True)
    report = models.TextField(blank=True, null=True)

class FileUpload(models.Model):
    file = models.FileField(upload_to='uploads/')
    extracted_text = models.TextField(blank=True, null=True)

    def delete(self, *args, **kwargs):
        self.file.delete(save=False)
        super().delete(*args, **kwargs)
