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

## API JSON para frontend React/Ionic

La app Jinja se mantiene funcionando. La nueva capa JSON vive bajo `/api` y reutiliza la misma sesion por cookie, roles, modelos y calculos de FastAPI.

Endpoints principales:

- `POST /api/login`
- `POST /api/logout`
- `GET /api/me`
- `GET /api/dashboard`
- `GET /api/cuadraturas`, `GET /api/cuadraturas/{id}`, `POST /api/cuadraturas`, `PUT /api/cuadraturas/{id}`, `DELETE /api/cuadraturas/{id}`
- `GET /api/depositos`, `GET /api/depositos/{id}`, `POST /api/depositos`, `PUT /api/depositos/{id}`, `DELETE /api/depositos/{id}`
- `POST /api/depositos/importar`
- `GET /api/operadores`, `GET /api/operadores/{codigo}`, `POST /api/operadores`, `PUT /api/operadores/{codigo}`, `DELETE /api/operadores/{codigo}`
- `GET /api/usuarios`, `GET /api/usuarios/{id}`, `POST /api/usuarios`, `PUT /api/usuarios/{id}`, `DELETE /api/usuarios/{id}`
- `GET /api/configuracion`, `PUT /api/configuracion`
- `GET /api/reportes/{tipo}`

Para desarrollo separado, FastAPI permite credenciales desde:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Puedes cambiarlo con:

```powershell
$env:CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
```

## Frontend React + Ionic

La migracion visual nueva esta en `frontend/`. No reemplaza los templates Jinja: permite comparar la app antigua y la nueva.

Levantar backend:

```powershell
uvicorn app.main:app --reload
```

Levantar frontend:

```powershell
cd frontend
npm install
npm run dev
```

URLs:

- Backend/Jinja: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Frontend Ionic: http://127.0.0.1:5173

El frontend usa el proxy de Vite para `/api`, `/reportes` y `/exportar`, por lo que mantiene cookies de sesion y puede descargar los XLSX existentes sin duplicar la logica de reportes. Por defecto el proxy apunta a `http://127.0.0.1:8010`; si quieres usar otro backend:

```powershell
$env:VITE_BACKEND_TARGET="http://127.0.0.1:8000"
npm run dev
```

Cobertura funcional en Ionic:

- Login/logout con sesion por cookie.
- Dashboard con estadisticas y registros recientes.
- Cuadraturas: listado, busqueda, crear, editar, eliminar y recuperar depositos del turno desde el backend.
- OCR de cuadraturas: carga de imagen/PDF para prellenar el formulario de cuadratura.
- Depositos: listado, busqueda, crear, editar, eliminar y calculo automatico de totales en FastAPI.
- OCR de boletas: carga de imagen y prellenado del formulario de deposito.
- Operadores: listado, crear, editar y desactivar.
- Usuarios admin: listado, crear, editar, cambiar password y desactivar.
- Configuracion admin: editar datos de empresa y membrete.
- Reportes: filtros por tipo, fechas y operador, tabla en Ionic, enlace imprimible HTML y exportacion XLSX.

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

La carga OCR acepta imagenes (`jpg`, `jpeg`, `png`, `tiff`, `bmp`) y PDF. Cuando se sube un PDF, el backend lo convierte internamente a imagenes y luego aplica Tesseract OCR.

El flujo es:

1. Subir imagen de la boleta o comprobante.
2. Si es PDF, la aplicacion convierte paginas a imagen.
3. La aplicacion lee texto con OCR.
4. Se abre el formulario de deposito prellenado.
5. El usuario revisa y guarda manualmente.

Dependencias externas requeridas en Windows:

- Instalar Tesseract OCR y agregar `tesseract.exe` al `PATH`.
- Para PDF, instalar Poppler y agregar la carpeta `bin` al `PATH`.

Tambien puedes configurar rutas manualmente:

```powershell
$env:TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"
$env:POPPLER_PATH="C:\poppler\Library\bin"
```

Si Tesseract o Poppler no estan instalados, la pantalla mostrara una advertencia y no guardara datos automaticamente.

## PostgreSQL

Por defecto usa SQLite (`rendicion.db`). Para PostgreSQL:

```powershell
$env:DATABASE_URL="postgresql+psycopg2://usuario:password@localhost:5432/rendicion"
```
