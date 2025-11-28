import fitz  # PyMuPDF
from pptx import Presentation

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_pptx(file_path):
    prs = Presentation(file_path)
    text = ""
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + "\n"
    return text

def process_document(document):
    file_path = document.file.path
    if file_path.endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    elif file_path.endswith('.pptx'):
        text = extract_text_from_pptx(file_path)
    else:
        text = ""
    
    document.text_content = text
    document.save()
    return text