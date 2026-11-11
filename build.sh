#!/usr/bin/env bash
# Salir inmediatamente si ocurre un error
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Recopilar archivos estáticos del Admin
python manage.py collectstatic --no-input

# Aplicar migraciones a PostgreSQL
python manage.py migrate