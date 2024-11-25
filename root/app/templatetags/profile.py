from app.models import Profile
from django.shortcuts import render
from django.template import Library
from django.core.exceptions import ObjectDoesNotExist

register = Library()

@register.simple_tag
def profile(user):
    print(user)
    if user.is_superuser == 1:
        return "avatars/avatar.jpg"
    else:
        profile = Profile.objects.get(user=user)
        image = profile.image
        return image