"""
Modelos base comunes para toda la aplicación
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """
    Modelo abstracto que proporciona campos de timestamping automático
    """
    fecha_creacion = models.DateTimeField(
        _('Fecha de creación'),
        auto_now_add=True,
        help_text=_('Fecha y hora en que se creó el registro')
    )
    fecha_actualizacion = models.DateTimeField(
        _('Fecha de actualización'),
        auto_now=True,
        help_text=_('Fecha y hora de la última actualización del registro')
    )

    class Meta:
        abstract = True
        ordering = ['-fecha_creacion']


class ActivableModel(TimeStampedModel):
    """
    Modelo abstracto que añade funcionalidad de activación/desactivación
    """
    activo = models.BooleanField(
        _('Activo'),
        default=True,
        help_text=_('Indica si el registro está activo')
    )

    class Meta:
        abstract = True

    def activar(self):
        """Activa el registro"""
        self.activo = True
        self.save(update_fields=['activo'])

    def desactivar(self):
        """Desactiva el registro"""
        self.activo = False
        self.save(update_fields=['activo'])


class OrderableModel(models.Model):
    """
    Modelo abstracto que proporciona funcionalidad de ordenamiento
    """
    orden = models.PositiveIntegerField(
        _('Orden'),
        default=0,
        help_text=_('Orden de visualización')
    )

    class Meta:
        abstract = True
        ordering = ['orden', 'id']


class SlugModel(models.Model):
    """
    Modelo abstracto que proporciona funcionalidad de slug
    """
    slug = models.SlugField(
        _('Slug'),
        max_length=255,
        unique=True,
        help_text=_('Identificador único para URLs amigables')
    )

    class Meta:
        abstract = True