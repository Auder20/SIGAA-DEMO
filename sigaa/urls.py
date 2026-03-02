from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from core import views

app_name = 'sigaa'

# Admin site customization
admin.site.site_header = 'SIGAA - Panel de Administración'
admin.site.site_title = 'SIGAA Admin'
admin.site.index_title = 'Bienvenido al Panel de Administración'

# URLs principales
urlpatterns = [
    # Django Admin (original) - Accessible at /admin/
    path('admin/', admin.site.urls),
    
    # Custom Admin Interface - Main admin dashboard
    path('custom_admin/', include('custom_admin.urls', namespace='custom_admin')),
    
    # Redirect root /admin/ to our custom admin
    path('admin/', RedirectView.as_view(url='/custom_admin/', permanent=False)),
    
    # Página principal
    path('', views.home, name='home'),
    
    # Apps principales
    path('users/', include(('users.urls', 'users'), namespace='users')),
    path('afiliados/', include(('afiliados.urls', 'afiliados'), namespace='afiliados')),
    path('liquidacion/', include(('liquidacion.urls', 'liquidacion'), namespace='liquidacion')),
    path('reportes/', include(('reportes.urls', 'reportes'), namespace='reportes')),
    path('tablas/', include(('tablas.urls', 'tablas'), namespace='tablas')),
    path('core/', include(('core.urls', 'core'), namespace='core')),
]

# Servir archivos estáticos en desarrollo (en producción usar WhiteNoise/Nginx)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
