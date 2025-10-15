# Portal web pentru OCRmyPDF

Interfata web simpla pentru procesarea PDF-urilor cu OCRmyPDF pe Ubuntu 24.04. Aplicatia include:

- autentificare separata fata de Django Admin;
- panou web pentru incarcarea documentelor PDF si selectarea uneia sau mai multor limbi;
- integrare OCRmyPDF cu pastrarea rezultatului si optiuni de descarcare;
- istoric al conversiilor salvate in baza de date;
- interfata moderna optimizata pentru mobil, cu comutator intre tema luminoasa si intunecata.
- suport pentru alegerea motorului OCR (OCRmyPDF sau Docling) direct din consola web de administrare.

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

Aplicatia este disponibila la `http://localhost:8000/`. Pagina de autentificare redirectioneaza automat utilizatorii neautentificati.

## Utilizare

1. Autentifica-te folosind credentialele create.
2. Acceseaza meniurile permise de administrator (OCR Studio, Biblioteci, Previzualizare, Documente Word etc.).
3. Incarca un fisier PDF (maxim un fisier per procesare) si alege limbile sau activati detectarea automata.
4. Asteapta finalizarea procesului (durata depinde de dimensiunea PDF-ului) si trimite rezultatul in biblioteca dorita.
5. Descarca, previzualizeaza sau converteste fisierele direct din interfata.

> Comutatorul „Zi/Noapte” din antet salveaza preferinta local si se sincronizeaza cu setarile sistemului (daca nu exista o preferinta explicita).

> In cazul unei erori (de exemplu depedente lipsa), mesajul este afisat in interfata si salvat in baza de date.

> Administratorii pot schimba motorul folosit pentru OCR (OCRmyPDF sau Docling) din meniul „Consolă administrator”. Optiunea Docling devine activa doar daca pachetul este instalat pe server.

## Structura

- `portal/` – aplicatia Django cu modele, formulare, views si URL-uri.
- `templates/` – layout global si pagini pentru autentificare si panou.
- `static/` – fisiere CSS pentru interfata.
- `media/uploads/`, `media/processed/` – directoare create automat de Django pentru fisierele incarcate si rezultatele OCR.
- `deploy/nginx/` – configuratia nginx folosita de docker compose pentru a servi aplicatia si fisierele statice.

## Docker pe Ubuntu 24.04

1. Instaleaza Docker Engine si Docker Compose Plugin (pe Ubuntu 24.04):

   ```bash
   sudo apt update
   sudo apt install docker.io docker-compose-plugin
   sudo systemctl enable --now docker
   ```

2. Cloneaza proiectul si pregateste variabilele de mediu:

   ```bash
   git clone <repo>
   cd ocrsite
   cp .env.example .env
   touch db.sqlite3
   ```

   > Editeaza `.env` pentru a seta `DJANGO_SECRET_KEY`, lista de domenii acceptate (`DJANGO_ALLOWED_HOSTS`), baza URL a site-ului (`SITE_BASE_URL`) si origini de incredere pentru CSRF (`CSRF_TRUSTED_ORIGINS`).

3. (Optional) Instaleaza Docling pentru a folosi motorul alternativ:

   ```bash
   pip install docling
   ```

   > Daca Docling nu este instalat, optiunea ramane indisponibila in consola de administrare.

4. Construieste imaginile si pregateste baza de date:

   ```bash
   docker compose build
   docker compose run --rm web python manage.py migrate
   docker compose run --rm web python manage.py collectstatic --noinput
   docker compose run --rm web python manage.py createsuperuser
   ```

   > `createsuperuser` este optional dar recomandat la prima rulare pentru a putea accesa interfata web.

5. Porneste serviciile (aplicatie Django + proxy nginx):

   ```bash
   docker compose up -d
   ```

   Serviciul `web` ruleaza `gunicorn` pe portul intern `8000`, iar nginx expune acelasi port catre gazda, servind resursele statice si media din volumele partajate.

6. Verifica log-urile si statusul:

   ```bash
   docker compose logs -f
   docker compose ps
   ```

7. Opreste serviciul:

   ```bash
   docker compose down
   ```

## Productie

- Seteaza `DJANGO_DEBUG=False` si configureaza `DJANGO_ALLOWED_HOSTS` (ex.: `ocr.casianhome.org`).
- Foloseste `entrypoint.sh` pentru a rula automat migrarile si `collectstatic` in container.
- Configureaza un reverse proxy (nginx/Traefik) pentru TLS si headere `X-Forwarded-*` atunci cand rulezi in productie.
