import os
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_303_SEE_OTHER

from app.auth import hash_password, role_allows, verify_password
from app.database import engine, get_db
from app.models import Base, Configuracion, Cuadratura, Deposito, Operador, Usuario
from app.ocr import extract_text_from_image, parse_deposit_text

app = FastAPI(title="Sistema de Cuadratura y Rendicion", version="1.0.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "rendicion-local-dev-secret-change-me"),
    same_site="lax",
    https_only=False,
)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

DENOMINACIONES = {
    "20k": 20000,
    "10k": 10000,
    "05k": 5000,
    "02k": 2000,
    "01k": 1000,
    "05c": 500,
    "01c": 100,
    "50u": 50,
    "10u": 10,
}


def format_number(value: Any) -> str:
    if value is None:
        return "0"
    return f"{int(value):,}".replace(",", ".")


def format_money(value: Any) -> str:
    return "$" + format_number(value or 0)


def format_date(value: Any) -> str:
    if not value:
        return "-"
    if isinstance(value, date):
        return value.strftime("%d-%m-%Y")
    return str(value)


templates.env.filters["number"] = format_number
templates.env.filters["money"] = format_money
templates.env.filters["date"] = format_date


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


def redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=HTTP_303_SEE_OTHER)


def parse_date(value: str | None, default: date | None = None) -> date | None:
    if not value:
        return default
    return datetime.strptime(value, "%Y-%m-%d").date()


def form_int(form: dict[str, Any], name: str, default: int = 0) -> int:
    value = form.get(name, default)
    if value in ("", None):
        return default
    try:
        return int(str(value).replace(".", "").replace("$", "").strip())
    except ValueError:
        return default


def form_bool(form: dict[str, Any], name: str) -> bool:
    return str(form.get(name, "")).lower() in {"1", "true", "on", "si", "yes"}


def current_user(request: Request, db: Session) -> Usuario | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(Usuario, user_id)


def require_user(request: Request, db: Session) -> Usuario:
    user = current_user(request, db)
    if not user or not user.activo:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


def require_role(user: Usuario, role: str) -> None:
    if not role_allows(user.rol, role):
        raise HTTPException(status_code=403, detail="No tienes permisos para esta accion.")


def render(request: Request, template: str, context: dict[str, Any], db: Session):
    context.setdefault("request", request)
    context.setdefault("current_user", current_user(request, db))
    return templates.TemplateResponse(request, template, context)


