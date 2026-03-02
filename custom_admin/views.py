from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from afiliados.models import Afiliado
from liquidacion.models import Sueldo, TablaSalarial

def is_staff_user(user):
    """Check if user is a staff member."""
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_staff_user)
def dashboard(request):
    """Custom admin dashboard view."""
    try:
        # Get counts for dashboard cards
        context = {
            'afiliados_count': Afiliado.objects.count(),
            'liquidaciones_count': Sueldo.objects.count(),
            'tablas_count': TablaSalarial.objects.count(),
            'reportes_count': 0,  # Update this if you have a report count
        }
        
        # Get recent admin actions
        context['recent_activity'] = LogEntry.objects.select_related('content_type', 'user').order_by('-action_time')[:10]
        
        return render(request, 'custom_admin/dashboard.html', context)
    except Exception as e:
        print(f"Error in dashboard view: {str(e)}")
        # Return a minimal context if there's an error
        return render(request, 'custom_admin/dashboard.html', {
            'afiliados_count': 0,
            'liquidaciones_count': 0,
            'tablas_count': 0,
            'reportes_count': 0,
            'recent_activity': []
        })

@login_required
@user_passes_test(is_staff_user)
def custom_admin_home(request):
    """Redirect to the custom admin dashboard."""
    return redirect('custom_admin:dashboard')
