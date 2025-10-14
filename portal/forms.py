from __future__ import annotations

from typing import Iterable

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import FileExtensionValidator

from .constants import FOLDER_COLOR_CHOICES, LANGUAGE_CHOICES, MENU_CHOICES
from .models import LibraryFolder, PortalAccess, StoredDocument, WordDocument


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email de contact')

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing} input-control".strip()


class OcrRequestForm(forms.Form):
    pdf_file = forms.FileField(
        label='Document PDF',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text='Încarcă un PDF pentru procesare cu OCRmyPDF.',
    )
    languages = forms.MultipleChoiceField(
        label='Limbi OCR',
        choices=LANGUAGE_CHOICES,
        required=False,
        initial=['ron', 'eng'],
        widget=forms.SelectMultiple,
        help_text='Selectează limbile recunoscute. Lasă necompletat pentru a activa detectarea automată.',
    )
    auto_language = forms.BooleanField(
        required=False,
        initial=True,
        label='Detectare automată a limbilor',
    )
    optimize_level = forms.IntegerField(
        min_value=0,
        max_value=3,
        initial=1,
        label='Nivel optimizare',
        help_text='Valoare între 0 și 3 transmisă către OCRmyPDF (--optimize).',
    )
    deskew = forms.BooleanField(required=False, initial=True, label='Corectează alinierea paginilor')
    rotate_pages = forms.BooleanField(required=False, initial=True, label='Detecție automată rotire pagini')
    remove_background = forms.BooleanField(required=False, label='Elimină fundalul')
    clean_final = forms.BooleanField(required=False, label='Curățare finală a imaginilor')
    skip_text = forms.BooleanField(
        required=False,
        label='Sari peste paginile care au deja text (skip-text)',
    )
    force_ocr = forms.BooleanField(
        required=False,
        label='Forcează OCR chiar dacă există text',
    )
    output_type = forms.ChoiceField(
        choices=[
            ('pdfa', 'PDF/A (implicit)'),
            ('pdf', 'PDF standard'),
            ('pdfa-1', 'PDF/A-1'),
            ('pdfa-2', 'PDF/A-2'),
            ('pdfa-3', 'PDF/A-3'),
        ],
        label='Tip fișier rezultat',
        initial='pdfa',
    )
    make_sidecar = forms.BooleanField(
        required=False,
        label='Generează fișier sidecar (.txt)',
    )
    destination_folder = forms.ModelChoiceField(
        queryset=LibraryFolder.objects.none(),
        required=False,
        label='Stochează în folder',
        help_text='Selectează un folder din bibliotecă în care să arhivezi documentul procesat.',
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['pdf_file'].widget.attrs.update(
            {
                'class': 'input-control',
                'accept': 'application/pdf',
            }
        )
        self.fields['languages'].widget.attrs.update({'class': 'input-control', 'size': '8'})
        for name in (
            'optimize_level',
            'output_type',
            'destination_folder',
        ):
            if name in self.fields:
                existing = self.fields[name].widget.attrs.get('class', '')
                self.fields[name].widget.attrs['class'] = f"{existing} input-control".strip()
        if user is not None:
            self.fields['destination_folder'].queryset = user.library_folders.all()

    def cleaned_language_codes(self) -> str:
        languages = self.cleaned_data.get('languages') or []
        return '+'.join(languages)

    def selected_options(self) -> dict:
        options = {
            'auto_language': self.cleaned_data.get('auto_language', False),
            'optimize': self.cleaned_data.get('optimize_level', 1),
            'deskew': self.cleaned_data.get('deskew', False),
            'rotate_pages': self.cleaned_data.get('rotate_pages', False),
            'remove_background': self.cleaned_data.get('remove_background', False),
            'clean_final': self.cleaned_data.get('clean_final', False),
            'skip_text': self.cleaned_data.get('skip_text', False),
            'force_ocr': self.cleaned_data.get('force_ocr', False),
            'output_type': self.cleaned_data.get('output_type'),
            'make_sidecar': self.cleaned_data.get('make_sidecar', False),
        }
        return options

    def clean(self):
        cleaned = super().clean()
        auto_language = cleaned.get('auto_language')
        languages = cleaned.get('languages')
        if not auto_language and not languages:
            self.add_error('languages', 'Selectează cel puțin o limbă sau activează detectarea automată.')
        return cleaned


class FolderForm(forms.ModelForm):
    class Meta:
        model = LibraryFolder
        fields = ('name', 'description', 'color', 'parent')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Nume folder'}),
            'description': forms.TextInput(
                attrs={'class': 'input-control', 'placeholder': 'Descriere (opțional)'}
            ),
            'color': forms.Select(attrs={'class': 'input-control'}),
            'parent': forms.Select(attrs={'class': 'input-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['parent'].queryset = user.library_folders.all()
        else:
            self.fields['parent'].queryset = LibraryFolder.objects.none()

    def color_choices(self) -> Iterable[tuple[str, str]]:
        return FOLDER_COLOR_CHOICES


class LibraryDocumentForm(forms.ModelForm):
    class Meta:
        model = StoredDocument
        fields = ('folder', 'title', 'description', 'original_file')
        widgets = {
            'folder': forms.Select(attrs={'class': 'input-control'}),
            'title': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Titlu document'}),
            'description': forms.TextInput(
                attrs={'class': 'input-control', 'placeholder': 'Descriere (opțional)'}
            ),
        }
        help_texts = {
            'original_file': 'Încarcă un PDF ce va fi gestionat în bibliotecă.',
        }

    original_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        label='PDF în bibliotecă',
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['folder'].queryset = user.library_folders.all()
        else:
            self.fields['folder'].queryset = LibraryFolder.objects.none()
        self.fields['original_file'].widget.attrs.update({'class': 'input-control', 'accept': 'application/pdf'})


class WordDocumentForm(forms.Form):
    title = forms.CharField(label='Titlu document', max_length=150)
    body = forms.CharField(
        label='Conținut document',
        widget=forms.Textarea(attrs={'rows': 10}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing} input-control".strip()


class PdfToWordForm(forms.Form):
    pdf_file = forms.FileField(
        label='PDF pentru conversie',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
    )
    title = forms.CharField(label='Titlu document Word', max_length=150)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing} input-control".strip()
        self.fields['pdf_file'].widget.attrs.update({'accept': 'application/pdf'})


class AccessApprovalForm(forms.ModelForm):
    allowed_menus = forms.MultipleChoiceField(
        choices=MENU_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label='Meniuri disponibile',
        required=False,
    )

    class Meta:
        model = PortalAccess
        fields = ('status', 'allowed_menus', 'notes')
        widgets = {
            'status': forms.Select(attrs={'class': 'input-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'input-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.allowed_menus:
            self.initial['allowed_menus'] = self.instance.allowed_menus

    def clean_allowed_menus(self):
        menus = self.cleaned_data.get('allowed_menus') or []
        return list(menus)
