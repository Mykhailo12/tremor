import random, string
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="avatars/", default='avatars/avatar.jpg', verbose_name="user avatar")
    bio = models.TextField(max_length=500, null=True)

class Post(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField(max_length=2000)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    img = models.ImageField(upload_to ='uploads/', null=True, blank=True)
    likes = models.ManyToManyField(User, blank=True, related_name='likes')
    comments = models.ManyToManyField('Comment', blank=True, related_name='comments')

    class Meta:
        ordering = ['-updated', '-created']

class Comment(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField(max_length=400)
    created = models.DateTimeField(auto_now_add=True)

    class Meta: 
        ordering = ['-created']

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
    text = models.TextField(max_length=2000, blank=True, null=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender', default="None") 
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receiver', default="None")
    image = models.ImageField(upload_to="uploads/", verbose_name="message image", null=True, blank=True) 
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    seen = models.BooleanField(default=False)
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')

    def __str__(self):
        return f"{self.text}"
    
    class Meta:
        ordering = ['-updated', '-created']

def get_first_name(self):
    return self.first_name

User.add_to_class("__str__", get_first_name)
