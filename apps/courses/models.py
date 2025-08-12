"""
Modelos de cursos - Versión ultra simplificada
"""
from django.db import models
import uuid


class Categoria(models.Model):
    """Categorías para organizar los cursos"""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    color_hex = models.CharField(max_length=7, default='#007bff')
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Curso(models.Model):
    """Modelo principal de Curso - ACTUALIZADO"""
    MODALIDAD_CHOICES = [
        ('asincrono', 'Asíncrono'),
        ('sincrono', 'Síncrono'),
        ('hibrido', 'Híbrido'),
    ]
    
    NIVEL_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    descripcion_corta = models.CharField(max_length=500, null=True, blank=True)
    categoria = models.ForeignKey('Categoria', on_delete=models.CASCADE, related_name='cursos')
    
    # CAMBIO PRINCIPAL: Ahora referencia al modelo Docente
    docente_principal = models.ForeignKey(
        'users.Docente',  # Referencia al modelo Docente
        on_delete=models.CASCADE,
        related_name='cursos_principal',
        help_text='Docente responsable del curso'
    )
    
    imagen_portada = models.URLField(max_length=500, null=True, blank=True)
    video_intro_url = models.URLField(max_length=500, null=True, blank=True)
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES, default='asincrono')
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='principiante')
    duracion_horas = models.PositiveIntegerField(null=True, blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    es_gratuito = models.BooleanField(default=True)
    valoracion_promedio = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    destacado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cursos'
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['-destacado', '-fecha_creacion']

    def __str__(self):
        return self.titulo

    @property
    def total_modulos(self):
        """Número total de módulos"""
        return self.modulos.filter(activo=True).count()

    @property
    def total_lecciones(self):
        """Número total de lecciones"""
        return sum(modulo.lecciones.filter(activa=True).count() for modulo in self.modulos.filter(activo=True))

    @property
    def total_estudiantes(self):
        """Número total de estudiantes inscritos"""
        return 0  # Implementar después

    @property
    def docente_nombre_completo(self):
        """Nombre completo del docente"""
        return self.docente_principal.nombre_completo

    @property
    def docente_email(self):
        """Email del docente"""
        return self.docente_principal.email

    def save(self, *args, **kwargs):
        """Override para lógica personalizada"""
        if self.es_gratuito:
            self.precio = 0.00
        super().save(*args, **kwargs)

class Modulo(models.Model):
    """Módulos que organizan el contenido del curso"""
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='modulos')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    orden = models.PositiveIntegerField(default=0)
    duracion_minutos = models.PositiveIntegerField(null=True, blank=True)
    expandible = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'modulos'
        verbose_name = 'Módulo'
        verbose_name_plural = 'Módulos'
        ordering = ['curso', 'orden']
        unique_together = [['curso', 'orden']]

    def __str__(self):
        return f"{self.curso.titulo} - {self.titulo}"

    @property
    def total_lecciones(self):
        """Número total de lecciones activas"""
        return self.lecciones.filter(activa=True).count()


class Leccion(models.Model):
    """Lecciones individuales dentro de cada módulo"""
    TIPO_CONTENIDO_CHOICES = [
        ('video', 'Video'),
        ('texto', 'Texto'),
        ('quiz', 'Quiz'),
        ('proyecto', 'Proyecto'),
    ]

    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, related_name='lecciones')
    titulo = models.CharField(max_length=200)
    contenido = models.TextField(null=True, blank=True)
    tipo_contenido = models.CharField(max_length=20, choices=TIPO_CONTENIDO_CHOICES, default='video')
    video_url = models.URLField(max_length=500, null=True, blank=True)
    duracion_minutos = models.PositiveIntegerField(null=True, blank=True)
    duracion_segundos = models.PositiveIntegerField(null=True, blank=True)
    orden = models.PositiveIntegerField(default=0)
    es_gratuita = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lecciones'
        verbose_name = 'Lección'
        verbose_name_plural = 'Lecciones'
        ordering = ['modulo', 'orden']
        unique_together = [['modulo', 'orden']]

    def __str__(self):
        return f"{self.modulo.titulo} - {self.titulo}"

    @property
    def duracion_total_segundos(self):
        """Duración total en segundos"""
        minutos = self.duracion_minutos or 0
        segundos = self.duracion_segundos or 0
        return (minutos * 60) + segundos

    def save(self, *args, **kwargs):
        """Override para validaciones"""
        if self.tipo_contenido == 'video' and not self.video_url:
            self.tipo_contenido = 'texto'
        super().save(*args, **kwargs)