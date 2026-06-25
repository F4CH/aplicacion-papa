import csv
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from dbfread import DBF
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import hash_password, role_from_security_level
from app.database import SessionLocal, engine
from app.models import Base, Configuracion, Cuadratura, Deposito, Operador, Usuario

LEGACY_DATA_DIR = ROOT_DIR / "data"
ERRORS_FILE = ROOT_DIR / "migration_errors.csv"


def dbf_table(filename: str) -> DBF:
    path = LEGACY_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo DBF: {path}")

    return DBF(path, encoding="cp1252", char_decode_errors="ignore", load=False)


def clean_text(value: Any, max_length: int | None = None) -> str:
    text = "" if value is None else str(value).strip()
    if max_length is not None:
        return text[:max_length]
    return text


def int_or_zero(value: Any) -> int:
    if value in (None, ""):
        return 0

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def parse_legacy_date(value: Any) -> date | None:
    if value is None:
        return None

    if isinstance(value, date):
        if 1990 <= value.year <= 2035:
            return value
        return None

    text = str(value).strip()
    if len(text) != 8 or not text.isdigit():
        return None

    try:
        parsed = datetime.strptime(text, "%Y%m%d").date()
    except ValueError:
        return None

    if parsed.year < 1990 or parsed.year > 2035:
        return None

    return parsed


def log_error(filename: str, row_number: int, reason: str, row: dict[str, Any]) -> None:
    file_exists = ERRORS_FILE.exists()

    with ERRORS_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["archivo", "fila", "motivo", "registro"])
        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "archivo": filename,
                "fila": row_number,
                "motivo": reason,
                "registro": dict(row),
            }
        )


def ensure_operador(db: Session, codigo: str) -> None:
    existing = db.get(Operador, codigo)
    if existing:
        return

    db.add(
        Operador(
            codigo=codigo,
            descripcion=f"Operador migrado sin maestro {codigo}",
            activo=True,
            ingreso=None,
            tinta=0,
        )
    )
    db.flush()


def migrate_operadores(db: Session) -> int:
    filename = "Operadores.DBF"
    if not (LEGACY_DATA_DIR / filename).exists():
        return 0

    total = 0
    for index, row in enumerate(dbf_table(filename), start=1):
        codigo = clean_text(row.get("CODIGO"), 5)
        if not codigo:
            log_error(filename, index, "Operador sin codigo", row)
            continue

        operador = Operador(
            codigo=codigo,
            descripcion=clean_text(row.get("DESCRI"), 100) or "Sin descripcion",
            activo=bool(row.get("ACTIVO", True)),
            ingreso=parse_legacy_date(row.get("INGRESO")),
            tinta=int_or_zero(row.get("TINTA")),
        )
        db.merge(operador)
        total += 1

    return total


def migrate_usuarios(db: Session) -> int:
    filename = "usuarios.dbf"
    total = 0

    for index, row in enumerate(dbf_table(filename), start=1):
        codigo = clean_text(row.get("COD_USU"), 20)
        nombre = clean_text(row.get("NOM_USU"), 100)

        if not codigo:
            log_error(filename, index, "Usuario sin codigo", row)
            continue

        legacy_security_level = int_or_zero(row.get("SEG_USU"))
        rol = role_from_security_level(legacy_security_level)
        legacy_password = clean_text(row.get("PSW_USU"))
        password = legacy_password or f"Cambiar-{codigo}-2026"

        user = Usuario(
            codigo=codigo,
            nombre=nombre or codigo,
            password_hash=hash_password(password, allow_weak=True),
            rol=rol,
            nivel_seguridad=legacy_security_level,
            menu=clean_text(row.get("MEN_USU"), 60),
            activo=True,
        )
        db.merge(user)
        total += 1

    return total


def migrate_cuadraturas(db: Session) -> int:
    filename = "cuadra.DBF"
    total = 0

    for index, row in enumerate(dbf_table(filename), start=1):
        fecha = parse_legacy_date(row.get("FECHA"))
        operador_codigo = clean_text(row.get("OPERADOR"), 5)

        if not fecha:
            log_error(filename, index, "Fecha invalida o fuera de rango", row)
            continue

        if not operador_codigo:
            log_error(filename, index, "OPERADOR vacio", row)
            continue

        ensure_operador(db, operador_codigo)

        cuadratura = Cuadratura(
            numero=int_or_zero(row.get("NUMERO")),
            fecha=fecha,
            turno=int_or_zero(row.get("TURNO")),
            operador_codigo=operador_codigo,
            combust_v=int_or_zero(row.get("COMBUST_V")),
            otros_v=int_or_zero(row.get("OTROS_V")),
            deposito_v=int_or_zero(row.get("DEPOSITO_V")),
            ventas_v=int_or_zero(row.get("VENTAS_V")),
            transbnk_v=int_or_zero(row.get("TRANSBNK_V")),
            transfer_v=int_or_zero(row.get("TRANSFER_V")),
            piloto_v=int_or_zero(row.get("PILOTO_V")),
        )
        db.add(cuadratura)
        total += 1

    return total


