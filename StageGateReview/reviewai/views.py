from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import get_language
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Chat, UserMessage, AiMessage, FileMessage, FileUpload
from .forms import ChatForm, FileUploadForm
from reviewai.utils import build_history, extract_text_from_pdf, parse_ai_response, generate_pdf, parse_markdown_response
from django.http import HttpResponse
import os
import google.generativeai as genai

# Configure Gemini API
os.environ["GOOGLE_API_KEY"] = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

with open("reviewai/instructions.txt", "r", encoding="utf-8") as f:
    instructions = f.read()
with open("reviewai/ja_instructions.txt", "r", encoding="utf-8") as f:
    ja_instructions = f.read()

model = genai.GenerativeModel("models/gemini-2.0-flash", system_instruction=instructions)
jaModel = genai.GenerativeModel("models/gemini-2.0-flash", system_instruction=ja_instructions)

### HOME VIEW ###
@login_required
def home(request):
    chats = Chat.objects.filter(user=request.user)

    if request.method == 'POST':
        file = FileUploadForm(request.POST, request.FILES)
        if file.is_valid():
            file = file.cleaned_data['file']

            uploaded_file = FileUpload.objects.create(file=file)
            extracted_text = extract_text_from_pdf(uploaded_file.file.path)
            uploaded_file.extracted_text = extracted_text
            uploaded_file.save()

            # Create chat
            chat_title = "New Chat" if get_language() == "en" else "新しいチャット"
            chat = Chat.objects.create(user=request.user, title=chat_title)

            # Create FileMessage for the file upload
            filemsg = FileMessage.objects.create(
                chat=chat, role="user", file_name=file.name, file=uploaded_file
            )
            uploaded_file.filemsg = filemsg

            filemsg.save()
            uploaded_file.save()

            # Start AI response session
            if get_language() == "ja":
                chat_session = jaModel.start_chat()
            else:
                chat_session = model.start_chat()
            ai_response = chat_session.send_message(extracted_text)
            content1, report, content2  = parse_ai_response(ai_response.text)
            content1, report, content2  = parse_markdown_response(content1=content1, report=report, content2=content2)

            # Save AI response
            AiMessage.objects.create(chat=chat, role="model", content1=content1, content2=content2, report=report)

            if report:
                chat.report = report
                chat.save()

            return redirect(f'chat/{chat.id}')

        else:
            # Create empty chat if no file is uploaded
            chat_title = "New Chat" if get_language() == "en" else "新しいチャット"
            chat = Chat.objects.create(user=request.user, title=chat_title)
            return redirect(f'chat/{chat.id}')
    
    return render(request, 'reviewai/home.html', {'chats': chats})


### CHAT VIEW ###
@login_required
def chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    form = ChatForm(request.POST or None)
    chats = Chat.objects.filter(user=request.user)
    if get_language() == "ja":
        chat_session = jaModel.start_chat(history=build_history(chat_id))
    else:
        chat_session = model.start_chat(history=build_history(chat_id))
    if request.method == 'POST':
        if (not form.is_valid()):
            return JsonResponse({"error": "Invalid form data"}, status=400)

        user_message = form.cleaned_data['message']

        with transaction.atomic():
            # Save user message
            UserMessage.objects.create(chat=chat, content=user_message, role="user")

            # Generate AI response
            ai_response = chat_session.send_message(user_message)
            content1, report, content2  = parse_ai_response(ai_response.text)

            # Save AI response
            AiMessage.objects.create(chat=chat, role="model", content1=content1, content2=content2, report=report)

            # Parse Markdown to HTML
            content1, report, content2  = parse_markdown_response(content1=content1, report=report, content2=content2)

            if report:
                chat.report = report
                chat.save()

        return JsonResponse({"content1": content1, "content2": content2, "report": report}, status=200)


    # Fetch messages from all subclasses (UserMessage, AiMessage, FileMessage)
    messages = list(UserMessage.objects.filter(chat=chat)) + \
               list(AiMessage.objects.filter(chat=chat)) + \
               list(FileMessage.objects.filter(chat=chat))
    
    messages.sort(key=lambda m: m.created_at)  # Ensure messages are in chronological order

    return render(request, 'reviewai/chat.html', {
        "chats": chats,
        "chat_id": chat_id,
        "messages": messages,
        "form": form,
    })


### CHAT MANAGEMENT VIEW ###
@login_required
def chat_management(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)

    if request.method == "DELETE":
        chat.delete()
        return JsonResponse({"message": "Chat deleted successfully"}, status=200)

    elif request.method == "PUT":
        import json  # For parsing JSON body
        
        try:
            data = json.loads(request.body)
            new_title = data.get("title")

            if not new_title or len(new_title) > 100:
                return JsonResponse({"error": "Invalid title"}, status=400)

            chat.title = new_title
            chat.save()

            return JsonResponse({"message": "Chat title updated", "title": chat.title}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
    elif request.method == "GET":
        # Generate and return the PDF containing chat.report
        if chat.report:
            pdf = generate_pdf(chat.report)
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="chat_report_{chat.id}.pdf"'
            return response
        else:
            return JsonResponse({"error": "No report found for this chat"}, status=404)

    return JsonResponse({"error": "Invalid request method"}, status=405)


### AUTH VIEWS ###
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            return render(request, 'reviewai/login.html', {'error_message': 'Invalid username or password'})
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
                return render(request, 'reviewai/register.html', {'error_message': 'Error creating account'})
        else:
            return render(request, 'reviewai/register.html', {'error_message': 'Passwords do not match'})

    return render(request, 'reviewai/register.html')


def logout(request):
    auth.logout(request)
    return redirect('login')
