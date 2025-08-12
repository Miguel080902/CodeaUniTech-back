@echo off
if "%1"=="install" (
    pip install -r requirements.txt
) else if "%1"=="db-up" (
    docker-compose up -d db
) else if "%1"=="setup" (
    call %0 install
    call %0 db-up
    timeout /t 5
    python manage.py makemigrations
    python manage.py migrate
    echo Setup completado!
) else if "%1"=="dev" (
    python manage.py runserver 0.0.0.0:8000
) else if "%1"=="migrate" (
    python manage.py migrate
) else if "%1"=="superuser" (
    python manage.py createsuperuser
) else (
    echo Comandos disponibles:
    echo   make install     - Instalar dependencias
    echo   make setup       - Configuracion inicial completa
    echo   make dev         - Iniciar servidor de desarrollo
    echo   make db-up       - Levantar base de datos con Docker
    echo   make migrate     - Ejecutar migraciones
    echo   make superuser   - Crear superusuario
)
