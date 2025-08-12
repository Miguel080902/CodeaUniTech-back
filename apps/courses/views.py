"""
Vistas corregidas para el módulo de cursos
"""
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_field, OpenApiExample
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from apps.users.models import Docente
from apps.users.serializers import DocenteListSerializer
from .filters import CursoFilter

from .models import Categoria, Curso, Modulo, Leccion
from .serializers import (
    CategoriaSerializer, CursoListSerializer, CursoDetailSerializer,
    CursoCreateSerializer, ModuloSerializer, ModuloSimpleSerializer,
    LeccionSerializer, EstadisticasCursoSerializer, CursoCompletoCreateSerializer,
    CursoCompletoUpdateSerializer
)


class CategoriaViewSet(ModelViewSet):
    """ViewSet para gestión de categorías"""
    queryset = Categoria.objects.filter(activa=True)
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['nombre']

    def get_permissions(self):
        """Permisos personalizados según la acción"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Listar categorías",
        description="Obtiene la lista de todas las categorías activas",
        tags=['Categorías']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Cursos por categoría",
        description="Obtiene todos los cursos de una categoría específica",
        responses={200: CursoListSerializer(many=True)},
        tags=['Categorías']
    )
    @action(detail=True, methods=['get'], url_path='cursos')
    def cursos(self, request, id=None):
        """Obtener cursos de una categoría"""
        categoria = self.get_object()
        cursos = categoria.cursos.filter(activo=True).select_related(
            'categoria', 'docente_principal'
        ).prefetch_related('modulos__lecciones')
        
        serializer = CursoListSerializer(cursos, many=True)
        return Response(serializer.data)


class CursoViewSet(ModelViewSet):
    """ViewSet para gestión de cursos - ACTUALIZADO"""
    queryset = Curso.objects.filter(activo=True).select_related(
        'categoria', 'docente_principal__usuario'
    ).prefetch_related('modulos__lecciones')
    
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'uuid'
    
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend] # type: ignore
    filterset_class = CursoFilter
    search_fields = ['titulo', 'descripcion', 'descripcion_corta', 
                    'docente_principal__usuario__first_name',
                    'docente_principal__usuario__last_name',
                    'docente_principal__especialidad']
    ordering_fields = ['titulo', 'precio', 'fecha_creacion', 'valoracion_promedio']
    ordering = ['-destacado', '-fecha_creacion']

    def get_serializer_class(self):
        """Seleccionar serializer según la acción"""
        if self.action == 'list':
            return CursoListSerializer
        elif self.action == 'create':
            return CursoCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return CursoDetailSerializer
        return CursoDetailSerializer

    def get_permissions(self):
        """Permisos personalizados"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Docentes disponibles para cursos",
        description="Obtiene la lista de docentes disponibles para asignar a cursos",
        responses={200: DocenteListSerializer(many=True)},
        tags=['Cursos']
    )
    @action(detail=False, methods=['get'], url_path='docentes-disponibles',
            permission_classes=[permissions.IsAdminUser])
    def docentes_disponibles(self, request):
        """Obtener docentes disponibles para asignar a cursos"""
        docentes = Docente.objects.select_related('usuario').filter(
            usuario__activo=True,
            usuario__perfil_completo=True
        ).order_by('usuario__first_name', 'usuario__last_name')
        
        serializer = DocenteListSerializer(docentes, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Cursos por docente",
        description="Obtiene todos los cursos de un docente específico",
        responses={200: CursoListSerializer(many=True)},
        tags=['Cursos']
    )
    @action(detail=False, methods=['get'], url_path='por-docente/(?P<docente_id>[^/.]+)')
    def por_docente(self, request, docente_id=None):
        """Obtener cursos por docente"""
        try:
            docente = Docente.objects.get(id=docente_id, usuario__activo=True)
        except Docente.DoesNotExist:
            return Response(
                {'error': 'Docente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        cursos = self.get_queryset().filter(docente_principal=docente)
        serializer = CursoListSerializer(cursos, many=True)
        
        return Response({
            'docente': {
                'id': docente.id,
                'nombre_completo': docente.nombre_completo,
                'especialidad': docente.especialidad,
                'avatar_url': docente.avatar_url
            },
            'total_cursos': cursos.count(),
            'cursos': serializer.data
        })

    @extend_schema(
        summary="Estadísticas del curso",
        description="Obtiene estadísticas detalladas de un curso incluyendo información del docente",
        tags=['Cursos']
    )
    @action(detail=True, methods=['get'], url_path='estadisticas')
    def estadisticas(self, request, uuid=None):
        """Obtener estadísticas del curso"""
        curso = self.get_object()
        
        estadisticas = {
            'curso': {
                'uuid': curso.uuid,
                'titulo': curso.titulo,
                'total_estudiantes': curso.total_estudiantes,
                'total_modulos': curso.total_modulos,
                'total_lecciones': curso.total_lecciones,
                'valoracion_promedio': curso.valoracion_promedio or 0.0,
            },
            'docente': {
                'id': curso.docente_principal.id,
                'nombre_completo': curso.docente_principal.nombre_completo,
                'especialidad': curso.docente_principal.especialidad,
                'experiencia_anos': curso.docente_principal.experiencia_anos,
                'total_cursos': curso.docente_principal.cursos_principal.filter(activo=True).count()
            },
            'metricas': {
                'porcentaje_completado_promedio': 0.0,
                'estudiantes_activos': 0,
                'estudiantes_completaron': 0,
            }
        }
        
        return Response(estadisticas)

    @extend_schema(
        summary="Crear curso completo con módulos y lecciones",
        description="Endpoint para administradores que permite crear un curso con todos sus módulos y lecciones en una sola petición",
        request=CursoCompletoCreateSerializer,
        examples=[
            OpenApiExample(
                "Curso Full Stack",
                summary="Ejemplo de curso completo de desarrollo web",
                description="Ejemplo completo mostrando cómo crear un curso con múltiples módulos y lecciones",
                value={
                    "curso": {
                        "titulo": "Desarrollo Web Full Stack con React y Django",
                        "descripcion": "Aprende a desarrollar aplicaciones web completas desde cero utilizando React para el frontend y Django para el backend. Incluye bases de datos, APIs REST y despliegue.",
                        "descripcion_corta": "Curso completo de desarrollo web moderno con React y Django",
                        "categoria": 1,
                        "docente_principal": 1,
                        "imagen_portada": "https://example.com/curso-fullstack.jpg",
                        "video_intro_url": "https://example.com/intro-video.mp4",
                        "modalidad": "asincrono",
                        "nivel": "intermedio",
                        "precio": 199.99,
                        "es_gratuito": False,
                        "destacado": True
                    },
                    "modulos": [
                        {
                            "titulo": "Fundamentos de React",
                            "descripcion": "Introducción a React, componentes y JSX",
                            "orden": 1,
                            "lecciones": [
                                {
                                    "titulo": "Introducción a React",
                                    "contenido": "En esta lección aprenderemos qué es React y por qué es tan popular",
                                    "tipo_contenido": "video",
                                    "video_url": "https://example.com/leccion1.mp4",
                                    "duracion_minutos": 25,
                                    "orden": 1,
                                    "es_gratuita": True
                                },
                                {
                                    "titulo": "Componentes y Props",
                                    "contenido": "Aprende a crear y usar componentes con props",
                                    "tipo_contenido": "video",
                                    "video_url": "https://example.com/leccion2.mp4",
                                    "duracion_minutos": 30,
                                    "orden": 2,
                                    "es_gratuita": False
                                }
                            ]
                        },
                        {
                            "titulo": "API REST con Django",
                            "descripcion": "Construcción de APIs REST usando Django REST Framework",
                            "orden": 2,
                            "lecciones": [
                                {
                                    "titulo": "Configurando Django REST Framework",
                                    "contenido": "Instalación y configuración inicial de DRF",
                                    "tipo_contenido": "video",
                                    "video_url": "https://example.com/leccion3.mp4",
                                    "duracion_minutos": 20,
                                    "orden": 1,
                                    "es_gratuita": False
                                }
                            ]
                        }
                    ]
                },
                request_only=True
            )
        ],
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'curso': {'$ref': '#/components/schemas/CursoDetail'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'details': {'type': 'object'}
                }
            }
        },
        tags=['Cursos']
    )
    @action(detail=False, methods=['post'], url_path='crear-completo',
            permission_classes=[permissions.IsAdminUser])
    def crear_completo(self, request):
        """Crear curso completo con módulos y lecciones para administradores"""
        from django.db import transaction
        import copy
        
        try:
            with transaction.atomic():
                # Validar estructura de datos
                if 'curso' not in request.data:
                    return Response({
                        'error': 'Falta información del curso'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if 'modulos' not in request.data:
                    return Response({
                        'error': 'Debe incluir al menos un módulo'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                curso_data = copy.deepcopy(request.data['curso'])
                modulos_data = copy.deepcopy(request.data['modulos'])
                
                # 1. Crear el curso
                curso_serializer = CursoCreateSerializer(data=curso_data)
                curso_serializer.is_valid(raise_exception=True)
                curso = curso_serializer.save()
                
                # 2. Crear módulos y lecciones
                modulos_creados = []
                for modulo_data in modulos_data:
                    lecciones_data = modulo_data.pop('lecciones', [])
                    modulo_data['curso'] = curso.id
                    
                    # Crear módulo
                    modulo_serializer = ModuloSerializer(data=modulo_data)
                    modulo_serializer.is_valid(raise_exception=True)
                    modulo = modulo_serializer.save()
                    
                    # Crear lecciones del módulo
                    lecciones_creadas = []
                    for leccion_data in lecciones_data:
                        leccion_data['modulo'] = modulo.id
                        leccion_serializer = LeccionSerializer(data=leccion_data)
                        leccion_serializer.is_valid(raise_exception=True)
                        leccion = leccion_serializer.save()
                        lecciones_creadas.append(leccion)
                    
                    modulos_creados.append({
                        'modulo': modulo,
                        'lecciones': lecciones_creadas
                    })
                
                # 3. Respuesta con curso completo
                curso_completo = Curso.objects.select_related(
                    'categoria', 'docente_principal__usuario'
                ).prefetch_related('modulos__lecciones').get(id=curso.id)
                
                response_serializer = CursoDetailSerializer(curso_completo)
                
                return Response({
                    'message': f'Curso "{curso.titulo}" creado exitosamente con {len(modulos_creados)} módulos',
                    'curso': response_serializer.data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': f'Error creando curso completo: {str(e)}',
                'details': getattr(e, 'detail', None) if hasattr(e, 'detail') else None
            }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Actualizar curso completo con módulos y lecciones",
        description="Endpoint para administradores que permite actualizar un curso completo. IMPORTANTE: Si incluyes 'modulos', reemplazará TODOS los módulos existentes.",
        request=CursoCompletoUpdateSerializer,
        examples=[
            OpenApiExample(
                "Actualizar Curso Full Stack",
                summary="Ejemplo de actualización completa de curso",
                description="Muestra cómo actualizar tanto información del curso como reemplazar todos sus módulos",
                value={
                    "curso": {
                        "titulo": "Desarrollo Web Full Stack con React y Django - Actualizado",
                        "descripcion": "Versión actualizada del curso con nuevos contenidos y React 18",
                        "precio": 249.99,
                        "destacado": True
                    },
                    "modulos": [
                        {
                            "titulo": "Fundamentos de React 18",
                            "descripcion": "Nueva versión del módulo con React 18 y sus features",
                            "orden": 1,
                            "lecciones": [
                                {
                                    "titulo": "Introducción a React 18",
                                    "contenido": "Nuevas características de React 18: Concurrent Features, Automatic Batching, etc.",
                                    "tipo_contenido": "video",
                                    "video_url": "https://example.com/react18-intro.mp4",
                                    "duracion_minutos": 35,
                                    "orden": 1,
                                    "es_gratuita": True
                                },
                                {
                                    "titulo": "Suspense y Concurrent Features",
                                    "contenido": "Profundizamos en las nuevas características concurrentes",
                                    "tipo_contenido": "video",
                                    "video_url": "https://example.com/suspense.mp4",
                                    "duracion_minutos": 40,
                                    "orden": 2,
                                    "es_gratuita": False
                                }
                            ]
                        },
                        {
                            "titulo": "Django REST Framework Avanzado",
                            "descripcion": "Características avanzadas de DRF y mejores prácticas",
                            "orden": 2,
                            "lecciones": [
                                {
                                    "titulo": "Autenticación JWT Avanzada",
                                    "contenido": "Implementación de autenticación JWT con refresh tokens",
                                    "tipo_contenido": "video",
                                    "video_url": "https://example.com/jwt-advanced.mp4",
                                    "duracion_minutos": 45,
                                    "orden": 1,
                                    "es_gratuita": False
                                }
                            ]
                        }
                    ]
                },
                request_only=True
            )
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'curso': {'$ref': '#/components/schemas/CursoDetail'}
                }
            }
        },
        tags=['Cursos']
    )
    @action(detail=True, methods=['put', 'patch'], url_path='actualizar-completo',
            permission_classes=[permissions.IsAdminUser])
    def actualizar_completo(self, request, uuid=None):
        """Actualizar curso completo - Solo administradores"""
        from django.db import transaction
        import copy
        
        try:
            with transaction.atomic():
                curso = self.get_object()
                
                # 1. Actualizar datos del curso si se proporcionan
                if 'curso' in request.data:
                    curso_data = copy.deepcopy(request.data['curso'])
                    curso_serializer = CursoCreateSerializer(curso, data=curso_data, partial=True)
                    curso_serializer.is_valid(raise_exception=True)
                    curso = curso_serializer.save()
                
                # 2. Si se proporcionan módulos, reemplazar completamente
                if 'modulos' in request.data:
                    # Eliminar módulos existentes (esto también eliminará lecciones por CASCADE)
                    curso.modulos.all().delete()
                    
                    # Crear nuevos módulos y lecciones
                    modulos_data = copy.deepcopy(request.data['modulos'])
                    for modulo_data in modulos_data:
                        lecciones_data = modulo_data.pop('lecciones', [])
                        modulo_data['curso'] = curso.id
                        
                        # Crear módulo
                        modulo_serializer = ModuloSerializer(data=modulo_data)
                        modulo_serializer.is_valid(raise_exception=True)
                        modulo = modulo_serializer.save()
                        
                        # Crear lecciones del módulo
                        for leccion_data in lecciones_data:
                            leccion_data['modulo'] = modulo.id
                            leccion_serializer = LeccionSerializer(data=leccion_data)
                            leccion_serializer.is_valid(raise_exception=True)
                            leccion_serializer.save()
                
                # 3. Obtener curso actualizado
                curso_actualizado = Curso.objects.select_related(
                    'categoria', 'docente_principal__usuario'
                ).prefetch_related('modulos__lecciones').get(id=curso.id)
                
                response_serializer = CursoDetailSerializer(curso_actualizado)
                
                return Response({
                    'message': f'Curso "{curso.titulo}" actualizado exitosamente',
                    'curso': response_serializer.data
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'error': f'Error actualizando curso: {str(e)}',
                'details': getattr(e, 'detail', None) if hasattr(e, 'detail') else None
            }, status=status.HTTP_400_BAD_REQUEST)


class ModuloViewSet(ModelViewSet):
    """ViewSet para gestión de módulos"""
    queryset = Modulo.objects.filter(activo=True).select_related('curso')
    serializer_class = ModuloSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['orden', 'fecha_creacion']
    ordering = ['curso', 'orden']

    def get_serializer_class(self):
        """Usar serializer simple en lista"""
        if self.action == 'list':
            return ModuloSimpleSerializer
        return ModuloSerializer

    @extend_schema(
        summary="Listar módulos",
        description="Obtiene la lista de módulos",
        tags=['Módulos']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Crear módulo con lecciones",
        description="Crea un módulo y sus lecciones en una sola petición",
        request={
            'type': 'object',
            'properties': {
                'curso': {'type': 'integer'},
                'titulo': {'type': 'string'},
                'descripcion': {'type': 'string'},
                'orden': {'type': 'integer'},
                'lecciones': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'titulo': {'type': 'string'},
                            'contenido': {'type': 'string'},
                            'tipo_contenido': {'type': 'string', 'enum': ['video', 'texto', 'pdf', 'quiz']},
                            'video_url': {'type': 'string', 'format': 'uri'},
                            'duracion_minutos': {'type': 'integer'},
                            'orden': {'type': 'integer'}
                        },
                        'required': ['titulo', 'tipo_contenido', 'orden']
                    }
                }
            },
            'required': ['curso', 'titulo', 'orden']
        },
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'modulo': {'$ref': '#/components/schemas/Modulo'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        tags=['Módulos']
    )
    @action(detail=False, methods=['post'], url_path='crear-con-lecciones')
    def crear_con_lecciones(self, request):
        """Crear módulo con lecciones en una sola petición"""
        from django.db import transaction
        import copy
        
        try:
            with transaction.atomic():
                # 1. Crear una copia de los datos para no modificar el request original
                data = copy.deepcopy(request.data)
                lecciones_data = data.pop('lecciones', [])
                
                # 2. Crear módulo
                modulo_serializer = ModuloSerializer(data=data)
                modulo_serializer.is_valid(raise_exception=True)
                modulo = modulo_serializer.save()
                
                # 3. Crear lecciones
                for leccion_data in lecciones_data:
                    leccion_data['modulo'] = modulo.id
                    leccion_serializer = LeccionSerializer(data=leccion_data)
                    leccion_serializer.is_valid(raise_exception=True)
                    leccion_serializer.save()
                
                # Respuesta con módulo completo
                response_serializer = ModuloSerializer(modulo)
                return Response({
                    'message': 'Módulo con lecciones creado exitosamente',
                    'modulo': response_serializer.data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': f'Error creando módulo: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class LeccionViewSet(ModelViewSet):
    """ViewSet para gestión de lecciones"""
    queryset = Leccion.objects.filter(activa=True).select_related('modulo__curso')
    serializer_class = LeccionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['titulo', 'contenido']
    ordering_fields = ['orden', 'fecha_creacion', 'duracion_minutos']
    ordering = ['modulo', 'orden']

    @extend_schema(
        summary="Listar lecciones",
        description="Obtiene la lista de lecciones",
        tags=['Lecciones']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)