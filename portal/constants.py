LANGUAGE_CHOICES = [
    ('ron', 'Romana'),
    ('eng', 'English'),
    ('fra', 'French'),
    ('deu', 'German'),
    ('ita', 'Italian'),
    ('spa', 'Spanish'),
    ('hun', 'Hungarian'),
    ('pol', 'Polish'),
    ('ukr', 'Ukrainian'),
]

LANGUAGE_LOOKUP = {code: label for code, label in LANGUAGE_CHOICES}


MENU_CHOICES = [
    ('home', 'Guided Home'),
    ('ocr', 'OCR Studio'),
    ('libraries', 'Document Libraries'),
    ('preview', 'Document Preview'),
    ('word', 'Word Studio'),
    ('admin', 'Admin Console'),
]


OCR_ENGINE_CHOICES = [
    ('ocrmypdf', 'OCRmyPDF'),
    ('docling', 'Docling'),
]


FOLDER_COLOR_CHOICES = [
    ('mint', 'Mint Green'),
    ('sage', 'Sage Gray'),
    ('aqua', 'Aqua Blue'),
    ('sunset', 'Sunset Coral'),
    ('lavender', 'Lavender'),
    ('amber', 'Golden Amber'),
]