def paginate(query, page: int, per_page: int = 25) -> tuple[list[Any], int, int]:
    page = max(page, 1)
    per_page = min(max(per_page, 10), 100)
    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max((total + per_page - 1) // per_page, 1)
    return rows, total, total_pages


def next_number(db: Session, model) -> int:
    return (db.query(func.max(model.numero)).scalar() or 0) + 1


def blank_deposito(numero: int) -> Deposito:
    return Deposito(
        numero=numero,
        fecha=date.today(),
        turno=1,
        operador_codigo="",
        por_20k=0,
        por_10k=0,
        por_05k=0,
        por_02k=0,
        por_01k=0,
        por_05c=0,
        por_01c=0,
        por_50u=0,
        por_10u=0,
        aceite_c=0,
        promo_c=0,
        aceite_v=0,
        promo_v=0,
        val_comb=0,
        val_otro=0,
        total_v=0,
    )


def recalculate_deposito(deposito: Deposito) -> None:
    deposito.val_20k = deposito.por_20k * DENOMINACIONES["20k"]
    deposito.val_10k = deposito.por_10k * DENOMINACIONES["10k"]
    deposito.val_05k = deposito.por_05k * DENOMINACIONES["05k"]
    deposito.val_02k = deposito.por_02k * DENOMINACIONES["02k"]
    deposito.val_01k = deposito.por_01k * DENOMINACIONES["01k"]
    deposito.val_05c = deposito.por_05c * DENOMINACIONES["05c"]
    deposito.val_01c = deposito.por_01c * DENOMINACIONES["01c"]
    deposito.val_50u = deposito.por_50u * DENOMINACIONES["50u"]
    deposito.val_10u = deposito.por_10u * DENOMINACIONES["10u"]
    deposito.val_otro = deposito.aceite_v + deposito.promo_v
    deposito.total_v = (
        deposito.val_20k
        + deposito.val_10k
        + deposito.val_05k
        + deposito.val_02k
        + deposito.val_01k
        + deposito.val_05c
        + deposito.val_01c
        + deposito.val_50u
        + deposito.val_10u
        + deposito.val_otro
    )
    deposito.val_comb = deposito.total_v - deposito.val_otro


def depositos_para_cuadratura(db: Session, fecha: date, turno: int, operador_codigo: str) -> tuple[int, int, int]:
    total, combust, otros = (
        db.query(
            func.coalesce(func.sum(Deposito.total_v), 0),
            func.coalesce(func.sum(Deposito.val_comb), 0),
            func.coalesce(func.sum(Deposito.val_otro), 0),
        )
        .filter(
            Deposito.fecha == fecha,
            Deposito.turno == turno,
            Deposito.operador_codigo == operador_codigo,
        )
        .one()
    )
    return int(total or 0), int(combust or 0), int(otros or 0)


def diferencia_cuadratura(item: Cuadratura) -> int:
    return (
        (item.combust_v or 0)
        - (item.ventas_v or 0)
        + (item.transbnk_v or 0)
        + (item.transfer_v or 0)
        + (item.piloto_v or 0)
    )


templates.env.globals["diferencia_cuadratura"] = diferencia_cuadratura


def filtered_cuadraturas(db: Session, fecha_desde: str = "", fecha_hasta: str = "", operador: str = ""):
    query = db.query(Cuadratura).join(Operador)
    if fecha_desde:
        query = query.filter(Cuadratura.fecha >= parse_date(fecha_desde))
    if fecha_hasta:
        query = query.filter(Cuadratura.fecha <= parse_date(fecha_hasta))
    if operador:
        query = query.filter(Cuadratura.operador_codigo == operador)
    return query


def filtered_depositos(db: Session, fecha_desde: str = "", fecha_hasta: str = "", operador: str = ""):
    query = db.query(Deposito).join(Operador)
    if fecha_desde:
        query = query.filter(Deposito.fecha >= parse_date(fecha_desde))
    if fecha_hasta:
        query = query.filter(Deposito.fecha <= parse_date(fecha_hasta))
    if operador:
        query = query.filter(Deposito.operador_codigo == operador)
    return query


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.get("/")
def root(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    if current_user(request, db):
        return redirect("/dashboard")
    return redirect("/login")


@app.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    if current_user(request, db):
        return redirect("/dashboard")
    return render(request, "login.html", {"title": "Acceso"}, db)


@app.post("/login")
async def login_submit(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    codigo = str(form.get("codigo", "")).strip()
    password = str(form.get("password", ""))
    user = db.query(Usuario).filter(Usuario.codigo == codigo, Usuario.activo.is_(True)).first()
    if not user or not verify_password(password, user.password_hash):
        return render(request, "login.html", {"title": "Acceso", "error": "Usuario o password incorrecto."}, db)
    request.session["user_id"] = user.id
    return redirect("/dashboard")


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return redirect("/login")


@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    require_user(request, db)
    stats = [
        {"label": "Cuadraturas", "value": db.query(func.count(Cuadratura.id)).scalar() or 0, "kind": "number"},
        {"label": "Depositos", "value": db.query(func.count(Deposito.id)).scalar() or 0, "kind": "number"},
        {"label": "Operadores", "value": db.query(func.count(Operador.codigo)).scalar() or 0, "kind": "number"},
        {"label": "Usuarios", "value": db.query(func.count(Usuario.id)).scalar() or 0, "kind": "number"},
        {"label": "Ventas", "value": db.query(func.coalesce(func.sum(Cuadratura.ventas_v), 0)).scalar() or 0, "kind": "money"},
        {"label": "Depositos rendidos", "value": db.query(func.coalesce(func.sum(Deposito.total_v), 0)).scalar() or 0, "kind": "money"},
    ]
    return render(
        request,
        "dashboard.html",
        {
            "title": "Panel",
            "stats": stats,
            "ultima_cuadratura": db.query(func.max(Cuadratura.fecha)).scalar(),
            "ultimo_deposito": db.query(func.max(Deposito.fecha)).scalar(),
            "recent_cuadraturas": db.query(Cuadratura).order_by(Cuadratura.fecha.desc(), Cuadratura.numero.desc()).limit(8).all(),
            "recent_depositos": db.query(Deposito).order_by(Deposito.fecha.desc(), Deposito.numero.desc()).limit(8).all(),
        },
        db,
    )


@app.get("/operadores")
def operadores(request: Request, q: str = "", page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    require_user(request, db)
    query = db.query(Operador)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Operador.codigo.ilike(like), Operador.descripcion.ilike(like)))
    rows, total, total_pages = paginate(query.order_by(Operador.activo.desc(), Operador.descripcion.asc()), page)
    return render(request, "operadores.html", {"title": "Operadores", "rows": rows, "q": q, "page": page, "total": total, "total_pages": total_pages}, db)


@app.get("/operadores/nuevo")
def operador_nuevo(request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "operador")
    return render(request, "operador_form.html", {"title": "Nuevo operador", "item": None}, db)


@app.get("/operadores/{codigo}/editar")
def operador_editar(codigo: str, request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "operador")
    item = db.get(Operador, codigo)
    if not item:
        raise HTTPException(404)
    return render(request, "operador_form.html", {"title": "Editar operador", "item": item}, db)


@app.post("/operadores/guardar")
async def operador_guardar(request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "operador")
    form = await request.form()
    original_codigo = str(form.get("original_codigo", "")).strip()
    codigo = str(form.get("codigo", "")).strip()[:5]
    if not codigo:
        raise HTTPException(400, detail="Codigo requerido.")
    item = db.get(Operador, original_codigo or codigo) if original_codigo else None
    if item and original_codigo != codigo:
        db.delete(item)
        db.flush()
        item = None
    item = item or Operador(codigo=codigo)
    item.codigo = codigo
    item.descripcion = str(form.get("descripcion", "")).strip() or "Sin descripcion"
    item.activo = form_bool(form, "activo")
    item.ingreso = parse_date(str(form.get("ingreso", ""))) if form.get("ingreso") else None
    item.tinta = form_int(form, "tinta")
    db.merge(item)
    db.commit()
    return redirect("/operadores")


@app.post("/operadores/{codigo}/eliminar")
def operador_eliminar(codigo: str, request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "supervisor")
    item = db.get(Operador, codigo)
    if item:
        item.activo = False
        db.commit()
    return redirect("/operadores")


@app.get("/usuarios")
def usuarios(request: Request, page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    require_role(require_user(request, db), "admin")
    rows, total, total_pages = paginate(db.query(Usuario).order_by(Usuario.activo.desc(), Usuario.codigo.asc()), page)
    return render(request, "usuarios.html", {"title": "Usuarios", "rows": rows, "page": page, "total": total, "total_pages": total_pages, "q": ""}, db)


@app.get("/usuarios/nuevo")
def usuario_nuevo(request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "admin")
    return render(request, "usuario_form.html", {"title": "Nuevo usuario", "item": None}, db)


@app.get("/usuarios/{user_id}/editar")
def usuario_editar(user_id: int, request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "admin")
    item = db.get(Usuario, user_id)
    if not item:
        raise HTTPException(404)
    return render(request, "usuario_form.html", {"title": "Editar usuario", "item": item}, db)


@app.post("/usuarios/guardar")
async def usuario_guardar(request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "admin")
    form = await request.form()
    user_id = form_int(form, "id")
    item = db.get(Usuario, user_id) if user_id else None
    item = item or Usuario(codigo="", nombre="", password_hash=hash_password("Cambiar-2026"))
    item.codigo = str(form.get("codigo", "")).strip()
    item.nombre = str(form.get("nombre", "")).strip()
    item.rol = str(form.get("rol", "consulta")).strip()
    item.nivel_seguridad = form_int(form, "nivel_seguridad", 3)
    item.menu = str(form.get("menu", "")).strip()
    item.activo = form_bool(form, "activo")
    new_password = str(form.get("password", ""))
    if new_password:
        item.password_hash = hash_password(new_password)
    db.merge(item)
    db.commit()
    return redirect("/usuarios")


@app.post("/usuarios/{user_id}/eliminar")
def usuario_eliminar(user_id: int, request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "admin")
    item = db.get(Usuario, user_id)
    if item:
        item.activo = False
        db.commit()
    return redirect("/usuarios")


@app.get("/depositos")
def depositos(request: Request, q: str = "", page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    require_user(request, db)
    query = db.query(Deposito).join(Operador)
    if q:
        term = q.strip()
        filters = [Deposito.operador_codigo.ilike(f"%{term}%"), Operador.descripcion.ilike(f"%{term}%")]
        if term.isdigit():
            filters.append(Deposito.numero == int(term))
        query = query.filter(or_(*filters))
    rows, total, total_pages = paginate(query.order_by(Deposito.fecha.desc(), Deposito.numero.desc()), page)
    return render(request, "depositos.html", {"title": "Depositos", "rows": rows, "q": q, "page": page, "total": total, "total_pages": total_pages}, db)


@app.get("/depositos/nuevo")
def deposito_nuevo(request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "operador")
    item = blank_deposito(next_number(db, Deposito))
    return render(request, "deposito_form.html", {"title": "Nuevo deposito", "item": item, "operadores": db.query(Operador).filter(Operador.activo.is_(True)).order_by(Operador.descripcion).all()}, db)


@app.get("/depositos/importar")
def deposito_importar(request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "operador")
    return render(request, "deposito_importar.html", {"title": "Leer boleta"}, db)


@app.post("/depositos/importar")
async def deposito_importar_post(
    request: Request,
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    require_role(require_user(request, db), "operador")
    image_bytes = await imagen.read()
    item = blank_deposito(next_number(db, Deposito))
    ocr_text = ""
    ocr_warning = ""

    try:
        ocr_text = extract_text_from_image(image_bytes)
        result = parse_deposit_text(ocr_text)
        ocr_warning = result.warning
        for key, value in result.fields.items():
            if hasattr(item, key):
                setattr(item, key, value)
        recalculate_deposito(item)
    except RuntimeError as exc:
        ocr_warning = str(exc)

    return render(
        request,
        "deposito_form.html",
        {
            "title": "Deposito desde boleta",
            "item": item,
            "operadores": db.query(Operador).filter(Operador.activo.is_(True)).order_by(Operador.descripcion).all(),
            "ocr_text": ocr_text,
            "ocr_warning": ocr_warning,
        },
        db,
    )


@app.get("/depositos/{item_id}/editar")
def deposito_editar(item_id: int, request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "operador")
    item = db.get(Deposito, item_id)
    if not item:
        raise HTTPException(404)
    return render(request, "deposito_form.html", {"title": "Editar deposito", "item": item, "operadores": db.query(Operador).filter(Operador.activo.is_(True)).order_by(Operador.descripcion).all()}, db)


@app.post("/depositos/guardar")
async def deposito_guardar(request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "operador")
    form = await request.form()
    item_id = form_int(form, "id")
    item = db.get(Deposito, item_id) if item_id else Deposito()
    item.numero = form_int(form, "numero", next_number(db, Deposito))
    item.fecha = parse_date(str(form.get("fecha", "")), date.today()) or date.today()
    item.turno = form_int(form, "turno", 1)
    item.operador_codigo = str(form.get("operador_codigo", "")).strip()
    for field in ["por_20k", "por_10k", "por_05k", "por_02k", "por_01k", "por_05c", "por_01c", "por_50u", "por_10u", "aceite_c", "promo_c", "aceite_v", "promo_v"]:
        setattr(item, field, form_int(form, field))
    recalculate_deposito(item)
    db.merge(item)
    db.commit()
    return redirect("/depositos")


@app.post("/depositos/{item_id}/eliminar")
def deposito_eliminar(item_id: int, request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "supervisor")
    item = db.get(Deposito, item_id)
    if item:
        db.delete(item)
        db.commit()
    return redirect("/depositos")


@app.get("/cuadraturas")
def cuadraturas(request: Request, q: str = "", page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    require_user(request, db)
    query = db.query(Cuadratura).join(Operador)
    if q:
        term = q.strip()
        filters = [Cuadratura.operador_codigo.ilike(f"%{term}%"), Operador.descripcion.ilike(f"%{term}%")]
        if term.isdigit():
            filters.append(Cuadratura.numero == int(term))
        query = query.filter(or_(*filters))
    rows, total, total_pages = paginate(query.order_by(Cuadratura.fecha.desc(), Cuadratura.numero.desc()), page)
    return render(request, "cuadraturas.html", {"title": "Cuadraturas", "rows": rows, "q": q, "page": page, "total": total, "total_pages": total_pages}, db)


@app.get("/cuadraturas/nuevo")
def cuadratura_nuevo(request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "operador")
    item = Cuadratura(
        numero=next_number(db, Cuadratura),
        fecha=date.today(),
        turno=1,
        operador_codigo="",
        combust_v=0,
        otros_v=0,
        deposito_v=0,
        ventas_v=0,
        transbnk_v=0,
        transfer_v=0,
        piloto_v=0,
    )
    return render(request, "cuadratura_form.html", {"title": "Nueva cuadratura", "item": item, "operadores": db.query(Operador).filter(Operador.activo.is_(True)).order_by(Operador.descripcion).all()}, db)


@app.get("/cuadraturas/{item_id}/editar")
def cuadratura_editar(item_id: int, request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "operador")
    item = db.get(Cuadratura, item_id)
    if not item:
        raise HTTPException(404)
    return render(request, "cuadratura_form.html", {"title": "Editar cuadratura", "item": item, "operadores": db.query(Operador).filter(Operador.activo.is_(True)).order_by(Operador.descripcion).all()}, db)


@app.post("/cuadraturas/guardar")
async def cuadratura_guardar(request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "operador")
    form = await request.form()
    item_id = form_int(form, "id")
    item = db.get(Cuadratura, item_id) if item_id else Cuadratura()
    item.numero = form_int(form, "numero", next_number(db, Cuadratura))
    item.fecha = parse_date(str(form.get("fecha", "")), date.today()) or date.today()
    item.turno = form_int(form, "turno", 1)
    item.operador_codigo = str(form.get("operador_codigo", "")).strip()
    if form_bool(form, "recuperar_depositos") and item.operador_codigo:
        item.deposito_v, item.combust_v, item.otros_v = depositos_para_cuadratura(db, item.fecha, item.turno, item.operador_codigo)
    else:
        item.combust_v = form_int(form, "combust_v")
        item.otros_v = form_int(form, "otros_v")
        item.deposito_v = form_int(form, "deposito_v")
    item.ventas_v = form_int(form, "ventas_v")
    item.transbnk_v = form_int(form, "transbnk_v")
    item.transfer_v = form_int(form, "transfer_v")
    item.piloto_v = form_int(form, "piloto_v")
    db.merge(item)
    db.commit()
    return redirect("/cuadraturas")


@app.post("/cuadraturas/{item_id}/eliminar")
def cuadratura_eliminar(item_id: int, request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "supervisor")
    item = db.get(Cuadratura, item_id)
    if item:
        db.delete(item)
        db.commit()
    return redirect("/cuadraturas")


@app.get("/configuracion")
def configuracion(request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "admin")
    item = db.get(Configuracion, 1) or Configuracion(id=1)
    return render(request, "configuracion.html", {"title": "Configuracion", "item": item}, db)


@app.post("/configuracion")
async def configuracion_guardar(request: Request, db: Session = Depends(get_db)):
    require_role(require_user(request, db), "admin")
    form = await request.form()
    item = db.get(Configuracion, 1) or Configuracion(id=1)
    item.empresa = str(form.get("empresa", "")).strip()
    item.rut = str(form.get("rut", "")).strip()
    item.local = str(form.get("local", "")).strip()
    item.email = str(form.get("email", "")).strip()
    item.membrete = str(form.get("membrete", "")).strip()
    db.merge(item)
    db.commit()
    return redirect("/configuracion")


@app.get("/reportes/{tipo}")
def reporte(tipo: str, request: Request, fecha_desde: str = "", fecha_hasta: str = "", operador: str = "", db: Session = Depends(get_db)):
    require_user(request, db)
    operadores = db.query(Operador).order_by(Operador.descripcion).all()
    if tipo == "cuadraturas":
        rows = filtered_cuadraturas(db, fecha_desde, fecha_hasta, operador).order_by(Cuadratura.fecha, Cuadratura.operador_codigo, Cuadratura.turno, Cuadratura.numero).all()
    elif tipo == "depositos":
        rows = filtered_depositos(db, fecha_desde, fecha_hasta, operador).order_by(Deposito.fecha, Deposito.operador_codigo, Deposito.turno, Deposito.numero).all()
    elif tipo == "operadores":
        rows = db.query(Operador).order_by(Operador.descripcion).all()
    else:
        raise HTTPException(404)
    return render(request, "reporte.html", {"title": f"Reporte {tipo}", "tipo": tipo, "rows": rows, "operadores": operadores, "fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta, "operador": operador}, db)


def workbook_response(filename: str, rows: list[list[Any]]) -> StreamingResponse:
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/exportar/{tipo}.xlsx")
def exportar(tipo: str, request: Request, fecha_desde: str = "", fecha_hasta: str = "", operador: str = "", db: Session = Depends(get_db)):
    require_user(request, db)
    if tipo == "cuadraturas":
        rows = [["Numero", "Fecha", "Turno", "Operador", "Combustible", "Otros", "Deposito", "Ventas", "TransBank", "Transferencia", "Piloto", "Diferencia"]]
        for item in filtered_cuadraturas(db, fecha_desde, fecha_hasta, operador).order_by(Cuadratura.fecha).all():
            rows.append([item.numero, item.fecha.isoformat(), item.turno, item.operador_codigo, item.combust_v, item.otros_v, item.deposito_v, item.ventas_v, item.transbnk_v, item.transfer_v, item.piloto_v, diferencia_cuadratura(item)])
    elif tipo == "depositos":
        rows = [["Numero", "Fecha", "Turno", "Operador", "20K", "10K", "5K", "2K", "1K", "500", "100", "50", "10", "Aceite", "Promo", "Val Comb", "Val Otro", "Total"]]
        for item in filtered_depositos(db, fecha_desde, fecha_hasta, operador).order_by(Deposito.fecha).all():
            rows.append([item.numero, item.fecha.isoformat(), item.turno, item.operador_codigo, item.por_20k, item.por_10k, item.por_05k, item.por_02k, item.por_01k, item.por_05c, item.por_01c, item.por_50u, item.por_10u, item.aceite_v, item.promo_v, item.val_comb, item.val_otro, item.total_v])
    elif tipo == "operadores":
        rows = [["Codigo", "Nombre", "Activo", "Ingreso", "Tinta"]]
        for item in db.query(Operador).order_by(Operador.descripcion).all():
            rows.append([item.codigo, item.descripcion, "Si" if item.activo else "No", item.ingreso.isoformat() if item.ingreso else "", item.tinta])
    else:
        raise HTTPException(404)
    return workbook_response(f"{tipo}.xlsx", rows)
