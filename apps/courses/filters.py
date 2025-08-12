"""
Filtros para el módulo de cursos
"""
import django_filters
from django.db import models
from .models import Curso

class CursoFilter(django_filters.FilterSet):
    """Filtros para cursos - ACTUALIZADO"""
    
    # Filtros por categoría
    categoria = django_filters.NumberFilter(field_name='categoria__id')
    categoria_nombre = django_filters.CharFilter(
        field_name='categoria__nombre',
        lookup_expr='icontains'
    )
    
    # Filtros por precios
    precio_min = django_filters.NumberFilter(field_name='precio', lookup_expr='gte')
    precio_max = django_filters.NumberFilter(field_name='precio', lookup_expr='lte')
    precio_rango = django_filters.RangeFilter(field_name='precio')
    
    # Filtros por duración
    duracion_min = django_filters.NumberFilter(field_name='duracion_horas', lookup_expr='gte')
    duracion_max = django_filters.NumberFilter(field_name='duracion_horas', lookup_expr='lte')
    
    # Filtros por valoración
    valoracion_min = django_filters.NumberFilter(field_name='valoracion_promedio', lookup_expr='gte')
    
    # Filtros por fecha
    fecha_desde = django_filters.DateFilter(field_name='fecha_creacion', lookup_expr='gte')
    fecha_hasta = django_filters.DateFilter(field_name='fecha_creacion', lookup_expr='lte')
    
    # FILTROS ACTUALIZADOS POR DOCENTE
    docente_id = django_filters.NumberFilter(field_name='docente_principal__id')
    docente_nombre = django_filters.CharFilter(
        field_name='docente_principal__usuario__first_name',
        lookup_expr='icontains'
    )
    docente_apellido = django_filters.CharFilter(
        field_name='docente_principal__usuario__last_name',
        lookup_expr='icontains'
    )
    docente_email = django_filters.CharFilter(
        field_name='docente_principal__usuario__email',
        lookup_expr='icontains'
    )
    docente_especialidad = django_filters.CharFilter(
        field_name='docente_principal__especialidad',
        lookup_expr='icontains'
    )
    docente_experiencia_min = django_filters.NumberFilter(
        field_name='docente_principal__experiencia_anos',
        lookup_expr='gte'
    )
    docente_usuario_unico = django_filters.CharFilter(
        field_name='docente_principal__usuario__usuario_unico',
        lookup_expr='icontains'
    )
    
    # Filtro personalizado por nombre completo del docente
    docente_nombre_completo = django_filters.CharFilter(
        method='filter_docente_nombre_completo'
    )
    
    # Filtros combinados
    gratuitos_y_destacados = django_filters.BooleanFilter(
        method='filter_gratuitos_destacados',
        label='Solo cursos gratuitos y destacados'
    )

    class Meta:
        model = Curso
        fields = {
            'titulo': ['icontains'],
            'modalidad': ['exact'],
            'nivel': ['exact'],
            'es_gratuito': ['exact'],
            'destacado': ['exact'],
            'activo': ['exact'],
        }

    def filter_docente_nombre_completo(self, queryset, name, value):
        """Filtro por nombre completo del docente"""
        return queryset.filter(
            models.Q(docente_principal__usuario__first_name__icontains=value) |
            models.Q(docente_principal__usuario__last_name__icontains=value)
        )

    def filter_gratuitos_destacados(self, queryset, name, value):
        """Filtro personalizado para cursos gratuitos y destacados"""
        if value:
            return queryset.filter(es_gratuito=True, destacado=True)
        return queryset

    class Meta:
        model = Curso
        fields = {
            'titulo': ['icontains'],
            'modalidad': ['exact'],
            'nivel': ['exact'],
            'es_gratuito': ['exact'],
            'destacado': ['exact'],
            'activo': ['exact'],
        }

    def filter_gratuitos_destacados(self, queryset, name, value):
        """Filtro personalizado para cursos gratuitos y destacados"""
        if value:
            return queryset.filter(es_gratuito=True, destacado=True)
        return queryset