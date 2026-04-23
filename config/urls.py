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

# Importamos las vistas (CON TUS NUEVAS RUTAS DE CARPETAS)
from apps.users.views import signup_view, login_view, logout_view, perfil_view
# Asegúrate de importar las vistas de soporte aquí
from apps.support.views import support_dashboard, ticket_messages_api, send_message_api, close_ticket_api

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
    # 1. Panel Principal (http://127.0.0.1:8000/soporte/)
    path('soporte/', support_dashboard, name='support_dashboard'),
    
    # 2. APIs para AJAX (No devuelven HTML, devuelven datos JSON)
    path('soporte/api/mensajes/<int:ticket_id>/', ticket_messages_api, name='ticket_messages_api'),
    path('soporte/api/enviar-mensaje/', send_message_api, name='send_message_api'),
    path('soporte/api/cerrar-ticket/', close_ticket_api, name='close_ticket_api'),
]