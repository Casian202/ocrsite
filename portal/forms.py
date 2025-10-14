from django import forms
from django.core.validators import FileExtensionValidator

from .constants import LANGUAGE_CHOICES


class DocumentUploadForm(forms.Form):
    pdf_file = forms.FileField(
        label='Document PDF',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text='Incarca un fisier PDF pentru OCR.',
    )
    languages = forms.MultipleChoiceField(
        label='Limbi OCR',
        choices=LANGUAGE_CHOICES,
        help_text='Selecteaza una sau mai multe limbi suportate de Tesseract (Ctrl/Cmd pentru selectii multiple).',
        initial=['ron'],
        widget=forms.SelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pdf_file'].widget.attrs.update({
            'class': 'input-control',
            'accept': 'application/pdf',
        })
        self.fields['languages'].widget.attrs.update({
            'class': 'input-control',
            'size': '6',
        })
