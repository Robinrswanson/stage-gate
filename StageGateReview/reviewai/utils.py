from .models import UserMessage, AiMessage, FileMessage, FileUpload
import fitz
import re
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
import markdown2
import markdown
import weasyprint

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])
    return text

def build_history(chat_id):
    messages = list(UserMessage.objects.filter(chat=chat_id)) + \
               list(AiMessage.objects.filter(chat=chat_id)) + \
               list(FileMessage.objects.filter(chat=chat_id))

    messages = sorted(messages, key=lambda x: x.created_at)

    history = []
    for message in messages:
        if message.role == "model":
            entry = {
                "role": "model",
                "parts": [message.content1] if message.content1 else []
            }
            if message.content2:
                entry["parts"].extend(["```markdown", message.report, "```", message.content2])
            history.append(entry)

        elif isinstance(message, FileMessage):
            if message.file and message.file.extracted_text:
                history.append({
                    "role": "user",
                    "parts": [message.file.extracted_text]
                })

        else:
            if message.content:
                history.append({
                    "role": "user",
                    "parts": [message.content]
                })
    
    return history


def parse_ai_response(response):
    # Regex to capture markdown content inside triple backticks
    pattern = re.compile(r"(.*?)```(?:markdown)?\n(.*?)\n```(.*)", re.DOTALL)

    match = pattern.search(response)

    if match:
        beginning_part = match.group(1).strip()
        markdown_content = match.group(2).strip()
        final_remarks = match.group(3).strip()
    else:
        # If no markdown found, return the full response as the beginning part
        return response.strip(), "", ""

    return beginning_part, markdown_content, final_remarks

def generate_pdf(report_content):
    """
    Converts Markdown content to a PDF and returns it as a byte stream.
    """
    buffer = BytesIO()
    
    # Convert Markdown to HTML with styling
    html_content = markdown2.markdown(report_content, extras=["fenced-code-blocks", "tables", "strike", "footnotes", "cuddled-lists"])
    
    # Convert HTML to PDF using WeasyPrint
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    
    buffer.write(pdf_bytes)
    buffer.seek(0)
    return buffer.getvalue()

def parse_markdown_response(content1, report=None, content2=None):
    """
    Converts markdown text to HTML for content1, report, and content2.

    Args:
        content1 (str): The primary markdown text to convert.
        report (str, optional): Additional markdown text to convert. Defaults to None.
        content2 (str, optional): Additional markdown text to convert. Defaults to None.

    Returns:
        tuple: A tuple containing the resulting HTML for content1, report, and content2.
               If report or content2 is not provided, an empty string is returned for that part.
    """
    html1 = markdown.markdown(content1) if content1 else ""
    html_report = markdown.markdown(report) if report is not None else ""
    html2 = markdown.markdown(content2) if content2 is not None else ""
    return html1, html_report, html2