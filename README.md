# Agenda Personal - Backend (Django & DRF)

Sistema backend y API RESTful desarrollado en **Python 3.11** y **Django 5.2** para la gestión integral del catálogo de servicios (estética y enfermería), control de citas y cálculo automatizado de saldos y anticipos.

## 🚀 Tecnologías Utilizadas
- **Lenguaje y Framework:** Python 3.11 & Django 5.2
- **API REST:** Django REST Framework (DRF)
- **Filtrado y Búsquedas:** `django-filter` + `SearchFilter` & `OrderingFilter`
- **Seguridad y Configuración:** `python-dotenv` (Variables de entorno)
- **Base de Datos:** SQLite (Entorno de desarrollo local)
- **Control de Versiones:** Git & GitHub (Flujo basado en ramas `feature/*`)

---

## 📌 Arquitectura y Lógica de Negocio (ORM)

- **Modelos Principales (`Service` y `Booking`):**
  - `Service`: Gestiona nombre, categoría (`ESTETICA`, `ENFERMERIA`) y `precio_base`.
  - `Booking`: Gestiona datos del cliente, fecha, hora, relación `ForeignKey` con `Service`, control financiero (`precio_total`, `monto_anticipo`, `saldo_pendiente`), notas y estado de la cita.
- **Integridad Financiera Automatizada (`clean()` y `save()`):**
  - **Asignación automática de precios:** El modelo `Booking` hereda automáticamente el `precio_base` del servicio seleccionado y lo asigna a `precio_total`.
  - **Cálculo dinámico de saldos:** Calcula en el servidor el `saldo_pendiente` (`precio_total - monto_anticipo`) y protege estos campos como solo lectura (`readonly_fields`) tanto en el Django Admin como en la API.
  - **Validaciones de negocio a nivel de servidor:** Prevención de solapamiento de horarios, bloqueo de fechas pasadas, exención de anticipos según categoría y validación para que el `monto_anticipo` nunca supere el `precio_total`.

---

## 🌐 Especificación de la API REST

La API está construida con `ModelViewSet` y `DefaultRouter`, aplicando la política de permisos **`IsAuthenticatedOrReadOnly`**:
- **Lectura (`GET`):** Pública para consulta de catálogo y disponibilidad.
- **Escritura (`POST`, `PUT`, `PATCH`, `DELETE`):** Restringida exclusivamente a usuarios autenticados (`SessionAuthentication` / `BasicAuthentication`).

### 1. Catálogo de Servicios (`/api/services/`)
Permite listar, crear, actualizar y eliminar servicios.
- **Filtros exactos (`filterset_fields`):** `?categoria=ESTETICA` o `?categoria=ENFERMERIA`
- **Búsqueda por texto (`search_fields`):** `?search=limpieza` (busca coincidencias parciales en `nombre`)
- **Ordenamiento (`ordering_fields`):** `?ordering=precio_base` (ascendente) o `?ordering=-precio_base` (descendente)

### 2. Gestión de Reservas (`/api/bookings/`)
Permite gestionar el ciclo de vida completo de las citas manteniendo las reglas financieras del ORM.
- **Serialización Inteligente:**
  - **Protección de datos:** `precio_total` y `saldo_pendiente` están declarados en `read_only_fields` para evitar manipulación desde el cliente HTTP.
  - **Puente de validación (`validate`):** Instancia temporalmente el modelo `Booking` para ejecutar `clean()` antes de guardar, transformando cualquier `ValidationError` del ORM en una respuesta estándar HTTP `400 Bad Request` de DRF.
  - **Respuesta enriquecida (`to_representation`):** Al crear/editar se envía únicamente el ID del servicio, pero al consultar (`GET`), la API devuelve el objeto `servicio` serializado con todos sus detalles.
- **Filtros exactos (`filterset_fields`):**
  - Por fecha: `/api/bookings/?fecha=2026-10-30`
  - Por estado: `/api/bookings/?estado=PENDIENTE`
  - Por servicio (ID): `/api/bookings/?servicio=1`
  - Combinados: `/api/bookings/?fecha=2026-10-30&estado=PENDIENTE`
- **Búsqueda por texto (`search_fields`):**
  - `/api/bookings/?search=Maria` (busca en `cliente_nombre`, `cliente_contacto` y `notas`)
- **Ordenamiento (`ordering_fields`):**
  - Por defecto ordena desde las citas más próximas/recientes (`-fecha`, `-hora`). Soporta ordenamiento por `fecha`, `hora`, `precio_total` y `saldo_pendiente`.

---

## ⚙️ Instalación y Ejecución Local

1. **Clonar el repositorio:**
   ```powershell
   git clone [https://github.com/Alafi98/agenda-backend.git](https://github.com/Alafi98/agenda-backend.git)
   cd agenda-backend

2. ** Crear y activar el entorno virtual(Windows PowerShell):
  python -m venv venv
  .\venv\Scripts\activate

3. Instalar dependencias
  pip install -r requirements.txt

4. Configurar variables de entorno
  Crea un archivo .env en la raíz del proyecto con tu clave secreta y configuración local:

  Fragmento de código -->
  SECRET_KEY=tu_clave_secreta_aqui
  DEBUG=True

5. Ejecutar migraciones e iniciar el servidor:

  PowerShell
    python manage.py migrate
    python manage.py runserver
  -Browsable API: http://127.0.0.1:8000/api/

  -Panel Administrativo: http://127.0.0.1:8000/admin/



