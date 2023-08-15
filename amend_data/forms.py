from django import forms
from .models import Image

class ImageUploadForm(forms.Form):
    file = forms.FileField(label='Select a file')
    
class FilesQuestionUploadForm(forms.Form):
    file = forms.FileField(label='Select a file')
    
class FilesAnswerUploadForm(forms.Form):
    file = forms.FileField(label='Select a file')