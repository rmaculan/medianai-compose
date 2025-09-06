from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required 
from django import forms
from .models import Item, ItemMessage, CategoryModel
from chat.models import Message, Room
import logging
from django.views.generic.edit import CreateView
from .forms import ItemPostForm
from django.core.files.storage import default_storage
from PIL import Image
from django.http import HttpResponseBadRequest
from django.db.models import Q
from chat.models import Message

logger = logging.getLogger(__name__)

class ItemPostView(CreateView):
    model = Item
    form_class = ItemPostForm
    template_name = 'marketplace/item_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.cleaned_data['image']:
            try:
                with default_storage.open(
                    form.instance.image.name, 'rb+') as img_file:
                    img = Image.open(img_file)
                    img = img.resize((300, 300)) 
                    img.save(img_file)
            except IOError:
                pass

        return response
    
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            return redirect('marketplace:index')  # Fix redirect URL
    else:
        form = UserCreationForm()

    return render(request, 'marketplace/register.html', {'form': form})

def login_view(request):
        if request.method == 'POST':
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)

                return redirect('marketplace:index')
        else:
            form = AuthenticationForm()

        return render(request, 'marketplace/login.html', {'form': form})

def logout_view(request):
    logger.info("Logout view accessed")
    logout(request)

    return redirect('marketplace:index')
        
def user_profile(request):
    user = request.user

    return render(request, 'marketplace/user_profile.html', {'user': user})

def index(request):
    newest_items = Item.objects.order_by('-id')
    context = {
        "newest_items": newest_items,
    }

    return render(request, "marketplace/index.html", context)

# Create
@login_required
def create_item(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        price = request.POST['price']
        quantity = request.POST.get('quantity', 1)
        image = request.FILES.get('image')

        logger.debug(f'Received files: {request.FILES}')

        category_name = request.POST['category']
        category, created = CategoryModel.objects.get_or_create(
            name=category_name
            )

        seller = request.user

        if name and description and price:  # Validate required fields
            Item.objects.create(
            name=name, 
            description=description, 
            price=price, 
            quantity=quantity, 
            condition=request.POST['condition'],
            image=image,
            category=category,
            seller=seller
        )
        
        return redirect('marketplace:index')
    else:
        form = ItemPostForm()
        categories = CategoryModel.objects.all()

        context  = {
            'form': form,
            'categories': categories,
        }

        return render(request, 'marketplace/item_form.html', context)
        
# Message seller
def contact_seller_form(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    
    if request.method == 'POST':
        message_text = request.POST.get('message', '')
        if message_text:
            room, created = Room.objects.get_or_create(  # Ensure unique room name
                creator=request.user,
                room_name=f"Item_{item_id}_{request.user.username}_{item.seller.username}"
            )
            
            # We'll skip adding participants for now since there's a database issue
            # and rely on the creator field which is properly set up
            
            message = Message.objects.create(
                room=room,
                sender=request.user, 
                message=message_text
            )
            
            ItemMessage.objects.create(
                room=room,
                sender=request.user,
                message=message,
                item=item,
                receiver=item.seller
            )
            
            return redirect('chat:room', room_name=room.room_name)
    
    return render(request, 'marketplace/contact_seller_form.html', {'item': item})

# user messages
def user_messages(request):
    # Get all conversations where the user is either sender or receiver
    messages = ItemMessage.objects.filter(
        Q(receiver=request.user) | Q(sender=request.user)
    ).select_related('item', 'sender', 'receiver', 'room').order_by('-id')
    
    # Group by room to show only the latest message from each conversation
    latest_messages = {}
    for message in messages:
        room_id = message.room.id
        if room_id not in latest_messages:
            latest_messages[room_id] = message
    
    # Convert dictionary values back to a list
    grouped_messages = list(latest_messages.values())
    
    context = {
        'messages': grouped_messages
    }

    return render(request, 'marketplace/messages.html', context)


# Reply to message
def reply_form(request, message_id):
    message = get_object_or_404(
        ItemMessage, 
        pk=message_id
        )
    if request.method == 'POST':
        message.message = request.POST['message']
        message.save()

        return redirect('marketplace:messages')
    else:
        
        return render(request, 'marketplace/reply_form.html', {'message': message})

# Read
def item_list(request):
    items = Item.objects.all().order_by('-id')
    
    return render(request, 'marketplace/index.html', {'items': items})

def item_detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    return render(request, 'marketplace/item_detail.html', {'item': item})

# view listed items by seller
def get_seller_items(request):
    items = Item.objects.filter(
        # name=request.name,
        seller=request.user
        )

    return render(request, 'marketplace/seller_items.html', {'items': items})

def search_items(request):
    query = request.GET.get('query')
    items = Item.objects.filter(title__icontains=query)

    return render(request, 'marketplace/search_results.html', {'items': items})

@login_required
def update_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if request.method == 'POST':
        form = ItemPostForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()

            return redirect('marketplace:item_detail', item_id=item.id)
    else:
        form = ItemPostForm(instance=item)

    return render(request, 'marketplace/update_item.html', {'form': form})

# Delete
@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if request.method == 'POST':
        item.delete()

        return redirect('marketplace:index')
    else:

        return render(request, 'marketplace/item_confirm_delete.html', {'item': item})

# Delete a conversation
@login_required
def delete_conversation(request, message_id):
    message = get_object_or_404(ItemMessage, pk=message_id)
    
    # Security check: only allow users to delete conversations they're part of
    if request.user != message.sender and request.user != message.receiver:
        return HttpResponseBadRequest("You don't have permission to delete this conversation.")
    
    if request.method == 'POST':
        # Store the room reference before deleting the message
        room = message.room
        
        # Delete the ItemMessage
        message.delete()
        
        # Check if there are no more ItemMessages for this room
        if not ItemMessage.objects.filter(room=room).exists():
            # Optionally delete the room and all its messages
            # Uncomment if you want to delete the entire room when conversation is deleted
            # Message.objects.filter(room=room).delete()
            # room.delete()
            pass
            
        return redirect('marketplace:messages')
        
    return HttpResponseBadRequest("Invalid request method.")
