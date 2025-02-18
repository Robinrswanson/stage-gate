from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import get_language
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .models import Chat, Message, FileUpload
from django.contrib import auth
from django.contrib.auth.models import User
from .forms import SignUpForm, ChatForm, FileUploadForm
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from reviewai.utils import build_history
import fitz
import os
import google.generativeai as genai

# Configure Gemini API
os.environ["GOOGLE_API_KEY"] = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

with open("reviewai/instructions.txt", "r", encoding="utf-8") as f:
    instructions = f.read()

model = genai.GenerativeModel("models/gemini-2.0-flash", system_instruction=instructions)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])
    return text


# def home(request):
#     if request.method == 'POST' and request.FILES.get('file'):
#         file = request.FILES['file']
#         uploaded_file = FileUpload.objects.create(file=file)

#         # Extract text from PDF
#         pdf_path = uploaded_file.file.path
#         extracted_text = extract_text_from_pdf(pdf_path)
#         uploaded_file.extracted_text = extracted_text
#         uploaded_file.save()

#         # Store extracted text for chat
#         request.session['extracted_text'] = extracted_text

#         return redirect('chat')

#     return render(request, 'reviewai/upload.html')


# def chat(request):
#     """Opens a new chat session every time the page is loaded."""
#     extracted_text = request.session.pop('extracted_text', None)

#     # Start a fresh chat every time the chat page is opened
#     global curr_chat
#     curr_chat = model.start_chat()

#     # Determine AI's initial message
#     if extracted_text:
#         # Generate a summarized report from the PDF
#         ai_prompt = f"Here is the pdf containting the business idea:\n\n{extracted_text}. Please give a brief introudction the generate an initial PREP report giving details where possible."
#     else:
#         ai_prompt = "Please give a brief introudction of youself and then proceed with part 1."

#     # Detect selected language
#     lang = get_language()

#     if lang == 'ja':
#         ai_prompt += "\n\nすべての回答を日本語で提供してください。"

#     response = curr_chat.send_message(ai_prompt)

#     request.session['ai_response'] = response.text

#     return render(request, 'reviewai/chat.html', {
#         'ai_response': response.text,
#     })

# def chat_api(request):
#     """Handles chat messages and adapts AI response to the selected language."""
#     if request.method == 'POST':
#         user_input = request.POST.get('message')

#         global curr_chat
#         if curr_chat is None:
#             curr_chat = model.start_chat()

#         # Detect selected language
#         lang = get_language()

#         # Modify AI system instruction based on language
#         if lang == 'ja':
#             user_input += "\n\nすべての回答を日本語で提供してください。"

#         # Send message with appropriate instruction
#         response = curr_chat.send_message(user_input)
#         ai_response = response.text if response and response.text else "Error generating response."

#         return JsonResponse({'response': ai_response})

#     return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def home(request):
    chats = Chat.objects.filter(user=request.user)
    
    if request.method == 'POST':
        file = FileUploadForm(request.POST, request.FILES)
        if file.is_valid():
            file = file.cleaned_data['file']
            if file:
                uploaded_file = FileUpload.objects.create(file=file)
                extracted_text = extract_text_from_pdf(uploaded_file.file.path)
                uploaded_file.extracted_text = extracted_text
                uploaded_file.save()
                message = extracted_text
            # Create chat
            chat = Chat.objects.create(user=request.user, title=message[:50])
            chat_session = model.start_chat()
            if get_language() == 'ja':
                message += "\n\nすべての回答を日本語で提供してください。"
            ai_response = chat_session.send_message(message)
            Message.objects.create(chat=chat, content=message, role="user")
            Message.objects.create(chat=chat, content=ai_response.text, role="model")
            return redirect(f'chat/{chat.id}', chat_id=chat.id)
        else:
            chat = Chat.objects.create(user=request.user, title="New Chat")
            return redirect(f'chat/{chat.id}', chat_id=chat.id)
    
    if request.method == 'GET':
        chat_id = request.GET.get('chat_id')
        if chat_id:
            chat = Chat.objects.get(id=chat_id)
            return redirect(f'chat/<{chat.id}>', chat_id=chat.id)
    
    return render(request, 'reviewai/home.html', {'chats': chats})

from django.http import JsonResponse

@login_required
def chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    form = ChatForm(request.POST or None)  
    chats = Chat.objects.filter(user=request.user)

    if request.method == 'POST' and form.is_valid():
        user_message = form.cleaned_data['message']
        chat_session = model.start_chat(history=build_history(chat_id))

        with transaction.atomic():
            # Save user message
            Message.objects.create(chat=chat, content=user_message, role="user")

            # Generate AI response
            if get_language() == 'ja':
                message += "\n\nすべての回答を日本語で提供してください。"
            ai_response = chat_session.send_message(user_message)
            ai_text = ai_response.text if hasattr(ai_response, "text") else str(ai_response)
            
            # Save AI response
            Message.objects.create(chat=chat, content=ai_text, role="model")

        # Return AI response as JSON
        return JsonResponse({"response": ai_text})

    # Initial GET request
    messages = Message.objects.filter(chat=chat).order_by('created_at')
    return render(request, 'reviewai/chat.html', {
        "chats": chats,
        "chat_id": chat_id,
        'messages': messages,
        'form': form
    })


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'reviewai/login.html', {'error_message': error_message})
    else:
        return render(request, 'reviewai/login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect('home')
            except:
                error_message = 'Error creating account'
                return render(request, 'reviewai/register.html', {'error_message': error_message})
        else:
            error_message = 'Password dont match'
            return render(request, 'reviewai/register.html', {'error_message': error_message})
    return render(request, 'reviewai/register.html')

def logout(request):
    auth.logout(request)
    return redirect('login')