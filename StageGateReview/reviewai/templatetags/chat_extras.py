import markdown
from django import template
from django.utils.safestring import mark_safe
from bs4 import BeautifulSoup

register = template.Library()

# Define Bootstrap class mappings
BOOTSTRAP_CLASSES = {
    "h1": "h1",
    "h2": "h2",
    "h3": "h3",
    "h4": "h4",
    "h5": "h5",
    "h6": "h6",
    "p": "mb-3",
    "ul": "list-disc pl-5",
    "ol": "list-decimal pl-5",
    "li": "mb-1",
    "code": "bg-gray-200 text-red-600 px-2 py-1 rounded",
    "blockquote": "border-l-4 border-gray-300 pl-4 italic text-gray-600",
    "pre": "bg-gray-900 text-white p-3 rounded",
    "table": "table table-striped",
    "th": "border px-4 py-2 bg-gray-200",
    "td": "border px-4 py-2"
}

def add_bootstrap_classes(html):
    """ Adds Bootstrap classes to generated HTML using BeautifulSoup """
    soup = BeautifulSoup(html, "html.parser")

    for tag, class_name in BOOTSTRAP_CLASSES.items():
        for element in soup.find_all(tag):
            existing_classes = element.get("class", [])
            if class_name not in existing_classes:
                existing_classes.append(class_name)
            element["class"] = existing_classes

    return str(soup)

@register.filter
def convert_markdown(text):
    """ Converts Markdown to HTML and applies Bootstrap styling """
    md_html = markdown.markdown(text, extensions=['fenced_code', 'attr_list'])
    styled_html = add_bootstrap_classes(md_html)
    return mark_safe(styled_html)
