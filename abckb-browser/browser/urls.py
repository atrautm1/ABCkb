"""abckb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="browser-home"),
    path('about/', views.about, name="browser-about"),
    path('search/', views.search, name="browser-search"),
    path('builder/', views.build, name="browser-builder"),
    path('query/', views.runquery, name="browser-runquery"),
    path('cypherquery/', views.viewcypher, name="browser-cypherquery"),
    path('download/', views.download, name="browser-download"),
]
