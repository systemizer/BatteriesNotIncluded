from django_facebook.models import FacebookProfileModel

class BatteriesProfile(FacebookProfileModel):
    user = models.OneToOneField('auth.User')

from django.contrib.auth.models import User
from django.db.models.signals import post_save

#Make sure we create a MyCustomProfile when creating a User
def create_facebook_profile(sender, instance, created, **kwargs):
    if created:
        BatteriesProfile.objects.create(user=instance)

post_save.connect(create_facebook_profile, sender=User)