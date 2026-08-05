import os
from typing import Optional
from fastapi import HTTPException

def validate_jpeg_file(filename: str, content_type: Optional[str]) -> str:
    ext = os.path.splitext(filename)[1].lower() if filename else ""
    allowed_exts = [".jpg", ".jpeg"]
    is_jpeg_ext = ext in allowed_exts
    is_jpeg_mime = content_type and ("jpeg" in content_type.lower() or "jpg" in content_type.lower())
    
    if not (is_jpeg_ext or is_jpeg_mime):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format! Only JPEG (.jpg / .jpeg) documents are allowed."
        )
    return ext if ext in allowed_exts else ".jpg"
