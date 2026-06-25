# Mapa funcional inferido de `rendicion.exe`

Fecha de analisis: 2026-06-25

## Alcance

Este documento resume funcionalidades inferidas mediante analisis estatico de:

- `rendicion.exe`
- `Sis Cuadratura/Sis Cuadratura/rendicion.exe`
- `Actualizacion 22102018.zip/rendicion.exe`
- `rendicion.zip/rendicion.exe`
- Estructuras DBF en `Sis Cuadratura/Sis Cuadratura/Datos`
- Cadenas internas extraidas del binario

No se ejecuto el EXE legacy para evitar escritura accidental sobre DBF.

## Formularios detectados

| Formulario | Funcion inferida | Evidencia |
|---|---|---|
| `frmLogin` / `Login()` | Acceso al sistema con usuario y password | `Caption = "Acceso al Sistema"`, `pcUsuario`, `pcPass`, `PasswordChar = "*"`, `if (Usuarios->psw_Usu == pcPass)` |
| `frmSelUsuario` / `SelUsuario` | Selector/listado de usuarios para login | `frmSelUsuario.grdUsuario.grcCodigo`, `grdUsuario`, `do form SelUsuario to lnReg` |
| `Usuarios` / `frmUsuarios` | Maestro CRUD de usuarios | `do form Usuarios`, `ControlSource = "m.cod_usu"`, `m.Nom_Usu`, `m.Seg_Usu`, `m.men_usu`, `m.psw_usu` |
| `Configuracion` / `frmConfiguracion` | Configuracion de empresa/local/membrete/reportes | `do form Configuracion`, `txtEmpresa`, `txtRUT`, `edtMembrete`, `jCaption = "E-mail Empresa"` |
| `Operadores` | Maestro CRUD de operadores | `do form Operadores`, `Caption = "Ingreso Maestro de Operadores"`, `codigo`, `descri`, `activo`, `ingreso`, `tinta` |
| `ingCuadratura` | Ingreso/edicion de cuadraturas o rendiciones | `do form ingCuadratura`, `Caption = "Ingreso Cuadratura"`, campos de `cuadra.DBF` |
| `ingDepositos` | Ingreso/edicion de depositos | `do form ingDepositos`, `Caption = "Ingreso de Depositos"`, campos de `deposito.DBF` |
| `ConsCuadratura` | Consulta/listado de cuadraturas por rango | `do form ConsCuadratura to lnReg`, join `Cuadra` + `Operadores`, filtros `pdFecMin/pdFecTop` |
| `ConsDepositos` / `frmConsDepositos` | Consulta/listado de depositos por rango | `do form ConsDepositos to lnReg`, join `Deposito` + `Operadores`, grilla `grdListas` |
| `infCuadratura` | Selector/emisor de informes de cuadratura | `do form infCuadratura`, captions `Detallado`, `Resumido`, `por Operador`, `por Turno` |
| `infCuadraOpe` | Informe de cuadraturas por operador | `do form infCuadraOpe`, `report form infCuadraOpe` |
| `infDepositos` | Selector/emisor de informes de depositos | `do form infDepositos`, `Informe Resumen Depositos` |
| `infDepositaOpe` | Informe de depositos por operador, nombre probable o typo interno | `do form infDepositaOpe` |
| `SelRegistro` | Selector generico de registros, usado para operadores | `SelRegistro("Operadores", "descri", "ind_nom", ...)` |
| `frmEjecutar` | Ejecucion de comando FoxPro, probablemente mantenimiento/debug | `Caption = "Ejecutar comando"`, `ControlSource = "pcComando"`, `&pcComando` |
| `frmIngresaNumeros` | Entrada numerica generica | `Caption = "Ingreso N"`, `pcMiNum` |

## Reportes detectados

| Reporte FRX inferido | Uso |
|---|---|
| `infCuadraDet` | Informe de cuadratura detallado |
| `infCuadraRes` | Informe de cuadratura resumido |
| `infCuadraOpe` | Informe de cuadratura por operador |
| `infDepositos` | Informe/resumen de depositos |
| `infDepositosxOpe` | Informe de depositos por operador |
| `infDepositosxTur` | Informe de depositos por turno |
| `infDepxOpeDet` | Informe de depositos por operador detallado |
| `lstCuadratura` | Listado de cuadraturas |
| `lstDeposito` | Listado de depositos |
| `lstOperadores` | Listado maestro de operadores |

