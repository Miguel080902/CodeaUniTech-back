from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import Usuario, Docente
from datetime import date


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer base para el modelo Usuario
    """
    @extend_schema_field(OpenApiTypes.STR)
    def get_nombre_completo(self, obj):
        """Obtiene el nombre completo del usuario"""
        return obj.get_full_name()
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_redes_sociales(self, obj):
        """Obtiene las redes sociales del usuario"""
        return obj.get_redes_sociales()
    
    nombre_completo = serializers.SerializerMethodField()
    redes_sociales = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'uuid', 'email', 'username', 'first_name', 'last_name',
            'nombre_completo', 'usuario_unico', 'tipo_usuario', 'edad',
            'fecha_nacimiento', 'pais', 'avatar_url', 'portada_url',
            'biografia', 'telefono', 'redes_sociales', 'perfil_completo',
            'activo', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'id', 'uuid', 'username', 'edad', 'perfil_completo',
            'activo', 'fecha_creacion', 'fecha_actualizacion'
        ]


class UsuarioSimpleSerializer(serializers.ModelSerializer):
    """
    Serializer simple para el modelo Usuario (para listas)
    """
    @extend_schema_field(OpenApiTypes.STR)
    def get_nombre_completo(self, obj):
        return obj.get_full_name()
    
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'uuid', 'email', 'first_name', 'last_name', 
            'nombre_completo', 'usuario_unico', 'tipo_usuario',
            'avatar_url', 'activo'
        ]


class DocenteSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Docente (información específica)
    """
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_redes_completas(self, obj):
        """Obtiene todas las redes sociales incluyendo GitHub"""
        return obj.get_redes_completas()
    
    redes_completas = serializers.SerializerMethodField()
    
    class Meta:
        model = Docente
        fields = [
            'id', 'titulo_profesional', 'especialidad', 'biografia_extendida',
            'experiencia_anos', 'certificaciones', 'github_url', 
            'redes_completas', 'perfil_docente_completo',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'perfil_docente_completo', 'fecha_creacion', 'fecha_actualizacion']


class DocenteDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para docentes (incluye información del usuario)
    """
    usuario = UsuarioSerializer(read_only=True)
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_redes_completas(self, obj):
        return obj.get_redes_completas()
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_nombre_completo(self, obj):
        return obj.nombre_completo
    
    redes_completas = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    email = serializers.CharField(source='usuario.email', read_only=True)
    avatar_url = serializers.URLField(source='usuario.avatar_url', read_only=True)
    
    class Meta:
        model = Docente
        fields = [
            'id', 'usuario', 'nombre_completo', 'email', 'avatar_url',
            'titulo_profesional', 'especialidad', 'biografia_extendida',
            'experiencia_anos', 'certificaciones', 'github_url',
            'redes_completas', 'perfil_docente_completo',
            'fecha_creacion', 'fecha_actualizacion'
        ]


class DocenteListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar docentes (información básica para selección)
    """
    @extend_schema_field(OpenApiTypes.STR)
    def get_nombre_completo(self, obj):
        return obj.nombre_completo
    
    nombre_completo = serializers.SerializerMethodField()
    email = serializers.CharField(source='usuario.email', read_only=True)
    avatar_url = serializers.URLField(source='usuario.avatar_url', read_only=True)
    activo = serializers.BooleanField(source='usuario.activo', read_only=True)
    
    class Meta:
        model = Docente
        fields = [
            'id', 'nombre_completo', 'email', 'avatar_url', 'especialidad',
            'experiencia_anos', 'activo'
        ]


