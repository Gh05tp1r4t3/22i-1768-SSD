import bleach

def sanitize_input(text):
    allowed_tags = ['b','i','u','em','strong','p','br','ul','li','ol']
    return bleach.clean(text or '', tags=allowed_tags, attributes={}, strip=True)
