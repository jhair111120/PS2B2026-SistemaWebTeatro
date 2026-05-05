"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

# Importación de vistas de aplicaciones
from apps.users.views import (
    signup_view,
    login_view,
    logout_view,
    perfil_view,
    admin_panel,
    admin_reserva_action,
    admin_report_export,
    admin_venta_detalle,
    admin_soporte_reply,
    admin_soporte_close,
    admin_config_general_save,
    admin_config_security_save,
)
from apps.events.views import admin_evento_create, admin_evento_delete, admin_evento_update
from apps.support.views import (
    support_dashboard, ticket_messages_api, send_message_api, close_ticket_api,
    cliente_soporte_view, cliente_mensajes_api, cliente_enviar_mensaje_api
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ================= RUTAS DE USUARIO (PÁGINAS PÚBLICAS Y PERFIL) =================
    path('', TemplateView.as_view(template_name='pages/users/inicio.html'), name='inicio'),
    path('comprar-entrada/', TemplateView.as_view(template_name='pages/users/comprar_entrada.html'), name='comprar_entradas'),
    path('perfil/', perfil_view, name='perfil'),

    # ================= RUTAS DE AUTENTICACIÓN =================
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('admin-panel/', admin_panel, name='admin_panel'),
    path('admin-panel/eventos/nuevo/', admin_evento_create, name='admin_evento_nuevo'),
    path('admin-panel/eventos/<int:evento_id>/editar/', admin_evento_update, name='admin_evento_editar'),
    path('admin-panel/eventos/<int:evento_id>/eliminar/', admin_evento_delete, name='admin_evento_eliminar'),
    path('admin-panel/reserva-accion/', admin_reserva_action, name='admin_reserva_action'),
    path('admin-panel/reporte-export/', admin_report_export, name='admin_report_export'),
    path('admin-panel/ventas/<int:venta_id>/', admin_venta_detalle, name='admin_venta_detalle'),
    path('admin-panel/soporte/reply/', admin_soporte_reply, name='admin_soporte_reply'),
    path('admin-panel/soporte/close/', admin_soporte_close, name='admin_soporte_close'),
    path('admin-panel/config/general/', admin_config_general_save, name='admin_config_general_save'),
    path('admin-panel/config/security/', admin_config_security_save, name='admin_config_security_save'),

    # ================= RUTAS DE MÓDULOS (SEGÚN TU ESTRUCTURA DE CARPETAS) =================
    
    # Eventos
    path('eventos/', TemplateView.as_view(template_name='pages/events/eventos.html'), name='eventos'),
    
    # Reservas
    path('reservas/', TemplateView.as_view(template_name='pages/reservations/reservas.html'), name='reservas'),
    
    # Pagos
    path('pagos/', TemplateView.as_view(template_name='pages/payments/pagos.html'), name='pagos'),
    
    # Mis Tickets (Entradas compradas)
    path('mis-tickets/', TemplateView.as_view(template_name='pages/tickets/tickets.html'), name='mis_tickets'),

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