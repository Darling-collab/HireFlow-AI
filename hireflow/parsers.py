from pathlib import Path
import io

def extract_upload(upload):
    name = upload.name or "upload"
    suffix = Path(name).suffix.lower()
    raw = upload.getvalue()
    if suffix in {".txt", ".md", ".csv"}:
        if suffix == ".csv":
            import pandas as pd
            return pd.read_csv(io.BytesIO(raw)).to_csv(index=False), "parsed"
        return raw.decode("utf-8", errors="replace"), "parsed"
    if suffix in {".xlsx", ".xls"}:
        import pandas as pd
        return pd.read_excel(io.BytesIO(raw)).to_csv(index=False), "parsed"
    if suffix == ".docx":
        try:
            from docx import Document
            doc = Document(io.BytesIO(raw)); return "\n".join(p.text for p in doc.paragraphs), "parsed"
        except ImportError:
            return "", "待接入：DOCX 解析依赖 python-docx 尚未安装"
    if suffix == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(raw)) as pdf: return "\n".join((p.extract_text() or "") for p in pdf.pages), "parsed"
        except ImportError:
            return "", "待接入：PDF 解析依赖 pdfplumber 尚未安装"
    if suffix in {".png", ".jpg", ".jpeg"}:
        try:
            import pytesseract
            from PIL import Image
            text=pytesseract.image_to_string(Image.open(io.BytesIO(raw)),lang="chi_sim+eng")
            return (text,"parsed") if text.strip() else ("","OCR 未识别到可用文字")
        except Exception as exc:
            return "", f"OCR 不可用：{exc}"
    return "", f"不支持的文件格式：{suffix}"
