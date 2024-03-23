from django.db import models
from accounts.models import User

# Create your models here.


class Friend(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("friend", "Friend"),
    )

    requester = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="requester"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="receiver"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("requester", "receiver")

    def __str__(self):
        return f"{self.requester} -> {self.receiver}: ({self.status})"
