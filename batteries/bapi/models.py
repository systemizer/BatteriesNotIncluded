from django.contrib.auth.models import User
from django.db import models

class CheckIn(models.Model):
    user = models.ForeignKey(User)
    event_url = models.CharField(max_length=250)
    date_created = models.DateTimeField(auto_now_add=True)

