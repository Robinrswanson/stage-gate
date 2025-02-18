from django import forms
from django.contrib.auth.forms import UserCreationForm

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

class ChatForm(forms.Form):
    message = forms.CharField(widget=forms.TextInput(attrs={'autocomplete': 'off'}))

class FileUploadForm(forms.Form):
    file = forms.FileField()