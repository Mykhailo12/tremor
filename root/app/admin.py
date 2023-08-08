from django.contrib import admin
from .models import Post, Friend, Message, Profile

admin.site.register(Post)
admin.site.register(Friend)
admin.site.register(Message)
admin.site.register(Profile)