Los reportes usan `preview noconsole to printer prompt`, por lo que el sistema antiguo abre vista previa y dialogo de impresion.

## Tablas y campos funcionales

### `usuarios.dbf`

- `COD_USU`: codigo de usuario.
- `NOM_USU`: nombre.
- `SEG_USU`: nivel de seguridad numerico.
- `MEN_USU`: menu asignado.
- `PSW_USU`: password legacy en texto/comparacion directa.

Usuarios activos detectados:

- `admin`, nivel 9.
- `ventas`, nivel 3.
- `root`, nivel 9.
- `jof386`, nivel 8.

### `Operadores.DBF`

- `CODIGO`
- `DESCRI`
- `ACTIVO`
- `INGRESO`
- `TINTA`

### `cuadra.DBF`

- `NUMERO`
- `FECHA`
- `TURNO`
- `OPERADOR`
- `COMBUST_V`
- `OTROS_V`
- `DEPOSITO_V`
- `VENTAS_V`
- `TRANSBNK_V`
- `TRANSFER_V`
- `PILOTO_V`

### `deposito.DBF`

- `NUMERO`, `FECHA`, `TURNO`, `OPERADOR`
- Conteos: `POR_20K`, `POR_10K`, `POR_05K`, `POR_02K`, `POR_01K`, `POR_05C`, `POR_01C`, `POR_50U`, `POR_10U`
- Valores: `VAL_20K`, `VAL_10K`, `VAL_05K`, `VAL_02K`, `VAL_01K`, `VAL_05C`, `VAL_01C`, `VAL_50U`, `VAL_10U`
- Otros: `ACEITE_C`, `PROMO_C`, `ACEITE_V`, `PROMO_V`, `VAL_OTRO`, `VAL_COMB`, `TOTAL_V`

## Reglas de negocio inferidas

### Login y seguridad

- El login busca usuario con `seek(pcUsuario)`.
- Compara `Usuarios->psw_Usu == pcPass`.
- Carga globales:
  - `pcUsuSis = pcUsuario`
  - `pnSegSis = Usuarios->Seg_Usu`
  - `pcMenSis = Usuarios->men_usu`
- Hay validacion de permiso para editar registros existentes:
  - `!this.NuevoReg .and. !empty(m.numero) .and. (pnSegSis >= 7)`
- Mensaje de error detectado:
  - `Usuario incorrecto`

### Ingreso de depositos

- Permite ingresar numero, fecha, turno y operador.
- Maneja conteos por denominacion y valores calculados.
- Calcula:
  - `m.val_otro = m.aceite_V + m.promo_V`
  - `m.val_comb = ThisForm.Total - (m.aceite_V + m.promo_V)`
  - `m.total_V = ThisForm.Total`
- Tiene campos de aceite y promo tanto en cantidad como valor.
- Usa `select max(numero) as maximo from Depositos` para correlativo.
- Usa `seek(str(m.numero, 9))` para buscar existencia.

### Ingreso de cuadratura/rendicion

- Usa alias `Rendicion` para tabla `cuadra`.
- Campos principales: fecha, turno, operador, combustible, otros/aceite, deposito, ventas, TransBank, transferencia y piloto/copiloto.
- Recupera depositos relacionados:
  - `ThisForm.RecuperaDepositos`
  - `store (m.deposito_v + loReg.total_v) to m.deposito_v`
  - `store (m.combust_v + loReg.val_comb) to m.combust_v`
  - acumulacion de `val_otro` hacia `lnOtro`
- Formula de diferencia detectada por version:
  - `combust_v - ventas_v + transbnk_v`
  - `combust_v - ventas_v + transbnk_v + transfer_v`
  - `combust_v - ventas_v + transbnk_v + transfer_v + piloto_v`
- En consultas/reportes tambien aparecen variantes con `deposito_v`:
  - `deposito_v - ventas_v + transbnk_v`
  - `deposito_v - ventas_v + transbnk_v + transfer_v + piloto_v`
- Usa `select max(numero) as maximo from Rendicion` para correlativo.
- Reemplaza campos con `replace Rendicion -> ...`.