class DocenteCreateSerializer(serializers.Serializer):
    """
    Serializer para crear docentes (crea Usuario + Docente)
    """
    # Datos del usuario
    email = serializers.EmailField(help_text="Email del docente")
    username = serializers.CharField(max_length=150, help_text="Nombre de usuario")
    first_name = serializers.CharField(max_length=150, help_text="Nombre")
    last_name = serializers.CharField(max_length=150, help_text="Apellido")
    fecha_nacimiento = serializers.DateField(help_text="Fecha de nacimiento")
    pais = serializers.CharField(max_length=100, help_text="País de residencia")
    password = serializers.CharField(write_only=True, min_length=8, help_text="Contraseña")
    confirm_password = serializers.CharField(write_only=True, help_text="Confirmar contraseña")
    
    # Datos opcionales del usuario
    avatar_url = serializers.URLField(required=False, help_text="URL del avatar (opcional)")
    biografia = serializers.CharField(required=False, help_text="Biografía básica (opcional)")
    telefono = serializers.CharField(required=False, help_text="Teléfono (opcional)")
    linkedin_url = serializers.URLField(required=False, help_text="LinkedIn (opcional)")
    
    # Datos obligatorios del docente
    especialidad = serializers.CharField(max_length=200, help_text="Especialidad (obligatorio)")
    biografia_extendida = serializers.CharField(help_text="Biografía profesional (obligatorio)")
    experiencia_anos = serializers.IntegerField(min_value=0, max_value=60, help_text="Años de experiencia (obligatorio)")
    
    # Datos opcionales del docente
    titulo_profesional = serializers.CharField(max_length=200, required=False, help_text="Título profesional (opcional)")
    certificaciones = serializers.CharField(required=False, help_text="Certificaciones (opcional)")
    github_url = serializers.URLField(required=False, help_text="GitHub URL (opcional)")

    def validate_email(self, value):
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        return value.lower()

    def validate_username(self, value):
        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        return value.lower()

    def validate_fecha_nacimiento(self, value):
        if value > date.today():
            raise serializers.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        
        # Calcular edad mínima
        today = date.today()
        edad = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        
        if edad < 18:
            raise serializers.ValidationError("Los docentes deben tener al menos 18 años.")
        
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })

        password = attrs.get('password')
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                raise serializers.ValidationError({'password': e.messages})

        attrs.pop('confirm_password', None)
        return attrs

    def create(self, validated_data):
        from django.db import transaction
        
        # Separar datos del usuario y del docente
        datos_docente = {
            'especialidad': validated_data.pop('especialidad'),
            'biografia_extendida': validated_data.pop('biografia_extendida'),
            'experiencia_anos': validated_data.pop('experiencia_anos'),
            'titulo_profesional': validated_data.pop('titulo_profesional', None),
            'certificaciones': validated_data.pop('certificaciones', None),
            'github_url': validated_data.pop('github_url', None),
        }
        
        password = validated_data.pop('password')
        
        with transaction.atomic():
            # Crear usuario
            validated_data['tipo_usuario'] = 'docente'
            validated_data['perfil_completo'] = True
            validated_data['usuario_unico'] = validated_data['username']
            
            usuario = Usuario(**validated_data)
            usuario.set_password(password)
            usuario.save()
            
            # Crear docente
            docente = Docente.objects.create(
                usuario=usuario,
                **datos_docente
            )
            
            return docente


class DocenteUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar información específica del docente
    """
    class Meta:
        model = Docente
        fields = [
            'titulo_profesional', 'especialidad', 'biografia_extendida',
            'experiencia_anos', 'certificaciones', 'github_url'
        ]

    def validate_experiencia_anos(self, value):
        if value < 0 or value > 60:
            raise serializers.ValidationError("Los años de experiencia deben estar entre 0 y 60.")
        return value


class RegistroInicialSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro inicial (PASO 1)
    Solo email y password
    """
    password = serializers.CharField(
        write_only=True, 
        min_length=8,
        help_text="Mínimo 8 caracteres"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Debe coincidir con la contraseña"
    )

    class Meta:
        model = Usuario
        fields = ['email', 'password', 'confirm_password']
        extra_kwargs = {
            'email': {
                'required': True,
                'help_text': 'Email válido para la cuenta'
            }
        }

    def validate_email(self, value):
        """Validar que el email sea único"""
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        return value.lower()

    def validate(self, attrs):
        """Validaciones generales"""
        # Validar que las contraseñas coincidan
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })

        # Validar fortaleza de la contraseña
        password = attrs.get('password')
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                raise serializers.ValidationError({'password': e.messages})

        # Remover confirm_password
        attrs.pop('confirm_password', None)
        return attrs

    def create(self, validated_data):
        """Crear usuario con registro inicial"""
        password = validated_data.pop('password')
        
        # Crear username temporal basado en email
        email = validated_data['email']
        username = email.split('@')[0].lower()
        
        # Asegurar que el username sea único
        counter = 1
        original_username = username
        while Usuario.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        usuario = Usuario(
            username=username,
            perfil_completo=False,  # Importante: perfil no está completo
            **validated_data
        )
        usuario.set_password(password)
        usuario.save()
        return usuario


class CompletarPerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para completar el perfil (PASO 2)
    """
    usuario_unico_sugerido = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            # Campos obligatorios
            'first_name', 'last_name', 'fecha_nacimiento', 'usuario_unico', 'pais',
            # Campos opcionales
            'avatar_url', 'portada_url', 'biografia', 'telefono',
            'facebook_url', 'linkedin_url', 'instagram_url',
            # Campo de ayuda
            'usuario_unico_sugerido'
        ]
        extra_kwargs = {
            'first_name': {
                'required': True,
                'help_text': 'Nombre del usuario (obligatorio)'
            },
            'last_name': {
                'required': True,
                'help_text': 'Apellido del usuario (obligatorio)'
            },
            'fecha_nacimiento': {
                'required': True,
                'help_text': 'Fecha de nacimiento (obligatorio)'
            },
            'usuario_unico': {
                'required': True,
                'help_text': 'Nombre de usuario único (obligatorio)'
            },
            'pais': {
                'required': True,
                'help_text': 'País de residencia (obligatorio)'
            },
            'avatar_url': {
                'help_text': 'URL del avatar (opcional)'
            },
            'portada_url': {
                'help_text': 'URL de la portada (opcional)'
            }
        }

    @extend_schema_field(OpenApiTypes.STR)
    def get_usuario_unico_sugerido(self, obj):
        """Genera una sugerencia de usuario único"""
        if obj.first_name and obj.last_name:
            return obj.generar_usuario_unico()
        return None

    def validate_usuario_unico(self, value):
        """Validar que el usuario_unico sea único"""
        if Usuario.objects.filter(usuario_unico=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        
        # Validar formato básico
        import re
        if not re.match(r'^[a-zA-Z0-9._]+$', value):
            raise serializers.ValidationError("El nombre de usuario solo puede contener letras, números, puntos y guiones bajos.")
        
        return value.lower()

    def validate_fecha_nacimiento(self, value):
        """Validar fecha de nacimiento"""
        if value > date.today():
            raise serializers.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        
        # Calcular edad mínima (13 años)
        today = date.today()
        edad = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        
        if edad < 13:
            raise serializers.ValidationError("Debes tener al menos 13 años para registrarte.")
        
        return value

    def validate(self, attrs):
        """Validaciones adicionales"""
        # Verificar que el usuario no tenga el perfil ya completo
        if self.instance and self.instance.perfil_completo:
            raise serializers.ValidationError("El perfil ya está completo.")
        
        return attrs

    def update(self, instance, validated_data):
        """Actualizar el perfil del usuario"""
        # Actualizar campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Guardar (esto activará verificar_perfil_completo en el save del modelo)
        instance.save()
        return instance


class CustomTokenObtainPairSerializer(serializers.Serializer):
    """
    Serializer personalizado para login con email
    """
    email = serializers.EmailField(help_text="Email de la cuenta")
    password = serializers.CharField(help_text="Contraseña de la cuenta")

    def validate(self, attrs):
        """Validar credenciales"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError('Email y contraseña son requeridos.')

        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError('Credenciales inválidas.')

        if not user.check_password(password):
            raise serializers.ValidationError('Credenciales inválidas.')

        if not user.is_active or not user.activo:
            raise serializers.ValidationError('Esta cuenta está desactivada.')

        attrs['user'] = user
        return attrs


class PerfilUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar el perfil (solo campos editables)
    """
    class Meta:
        model = Usuario
        fields = [
            'first_name', 'last_name', 'fecha_nacimiento', 'pais',
            'avatar_url', 'portada_url', 'biografia', 'telefono',
            'facebook_url', 'linkedin_url', 'instagram_url'
        ]

    def validate_fecha_nacimiento(self, value):
        if value > date.today():
            raise serializers.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        return value