from django.db import models
from accounts.models import User

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    action = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=50)
    entity_id = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
