# Sistema de Cuadratura y Rendicion Moderno

Proyecto base en FastAPI para migrar el sistema legacy Visual FoxPro/DBF a Python.

## Instalacion

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Migrar datos DBF

Los DBF deben estar en la carpeta `data`.

```powershell
python .\scripts\migrar_dbf.py
```

El script descarta registros con fechas invalidas o `OPERADOR` vacio y los deja en `migration_errors.csv`.
Las contrasenas legacy no se migran: cada usuario queda con una clave temporal del formato `Cambiar-{codigo}-2026`.

## Levantar aplicacion

```powershell
uvicorn app.main:app --reload
```

Luego abrir:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/login
- http://127.0.0.1:8000/dashboard
- http://127.0.0.1:8000/cuadraturas
- http://127.0.0.1:8000/depositos
- http://127.0.0.1:8000/operadores
- http://127.0.0.1:8000/reportes/cuadraturas
- http://127.0.0.1:8000/reportes/depositos
- http://127.0.0.1:8000/usuarios
- http://127.0.0.1:8000/configuracion
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

## Funcionalidades implementadas

- Login con usuarios migrados desde `usuarios.dbf`.
- Roles: `consulta`, `operador`, `supervisor`, `admin`.
- Maestro de usuarios.
- Maestro de operadores.
- Ingreso, edicion y eliminacion de depositos.
- Lectura OCR de imagenes de boletas/comprobantes para prellenar depositos.
- Calculo automatico de denominaciones, aceite, promo, `VAL_COMB`, `VAL_OTRO` y `TOTAL_V`.
- Ingreso, edicion y eliminacion de cuadraturas.
- Recuperacion de depositos por fecha, turno y operador.
- Calculo de diferencia de cuadratura.
- Consultas paginadas.
- Reportes HTML imprimibles.
- Exportacion XLSX para cuadraturas, depositos y operadores.
- Configuracion de empresa, RUT, local, email y membrete.

## OCR de boletas

Ruta:

```text
http://127.0.0.1:8000/depositos/importar
```

El flujo es:

1. Subir imagen de la boleta o comprobante.
2. La aplicacion lee texto con OCR.
3. Se abre el formulario de deposito prellenado.
4. El usuario revisa y guarda manualmente.

Dependencia externa requerida en Windows:

- Instalar Tesseract OCR.
- Agregar `tesseract.exe` al `PATH`.

Si Tesseract no esta instalado, la pantalla mostrara una advertencia y no guardara datos automaticamente.

## PostgreSQL

Por defecto usa SQLite (`rendicion.db`). Para PostgreSQL:

```powershell
$env:DATABASE_URL="postgresql+psycopg2://usuario:password@localhost:5432/rendicion"
```
