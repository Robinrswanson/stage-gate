from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import FileUpload, ChatMessage
import fitz
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])
    return text

def home(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        uploaded_file = FileUpload.objects.create(file=file)
        
        # Extract text and save it to the database
        pdf_path = uploaded_file.file.path  # Get the saved file path
        extracted_text = extract_text_from_pdf(pdf_path)
        uploaded_file.extracted_text = extracted_text
        uploaded_file.save()

        # Store extracted text in session
        request.session['extracted_text'] = extracted_text

        # # Send extracted text to GPT API
        # response = client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": extracted_text}]
        # )

        # # Save AI response in session to display in chat
        # ai_response = response.choices[0].message.content

        ai_response = "This is a placeholder response from the AI."

        request.session['ai_response'] = ai_response

        return redirect('chat')

    return render(request, 'reviewai/upload.html')

def chat(request):
    """Render the chat page and retrieve extracted text & AI response."""
    extracted_text = request.session.pop('extracted_text', None)  # Remove from session after retrieval
    ai_response = request.session.pop('ai_response', None)  # Remove from session after retrieval
    return render(request, 'reviewai/chat.html', {'extracted_text': extracted_text, 'ai_response': ai_response})


def chat_api(request):
    if request.method == 'POST':
        user_input = request.POST.get('message')
        session_id = request.POST.get('session_id')

        # Retrieve the most recent uploaded file's extracted text
        latest_file = FileUpload.objects.last()
        file_text = latest_file.extracted_text if latest_file else ""

        # Save user message
        ChatMessage.objects.create(content=user_input, is_user=True, session_id=session_id)

        # Send extracted text + user input to GPT
        messages = [
            {"role": "system", "content": "This is extracted text from the uploaded document:\n" + file_text},
            {"role": "user", "content": user_input}
        ]

        # response = client.chat.completions.create(model="gpt-4", messages=messages)
        # ai_response = response.choices[0].message.content

        # Save AI response
        # ChatMessage.objects.create(content=ai_response, is_user=False, session_id=session_id)

        ai_response = "This is a placeholder response from the AI."

        return JsonResponse({'response': ai_response})
