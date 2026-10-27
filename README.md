# Agenda Personal - Backend (Django)

Aplicación backend desarrollada en Python con Django para la gestión de citas de servicios de estética (maquillaje/peinado) y enfermería.

## 🚀 Tecnologías utilizadas
* Python & Django
* Django REST Framework
* SQLite (Base de datos local)
* Git y GitHub (Control de versiones)

## 📌 Estado actual del proyecto (Progreso)
* **Modelos ORM (`Service` y `Booking`):** Implementados con reglas de negocio robustas (validación de solapamiento de horarios, cálculo automático de saldo pendiente, bloqueo de fechas pasadas y exención de anticipos para enfermería).
* **Seguridad:** Configuración de variables de entorno con `python-dotenv` y `.gitignore` para proteger credenciales.
* **Control de versiones:** Repositorio estructurado y sincronizado en GitHub mediante ramas y *commits*.

### 🔄 Progreso Reciente 
* **Automatización de Precios:** Configuración del modelo `Booking` para que asigne automáticamente el precio base del servicio seleccionado, evitando duplicidad de datos en los formularios.
* **Validaciones del Lado del Servidor:** Integración del método `clean()` y `full_clean()` para asegurar la ejecución correcta de las reglas de negocio (como la validación de montos de anticipo y prevención de conflictos) antes de guardar en la base de datos.
* **Cálculo Dinámico:** Automatización del cálculo del `saldo_pendiente` restando el anticipo al precio total de forma segura en el servidor.