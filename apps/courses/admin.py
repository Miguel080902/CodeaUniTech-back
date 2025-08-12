"""
Configuración del admin para el módulo de cursos - Versión simplificada
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Curso, Modulo, Leccion


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Admin para Categoria"""
    list_display = ['nombre', 'descripcion_corta', 'total_cursos', 'activa', 'fecha_creacion']
    list_filter = ['activa', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']

    def descripcion_corta(self, obj):
        """Descripción truncada"""
        if obj.descripcion:
            return obj.descripcion[:50] + "..." if len(obj.descripcion) > 50 else obj.descripcion
        return "-"
    descripcion_corta.short_description = 'Descripción'

    def total_cursos(self, obj):
        """Número total de cursos"""
        return obj.cursos.filter(activo=True).count()
    total_cursos.short_description = 'Cursos activos'


class ModuloInline(admin.TabularInline):
    """Inline para módulos en curso"""
    model = Modulo
    extra = 0
    fields = ['titulo', 'orden', 'duracion_minutos', 'activo']
    ordering = ['orden']


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    """Admin para Curso"""
    list_display = [
        'titulo', 'categoria', 'docente_nombre', 'modalidad', 'nivel',
        'precio_display', 'es_gratuito', 'destacado', 'total_estudiantes_display',
        'activo', 'fecha_creacion'
    ]
    list_filter = [
        'categoria', 'modalidad', 'nivel', 'es_gratuito', 'destacado',
        'activo', 'fecha_creacion'
    ]
    search_fields = ['titulo', 'descripcion', 'docente_principal__first_name']
    ordering = ['-destacado', '-fecha_creacion']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion', 'total_modulos', 'total_lecciones']
    
    # Inlines
    inlines = [ModuloInline]

    fieldsets = (
        ('Información básica', {
            'fields': ('titulo', 'descripcion', 'descripcion_corta')
        }),
        ('Clasificación', {
            'fields': ('categoria', 'modalidad', 'nivel')
        }),
        ('Docente', {
            'fields': ('docente_principal',)
        }),
        ('Multimedia', {
            'fields': ('imagen_portada', 'video_intro_url')
        }),
        ('Duración', {
            'fields': ('duracion_horas',)
        }),
        ('Precios', {
            'fields': ('precio', 'es_gratuito')
        }),
        ('Configuración', {
            'fields': ('destacado', 'activo', 'valoracion_promedio')
        }),
        ('Estadísticas', {
            'fields': ('total_modulos', 'total_lecciones'),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('uuid', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related(
            'categoria', 'docente_principal'
        ).prefetch_related('modulos')

    def docente_nombre(self, obj):
        """Nombre del docente principal"""
        if obj.docente_principal:
            return obj.docente_principal.get_full_name()
        return "-"
    docente_nombre.short_description = 'Docente'
    docente_nombre.admin_order_field = 'docente_principal__first_name'

    def precio_display(self, obj):
        """Mostrar precio formateado"""
        if obj.es_gratuito:
            return format_html('<span style="color: green; font-weight: bold;">GRATIS</span>')
        return f"${obj.precio}"
    precio_display.short_description = 'Precio'
    precio_display.admin_order_field = 'precio'

    def total_estudiantes_display(self, obj):
        """Número de estudiantes"""
        return obj.total_estudiantes
    total_estudiantes_display.short_description = 'Estudiantes'

    # Acciones personalizadas
    @admin.action(description='Marcar como destacados')
    def marcar_destacados(self, request, queryset):
        """Marcar cursos como destacados"""
        count = queryset.update(destacado=True)
        self.message_user(request, f'{count} curso(s) marcado(s) como destacado(s).')

    @admin.action(description='Quitar destacado')
    def quitar_destacados(self, request, queryset):
        """Quitar destacado de cursos"""
        count = queryset.update(destacado=False)
        self.message_user(request, f'{count} curso(s) sin destacado.')

    actions = [marcar_destacados, quitar_destacados]


class LeccionInline(admin.TabularInline):
    """Inline para lecciones en módulo"""
    model = Leccion
    extra = 0
    fields = ['titulo', 'tipo_contenido', 'duracion_minutos', 'es_gratuita', 'orden', 'activa']
    ordering = ['orden']


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    """Admin para Modulo"""
    list_display = ['titulo', 'curso', 'orden', 'total_lecciones_display', 'duracion_minutos', 'activo']
    list_filter = ['curso__categoria', 'activo', 'fecha_creacion']
    search_fields = ['titulo', 'descripcion', 'curso__titulo']
    ordering = ['curso', 'orden']
    
    # Inlines
    inlines = [LeccionInline]

    fieldsets = (
        ('Información básica', {
            'fields': ('curso', 'titulo', 'descripcion')
        }),
        ('Configuración', {
            'fields': ('orden', 'duracion_minutos', 'expandible', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']

    def total_lecciones_display(self, obj):
        """Número de lecciones"""
        return obj.total_lecciones
    total_lecciones_display.short_description = 'Lecciones'


@admin.register(Leccion)
class LeccionAdmin(admin.ModelAdmin):
    """Admin para Leccion"""
    list_display = [
        'titulo', 'modulo', 'tipo_contenido', 'duracion_display',
        'es_gratuita', 'orden', 'activa'
    ]
    list_filter = [
        'modulo__curso__categoria', 'tipo_contenido', 'es_gratuita',
        'activa', 'fecha_creacion'
    ]
    search_fields = ['titulo', 'contenido', 'modulo__titulo', 'modulo__curso__titulo']
    ordering = ['modulo', 'orden']

    fieldsets = (
        ('Información básica', {
            'fields': ('modulo', 'titulo', 'contenido')
        }),
        ('Tipo y multimedia', {
            'fields': ('tipo_contenido', 'video_url')
        }),
        ('Duración', {
            'fields': ('duracion_minutos', 'duracion_segundos')
        }),
        ('Configuración', {
            'fields': ('orden', 'es_gratuita', 'activa')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']

    def duracion_display(self, obj):
        """Mostrar duración formateada"""
        total_segundos = obj.duracion_total_segundos
        if total_segundos:
            minutos = total_segundos // 60
            segundos = total_segundos % 60
            return f"{minutos}:{segundos:02d}"
        return "-"
    duracion_display.short_description = 'Duración'