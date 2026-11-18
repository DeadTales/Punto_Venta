# Punto · Sistema POS

Punto de venta de escritorio desarrollado con **FastAPI**, **Flet (Flutter para Python)** y **PostgreSQL (Supabase)**. Integra control de acceso, clientes y empleados, catálogo e inventario con lector de código de barras, caja con cortes de turno, transacciones de venta atómicas, cancelaciones auditadas con devolución de stock, tickets PDF con ReportLab e impresión térmica directa mediante adaptadores ESC/POS (USB, Serial y Red).

---

## 🚀 Arranque Rápido en Windows

Puedes ejecutar el proyecto utilizando un entorno virtual unificado con **`uv`** (recomendado por velocidad y sencillez) o con entornos estándar de **`python -m venv`**.

### Opción A: Entorno Unificado con `uv` (Recomendado)

Desde la raíz del proyecto (`c:\Users\cdepu\Downloads\Proyectos\Punto_Venta`):

```powershell
# 1. Crear y activar el entorno virtual
uv venv .venv
.venv\Scripts\activate

# 2. Instalar todas las dependencias (Backend + Frontend)
uv pip install -r backend/requirements.txt -r frontend/requirements.txt
```

### Opción B: Entornos Separados con `venv` estándar

```powershell
# Crear entornos independientes
python -m venv backend/.venv
python -m venv frontend/.venv

# Instalar dependencias
./backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
./frontend/.venv/Scripts/python.exe -m pip install -r frontend/requirements.txt
```

---

## ⚙️ Configuración de Variables de Entorno

El proyecto incluye plantillas documentadas:
1. **Backend (`backend/.env`):**  
   Copia `backend/.env.example` a `backend/.env` y define tu conexión a Supabase (`DATABASE_URL`) y tu `JWT_SECRET` (mínimo 32 caracteres):
   ```powershell
   Copy-Item backend/.env.example backend/.env
   ```
2. **Frontend (`frontend/.env`):**  
   Configura el modo de ejecución:
   - `POS_MODE=api` y `API_BASE_URL=http://127.0.0.1:8000` para operar contra el servidor y la base de datos real.
   - `POS_MODE=demo` para explorar la interfaz con datos simulados en memoria sin requerir backend.

---

## 🗄️ Base de Datos y Primer Acceso

Antes de arrancar la API por primera vez, aplica las migraciones y crea el usuario Administrador inicial:

```powershell
# Aplica tablas y migraciones en Supabase
python -m backend.src.cli migrate

# Crea el usuario inicial admin@pos.local (solicita contraseña segura por terminal)
python -m backend.src.cli bootstrap
```

> **Recuperación de contraseñas:** Si necesitas restablecer la clave de cualquier usuario:
> ```powershell
> python -m backend.src.cli reset-password --email usuario@ejemplo.com
> ```

---

## ▶️ Ejecución del Sistema

El sistema requiere dos terminales activas:

### Terminal 1: Iniciar el Backend (API FastAPI)
```powershell
.venv\Scripts\activate
python -m uvicorn backend.src.main:app --host 127.0.0.1 --port 8000 --reload
```
*Documentación interactiva Swagger disponible en:* <http://127.0.0.1:8000/docs>

### Terminal 2: Iniciar el Frontend (Aplicación de Escritorio Flet)
```powershell
.venv\Scripts\activate
python -m frontend.src.main
```

---

## 📋 Módulos y Funcionalidades del Sistema

| Módulo | Funcionalidades Principales |
| :--- | :--- |
| **Acceso & Seguridad** | Login con tokens JWT Bearer, control de roles (`Administrador`, `Supervisor`, `Cajero`), hashing seguro con `bcrypt`, e invalidación instantánea de sesiones por versión de token. |
| **Personal & Clientes** | Altas, edición, bajas lógicas preservando trazabilidad histórica y directorio de clientes frecuentes / RFC. |
| **Inventario & Catálogo** | Productos y categorías, lectura de código de barras, cálculo de márgenes, alertas de stock mínimo, ajustes auditados (entradas/mermas) e importación masiva desde Excel (`openpyxl`). |
| **Caja & Turnos** | Apertura con fondo inicial, corte de caja con conciliación de efectivo esperado vs contado, y registro de sobrante/faltante por turno. |
| **Punto de Venta (Ventas)** | Carrito ágil, soporte de cantidades decimales (kilos/fracciones), precios congelados, transacción atómica con bloqueo pesimista (`SELECT ... FOR UPDATE`) y reintentos idempotentes. |
| **Comprobantes & Cancelación** | Reimpresión de tickets, cancelación con devolución íntegra de stock (requiere permiso de supervisor/admin), tickets en PDF con ReportLab e impresión física ESC/POS. |
| **Reportes & Analítica** | Consultas agregadas de ventas por periodos, exportación a CSV y algoritmo de reposición sugerida según demanda media. |
| **Hardware & Periféricos** | Soporte para impresoras térmicas conectadas por USB (`pyusb`), puerto Serial/COM (`pyserial`) o Red/Ethernet con prueba de impresión desde la configuración. |

---

## 📚 Documentación Técnica Adicional

- [Manual Ilustrado de Usuario (Markdown)](docs/manual_usuario.md) y [Versión en PDF](docs/manual_usuario.pdf): Capturas de pantalla numeradas, flujos de trabajo y guía paso a paso.
- [Reporte Técnico de Arquitectura y Código](reporte_final.md): Análisis detallado de la arquitectura de software, patrones de diseño y operaciones CRUD en la base de datos.
- [Operación, Despliegue y Límites del Sistema](docs/operacion.md).
- [Estructura y Código Limpio](docs/code_style.md).
- [Arquitectura de Conexión y Modo Offline](docs/arquitectura_y_offline.md).

---

## 🧪 Pruebas Automatizadas

```powershell
python -m pytest tests -q
```
