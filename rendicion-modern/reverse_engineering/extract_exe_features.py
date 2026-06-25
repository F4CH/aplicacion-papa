from __future__ import annotations

import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent

TARGETS = {
    "root_rendicion": ROOT / "rendicion.exe",
    "installed_rendicion": ROOT / "Sis Cuadratura" / "Sis Cuadratura" / "rendicion.exe",
}

ZIP_TARGETS = {
    "actualizacion_22102018": (ROOT / "Actualizacion 22102018.zip", "rendicion.exe"),
    "rendicion_zip": (ROOT / "rendicion.zip", "rendicion.exe"),
}

CATEGORIES = {
    "tables_paths": re.compile(r"(?i)(datos\\[^\\\s]+|tmp\\[^\\\s]+|\.dbf|\.cdx|usuarios|operadores|deposito|cuadra)"),
    "forms_reports": re.compile(r"(?i)(frm|form|report|reporte|informe|listado|planilla|excel|preview|print|imprimir)"),
    "auth_users": re.compile(r"(?i)(usuario|usuarios|password|pass|psw|clave|login|seg_usu|men_usu|admin|root)"),
    "data_ops": re.compile(r"(?i)(select |insert |update |delete|append|replace|seek|locate|pack|zap|set deleted|create cursor|into cursor|order by)"),
    "ui_text": re.compile(r"(?i)(caption|tooltiptext|command|label|btn|txt|grid|combo|menu|salir|guardar|nuevo|modificar|eliminar|buscar|exportar|cancelar|aceptar)"),
    "business": re.compile(r"(?i)(cuadratura|rendicion|deposito|combust|operador|turno|venta|transbank|transfer|piloto|aceite|promo|cartola|saldo)"),
    "external": re.compile(r"(?i)(createobject|excel\.application|shell|run|ole|com|http|mailto|smtp)"),
}


def printable_strings(data: bytes, min_len: int = 4) -> list[str]:
    ascii_matches = re.findall(rb"[\x20-\x7e]{%d,}" % min_len, data)
    utf16_matches = re.findall((rb"(?:[\x20-\x7e]\x00){%d,}" % min_len), data)

    strings = []
    strings.extend(s.decode("latin1", "ignore") for s in ascii_matches)
    strings.extend(s.decode("utf-16le", "ignore") for s in utf16_matches)
    return [clean_string(s) for s in strings if clean_string(s)]


def clean_string(value: str) -> str:
    value = value.replace("\x00", "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def load_target_bytes(name: str) -> bytes:
    if name in TARGETS:
        return TARGETS[name].read_bytes()

    zip_path, member = ZIP_TARGETS[name]
    with zipfile.ZipFile(zip_path) as zf:
        return zf.read(member)


def interesting_context(strings: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for category, pattern in CATEGORIES.items():
        values = []
        for item in strings:
            if pattern.search(item):
                values.append(item)
        grouped[category] = sorted(set(values), key=str.lower)
    return grouped


def extract_assignments(strings: list[str]) -> dict[str, list[str]]:
    keys = [
        "Caption",
        "ToolTipText",
        "Name",
        "ControlSource",
        "RecordSource",
        "CursorSource",
        "Alias",
        "InitialSelectedAlias",
        "PasswordChar",
    ]
    result = defaultdict(list)
    for s in strings:
        for key in keys:
            if key.lower() in s.lower():
                result[key].append(s)
    return {key: sorted(set(values), key=str.lower) for key, values in result.items()}


def summarize(name: str) -> dict:
    data = load_target_bytes(name)
    strings = printable_strings(data)
    normalized = [s for s in strings if len(s) <= 240]
    counter = Counter(normalized)

    grouped = interesting_context(normalized)
    assignments = extract_assignments(normalized)

    return {
        "name": name,
        "size": len(data),
        "string_count": len(strings),
        "unique_string_count": len(set(normalized)),
        "top_repeated": counter.most_common(40),
        "grouped": grouped,
        "assignments": assignments,
    }


def write_text_report(reports: list[dict]) -> None:
    lines = []
    for report in reports:
        lines.append(f"# {report['name']} ({report['size']} bytes)")
        lines.append(f"strings={report['string_count']} unique={report['unique_string_count']}")
        lines.append("")

        for category, values in report["grouped"].items():
            lines.append(f"## {category} ({len(values)})")
            for value in values[:300]:
                lines.append(f"- {value}")
            lines.append("")

        lines.append("## assignments")
        for key, values in report["assignments"].items():
            lines.append(f"### {key} ({len(values)})")
            for value in values[:200]:
                lines.append(f"- {value}")
            lines.append("")

    (OUT_DIR / "exe_feature_report.txt").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    reports = [summarize(name) for name in [*TARGETS.keys(), *ZIP_TARGETS.keys()]]
    (OUT_DIR / "exe_feature_report.json").write_text(
        json.dumps(reports, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_text_report(reports)

    for report in reports:
        print(
            report["name"],
            "size=", report["size"],
            "strings=", report["string_count"],
            "unique=", report["unique_string_count"],
        )


if __name__ == "__main__":
    main()
