from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView,RetrieveAPIView, ListAPIView, RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Usuario, Docente
from .serializers import (
    UsuarioSerializer, UsuarioSimpleSerializer, RegistroInicialSerializer,
    CompletarPerfilSerializer, DocenteCreateSerializer, DocenteListSerializer,
    DocenteDetailSerializer, DocenteUpdateSerializer, DocenteSerializer,
    CustomTokenObtainPairSerializer, PerfilUpdateSerializer
)


# ============================================================================
# VIEWS DE AUTENTICACIÓN
# ============================================================================

class RegistroInicialView(CreateAPIView):
    """
    Vista para el registro inicial (PASO 1)
    Solo email y password
    """
    queryset = Usuario.objects.all()
    serializer_class = RegistroInicialSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Registro inicial de usuario (Paso 1)",
        description="Primer paso del registro: solo email y contraseña. "
                   "Después de esto, el usuario debe completar su perfil.",
        tags=['Autenticación'],
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'usuario': {'$ref': '#/components/schemas/UsuarioSimple'},
                    'perfil_completo': {'type': 'boolean'},
                    'siguiente_paso': {'type': 'string'}
                }
            }
        }
    )
    def post(self, request, *args, **kwargs):
        """Crear usuario con datos iniciales"""
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Override para personalizar la respuesta"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        usuario = serializer.save()
        
        # Usar el serializer simple para la respuesta
        response_serializer = UsuarioSimpleSerializer(usuario)
        
        return Response(
            {
                'message': 'Registro inicial exitoso. Ahora completa tu perfil.',
                'usuario': response_serializer.data,
                'perfil_completo': usuario.perfil_completo,
                'siguiente_paso': 'completar_perfil'
            },
            status=status.HTTP_201_CREATED
        )


