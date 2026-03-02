from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import password_validation
from django.utils.translation import gettext_lazy as _
from .models import User

class UserRegistrationForm(UserCreationForm):
    """
    Formulario para el registro de nuevos usuarios.
    Incluye validación de contraseña y campos personalizados.
    """
    email = forms.EmailField(
        label=_("Correo electrónico"),
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'})
    )
    
    password1 = forms.CharField(
        label=_("Contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    
    password2 = forms.CharField(
        label=_("Confirmar contraseña"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        strip=False,
        help_text=_("Ingrese la misma contraseña que antes, para verificación."),
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'rol')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario',
                'autocomplete': 'username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com',
                'autocomplete': 'email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres',
                'autocomplete': 'given-name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos',
                'autocomplete': 'family-name'
            }),
            'rol': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si se está editando un usuario, hacer que el campo de contraseña no sea obligatorio
        if self.instance.pk is not None:
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            self.fields['password1'].help_text = _("Dejar en blanco para mantener la contraseña actual.")
            self.fields['password2'].help_text = _("Confirmar nueva contraseña (solo si desea cambiarla).")
    
    def clean_password2(self):
        # Solo validar la contraseña si se está creando un nuevo usuario o cambiando la contraseña
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        
        # Si es una actualización y no se está cambiando la contraseña, omitir validación
        if self.instance.pk and not password1 and not password2:
            return password2
            
        if password1:
            password_validation.validate_password(password1, self.instance)
        
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Establecer la contraseña hasheada
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        
        # Establecer is_active como True por defecto para nuevos usuarios
        if not user.pk:
            user.is_active = True
            
        if commit:
            user.save()
            
            # Crear el perfil de usuario si no existe
            from .models import UserProfile
            if not hasattr(user, 'profile'):
                UserProfile.objects.create(user=user)
                
        return user
