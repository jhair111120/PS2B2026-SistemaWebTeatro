"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

# Importamos las vistas
from apps.users.views import signup_view, login_view, logout_view, perfil_view
from apps.support.views import (
    support_dashboard, ticket_messages_api, send_message_api, close_ticket_api,
    cliente_soporte_view, cliente_mensajes_api, cliente_enviar_mensaje_api
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas de las interfaces visuales públicas
    path('', TemplateView.as_view(template_name='pages/usuarios/inicio.html'), name='inicio'),
    
    # Rutas de Autenticación
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # Ruta: Mi Perfil
    path('perfil/', perfil_view, name='perfil'),
    
    # ================= RUTAS DE SOPORTE (ADMIN) =================
    path('soporte/', support_dashboard, name='support_dashboard'),
    path('soporte/api/mensajes/<int:ticket_id>/', ticket_messages_api, name='ticket_messages_api'),
    path('soporte/api/enviar-mensaje/', send_message_api, name='send_message_api'),
    path('soporte/api/cerrar-ticket/', close_ticket_api, name='close_ticket_api'),

    # ================= RUTAS DE SOPORTE (CLIENTE) =================
    path('mi-soporte/', cliente_soporte_view, name='cliente_soporte'),
    path('mi-soporte/<int:ticket_id>/', cliente_soporte_view, name='cliente_soporte_detalle'),
    path('mi-soporte/api/mensajes/<int:ticket_id>/', cliente_mensajes_api, name='cliente_mensajes_api'),
    path('mi-soporte/api/enviar/<int:ticket_id>/', cliente_enviar_mensaje_api, name='cliente_enviar_mensaje_api'),
]