### Consultas

- Consulta cuadraturas:
  - `Cuadra C inner join Operadores O`
  - filtros por `between(C.fecha, pdFecMin, pdFecTop)`
  - ordenes por `fecha, operador, turno, numero` y por `operador, fecha, turno, numero`
- Consulta depositos:
  - `Deposito D inner join Operadores O`
  - filtros por `between(D.fecha, pdFecMin, pdFecTop)`
  - grilla con columnas `numero`, `fecha`, `turno`, `val_comb`

### Exportacion a Excel

Plantillas/archivos detectados:

- `planillas/Cuadratura.xls`
- `planillas/CuadraxOpe.xls`
- `planillas/DeposixOpe.xls`
- `planillas/Operadores.xls`

Mecanismo legacy:

- Genera comando: `export to '<archivo>' type xl5`
- Ejecuta macro-comando con `&lcCommand`
- Abre Excel con COM:
  - `CREATEOBJECT("excel.application")`
  - `m.objexcel.Workbooks.Open(lcExport)`
  - `m.objExcel.Visible=.t.`

Nota: en la carpeta instalada no se observo `DeposixOpe.xls`, aunque el EXE lo referencia.

### Configuracion

Variables detectadas en `config.MEM`:

- Empresa: `Comerc. Sur Energy SPA`
- Local: `Shell Alerce`
- Membrete: `Comerc. Sur Energy Spa. / Avda. Gabriela Mistral 900 / Sector Alerce, Puerto Montt`
- RUT: `76856384-5`
- Email: `surenergy.ptomontt@gmail.com`

La pantalla `Configuracion` permite editar empresa, RUT, local, email y membrete.

### Mantenimiento/debug

Se detecto formulario `Ejecutar comando` con `&pcComando`, lo que implica ejecucion dinamica de comandos FoxPro. Esto debe excluirse o bloquearse en la migracion moderna salvo que se reemplace por herramientas administrativas seguras y auditadas.

## Funcionalidades que faltan en la app Python actual

| Modulo | Estado actual | Pendiente |
|---|---|---|
| Login | No implementado en UI | Formulario de login, sesiones, roles, cambio de clave |
| Usuarios | Solo modelo/migracion | CRUD web, reset de claves, roles |
| Operadores | Listado | Crear, editar, activar/desactivar, listado imprimible/exportable |
| Depositos | Listado | Formulario de ingreso/edicion, calculo de denominaciones, validaciones, impresion/exportacion |
| Cuadraturas | Listado | Formulario de ingreso/edicion, recuperar depositos, calculo de diferencia, validaciones |
| Consultas | Listados con busqueda simple | Filtros por rango de fechas, operador, turno, numero |
| Reportes | No implementado | Reproducir 10 reportes detectados |
| Excel | No implementado | Exportar XLSX con `openpyxl`, sin COM |
| Configuracion | No implementado | CRUD de parametros de empresa/local/membrete |
| Auditoria | No implementado | Registrar altas, cambios, anulaciones, login |
| Tmp/cache | No aplica | Evitar DBF temporales, usar queries SQL/transacciones |

## Recomendaciones para completar migracion funcional

1. Implementar autenticacion y RBAC antes de permitir edicion.
2. Completar modelos con todos los campos de `deposito.DBF` y `cuadra.DBF`; la primera version Python migro solo subconjunto de depositos.
3. Implementar formulario de depositos con calculo automatico:
   - denominaciones
   - aceite
   - promo
   - `VAL_COMB`
   - `VAL_OTRO`
   - `TOTAL_V`
4. Implementar formulario de cuadratura:
   - fecha, turno, operador
   - ventas, TransBank, transferencia, piloto/copiloto
   - recuperacion de depositos asociados
   - diferencia calculada
5. Implementar consultas con filtros equivalentes a `pdFecMin/pdFecTop`.
6. Reproducir reportes en PDF/HTML y exportacion XLSX.
7. Reemplazar `Configuracion` por tabla SQL `configuracion`.
8. No migrar `frmEjecutar`; si se requiere soporte, crear acciones administrativas permitidas y auditadas.

## Artefactos generados

- `exe_feature_report.json`
- `exe_feature_report.txt`
- `funcionalidades_rendicion_exe.md`

