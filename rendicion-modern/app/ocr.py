import re
import os
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from PIL import Image, ImageOps

DENOMINATIONS = {
    "por_20k": 20000,
    "por_10k": 10000,
    "por_05k": 5000,
    "por_02k": 2000,
    "por_01k": 1000,
    "por_05c": 500,
    "por_01c": 100,
    "por_50u": 50,
    "por_10u": 10,
}

DENOM_ALIASES = {
    "por_20k": ["20.000", "20000", "20k", "20 k"],
    "por_10k": ["10.000", "10000", "10k", "10 k"],
    "por_05k": ["5.000", "5000", "5k", "5 k"],
    "por_02k": ["2.000", "2000", "2k", "2 k"],
    "por_01k": ["1.000", "1000", "1k", "1 k"],
    "por_05c": ["500"],
    "por_01c": ["100"],
    "por_50u": ["50"],
    "por_10u": ["10"],
}


@dataclass
class OcrDepositResult:
    fields: dict[str, int | str | date] = field(default_factory=dict)
    raw_text: str = ""
    warning: str = ""


def extract_text_from_image(image_bytes: bytes, filename: str = "", content_type: str = "") -> str:
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("Falta instalar pytesseract.") from exc

    configure_tesseract_command(pytesseract)

    if is_pdf_upload(image_bytes, filename, content_type):
        return extract_text_from_pdf(image_bytes, pytesseract)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(image_bytes)
        tmp_path = Path(tmp.name)

    try:
        image = Image.open(tmp_path)
        return ocr_image(image, pytesseract)
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "No se encontro Tesseract OCR instalado. Instala Tesseract y agrega tesseract.exe al PATH."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"No se pudo procesar la imagen con OCR: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)


def is_pdf_upload(file_bytes: bytes, filename: str = "", content_type: str = "") -> bool:
    return (
        content_type.lower() == "application/pdf"
        or filename.lower().endswith(".pdf")
        or file_bytes[:4] == b"%PDF"
    )


def extract_text_from_pdf(pdf_bytes: bytes, pytesseract_module) -> str:
    try:
        from pdf2image import convert_from_bytes
    except ImportError as exc:
        raise RuntimeError("Falta instalar pdf2image para leer archivos PDF.") from exc

    poppler_path = os.getenv("POPPLER_PATH") or None
    try:
        pages = convert_from_bytes(
            pdf_bytes,
            dpi=220,
            first_page=1,
            last_page=3,
            poppler_path=poppler_path,
        )
    except Exception as exc:
        raise RuntimeError(
            "No se pudo convertir el PDF a imagen. Instala Poppler y agrega su carpeta bin al PATH, "
            "o configura POPPLER_PATH."
        ) from exc

    if not pages:
        raise RuntimeError("El PDF no contiene paginas convertibles a imagen.")

    texts = []
    for index, page in enumerate(pages, start=1):
        text = ocr_image(page, pytesseract_module)
        if text.strip():
            texts.append(f"--- Pagina {index} ---\n{text.strip()}")
    return "\n\n".join(texts)


def ocr_image(image: Image.Image, pytesseract_module) -> str:
    image = ImageOps.exif_transpose(image).convert("L")
    image = ImageOps.autocontrast(image)
    try:
        return pytesseract_module.image_to_string(image, lang="spa+eng")
    except pytesseract_module.TesseractError:
        return pytesseract_module.image_to_string(image, lang="eng")


def configure_tesseract_command(pytesseract_module) -> None:
    configured = os.getenv("TESSERACT_CMD")
    if configured:
        pytesseract_module.pytesseract.tesseract_cmd = configured
        return

    common_paths = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]
    for path in common_paths:
        if path.exists():
            pytesseract_module.pytesseract.tesseract_cmd = str(path)
            return


