from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors

from django.conf import settings


def clean_filename(value):
    return ''.join(
        char for char in value
        if char.isalnum() or char in (' ', '_', '-')
    ).replace(' ', '_')


def generate_business_pdf(document):
    output_dir = Path(settings.BASE_DIR) / 'generated_documents' / 'pdfs'
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_client = clean_filename(document.client_name)
    safe_title = clean_filename(document.title)

    filename = f'{document.document_type}_{safe_client}_{document.id}_{safe_title}.pdf'
    file_path = output_dir / filename

    c = canvas.Canvas(str(file_path), pagesize=A4)
    width, height = A4

    c.setFillColor(colors.HexColor('#080b12'))
    c.rect(0, height - 48 * mm, width, 48 * mm, fill=True, stroke=False)

    c.setFillColor(colors.HexColor('#d4af37'))
    c.setFont('Helvetica-Bold', 24)
    c.drawString(22 * mm, height - 22 * mm, 'That Corporate Flow')

    c.setFillColor(colors.white)
    c.setFont('Helvetica', 10)
    c.drawString(22 * mm, height - 30 * mm, 'Business Automation Simplified')

    c.setFillColor(colors.HexColor('#f8fafc'))
    c.setFont('Helvetica-Bold', 18)
    c.drawRightString(width - 22 * mm, height - 23 * mm, document.get_document_type_display().upper())

    c.setFillColor(colors.HexColor('#111827'))
    c.setFont('Helvetica-Bold', 16)
    c.drawString(22 * mm, height - 66 * mm, document.title[:75])

    c.setStrokeColor(colors.HexColor('#d4af37'))
    c.line(22 * mm, height - 72 * mm, width - 22 * mm, height - 72 * mm)

    y = height - 88 * mm

    details = [
        ('Client Name', document.client_name),
        ('Client Email', document.client_email or 'Not provided'),
        ('Amount', f'R {document.amount}'),
        ('Document ID', f'TCF-{document.id}'),
    ]

    for label, value in details:
        c.setFillColor(colors.HexColor('#6b7280'))
        c.setFont('Helvetica-Bold', 10)
        c.drawString(22 * mm, y, label)

        c.setFillColor(colors.HexColor('#111827'))
        c.setFont('Helvetica', 11)
        c.drawString(65 * mm, y, str(value)[:80])

        y -= 10 * mm

    y -= 6 * mm

    c.setFillColor(colors.HexColor('#111827'))
    c.setFont('Helvetica-Bold', 13)
    c.drawString(22 * mm, y, 'Description')

    y -= 9 * mm

    c.setFillColor(colors.HexColor('#374151'))
    text = c.beginText(22 * mm, y)
    text.setFont('Helvetica', 10)
    text.setLeading(15)

    description = document.description or 'No description provided.'

    for paragraph in description.splitlines():
        line = paragraph.strip()
        while len(line) > 95:
            text.textLine(line[:95])
            line = line[95:]
        text.textLine(line)

    c.drawText(text)

    c.setStrokeColor(colors.HexColor('#e5e7eb'))
    c.line(22 * mm, 32 * mm, width - 22 * mm, 32 * mm)

    c.setFillColor(colors.HexColor('#6b7280'))
    c.setFont('Helvetica', 9)
    c.drawString(22 * mm, 24 * mm, 'Generated automatically by That Corporate Flow.')
    c.drawRightString(width - 22 * mm, 24 * mm, 'Version 1')

    c.save()

    return str(file_path), filename
