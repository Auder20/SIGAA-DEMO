

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView
from .models import User
from .forms import UserRegistrationForm

def users_main(request):
    """
    Vista principal de usuarios. Muestra enlaces a lista y creación de usuarios.
    """
    return render(request, 'users/main.html')

class UserRegistrationView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')  # Updated to use namespaced URL

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '¡Registro exitoso! Por favor inicia sesión.')
        return response

class UserLoginView(FormView):
    template_name = 'users/login.html'
    form_class = AuthenticationForm
    
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        return next_url if next_url else reverse_lazy('home')

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Usuario o contraseña incorrectos')
            return self.form_invalid(form)

def user_logout(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('users:login')

@login_required
def user_list(request):
    users = User.objects.all()
    return render(request, 'users/user_list.html', {'users': users})

@login_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, 'users/user_detail.html', {'user': user})

@login_required
def user_create(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('user_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/user_form.html', {'form': form})

@login_required
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password1']:
                user.set_password(form.cleaned_data['password1'])
            user.save()
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('user_detail', pk=user.pk)
    else:
        form = UserRegistrationForm(instance=user)
    return render(request, 'users/user_form.html', {'form': form, 'editing': True})

@login_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if request.user == user:
            messages.error(request, 'No puedes eliminar tu propio usuario mientras estás conectado.')
            return redirect('user_list')
        user.delete()
        messages.success(request, 'Usuario eliminado exitosamente.')
        return redirect('user_list')
    return render(request, 'users/user_confirm_delete.html', {'user': user})
