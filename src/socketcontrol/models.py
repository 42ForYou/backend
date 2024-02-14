from django.db import models
from accounts.models import User


class SocketSession(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="socket_session"
    )
    session_id = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SocketSession {self.session_id} of {self.user.username}"
