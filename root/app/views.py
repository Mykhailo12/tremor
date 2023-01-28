from django.shortcuts import render, redirect
from .forms import CreateUserForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

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
    return render(request, 'home.html')