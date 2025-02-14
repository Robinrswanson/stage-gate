from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import FileUpload, ChatMessage
import fitz
import os
import google.generativeai as genai

# Configure Gemini API
os.environ["GOOGLE_API_KEY"] = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

with open("reviewai/instructions.txt", "r", encoding="utf-8") as f:
    instructions = f.read()

model = genai.GenerativeModel("models/gemini-2.0-flash", system_instruction=instructions)

# Global variable for chat session
curr_chat = None  # Initialized as None


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])
    return text


def home(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        uploaded_file = FileUpload.objects.create(file=file)

        # Extract text from PDF
        pdf_path = uploaded_file.file.path
        extracted_text = extract_text_from_pdf(pdf_path)
        uploaded_file.extracted_text = extracted_text
        uploaded_file.save()

        # Store extracted text for chat
        request.session['extracted_text'] = extracted_text

        return redirect('chat')

    return render(request, 'reviewai/upload.html')


def chat(request):
    """Opens a new chat session every time the page is loaded."""
    extracted_text = request.session.pop('extracted_text', None)

    # Start a fresh chat every time the chat page is opened
    global curr_chat
    curr_chat = model.start_chat()

    # Determine AI's initial message
    if extracted_text:
        # Generate a summarized report from the PDF
        ai_prompt = f"Here is the pdf containting the business idea:\n\n{extracted_text}. Please give a brief introudction the generate an initial PREP report giving details where possible."
    else:
        ai_prompt = "Please give a brief introudction of youself and then proceed with part 1."
    response = curr_chat.send_message(ai_prompt)

    request.session['ai_response'] = response.text

    return render(request, 'reviewai/chat.html', {
        'ai_response': response.text,
    })



def chat_api(request):
    """Handles chat messages, but does NOT persist chat history."""
    if request.method == 'POST':
        user_input = request.POST.get('message')

        global curr_chat
        if curr_chat is None:
            curr_chat = model.start_chat()  # Ensure chat exists

        response = curr_chat.send_message(user_input)
        ai_response = response.text if response and response.text else "Error generating response."

        return JsonResponse({'response': ai_response})

    return JsonResponse({'error': 'Invalid request'}, status=400)
