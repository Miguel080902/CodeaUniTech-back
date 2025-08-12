from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    # Autenticación
    RegistroInicialView, CustomTokenObtainPairView, LogoutView,
    
    # Perfil de usuario
    CompletarPerfilView, PerfilView, EstadoPerfilView, VerificarUsuarioUnicoView,
    
    # Administración de docentes
    DocenteCreateView, DocenteListView, DocenteDetailView,
    
    # Vistas públicas de docentes
    DocentesPublicosView, DocentePublicoDetailView
)

app_name = 'users'

urlpatterns = [
    # ===============================
    # AUTENTICACIÓN
    # ===============================
    path('auth/registro/', RegistroInicialView.as_view(), name='registro_inicial'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ===============================
    # PERFIL DE USUARIO
    # ===============================
    # Perfil actual del usuario autenticado
    path('perfil/', PerfilView.as_view(), name='perfil'),
    
    # Completar perfil (paso 2 del registro)
    path('completar-perfil/', CompletarPerfilView.as_view(), name='completar_perfil'),
    
    # Estado del perfil
    path('estado-perfil/', EstadoPerfilView.as_view(), name='estado_perfil'),
    
    # Verificar disponibilidad de usuario único
    path('verificar-usuario/', VerificarUsuarioUnicoView.as_view(), name='verificar_usuario_unico'),

    # ===============================
    # ADMINISTRACIÓN DE DOCENTES (Solo admins)
    # ===============================
    # Crear docentes
    path('admin/docentes/crear/', DocenteCreateView.as_view(), name='crear_docente'),
    
    # Listar docentes disponibles para asignar a cursos
    path('admin/docentes/', DocenteListView.as_view(), name='listar_docentes'),
    
    # Ver, editar y eliminar docente específico
    path('admin/docentes/<int:id>/', DocenteDetailView.as_view(), name='detalle_docente'),

    # ===============================
    # VISTAS PÚBLICAS DE DOCENTES
    # ===============================
    # Listar docentes públicamente (para mostrar en la web)
    path('docentes/', DocentesPublicosView.as_view(), name='docentes_publicos'),
    
    # Ver perfil público de un docente específico
    path('docentes/<int:id>/', DocentePublicoDetailView.as_view(), name='docente_publico_detalle'),
]


# ===============================
# DOCUMENTACIÓN DE URLs
# ===============================
"""
ESTRUCTURA DE URLs - API DE USUARIOS

📁 AUTENTICACIÓN (/users/auth/)
├── POST /registro/           - Registro inicial (paso 1)
├── POST /login/             - Login con email y password
├── POST /logout/            - Logout y blacklist del token
└── POST /refresh/           - Renovar access token

📁 PERFIL DE USUARIO (/users/)
├── GET,PUT,PATCH /perfil/              - Ver/actualizar perfil propio
├── GET,PUT,PATCH /completar-perfil/    - Completar perfil (paso 2)
├── GET /estado-perfil/                 - Verificar estado del perfil
└── GET /verificar-usuario/             - Verificar disponibilidad de usuario único

📁 ADMINISTRACIÓN DE DOCENTES (/users/admin/docentes/)
├── POST /crear/             - Crear nuevo docente (admin)
├── GET /                    - Listar docentes para asignar a cursos (admin)
└── GET,PUT,PATCH,DELETE /<id>/  - Gestionar docente específico (admin)

📁 VISTAS PÚBLICAS DE DOCENTES (/users/docentes/)
├── GET /                    - Listar docentes públicamente
└── GET /<id>/              - Ver perfil público de docente específico

📋 PARÁMETROS DE QUERY DISPONIBLES:
- /verificar-usuario/?usuario_unico=nombre_usuario
"""

# ===============================
# EJEMPLOS DE USO
# ===============================
"""
EJEMPLOS DE ENDPOINTS:

🔐 AUTENTICACIÓN:
- POST /users/auth/registro/
- POST /users/auth/login/
- POST /users/auth/logout/
- POST /users/auth/refresh/

👤 PERFIL:
- GET /users/perfil/
- PUT /users/completar-perfil/
- GET /users/estado-perfil/
- GET /users/verificar-usuario/?usuario_unico=juan.perez

🛡️ ADMIN - DOCENTES:
- POST /users/admin/docentes/crear/
- GET /users/admin/docentes/
- GET /users/admin/docentes/15/
- PUT /users/admin/docentes/15/
- DELETE /users/admin/docentes/15/

🌐 PÚBLICO - DOCENTES:
- GET /users/docentes/
- GET /users/docentes/15/
"""