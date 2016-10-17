from django.db.models.signals import post_save
from django.contrib.auth.models import User
from .models import UserProfile


def create_profile(sender, instance, created, **kwargs):
    user = instance
    if created:
        profile = UserProfile(user=user)
        profile.save()


post_save.connect(create_profile, sender=User,
                  dispatch_uid="users-profile-create-signal")
