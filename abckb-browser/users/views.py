from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("Username")
            messages.success(request, f"Account created for {username}")
            return redirect("browser-home")
    else:
        form = UserCreationForm()
    return render(request, "users/register.html", {"form":form})

@login_required
def profile(request):
    return render(request, "users/profile.html")