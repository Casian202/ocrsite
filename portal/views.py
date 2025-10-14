import logging
import shutil
import tempfile
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DocumentUploadForm
from .models import OcrJob

log = logging.getLogger(__name__)


def _run_ocr(job: OcrJob) -> None:
    try:
        import ocrmypdf
        from ocrmypdf import exceptions as ocrmypdf_exceptions
    except ImportError as exc:  # pragma: no cover - import error only on misconfigured env
        raise RuntimeError(
            'OCRmyPDF nu este instalat. Instaleaza pachetul "ocrmypdf" si dependentele Tesseract.'
        ) from exc

    job.ensure_directories()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        input_path = temp_dir_path / 'input.pdf'
        output_path = temp_dir_path / 'output.pdf'

        with job.source_file.open('rb') as uploaded, input_path.open('wb') as destination:
            shutil.copyfileobj(uploaded, destination)

        try:
            ocrmypdf.ocr(
                str(input_path),
                str(output_path),
                language=job.language,
                deskew=True,
                rotate_pages=True,
                optimize=1,
                skip_text=False,
            )
        except (
            ocrmypdf_exceptions.MissingDependencyError,
            ocrmypdf_exceptions.PriorOcrFoundError,
            ocrmypdf_exceptions.SubprocessError,
            ocrmypdf_exceptions.OcrError,
        ) as exc:
            log.exception("OCR failed for job %s", job.id)
            raise RuntimeError(str(exc)) from exc

        with output_path.open('rb') as processed:
            job.processed_file.save(
                f"{Path(job.source_file.name).stem}_ocr.pdf",
                File(processed),
                save=False,
            )

    job.status = OcrJob.Status.COMPLETED
    job.error_message = ''
    job.save(update_fields=['processed_file', 'status', 'error_message', 'updated_at'])


@login_required
def dashboard(request):
    form = DocumentUploadForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        pdf_file = form.cleaned_data['pdf_file']
        languages = form.cleaned_data['languages']
        language_codes = '+'.join(languages)

        job = OcrJob(
            user=request.user,
            language=language_codes,
            status=OcrJob.Status.PROCESSING,
        )
        job.source_file.save(pdf_file.name, pdf_file, save=False)
        job.save()

        try:
            _run_ocr(job)
            messages.success(request, 'Documentul a fost procesat cu succes.')
        except RuntimeError as exc:
            job.status = OcrJob.Status.FAILED
            job.error_message = str(exc)
            job.save(update_fields=['status', 'error_message', 'updated_at'])
            messages.error(request, f'Procesarea a esuat: {exc}')

        return redirect('dashboard')

    jobs = OcrJob.objects.filter(user=request.user)[:25]
    return render(
        request,
        'portal/dashboard.html',
        {
            'form': form,
            'jobs': jobs,
        },
    )


@login_required
def download_job(request, job_id):
    job = get_object_or_404(OcrJob, id=job_id, user=request.user)

    if job.status != OcrJob.Status.COMPLETED or not job.processed_file:
        raise Http404('Documentul nu este disponibil pentru descarcare.')

    return FileResponse(
        job.processed_file.open('rb'),
        as_attachment=True,
        filename=job.processed_filename() or 'document_ocr.pdf',
    )
