"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path

# ── Auth & perfil ─────────────────────────────────────────────────────────────
from apps.users.views import (
    signup_view, login_view, logout_view, perfil_view,
    admin_panel,
    admin_reserva_action, admin_report_export, admin_venta_detalle,
    admin_soporte_reply, admin_soporte_close,
    admin_config_general_save, admin_config_security_save,
    admin_usuario_action, admin_usuario_create,
)

# ── Eventos (públicas + admin CRUD) ───────────────────────────────────────────
from apps.events.views import (
    inicio_view, eventos_view, comprar_entrada_view,
    admin_evento_create, admin_evento_delete, admin_evento_update,
)

# ── Páginas estáticas ─────────────────────────────────────────────────────────
from apps.events.static_views import sobre_nosotros_view, contacto_view, terminos_view, privacidad_view

# ── Flujo de compra ───────────────────────────────────────────────────────────
from apps.reservations.views import (
    seleccionar_zona_view,
    seleccionar_asientos_view,
    api_asientos_view,
    finalizar_compra_view,
    confirmar_compra_view,
    compra_exitosa_view,
    guardar_carrito_api,
)

# ── Mis tickets ───────────────────────────────────────────────────────────────
from apps.tickets.views import (
    mis_tickets_view,
    boleteria_view, api_get_zonas, boleteria_confirmar_view,
)

# ── Soporte ───────────────────────────────────────────────────────────────────
from apps.support.views import (
    support_dashboard, ticket_messages_api, send_message_api,
    close_ticket_api, tickets_list_api,
    cliente_soporte_view, cliente_mensajes_api, cliente_enviar_mensaje_api,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── PÁGINAS PÚBLICAS ──────────────────────────────────────────────────────
    path('', inicio_view, name='inicio'),
    path('eventos/', eventos_view, name='eventos'),

    # ── PÁGINAS ESTÁTICAS ─────────────────────────────────────────────────────
    path('sobre-nosotros/', sobre_nosotros_view, name='sobre_nosotros'),
    path('contacto/', contacto_view, name='contacto'),
    path('terminos/', terminos_view, name='terminos'),
    path('privacidad/', privacidad_view, name='privacidad'),

    # ── FLUJO DE COMPRA ───────────────────────────────────────────────────────
    path('comprar-entrada/<int:evento_id>/', comprar_entrada_view, name='comprar_entradas'),
    path('comprar-entrada/<int:evento_id>/zonas/', seleccionar_zona_view, name='seleccionar_zona'),
    path('comprar-entrada/<int:evento_id>/zonas/<int:evento_zona_id>/asientos/', seleccionar_asientos_view, name='seleccionar_asientos'),
    path('api/asientos/<int:evento_id>/<int:evento_zona_id>/', api_asientos_view, name='api_asientos'),
    path('comprar-entrada/<int:evento_id>/finalizar/', finalizar_compra_view, name='finalizar_compra'),
    path('comprar-entrada/<int:evento_id>/confirmar/', confirmar_compra_view, name='confirmar_compra'),
    path('compra-exitosa/<int:venta_id>/', compra_exitosa_view, name='compra_exitosa'),
    path('api/carrito/<int:evento_id>/', guardar_carrito_api, name='guardar_carrito_api'),

    # ── PERFIL Y AUTH ─────────────────────────────────────────────────────────
    path('perfil/', perfil_view, name='perfil'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # ── MIS ENTRADAS ──────────────────────────────────────────────────────────
    path('mis-tickets/', mis_tickets_view, name='mis_tickets'),

    # ── BOLETERÍA (venta presencial) ──────────────────────────────────────────
    path('boleteria/', boleteria_view, name='boleteria'),
    path('boleteria/confirmar/', boleteria_confirmar_view, name='boleteria_confirmar'),
    path('api/boleteria/zonas/<int:evento_id>/', api_get_zonas, name='api_boleteria_zonas'),

    # ── PANEL ADMINISTRADOR ───────────────────────────────────────────────────
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
    path('admin-panel/usuarios/action/', admin_usuario_action, name='admin_usuario_action'),
    path('admin-panel/usuarios/nuevo/', admin_usuario_create, name='admin_usuario_create'),

    # ── SOPORTE (STAFF) ───────────────────────────────────────────────────────
    path('soporte/', support_dashboard, name='support_dashboard'),
    path('soporte/api/mensajes/<int:ticket_id>/', ticket_messages_api, name='ticket_messages_api'),
    path('soporte/api/enviar-mensaje/', send_message_api, name='send_message_api'),
    path('soporte/api/cerrar-ticket/', close_ticket_api, name='close_ticket_api'),
    path('soporte/api/tickets/', tickets_list_api, name='tickets_list_api'),

    # ── SOPORTE (CLIENTE) ─────────────────────────────────────────────────────
    path('mi-soporte/', cliente_soporte_view, name='cliente_soporte'),
    path('mi-soporte/<int:ticket_id>/', cliente_soporte_view, name='cliente_soporte_detalle'),
    path('mi-soporte/api/mensajes/<int:ticket_id>/', cliente_mensajes_api, name='cliente_mensajes_api'),
    path('mi-soporte/api/enviar/<int:ticket_id>/', cliente_enviar_mensaje_api, name='cliente_enviar_mensaje_api'),
]
