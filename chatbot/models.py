from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CustomUser(AbstractUser):
    phone = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.username


class ChatHistory(models.Model):
    user_query = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.user_query[:50]}..."


class Document(models.Model):
    filename = models.CharField(max_length=255)
    content = models.TextField()
    embedding_id = models.CharField(max_length=255, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"



class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions') #setting.py line no 115
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.title} ({self.user.username})"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    user_query = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"[{self.timestamp}] {self.user_query[:50]}..."