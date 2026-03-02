
content = """{% extends 'users/base_auth.html' %}

{% block title %}Nueva Contraseña - SIGAA{% endblock %}

{% block content %}
<h4 class="text-center mb-4">Establecer nueva contraseña</h4>

{% if validlink %}
<p class="text-muted mb-4">
  Por favor ingresa tu nueva contraseña dos veces para verificar que la hayas escrito correctamente.
</p>

<form method="post">
  {% csrf_token %}

  <div class="mb-3">
    <label for="id_new_password1" class="form-label">Nueva contraseña</label>
    <input
      type="password"
      name="new_password1"
      class="form-control"
      id="id_new_password1"
      required
    />
    {% if form.new_password1.errors %}
    <div class="invalid-feedback d-block">
      {{ form.new_password1.errors.0 }}
    </div>
    {% else %}
    <div class="form-text">
      <ul class="mb-0 ps-3">
        <li>
          Tu contraseña no puede ser demasiado similar a tu otra información personal.
        </li>
        <li>Tu contraseña debe contener al menos 8 caracteres.</li>
        <li>Tu contraseña no puede ser una contraseña de uso común.</li>
        <li>Tu contraseña no puede ser enteramente numérica.</li>
      </ul>
    </div>
    {% endif %}
  </div>

  <div class="mb-4">
    <label for="id_new_password2" class="form-label">Confirmar nueva contraseña</label>
    <input
      type="password"
      name="new_password2"
      class="form-control"
      id="id_new_password2"
      required
    />
    {% if form.new_password2.errors %}
    <div class="invalid-feedback d-block">
      {{ form.new_password2.errors.0 }}
    </div>
    {% endif %}
  </div>

  <div class="d-grid gap-2 mb-3">
    <button type="submit" class="btn btn-primary">
      <i class="fas fa-key me-2"></i>Cambiar mi contraseña
    </button>
  </div>

  <div class="d-grid gap-2">
    <a href="{% url 'users:login' %}" class="btn btn-outline-secondary">
      <i class="fas fa-arrow-left me-2"></i>Volver al inicio de sesión
    </a>
  </div>
</form>
{% else %}
<div class="alert alert-danger">
  <i class="fas fa-exclamation-triangle me-2"></i>
  <strong>Enlace inválido o expirado.</strong> Por favor, solicita un nuevo restablecimiento de contraseña.
</div>

<div class="d-grid gap-2 mt-4">
  <a href="{% url 'users:password_reset' %}" class="btn btn-outline-primary">
    <i class="fas fa-undo me-2"></i>Solicitar nuevo restablecimiento
  </a>
</div>
{% endif %}
{% endblock %}

{% block extra_links %}
<p class="mb-0">
  <a href="{% url 'users:login' %}">
    <i class="fas fa-arrow-left me-1"></i>Volver al inicio de sesión
  </a>
</p>
{% endblock %}
"""

with open(r'd:\SIGAA\users\templates\users\password_reset_confirm.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Archivo password_reset_confirm.html recreado exitosamente!")
