import os
from django.shortcuts import render, redirect
from .forms import CreateUserForm, PostForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Friend, Post
from django.http import HttpResponse

@login_required(login_url='login')
def room(request, room_name):
    if request.method == 'GET':
        print(request)

    sender=request.user 
    receiver=User.objects.get(username=room_name)

    return render(request, "chatbox.html", {"room_name": room_name, 'sender':sender, 'receiver':receiver })

@login_required(login_url='login')
def createPost(request):
    form = PostForm()

    if request.method == 'POST':
        Post.objects.create(
            host=request.user,
            text=request.POST.get('text'),
            img=request.FILES['img'],
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
            if len(post.img) > 0:
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

def registerPage(request):
    form = CreateUserForm()

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')

    context = {'form':form}
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

#if user is not login, he will be redirectered to the login page
@login_required(login_url='/login/')
def home(request):
    posts = Post.objects.all()
    context={'posts' : posts}
    return render(request, 'home.html', context)

def friendsPage(request):
    try:
        friend = Friend.objects.get(current_user = request.user)
        friends = friend.users.all()
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
        users = User.objects.filter(username__icontains=search_query)
    else:
        users = None
    context = {'users':users}
    return render(request, 'peoples.html', context)

def profilePage(request, pk):
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
        
    user = User.objects.get(id=pk)

    chat_name = f"{user.username}"

    context = {'user':user, 'friends':friends, 'is_friend':guy_is_already, 'chat_name' : chat_name}
    return render(request, 'profile.html', context)