from django.conf import settings
from django.db import models
from django.utils import timezone


class Chat(models.Model):
    announcement = models.ForeignKey(
        "apps.Announcement",
        on_delete=models.CASCADE,
        related_name="chats"
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="buyer_chats"
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_chats"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("announcement", "buyer", "seller")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Chat #{self.id}"


class Message(models.Model):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    @property
    def is_delivered(self):
        return self.delivered_at is not None

    @property
    def is_read(self):
        return self.read_at is not None

    def __str__(self):
        return f"{self.sender} -> {self.chat_id}"


class ChatPresence(models.Model):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="presences"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_presences"
    )
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("chat", "user")

    def __str__(self):
        return f"{self.user} in chat {self.chat_id}"