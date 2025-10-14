# Portal web pentru OCRmyPDF

Interfata web simpla pentru procesarea PDF-urilor cu OCRmyPDF pe Ubuntu 24.04. Aplicatia include:

- autentificare separata fata de Django Admin;
- panou web pentru incarcarea documentelor PDF si selectarea uneia sau mai multor limbi;
- integrare OCRmyPDF cu pastrarea rezultatului si optiuni de descarcare;
- istoric al conversiilor salvate in baza de date.

## Cerinte de sistem

Ubuntu 24.04 cu urmatoarele pachete:

```bash
sudo apt update
sudo apt install python3-venv python3-dev build-essential \
    tesseract-ocr tesseract-ocr-ron tesseract-ocr-eng \
    qpdf ghostscript pngquant unpaper
```

> Adauga pachete `tesseract-ocr-<limba>` suplimentare dupa nevoi (ex.: `tesseract-ocr-deu` pentru germana).

## Instalare

```bash
git clone <repo>
cd ocrsite
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
```

Aplica migratiile si creeaza un utilizator:

```bash
python manage.py migrate
python manage.py createsuperuser
```

## Rulare

```bash
python manage.py runserver 0.0.0.0:8000
```

Acceseaza:

- Portal OCR: `http://localhost:8000/`
- Autentificare: `http://localhost:8000/autentificare/`
- Django Admin: `http://localhost:8000/admin/`

## Utilizare

1. Autentifica-te folosind credentialele create.
2. Incarca un fisier PDF (maxim un fisier per procesare).
3. Selecteaza una sau mai multe limbi; combinatiile sunt trimise catre OCRmyPDF (`ron+eng`, `ron+deu` etc.).
4. Asteapta finalizarea procesului (durata depinde de dimensiunea PDF-ului).
5. Descarca fisierul procesat din tabelul de istoric.

> In cazul unei erori (de exemplu depedente lipsa), mesajul este afisat in interfata si salvat in baza de date.

## Structura

- `portal/` – aplicatia Django cu modele, formulare, views si URL-uri.
- `templates/` – layout global si pagini pentru autentificare si panou.
- `static/` – fisiere CSS pentru interfata.
- `media/uploads/`, `media/processed/` – directoare create automat de Django pentru fisierele incarcate si rezultatele OCR.

## Productie

- Configureaza variabila `DEBUG=False` si setarile pentru `ALLOWED_HOSTS`.
- Serveste fisierele statice cu `collectstatic`.
- Ruleaza aplicatia printr-un server WSGI (gunicorn + nginx) si configureaza un worker dedicat pentru sarcini lungi daca volumele sunt mari.
