"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

# Importación de vistas de aplicaciones
from apps.users.views import signup_view, login_view, logout_view, perfil_view
from apps.support.views import support_dashboard, ticket_messages_api, send_message_api, close_ticket_api

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ================= RUTAS DE USUARIO (PÁGINAS PÚBLICAS Y PERFIL) =================
    path('', TemplateView.as_view(template_name='pages/users/inicio.html'), name='inicio'),
    path('comprar-entrada/', TemplateView.as_view(template_name='pages/users/comprar_entrada.html'), name='comprar_entradas'),
    path('seleccionar-zona/', TemplateView.as_view(template_name='pages/users/seleccionar_zona.html'), name='seleccionar_zona'),
    path('finalizar-compra/', TemplateView.as_view(template_name='pages/users/finalizar_compra.html'), name='finalizar_compra'),
    path('compra-exitosa/', TemplateView.as_view(template_name='pages/users/compra_exitosa.html'), name='compra_exitosa'),
    path('perfil/', perfil_view, name='perfil'),

    # ================= RUTAS DE AUTENTICACIÓN =================
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # ================= RUTAS DE MÓDULOS (SEGÚN TU ESTRUCTURA DE CARPETAS) =================
    
    # Eventos
    path('eventos/', TemplateView.as_view(template_name='pages/events/eventos.html'), name='eventos'),
    
    # Reservas
    path('reservas/', TemplateView.as_view(template_name='pages/reservations/reservas.html'), name='reservas'),
    
    # Pagos
    path('pagos/', TemplateView.as_view(template_name='pages/payments/pagos.html'), name='pagos'),
    
    # Mis Tickets (Entradas compradas)
    path('mis-tickets/', TemplateView.as_view(template_name='pages/tickets/tickets.html'), name='mis_tickets'),

    # ================= RUTAS DE SOPORTE =================
    # Vista principal de soporte
    path('soporte/', TemplateView.as_view(template_name='pages/support/support.html'), name='support'),
    
    # APIs para AJAX (JSON)
    path('soporte/api/mensajes/<int:ticket_id>/', ticket_messages_api, name='ticket_messages_api'),
    path('soporte/api/enviar-mensaje/', send_message_api, name='send_message_api'),
    path('soporte/api/cerrar-ticket/', close_ticket_api, name='close_ticket_api'),
]
