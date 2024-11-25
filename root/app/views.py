import os
import math
from django.shortcuts import render, redirect
from .forms import CreateUserForm, PostForm, ProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Friend, Post, Message, Profile
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.forms.models import model_to_dict


@login_required(login_url='login')
def room(request, room_name):
    if request.method == 'GET':
        print(request)

    sender=request.user 
    receiver=User.objects.get(username=room_name)

    messages = reversed(Message.objects.filter(receiver=receiver, sender=sender).select_related('receiver', 'sender')|Message.objects.filter(receiver=sender, sender=receiver).select_related('receiver', 'sender'))
    
    receiver_profile = Profile.objects.get(user = receiver)

    return render(request, "chatbox.html", {"room_name": room_name, 'sender':sender, 'receiver':receiver, 'messages':messages, 'receiver_profile' : receiver_profile})

@login_required(login_url='login')
def createPost(request):
    form = PostForm()

    if request.method == 'POST':
        if len(request.FILES) != 0:
            Post.objects.create(
                host=request.user,
                text=request.POST.get('text'),
                img=request.FILES['img'],
            )
        else:
            Post.objects.create(
                host=request.user,
                text=request.POST.get('text'),
                img=None,
            )
        return redirect('home')

    context = {'form':form}
    return render(request, 'post_form.html', context)

@login_required(login_url='login')
def updatePost(request, pk):
    post = Post.objects.get(id=pk)   

    if request.user != post.host:
        return HttpResponse("Your are not allowed here!!")

    if request.method == 'POST':
        if len(request.FILES) != 0:
            if post.img != '':
                os.remove(post.img.path)
            post.img = request.FILES['img']
        post.text = request.POST.get('text', None)
        print(post.text)
        if post.text:
            print("f")
            post.text_field = post.text
        post.save()

        context = {'post':post}
        return redirect('home')

    context = {'post':post}
    return render(request, 'update_post.html', context)

@login_required(login_url='login')
def deletePost(request, pk):
    Post.objects.filter(id=pk).delete()

    return redirect('home')
    

@login_required(login_url='login')
def updateProfile(request, pk):
    profile = Profile.objects.get(user_id=pk)

    if request.user != profile.user:
        return HttpResponse("Your are not allowed here!!")

    if request.method == 'POST':
        if len(request.FILES) != 0:
            path = os.path.normpath(profile.image.path).split(os.path.sep)
            new_path = os.path.join(*path[-1:])
            if len(profile.image) > 0 and new_path != 'avatar.jpg':
                os.remove(profile.image.path)
            
            profile.image = request.FILES['img']

        print(request.POST)
        profile.bio = request.POST.get('text')
        print(profile.bio)
        profile.save()

        return redirect('home')

    context = {'profile':profile}
    return render(request, 'update_post.html', context)

def registerPage(request):
    user_form = CreateUserForm()

    if request.method == 'POST':
        user_form = CreateUserForm(request.POST)
        if user_form.is_valid():
            user_form.save()

            username = user_form.cleaned_data["username"]

            user = User.objects.get(username=username)
            Profile.objects.create(user=user)   

            return redirect('home')

    context = {'user_form':user_form}
    return render(request, 'register.html', context)

def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password) 

        if user is not None:
            login(request, user)
            return redirect('home')

    context = {}

    return render(request, 'login.html', context)

def logoutUser(request):
    logout(request)
    return redirect('login')

@login_required(login_url='/login/')
def home(request):
    posts = Post.objects.all()

    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page', 1)
    max_page_num = math.ceil(posts.count()/5)

    posts = paginator.get_page(page_number)

    user = request.user
    liked_posts = Post.objects.filter(likes=user)

    is_post = False
    if len(posts) > 0:
        is_post = True

    context={'page_number' : page_number, 'max_page_num':max_page_num, 'is_post' : is_post, 'liked_posts' : liked_posts, 'posts': posts}
    if max_page_num >= int(page_number):
        if request.htmx:
            print(request.htmx)
            return render(request, "posts.html", context)
    else: 
        return HttpResponse('')

    return render(request, "home.html", context)

@login_required(login_url='/login/')
def getComment(request, pk):
    post = Post.objects.get(id=pk)

    paginator = Paginator(post.comments.all(), 5)
    page_number = request.GET.get('page', 1)

    comments = paginator.get_page(page_number)

    for comment in comments:
        print(comment.text)

    context = {'comments': comments, 'page_number' : page_number, 'id' : pk}

    return render(request, "get_comment.html", context)

def friendsPage(request):
    try:
        friends = Friend.objects.get(current_user = request.user).users.all().values('id', 'username', 'pk')
        context = {'friends':friends}
    except Friend.DoesNotExist:
        text = 'No friends yet.'
        friends = None
        context = {'friends':friends, 'text':text}
    
    return render(request, 'friends.html', context)   
    
def change_friends(request, operation, pk):
    friend = User.objects.get(pk=pk)
    if operation == 'add':
        Friend.make_friend(request.user, friend)
        return redirect('peoples')
    elif operation == 'remove':
        Friend.lose_friend(request.user, friend)
        return redirect('friends')

def peoplesPage(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        print(search_query)
        users = User.objects.filter(username__icontains=search_query)
    else:
        users = None
    context = {'users':users}
    return render(request, 'peoples.html', context)

def profilePage(request, pk):
    user = User.objects.get(id=pk)
    
    try:
        friend = Friend.objects.get(current_user = request.user)
        friends = friend.users.all()
    except Friend.DoesNotExist:
        friends = None

    guy_is_already = False
    if friends:
        for i in range(len(friends)):
            if int(friends[i].id) == int(pk):
                guy_is_already = True
    
    if user.is_superuser != True:
        profile = Profile.objects.get(user_id=pk)
    else: 
        profile = None

    chat_name = f"{user.username}"

    context = {'user':user, 'friends':friends, 'is_friend':guy_is_already, 'chat_name' : chat_name, 'profile' : profile}
    return render(request, 'profile.html', context)

