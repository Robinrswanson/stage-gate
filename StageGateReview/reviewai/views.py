from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import FileUpload, ChatMessage
import fitz
import os
import google.generativeai as genai

# Set your Gemini API key
os.environ["GOOGLE_API_KEY"] = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))  # Configure Gemini

with open("reviewai/instructions.txt", "r", encoding="utf-8") as f:
    instructions = f.read()

model = genai.GenerativeModel("models/gemini-2.0-flash", system_instruction=instructions) # Pass instructions here


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
    extracted_text = request.session.pop('extracted_text', None)
    ai_response = request.session.pop('ai_response', None)
    return render(request, 'reviewai/chat.html', {'extracted_text': extracted_text, 'ai_response': ai_response})

def chat_api(request):
    if request.method == 'POST':
        user_input = request.POST.get('message')
        session_id = request.POST.get('session_id')
        requirements_document = request.POST.get('requirements_document')  # Get the requirements document
        pdf_uploaded = request.POST.get('pdf_uploaded') == 'true' # Check if a pdf was uploaded

        latest_file = FileUpload.objects.last()
        file_text = latest_file.extracted_text if latest_file else ""

        ChatMessage.objects.create(content=user_input, is_user=True, session_id=session_id)
        chat = model.start_chat()

        if pdf_uploaded:
            prompt = f"""
                PDF Content:
                {file_text}
                """
        else:
            prompt = f"""
                No file provided.
                """

        response = chat.send_message(prompt)

        ai_response = response.text if response and response.text else "Error generating response."

        ChatMessage.objects.create(content=ai_response, is_user=False, session_id=session_id)

        return JsonResponse({'response': ai_response})