def migrate_depositos(db: Session) -> int:
    filename = "deposito.DBF"
    total = 0

    for index, row in enumerate(dbf_table(filename), start=1):
        fecha = parse_legacy_date(row.get("FECHA"))
        operador_codigo = clean_text(row.get("OPERADOR"), 5)

        if not fecha:
            log_error(filename, index, "Fecha invalida o fuera de rango", row)
            continue

        if not operador_codigo:
            log_error(filename, index, "OPERADOR vacio", row)
            continue

        ensure_operador(db, operador_codigo)

        deposito = Deposito(
            numero=int_or_zero(row.get("NUMERO")),
            fecha=fecha,
            turno=int_or_zero(row.get("TURNO")),
            operador_codigo=operador_codigo,
            por_20k=int_or_zero(row.get("POR_20K")),
            por_10k=int_or_zero(row.get("POR_10K")),
            por_05k=int_or_zero(row.get("POR_05K")),
            por_02k=int_or_zero(row.get("POR_02K")),
            por_01k=int_or_zero(row.get("POR_01K")),
            por_05c=int_or_zero(row.get("POR_05C")),
            por_01c=int_or_zero(row.get("POR_01C")),
            por_50u=int_or_zero(row.get("POR_50U")),
            por_10u=int_or_zero(row.get("POR_10U")),
            aceite_c=int_or_zero(row.get("ACEITE_C")),
            promo_c=int_or_zero(row.get("PROMO_C")),
            val_20k=int_or_zero(row.get("VAL_20K")),
            val_10k=int_or_zero(row.get("VAL_10K")),
            val_05k=int_or_zero(row.get("VAL_05K")),
            val_02k=int_or_zero(row.get("VAL_02K")),
            val_01k=int_or_zero(row.get("VAL_01K")),
            val_05c=int_or_zero(row.get("VAL_05C")),
            val_01c=int_or_zero(row.get("VAL_01C")),
            val_50u=int_or_zero(row.get("VAL_50U")),
            val_10u=int_or_zero(row.get("VAL_10U")),
            aceite_v=int_or_zero(row.get("ACEITE_V")),
            promo_v=int_or_zero(row.get("PROMO_V")),
            val_comb=int_or_zero(row.get("VAL_COMB")),
            val_otro=int_or_zero(row.get("VAL_OTRO")),
            total_v=int_or_zero(row.get("TOTAL_V")),
        )
        db.add(deposito)
        total += 1

    return total


def migrate_configuracion(db: Session) -> None:
    config = Configuracion(
        id=1,
        empresa="Comerc. Sur Energy SPA",
        rut="76856384-5",
        local="Shell Alerce",
        email="surenergy.ptomontt@gmail.com",
        membrete="Comerc. Sur Energy Spa.\nAvda. Gabriela Mistral 900\nSector Alerce, Puerto Montt",
    )
    db.merge(config)


def main() -> None:
    Base.metadata.create_all(bind=engine)

    if ERRORS_FILE.exists():
        ERRORS_FILE.unlink()

    db = SessionLocal()
    try:
        operadores = migrate_operadores(db)
        db.flush()

        usuarios = migrate_usuarios(db)
        db.flush()

        migrate_configuracion(db)
        db.flush()

        cuadraturas = migrate_cuadraturas(db)
        depositos = migrate_depositos(db)
        db.commit()

        print("Migracion finalizada correctamente.")
        print(f"Operadores migrados: {operadores}")
        print(f"Usuarios migrados: {usuarios}")
        print(f"Cuadraturas migradas: {cuadraturas}")
        print(f"Depositos migrados: {depositos}")
        print(f"Errores/cuarentena: {ERRORS_FILE}")
    except IntegrityError as error:
        db.rollback()
        raise RuntimeError("Error de integridad durante la migracion.") from error
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
