# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from apps.common.models import TimeStampedModel
import uuid


class Usuario(AbstractUser, TimeStampedModel):
    """
    Modelo de usuario personalizado con registro en dos pasos
    """
    # Choices
    TIPO_USUARIO_CHOICES = [
        ('estudiante', 'Estudiante'),
        ('docente', 'Docente'),
        ('admin', 'Administrador'),
    ]

    # PASO 1: Registro inicial (solo email y password)
    # email viene de AbstractUser
    # password viene de AbstractUser
    
    # PASO 2: Completar perfil
    
    # Campos obligatorios en completar perfil
    fecha_nacimiento = models.DateField(
        _('Fecha de nacimiento'),
        null=True,
        blank=True,
        help_text=_('Fecha de nacimiento del usuario (obligatorio en completar perfil)')
    )
    
    edad = models.PositiveIntegerField(
        _('Edad'),
        null=True,
        blank=True,
        validators=[MinValueValidator(13), MaxValueValidator(120)],
        help_text=_('Edad del usuario (se calcula automáticamente)')
    )
    
    usuario_unico = models.CharField(
        _('Usuario único'),
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text=_('Nombre de usuario único (obligatorio en completar perfil)')
    )
    
    pais = models.CharField(
        _('País'),
        max_length=100,
        null=True,
        blank=True,
        help_text=_('País de residencia (obligatorio en completar perfil)')
    )

    # Campos opcionales en completar perfil
    avatar_url = models.URLField(
        _('Avatar URL'),
        max_length=500,
        null=True,
        blank=True,
        help_text=_('URL del avatar del usuario (opcional)')
    )
    
    portada_url = models.URLField(
        _('Portada URL'),
        max_length=500,
        null=True,
        blank=True,
        help_text=_('URL de la imagen de portada del perfil (opcional)')
    )
    
    biografia = models.TextField(
        _('Biografía'),
        null=True,
        blank=True,
        help_text=_('Descripción personal del usuario (opcional)')
    )

    # Redes sociales (opcionales)
    facebook_url = models.URLField(
        _('Facebook URL'),
        max_length=300,
        null=True,
        blank=True,
        help_text=_('URL del perfil de Facebook (opcional)')
    )
    
    linkedin_url = models.URLField(
        _('LinkedIn URL'),
        max_length=300,
        null=True,
        blank=True,
        help_text=_('URL del perfil de LinkedIn (opcional)')
    )
    
    instagram_url = models.URLField(
        _('Instagram URL'),
        max_length=300,
        null=True,
        blank=True,
        help_text=_('URL del perfil de Instagram (opcional)')
    )

    # Campos de sistema
    tipo_usuario = models.CharField(
        _('Tipo de usuario'),
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='estudiante',
        help_text=_('Tipo de usuario en la plataforma')
    )
    
    telefono = models.CharField(
        _('Teléfono'),
        max_length=20,
        null=True,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message=_('Ingrese un número de teléfono válido')
        )],
        help_text=_('Número de teléfono del usuario (opcional)')
    )

    # Estado del perfil
    perfil_completo = models.BooleanField(
        _('Perfil completo'),
        default=False,
        help_text=_('Indica si el usuario completó su perfil')
    )
    
    activo = models.BooleanField(
        _('Activo'),
        default=True,
        help_text=_('Indica si el usuario está activo')
    )

    # UUID para identificación única
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_('Identificador único universal')
    )

    class Meta:
        db_table = 'usuarios'
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def save(self, *args, **kwargs):
        """
        Override del método save para lógica personalizada
        """
        # Calcular edad si hay fecha de nacimiento
        if self.fecha_nacimiento:
            from datetime import date
            today = date.today()
            self.edad = today.year - self.fecha_nacimiento.year - (
                (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )

        # Verificar si el perfil está completo
        self.verificar_perfil_completo()

        super().save(*args, **kwargs)

    def verificar_perfil_completo(self):
        """
        Verifica si el perfil está completo basado en los campos obligatorios
        """
        campos_obligatorios = [
            self.first_name,
            self.last_name,
            self.fecha_nacimiento,
            self.usuario_unico,
            self.pais
        ]
        
        self.perfil_completo = all(campo for campo in campos_obligatorios)

    def get_full_name(self):
        """Retorna el nombre completo del usuario"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

    def generar_usuario_unico(self, base_username=None):
        """
        Genera un usuario_unico disponible
        """
        if not base_username:
            if self.first_name and self.last_name:
                base_username = f"{self.first_name.lower()}.{self.last_name.lower()}"
            else:
                base_username = self.email.split('@')[0].lower()
        
        # Limpiar caracteres especiales
        import re
        base_username = re.sub(r'[^a-z0-9._]', '', base_username)
        
        counter = 1
        unique_username = base_username
        
        while Usuario.objects.filter(usuario_unico=unique_username).exclude(id=self.id).exists():
            unique_username = f"{base_username}{counter}"
            counter += 1
        
        return unique_username

    # Properties para verificar tipo de usuario
    @property
    def es_estudiante(self):
        """Verifica si el usuario es estudiante"""
        return self.tipo_usuario == 'estudiante'

    @property
    def es_docente(self):
        """Verifica si el usuario es docente"""
        return self.tipo_usuario == 'docente'

    @property
    def es_admin(self):
        """Verifica si el usuario es administrador"""
        return self.tipo_usuario == 'admin'

    @property
    def puede_completar_perfil(self):
        """Verifica si el usuario puede completar su perfil"""
        return not self.perfil_completo

    def activar_perfil(self):
        """Activa el perfil del usuario"""
        self.activo = True
        self.save(update_fields=['activo'])

    def desactivar_perfil(self):
        """Desactiva el perfil del usuario"""
        self.activo = False
        self.save(update_fields=['activo'])

    def get_redes_sociales(self):
        """Retorna un diccionario con las redes sociales del usuario"""
        return {
            'facebook': self.facebook_url,
            'linkedin': self.linkedin_url,
            'instagram': self.instagram_url,
        }

    def has_redes_sociales(self):
        """Verifica si el usuario tiene al menos una red social configurada"""
        redes = self.get_redes_sociales()
        return any(redes.values())


class Docente(TimeStampedModel):
    """
    Modelo que extiende la información específica de docentes
    """
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='docente',
        help_text=_('Usuario asociado al docente')
    )
    
    # Campos obligatorios para docentes
    especialidad = models.CharField(
        _('Especialidad'),
        max_length=200,
        help_text=_('Especialidad principal del docente (obligatorio)')
    )
    
    biografia_extendida = models.TextField(
        _('Biografía extendida'),
        help_text=_('Biografía profesional detallada del docente (obligatorio)')
    )
    
    experiencia_anos = models.PositiveIntegerField(
        _('Años de experiencia'),
        validators=[MinValueValidator(0), MaxValueValidator(60)],
        help_text=_('Años de experiencia profesional (obligatorio)')
    )
    
    # Campos opcionales para docentes
    titulo_profesional = models.CharField(
        _('Título profesional'),
        max_length=200,
        null=True,
        blank=True,
        help_text=_('Título profesional o académico principal (opcional)')
    )
    
    certificaciones = models.TextField(
        _('Certificaciones'),
        null=True,
        blank=True,
        help_text=_('Certificaciones y cursos adicionales (opcional)')
    )
    
    github_url = models.URLField(
        _('GitHub URL'),
        max_length=300,
        null=True,
        blank=True,
        help_text=_('URL del perfil de GitHub (opcional)')
    )

    class Meta:
        db_table = 'docentes'
        verbose_name = _('Docente')
        verbose_name_plural = _('Docentes')
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Docente: {self.usuario.get_full_name()} - {self.especialidad}"

    def save(self, *args, **kwargs):
        """Override para validaciones adicionales"""
        # Asegurar que el usuario asociado sea de tipo docente
        if self.usuario.tipo_usuario != 'docente':
            self.usuario.tipo_usuario = 'docente'
            self.usuario.save()
        
        super().save(*args, **kwargs)

    @property
    def perfil_docente_completo(self):
        """Verifica si el perfil específico de docente está completo"""
        campos_obligatorios = [
            self.especialidad,
            self.biografia_extendida,
            self.experiencia_anos is not None
        ]
        return all(campos_obligatorios) and self.usuario.perfil_completo

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del docente"""
        return self.usuario.get_full_name()

    @property
    def email(self):
        """Retorna el email del docente"""
        return self.usuario.email

    @property
    def avatar_url(self):
        """Retorna la URL del avatar del docente"""
        return self.usuario.avatar_url

    def get_redes_completas(self):
        """Retorna todas las redes sociales incluyendo GitHub"""
        redes = self.usuario.get_redes_sociales()
        redes['github'] = self.github_url
        return redes

    def activar(self):
        """Activa el docente y su usuario asociado"""
        self.usuario.activar_perfil()

    def desactivar(self):
        """Desactiva el docente y su usuario asociado"""
        self.usuario.desactivar_perfil()