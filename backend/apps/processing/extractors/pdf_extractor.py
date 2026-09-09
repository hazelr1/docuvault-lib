from io import BytesIO

from pypdf import PdfReader


def extract_text_from_pdf(file_obj):
    file_obj.seek(0)
    reader = PdfReader(BytesIO(file_obj.read()))
    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        pages.append({"text": page.extract_text() or "", "page_number": idx})
    return pages
