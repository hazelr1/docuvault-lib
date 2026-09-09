def extract_text_from_plaintext(file_obj):
    file_obj.seek(0)
    content = file_obj.read()
    if isinstance(content, bytes):
        text = content.decode("utf-8", errors="ignore")
    else:
        text = str(content)
    return [{"text": text, "page_number": None}]
