from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import os

def user_profile_picture_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/users/<id>/<filename>
    return 'users/{0}/{1}'.format(instance.user.id, filename)

class UserProfile(models.Model):
    """
    Perfil extendido para los usuarios del sistema.
    """
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='user_profile',
        verbose_name='usuario'
    )

    profile_picture = models.ImageField(
        upload_to=user_profile_picture_path,
        null=True,
        blank=True,
        verbose_name='foto de perfil'
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='teléfono'
    )

    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='dirección'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='fecha de creación'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='última actualización'
    )

    class Meta:
        verbose_name = 'perfil de usuario'
        verbose_name_plural = 'perfiles de usuario'

    def __str__(self):
        return f'Perfil de {self.user.username}'

# Señal para crear automáticamente un perfil cuando se crea un usuario
@receiver(post_save, sender='users.User')
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Señal para guardar el perfil cuando se guarda el usuario
@receiver(post_save, sender='users.User')
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'user_profile'):
        instance.user_profile.save()

class User(AbstractUser):
    """
    Modelo de usuario personalizado para el sistema SIGAA.

    Extiende el modelo AbstractUser de Django agregando un campo de rol
    para controlar permisos y accesos específicos del sistema.

    Los roles disponibles determinan qué funcionalidades puede acceder
    cada usuario dentro del sistema de gestión de afiliados y sueldos.
    """

    # Definición de roles del sistema
    ROLES = [
        ('admin', 'Administrador'),
        ('analista', 'Analista'),
        ('consultor', 'Consultor'),
    ]

    rol = models.CharField(
        max_length=50,
        choices=ROLES,
        default='analista',
        help_text="Rol del usuario que determina sus permisos en el sistema"
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['username']

    def __str__(self):
        """
        Representación en cadena del usuario.

        Returns:
            str: Nombre de usuario y rol
        """
        return f"{self.username} ({self.get_rol_display()})"

    def is_admin(self):
        """
        Verifica si el usuario tiene rol de administrador.

        Returns:
            bool: True si el usuario es administrador
        """
        return self.rol == 'admin'

    @property
    def profile(self):
        """
        Obtiene o crea un perfil de usuario.
        """
        from .models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=self)
        return profile

    def is_analista(self):
        """
        Verifica si el usuario tiene rol de analista.

        Returns:
            bool: True si el usuario es analista
        """
        return self.rol == 'analista'

    def is_consultor(self):
        """
        Verifica si el usuario tiene rol de consultor.

        Returns:
            bool: True si el usuario es consultor
        """
        return self.rol == 'consultor'

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para establecer automáticamente is_staff
        para usuarios con rol de administrador.
        """
        # Si el usuario tiene rol de admin, automáticamente debe ser staff
        if self.rol == 'admin':
            self.is_staff = True

        super().save(*args, **kwargs)
