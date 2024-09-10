from django.shortcuts import render
from website.models import MyApp
from django.contrib.auth.decorators import login_required

@login_required(login_url="/members/login_user")
def index(request):
    all_apps = MyApp.objects.all()
    context = {
        'my_apps': all_apps,
        'page' : request.path
    }
    return render(request, 'website/index.html', context)



@login_required(login_url="/members/login_user")
def home(request):
    all_apps = MyApp.objects.all()
    context = {
        'my_apps': all_apps,
        'page' : request.path
    }
    return render(request, 'website/home.html', context)




