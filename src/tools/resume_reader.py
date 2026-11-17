"""Read text resumes and text-based PDF resumes."""
from pathlib import Path

import pdfplumber
def read_resume(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        pages = []
        with pdfplumber.open(str(file_path)) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()

    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8-sig").strip()

    raise ValueError("Unsupported resume format. Please use .txt or .pdf.")
