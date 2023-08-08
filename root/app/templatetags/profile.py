from app.models import Profile
from django.shortcuts import render
from django.template import Library

register = Library()

@register.simple_tag
def profile(user):
    profile = Profile.objects.get(user=user)
    image = profile.image
    return image