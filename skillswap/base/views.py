from base64 import b64encode
import codecs
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login, logout
from django.contrib.auth.forms import UserCreationForm
from .models import Room, Topic, Message
from .forms import RoomForm, UserForm
from .forms import CustomUserCreationForm
from .models import AdditionalUserDetails

# rooms =[
#     {'id':1, 'name': 'Learn python'},
#     {'id':2, 'name': 'Learn DSA'},
#     {'id':3, 'name': 'Learn Web development'},
# ]

# Create your views here.

def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method =='POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
            user = authenticate(request, username = username , password = password)

            if user is not None:
                login(request, user)
                messages.success(request,'Login Successfully.')
                return redirect('home')
            else:
                messages.error(request,'Username or Password is invalid.')
        except:
            messages.error(request, 'User does not exist.')
        
        

    context = {'page':page}
    return render (request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('/')

def registerPage(request):
    page = 'register'
    form = CustomUserCreationForm()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        print(request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()

            # Create additional user details
            gender = form.cleaned_data.get('gender')
            avatar = form.cleaned_data.get('avatar')

            # Set avatar URL based on gender and username
            avatar_url = f"https://avatar.iran.liara.run/public/{gender}?username={user.username}"

            additional_details = AdditionalUserDetails(
                username=user,
                gender=gender,
                avatar=avatar.read() if avatar else None  # Save the avatar binary data if provided
            )
            additional_details.save()

            login(request, user)
            return redirect('home')
        else:
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, f"{error}")
    return render(request, 'base/login_register.html', {'form': form})

@login_required(login_url='login')
def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    current_user = request.user

    rooms = Room.objects.filter(Q(topic__name__icontains = q) | Q(name__icontains=q) | Q(description__icontains=q))

    room_count = rooms.count()

    topics = Topic.objects.all()[0:5]
    input_image = 'https://randomuser.me/api/portraits/men/22.jpg'
 
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    additional_info = AdditionalUserDetails.objects.filter(username = current_user)
    
    context = {'rooms':rooms,'topics':topics ,'room_count':room_count, 'room_messages':room_messages, 'avatar':input_image}
    context = addLogo(additional_info, context)
    return render(request,'base/home.html',context)

@login_required(login_url='login')
def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk = room.id)

    context = {'room':room,'room_messages':room_messages, 'participants':participants}
    return render(request,'base/room.html', context)

def userProfile(request,pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user':user, 'rooms':rooms, 'room_messages':room_messages, 'topics':topics}
    return render(request,'base/profile.html', context)

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method =='POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name = topic_name)
        Room.objects.create(
            host =request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description'),
        )
        return redirect('home')

    context = {'form': form, 'topics':topics}
    return render(request,'base/room_form.html', context)

@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance = room)
    topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse("You are not allowed here !!")

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
    
    context = {'form':form, 'topics':topics,'room':room}
    return render(request,'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse("You are not allowed here !!")

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj':room})

@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse("You are not allowed here !!")

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj':message})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile',pk = user.id)
    return render(request,'base/update-user.html',{'form':form})

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {'topics':topics}
    return render(request, 'base/topics.html', context)

def activityPage(request):
    room_messages = Message.objects.all()
    context = {'room_messages':room_messages}
    return render(request,'base/activity.html', context)

def homePage(request):
    return render(request, 'base/homepage.html')


def addLogo(additional_info, context):
    if additional_info:
        avatar = additional_info[0].avatar
        if avatar:
            encoded = b64encode(avatar)
            encoded = codecs.decode(encoded, 'utf-8')
            mime = ['image/jpeg','image/svg+xml','image/png','image/x-icon']
            for mime_val in mime:
                input_image = "data:%s;base64,%s" % (mime_val, encoded)
            context['avatar']=input_image
    return context