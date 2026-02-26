def clean_text(text):
    text = str(text).lower()
    import re
    text = re.sub(r'[^a-z\s]', '', text)
    return text