class CustomTokenObtainPairView(APIView):
    """
    Vista personalizada para login con email
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Login de usuario",
        description="Autentica un usuario con email y contraseña, devuelve tokens JWT y estado del perfil",
        request=CustomTokenObtainPairSerializer,
        tags=['Autenticación'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'access': {'type': 'string'},
                    'refresh': {'type': 'string'},
                    'message': {'type': 'string'},
                    'usuario': {'$ref': '#/components/schemas/Usuario'},
                    'perfil_completo': {'type': 'boolean'},
                    'siguiente_paso': {'type': 'string', 'nullable': True}
                }
            }
        }
    )
    def post(self, request, *args, **kwargs):
        """Login del usuario"""
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Crear tokens JWT
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            
            # Personalizar claims del token
            access['user_id'] = user.id
            access['email'] = user.email
            access['username'] = user.username
            access['tipo_usuario'] = user.tipo_usuario
            access['perfil_completo'] = user.perfil_completo
            
            # Preparar datos del usuario
            usuario_serializer = UsuarioSerializer(user)
            
            # Determinar siguiente paso
            siguiente_paso = None if user.perfil_completo else 'completar_perfil'
            
            return Response({
                'access': str(access),
                'refresh': str(refresh),
                'message': 'Login exitoso',
                'usuario': usuario_serializer.data,
                'perfil_completo': user.perfil_completo,
                'siguiente_paso': siguiente_paso
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    Vista para cerrar sesión
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Logout de usuario",
        description="Cierra la sesión del usuario invalidando el refresh token",
        tags=['Autenticación']
    )
    def post(self, request):
        """Cerrar sesión del usuario"""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logout(request)
            return Response(
                {'message': 'Logout exitoso'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Token inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================================
# VIEWS DE PERFIL DE USUARIO
# ============================================================================

class CompletarPerfilView(RetrieveUpdateAPIView):
    """
    Vista para completar el perfil (PASO 2)
    """
    serializer_class = CompletarPerfilSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Obtener el usuario actual"""
        return self.request.user

    @extend_schema(
        summary="Obtener datos actuales para completar perfil",
        description="Obtiene los datos actuales del usuario y sugerencias para completar el perfil",
        tags=['Usuario'],
        responses={200: CompletarPerfilSerializer}
    )
    def get(self, request, *args, **kwargs):
        """Obtener datos actuales del perfil"""
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Completar perfil de usuario (Paso 2)",
        description="Segundo paso del registro: completar datos obligatorios y opcionales del perfil. "
                   "Campos obligatorios: nombre, apellido, fecha_nacimiento, usuario_unico, país.",
        tags=['Usuario'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'usuario': {'$ref': '#/components/schemas/Usuario'},
                    'perfil_completo': {'type': 'boolean'}
                }
            }
        }
    )
    def put(self, request, *args, **kwargs):
        """Completar perfil del usuario"""
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="Actualizar parcialmente el perfil",
        description="Actualización parcial del perfil del usuario",
        tags=['Usuario']
    )
    def patch(self, request, *args, **kwargs):
        """Actualización parcial del perfil"""
        return self.partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Override para personalizar la respuesta"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Verificar que el perfil no esté ya completo (para PUT completo)
        if not partial and instance.perfil_completo:
            return Response(
                {'error': 'El perfil ya está completo. Usa PATCH para actualizaciones parciales.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        
        # Respuesta completa del usuario
        response_serializer = UsuarioSerializer(usuario)
        
        mensaje = 'Perfil completado exitosamente' if usuario.perfil_completo else 'Perfil actualizado'
        
        return Response({
            'message': mensaje,
            'usuario': response_serializer.data,
            'perfil_completo': usuario.perfil_completo
        })


class PerfilView(RetrieveUpdateAPIView):
    """
    Vista para obtener y actualizar el perfil del usuario actual
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UsuarioSerializer
        return PerfilUpdateSerializer

    @extend_schema(
        summary="Obtener perfil del usuario actual",
        description="Obtiene el perfil completo del usuario autenticado",
        responses={200: UsuarioSerializer},
        tags=['Usuario']
    )
    def get(self, request, *args, **kwargs):
        """Obtener el perfil del usuario actual"""
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Actualizar perfil del usuario",
        description="Actualiza el perfil del usuario autenticado (solo campos editables)",
        request=PerfilUpdateSerializer,
        responses={200: UsuarioSerializer},
        tags=['Usuario']
    )
    def put(self, request, *args, **kwargs):
        """Actualizar perfil del usuario"""
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Actualizar parcialmente el perfil",
        description="Actualización parcial del perfil del usuario",
        request=PerfilUpdateSerializer,
        responses={200: UsuarioSerializer},
        tags=['Usuario']
    )
    def patch(self, request, *args, **kwargs):
        """Actualización parcial del perfil"""
        return super().patch(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Override para usar UsuarioSerializer en la respuesta"""
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            # Devolver datos completos del usuario
            usuario_serializer = UsuarioSerializer(self.get_object())
            response.data = usuario_serializer.data
        return response


# ============================================================================
# VIEWS DE GESTIÓN DE DOCENTES (ADMIN)
# ============================================================================

class DocenteCreateView(CreateAPIView):
    """
    Vista para crear docentes (solo admins)
    """
    queryset = Docente.objects.all()
    serializer_class = DocenteCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        summary="Crear docente (Solo admins)",
        description="Permite a los administradores crear cuentas de docentes completas (Usuario + información específica de docente)",
        tags=['Administración - Docentes']
    )
    def post(self, request, *args, **kwargs):
        """Crear un nuevo docente"""
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Override para personalizar la respuesta"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        docente = serializer.save()
        
        response_serializer = DocenteDetailSerializer(docente)
        
        return Response(
            {
                'message': 'Docente creado exitosamente',
                'docente': response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class DocenteListView(ListAPIView):
    """
    Vista para listar docentes disponibles (para admins)
    """
    serializer_class = DocenteListSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Docente.objects.select_related('usuario').filter(
            usuario__activo=True,
            usuario__perfil_completo=True
        ).order_by('usuario__first_name', 'usuario__last_name')

    @extend_schema(
        summary="Listar docentes disponibles",
        description="Obtiene la lista de docentes activos para selección en cursos (solo admins)",
        tags=['Administración - Docentes'],
        responses={200: DocenteListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """Listar docentes disponibles"""
        return super().get(request, *args, **kwargs)


class DocenteDetailView(RetrieveUpdateDestroyAPIView):
    """
    Vista para ver, actualizar y eliminar docentes específicos (solo admins)
    """
    queryset = Docente.objects.select_related('usuario').all()
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DocenteDetailSerializer
        return DocenteUpdateSerializer

    @extend_schema(
        summary="Obtener detalles del docente",
        description="Obtiene información completa de un docente específico",
        responses={200: DocenteDetailSerializer},
        tags=['Administración - Docentes']
    )
    def get(self, request, *args, **kwargs):
        """Obtener detalles del docente"""
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Actualizar información del docente",
        description="Actualiza la información específica del docente (no del usuario base)",
        request=DocenteUpdateSerializer,
        responses={200: DocenteDetailSerializer},
        tags=['Administración - Docentes']
    )
    def put(self, request, *args, **kwargs):
        """Actualizar información del docente"""
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="Actualizar parcialmente el docente",
        description="Actualización parcial de la información del docente",
        request=DocenteUpdateSerializer,
        responses={200: DocenteDetailSerializer},
        tags=['Administración - Docentes']
    )
    def patch(self, request, *args, **kwargs):
        """Actualización parcial del docente"""
        return self.partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Eliminar docente",
        description="Elimina un docente del sistema (desactiva el usuario asociado)",
        tags=['Administración - Docentes']
    )
    def delete(self, request, *args, **kwargs):
        """Eliminar docente (desactivar)"""
        docente = self.get_object()
        
        # En lugar de eliminar, desactivamos
        docente.usuario.activo = False
        docente.usuario.save()
        
        return Response({
            'message': 'Docente desactivado exitosamente'
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        """Override para devolver información completa"""
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            # Devolver datos completos del docente
            docente_serializer = DocenteDetailSerializer(self.get_object())
            response.data = docente_serializer.data
        return response


# ============================================================================
# VIEWS DE UTILIDAD
# ============================================================================

class EstadoPerfilView(APIView):
    """
    Vista para verificar el estado del perfil del usuario
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Estado del perfil del usuario",
        description="Verifica el estado del perfil del usuario autenticado",
        tags=['Usuario'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'perfil_completo': {'type': 'boolean'},
                    'campos_faltantes': {'type': 'array', 'items': {'type': 'string'}},
                    'siguiente_paso': {'type': 'string', 'nullable': True},
                    'usuario_unico_sugerido': {'type': 'string', 'nullable': True},
                    'es_docente': {'type': 'boolean'},
                    'perfil_docente_completo': {'type': 'boolean', 'nullable': True}
                }
            }
        }
    )
    def get(self, request):
        """Obtener estado del perfil"""
        user = request.user
        
        # Verificar campos faltantes
        campos_requeridos = {
            'first_name': 'Nombre',
            'last_name': 'Apellido', 
            'fecha_nacimiento': 'Fecha de nacimiento',
            'usuario_unico': 'Nombre de usuario',
            'pais': 'País'
        }
        
        campos_faltantes = []
        for campo, nombre in campos_requeridos.items():
            if not getattr(user, campo):
                campos_faltantes.append(nombre)
        
        # Generar sugerencia de usuario único si no tiene
        usuario_unico_sugerido = None
        if not user.usuario_unico and user.first_name and user.last_name:
            usuario_unico_sugerido = user.generar_usuario_unico()
        
        # Verificar si es docente y estado del perfil docente
        perfil_docente_completo = None
        if user.es_docente:
            try:
                docente = user.docente
                perfil_docente_completo = docente.perfil_docente_completo
            except Docente.DoesNotExist:
                perfil_docente_completo = False
        
        return Response({
            'perfil_completo': user.perfil_completo,
            'campos_faltantes': campos_faltantes,
            'siguiente_paso': None if user.perfil_completo else 'completar_perfil',
            'usuario_unico_sugerido': usuario_unico_sugerido,
            'es_docente': user.es_docente,
            'perfil_docente_completo': perfil_docente_completo
        })


class VerificarUsuarioUnicoView(APIView):
    """
    Vista para verificar disponibilidad de usuario único
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Verificar disponibilidad de usuario único",
        description="Verifica si un nombre de usuario está disponible",
        tags=['Usuario'],
        parameters=[
            OpenApiParameter(
                name='usuario_unico',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Nombre de usuario a verificar'
            )
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'disponible': {'type': 'boolean'},
                    'usuario_unico': {'type': 'string'},
                    'mensaje': {'type': 'string'}
                }
            }
        }
    )
    def get(self, request):
        """Verificar disponibilidad de usuario único"""
        usuario_unico = request.query_params.get('usuario_unico', '').strip()
        
        if not usuario_unico:
            return Response({
                'error': 'Parámetro usuario_unico es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar formato
        import re
        if not re.match(r'^[a-zA-Z0-9._]+$', usuario_unico):
            return Response({
                'disponible': False,
                'usuario_unico': usuario_unico,
                'mensaje': 'El nombre de usuario solo puede contener letras, números, puntos y guiones bajos'
            })
        
        # Verificar disponibilidad
        existe = Usuario.objects.filter(usuario_unico=usuario_unico.lower()).exclude(id=request.user.id).exists()
        
        return Response({
            'disponible': not existe,
            'usuario_unico': usuario_unico.lower(),
            'mensaje': 'Disponible' if not existe else 'Ya está en uso'
        })


class DocentesPublicosView(ListAPIView):
    """
    Vista pública para mostrar docentes (para páginas de cursos, etc.)
    """
    serializer_class = DocenteListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Docente.objects.select_related('usuario').filter(
            usuario__activo=True,
            usuario__perfil_completo=True
        ).order_by('usuario__first_name', 'usuario__last_name')

    @extend_schema(
        summary="Listar docentes públicamente",
        description="Obtiene la lista de docentes activos para mostrar públicamente",
        tags=['Público'],
        responses={200: DocenteListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """Listar docentes públicamente"""
        return super().get(request, *args, **kwargs)


class DocentePublicoDetailView(RetrieveAPIView):
    """
    Vista pública para ver detalles de un docente específico
    """
    queryset = Docente.objects.select_related('usuario').filter(
        usuario__activo=True,
        usuario__perfil_completo=True
    )
    serializer_class = DocenteDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'

    @extend_schema(
        summary="Obtener detalles públicos del docente",
        description="Obtiene información pública de un docente específico",
        responses={200: DocenteDetailSerializer},
        tags=['Público']
    )
    def get(self, request, *args, **kwargs):
        """Obtener detalles públicos del docente"""
        return super().get(request, *args, **kwargs)


class VerificarEmailExistenteView(APIView):
    """
    Vista para verificar si un email ya está registrado
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Verificar si email existe",
        description="Verifica si un email ya está registrado en el sistema",
        tags=['Utilidades'],
        parameters=[
            OpenApiParameter(
                name='email',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Email a verificar'
            )
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'existe': {'type': 'boolean'},
                    'email': {'type': 'string'},
                    'message': {'type': 'string'}
                }
            }
        }
    )
    def get(self, request):
        """Verificar si un email ya está registrado"""
        email = request.query_params.get('email', '').strip().lower()
        
        if not email:
            return Response({
                'error': 'Parámetro email es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si el email existe
        existe = Usuario.objects.filter(email=email).exists()
        
        return Response({
            'existe': existe,
            'email': email,
            'message': 'Email encontrado' if existe else 'Email disponible'
        })