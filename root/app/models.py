import random, string
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Post(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField(max_length=2000)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    img = models.ImageField(upload_to ='uploads/', null=True, blank=True)

    class Meta:
        ordering = ['-updated', '-created']

class Friend(models.Model):
    users = models.ManyToManyField(User, blank=False)
    current_user = models.ForeignKey(User, related_name='owner', null=True, on_delete=models.CASCADE)

    @classmethod
    def make_friend(cls, current_user, new_friend):
        friend, created = cls.objects.get_or_create(current_user=current_user)
        friend.users.add(new_friend)
    
    @classmethod
    def lose_friend(cls, current_user, new_friend):
        friend, created = cls.objects.get_or_create(current_user=current_user)
        friend.users.remove(new_friend)

class Message(models.Model):
    text = models.TextField(max_length=2000, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender', blank=True, default="None") 
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receiver', blank=True, default="None") 
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    seen = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text}"
    
    class Meta:
        ordering = ['-updated', '-created']
