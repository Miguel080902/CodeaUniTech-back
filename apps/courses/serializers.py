"""
Ejemplo de cómo corregir los serializers con type hints
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import Categoria, Curso, Leccion, Modulo
from apps.users.models import Docente


class CategoriaSerializer(serializers.ModelSerializer):
    # Corregir este método
    @extend_schema_field(OpenApiTypes.INT)
    def get_total_cursos(self, obj) -> int:
        """Obtiene el total de cursos activos en esta categoría"""
        return obj.cursos.filter(activo=True).count()
    
    total_cursos = serializers.SerializerMethodField()
    
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'color_hex', 'total_cursos']


class LeccionSerializer(serializers.ModelSerializer):
    @extend_schema_field(OpenApiTypes.INT)
    def duracion_total_segundos(self, obj) -> int:
        """Duración total en segundos"""
        return (obj.duracion_minutos or 0) * 60
    
    duracion_total_segundos = serializers.SerializerMethodField()
    
    class Meta:
        model = Leccion
        fields = ['id', 'titulo', 'contenido', 'tipo_contenido', 'video_url', 
                 'duracion_minutos', 'duracion_total_segundos', 'orden', 'activa']


class ModuloSerializer(serializers.ModelSerializer):
    @extend_schema_field(OpenApiTypes.INT)
    def total_lecciones(self, obj) -> int:
        """Total de lecciones activas en este módulo"""
        return obj.lecciones.filter(activa=True).count()
    
    total_lecciones = serializers.SerializerMethodField()
    lecciones = LeccionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Modulo
        fields = ['id', 'titulo', 'descripcion', 'orden', 'total_lecciones', 'lecciones']


class ModuloSimpleSerializer(serializers.ModelSerializer):
    @extend_schema_field(OpenApiTypes.INT)
    def total_lecciones(self, obj) -> int:
        """Total de lecciones activas en este módulo"""
        return obj.lecciones.filter(activa=True).count()
    
    total_lecciones = serializers.SerializerMethodField()
    
    class Meta:
        model = Modulo
        fields = ['id', 'titulo', 'descripcion', 'orden', 'total_lecciones']


class CursoListSerializer(serializers.ModelSerializer):
    """Serializer para listar cursos - ACTUALIZADO"""
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_docente_info(self, obj):
        """Información básica del docente"""
        return {
            'id': obj.docente_principal.id,
            'nombre_completo': obj.docente_principal.nombre_completo,
            'especialidad': obj.docente_principal.especialidad,
            'avatar_url': obj.docente_principal.avatar_url
        }
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_total_modulos(self, obj):
        return obj.total_modulos
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_total_lecciones(self, obj):
        return obj.total_lecciones
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_total_estudiantes(self, obj):
        return obj.total_estudiantes
    
    docente_info = serializers.SerializerMethodField()
    total_modulos = serializers.SerializerMethodField()
    total_lecciones = serializers.SerializerMethodField()
    total_estudiantes = serializers.SerializerMethodField()
    
    class Meta:
        model = Curso
        fields = ['uuid', 'titulo', 'descripcion_corta', 'precio', 'es_gratuito',
                 'imagen_portada', 'nivel', 'valoracion_promedio', 'destacado',
                 'docente_info', 'total_modulos', 'total_lecciones', 'total_estudiantes']


class CursoDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para cursos - ACTUALIZADO"""
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_docente_completo(self, obj):
        """Información completa del docente principal"""
        docente = obj.docente_principal
        return {
            'id': docente.id,
            'nombre_completo': docente.nombre_completo,
            'email': docente.email,
            'avatar_url': docente.avatar_url,
            'especialidad': docente.especialidad,
            'titulo_profesional': docente.titulo_profesional,
            'biografia_extendida': docente.biografia_extendida,
            'experiencia_anos': docente.experiencia_anos,
            'certificaciones': docente.certificaciones,
            'redes_completas': docente.get_redes_completas(),
            'usuario_unico': docente.usuario.usuario_unico,
            'pais': docente.usuario.pais
        }
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_total_modulos(self, obj):
        return obj.total_modulos
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_total_lecciones(self, obj):
        return obj.total_lecciones
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_total_estudiantes(self, obj):
        return obj.total_estudiantes
    
    docente_completo = serializers.SerializerMethodField()
    total_modulos = serializers.SerializerMethodField()
    total_lecciones = serializers.SerializerMethodField()
    total_estudiantes = serializers.SerializerMethodField()
    modulos = ModuloSerializer(many=True, read_only=True)
    
    class Meta:
        model = Curso
        fields = ['uuid', 'titulo', 'descripcion', 'descripcion_corta', 'precio',
                 'es_gratuito', 'imagen_portada', 'video_intro_url', 'nivel',
                 'valoracion_promedio', 'destacado', 'docente_completo',
                 'total_modulos', 'total_lecciones', 'total_estudiantes', 'modulos']

class EstadisticasCursoSerializer(serializers.Serializer):
    """Serializer para estadísticas del curso"""
    total_estudiantes = serializers.IntegerField()
    total_modulos = serializers.IntegerField()
    total_lecciones = serializers.IntegerField()
    valoracion_promedio = serializers.DecimalField(max_digits=3, decimal_places=2)
    porcentaje_completado_promedio = serializers.DecimalField(max_digits=5, decimal_places=2)
    estudiantes_activos = serializers.IntegerField()
    estudiantes_completaron = serializers.IntegerField()

# Si tienes un CursoCreateSerializer, asegúrate de que esté bien definido
class CursoCreateSerializer(serializers.ModelSerializer):
    """Serializer específico para crear cursos - ACTUALIZADO"""
    docente_principal = serializers.PrimaryKeyRelatedField(
        queryset=Docente.objects.select_related('usuario').filter(
            usuario__activo=True,
            usuario__perfil_completo=True
        ),
        help_text="ID del docente que será responsable del curso"
    )
    
    class Meta:
        model = Curso
        fields = ['titulo', 'descripcion', 'descripcion_corta', 'categoria',
                 'docente_principal', 'precio', 'es_gratuito', 'nivel', 
                 'imagen_portada', 'video_intro_url', 'destacado']

    def validate_docente_principal(self, value):
        """Validar que el docente esté activo y tenga perfil completo"""
        if not value.usuario.activo:
            raise serializers.ValidationError("El docente seleccionado no está activo")
        
        if not value.usuario.perfil_completo:
            raise serializers.ValidationError("El docente debe tener su perfil completo")
        
        if not value.perfil_docente_completo:
            raise serializers.ValidationError("El docente debe tener su perfil profesional completo")
        
        return value


class LeccionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear lecciones dentro de módulos"""
    class Meta:
        model = Leccion
        fields = ['titulo', 'contenido', 'tipo_contenido', 'video_url', 
                 'duracion_minutos', 'duracion_segundos', 'orden', 'es_gratuita']


class ModuloCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear módulos con lecciones"""
    lecciones = LeccionCreateSerializer(many=True)
    
    class Meta:
        model = Modulo
        fields = ['titulo', 'descripcion', 'orden', 'lecciones']


class CursoCompletoCreateSerializer(serializers.Serializer):
    """Serializer para crear curso completo con módulos y lecciones"""
    curso = CursoCreateSerializer()
    modulos = ModuloCreateSerializer(many=True)


class CursoCompletoUpdateSerializer(serializers.Serializer):
    """Serializer para actualizar curso completo"""
    curso = CursoCreateSerializer(required=False)
    modulos = ModuloCreateSerializer(many=True, required=False)