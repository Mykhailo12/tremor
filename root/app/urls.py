from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('register/', views.registerPage, name="register"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('friends/', views.friendsPage, name="friends"),
    path('peoples/', views.peoplesPage, name="peoples"),
    path('profile/<str:pk>/', views.profilePage, name="profile"),
    path('create/', views.createPost, name="create"),
    path('update/<str:pk>/', views.updatePost, name="update"),
    path('update_profile/<str:pk>/', views.updateProfile, name="update_profile"),
    path('delete/<str:pk>/', views.deletePost, name='delete'),

    path('getcomment/<str:pk>/', views.getComment, name='getcomment'),

    path("chat/<str:room_name>/", views.room, name="room"),

    re_path(r'^connect/(?P<operation>.+)/(?P<pk>\d+)/$', views.change_friends, name="change_friends"),
]