def parse_deposit_text(text: str) -> OcrDepositResult:
    normalized = normalize_text(text)
    fields: dict[str, int | str | date] = {}

    parsed_date = parse_date(normalized)
    if parsed_date:
        fields["fecha"] = parsed_date

    operator_value = parse_operator_value(text)
    if operator_value:
        fields["operador_codigo"] = operator_value

    for key, pattern in {
        "numero": r"(?:numero|nro|folio|comprobante)\D{0,12}(\d{3,12})",
        "turno": r"(?:turno)\D{0,8}(\d{1,2})",
    }.items():
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip().upper()
            fields[key] = int(value) if key in {"numero", "turno"} and value.isdigit() else value

    for field_name, aliases in DENOM_ALIASES.items():
        quantity = parse_denomination_quantity(normalized, aliases, DENOMINATIONS[field_name])
        if quantity is not None:
            fields[field_name] = quantity

    aceite_v = parse_labeled_money(normalized, ["aceite"])
    promo_v = parse_labeled_money(normalized, ["promo", "promocion"])
    if aceite_v is not None:
        fields["aceite_v"] = aceite_v
        fields.setdefault("aceite_c", 1 if aceite_v > 0 else 0)
    if promo_v is not None:
        fields["promo_v"] = promo_v
        fields.setdefault("promo_c", 1 if promo_v > 0 else 0)

    return OcrDepositResult(fields=fields, raw_text=text.strip(), warning=build_warning(fields))


def parse_cuadratura_text(text: str) -> OcrDepositResult:
    normalized = normalize_text(text)
    fields: dict[str, int | str | date] = {}

    parsed_date = parse_date(normalized)
    if parsed_date:
        fields["fecha"] = parsed_date

    operator_value = parse_operator_value(text)
    if operator_value:
        fields["operador_codigo"] = operator_value

    for key, pattern in {
        "numero": r"(?:numero|nro|folio|cuadratura)\D{0,12}(\d{3,12})",
        "turno": r"(?:turno)\D{0,8}(\d{1,2})",
    }.items():
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            fields[key] = int(match.group(1))

    money_fields = {
        "combust_v": ["combustible", "comb."],
        "otros_v": ["otros"],
        "deposito_v": ["deposito", "depositos"],
        "ventas_v": ["ventas", "venta turno", "ventas turno"],
        "transbnk_v": ["transbank", "trans bank", "tbk"],
        "transfer_v": ["transferencia", "transfer"],
        "piloto_v": ["piloto", "copiloto"],
    }
    for field_name, labels in money_fields.items():
        value = parse_labeled_money(normalized, labels)
        if value is not None:
            fields[field_name] = value

    return OcrDepositResult(fields=fields, raw_text=text.strip(), warning=build_warning(fields))


def parse_operator_value(text: str) -> str | None:
    for line in text.splitlines():
        match = re.search(r"(?:operador|cajero|usuario)\s*[:.-]?\s*(.+)", line, flags=re.IGNORECASE)
        if not match:
            continue
        value = re.sub(r"\s+", " ", match.group(1)).strip(" .:-")
        if value:
            return value.upper()
    return None


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace(",", ".")
    text = re.sub(r"[^\w\s.$:/-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_date(text: str) -> date | None:
    patterns = [
        (r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", "%Y-%m-%d"),
        (r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", "%d-%m-%Y"),
    ]
    for pattern, fmt in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        value = "-".join(match.groups())
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_number(value: str) -> int:
    cleaned = re.sub(r"[^\d]", "", value)
    return int(cleaned) if cleaned else 0


def parse_denomination_quantity(text: str, aliases: list[str], denomination_value: int) -> int | None:
    for alias in aliases:
        escaped = re.escape(alias.lower())
        token = rf"(?<![\d.]){escaped}(?![\d.])"
        patterns = [
            rf"{token}\s*(?:x|\*)\s*(\d{{1,5}})",
            rf"(\d{{1,5}})\s*(?:x|\*)\s*{token}",
            rf"(?:billete|moneda|denom(?:inacion)?)\s*{token}\s*(?:x|\*)?\s*(\d{{1,5}})",
            rf"{token}\s*\$?\s*([\d.]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if not match:
                continue
            number = parse_number(match.group(1))
            if number <= 0:
                continue
            if number >= denomination_value and number % denomination_value == 0:
                return number // denomination_value
            return number
    return None


def parse_labeled_money(text: str, labels: list[str]) -> int | None:
    for label in labels:
        match = re.search(rf"{label}\D{{0,12}}\$?\s*([\d.]+)", text, flags=re.IGNORECASE)
        if match:
            return parse_number(match.group(1))
    return None


def build_warning(fields: dict[str, int | str | date]) -> str:
    missing = []
    for key, label in [("fecha", "fecha"), ("turno", "turno"), ("operador_codigo", "operador")]:
        if key not in fields:
            missing.append(label)
    if missing:
        return "No se detecto automaticamente: " + ", ".join(missing) + ". Revisa antes de guardar."
    return "Datos leidos por OCR. Revisa visualmente antes de guardar."
