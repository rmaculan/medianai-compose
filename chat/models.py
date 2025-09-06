from django.db import models
from django.conf import settings
import datetime
# Use string literal to avoid circular imports
# from blog.models import Profile

class Room(models.Model):
    room_name = models.CharField(max_length=255)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='creator_id',
        default=None,
        )
    participant = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='chat_rooms',
        )
    created_at = models.DateTimeField(
        default=datetime.datetime.now
        )
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.room_name

class Message(models.Model):
    room = models.ForeignKey(
        Room, 
        on_delete=models.CASCADE
        )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        related_name='sender_id',
        null=True,
        )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='receiver_id',
        default=None,
        null=True,
        blank=True,

        )
    message = models.TextField()
    date = models.DateTimeField(
        default=datetime.datetime.now)

    def __str__(self):
        return f"{str(self.room)} - {self.sender}"
