"""
Servicio de integración con PayPal Sandbox.

CONFIGURACIÓN:
1. Ve a https://developer.paypal.com
2. Crea una cuenta de desarrollador (gratis)
3. Ve a "My Apps & Credentials" → Sandbox
4. Crea una app copia el Client ID y Secret
5. Colócalos en el archivo .env del proyecto:

   PAYPAL_CLIENT_ID=AQUI_TU_CLIENT_ID
   PAYPAL_CLIENT_SECRET=AQUI_TU_CLIENT_SECRET
   PAYPAL_MODE=sandbox

6. Para probar, usa las tarjetas de prueba de PayPal Sandbox:
   - Visa: 4111111111111111
   - Mastercard: 5500000000000004
   - CVV: 123
   - Fecha: cualquier fecha futura
"""
import paypalrestsdk
from django.conf import settings


def configure_paypal():
    """Configura el SDK de PayPal con las credenciales del .env"""
    paypalrestsdk.configure({
        'mode': settings.PAYPAL_MODE,
        'client_id': settings.PAYPAL_CLIENT_ID,
        'client_secret': settings.PAYPAL_CLIENT_SECRET,
    })


def crear_pago(monto_bs, monto_usd, referencia, evento_id, return_url, cancel_url):
    """
    Crea un pago en PayPal y retorna el objeto Payment.

    Args:
        monto_bs: Monto en Bolivianos
        monto_usd: Monto en USD (convertido con PAYPAL_RATE_TO_USD)
        referencia: Referencia interna del teatro
        evento_id: ID del evento
        return_url: URL a la que PayPal redirige después del pago exitoso
        cancel_url: URL a la que PayPal redirige si el usuario cancela

    Returns:
        Objeto Payment de PayPal o None si hay error
    """
    configure_paypal()

    payment = paypalrestsdk.Payment({
        'intent': 'sale',
        'payer': {
            'payment_method': 'paypal',
        },
        'redirect_urls': {
            'return_url': return_url,
            'cancel_url': cancel_url,
        },
        'transactions': [{
            'item_list': {
                'items': [{
                    'name': f'Teatro Al Aire Libre - Evento #{evento_id}',
                    'sku': f'EVENTO-{evento_id}-{referencia}',
                    'price': f'{monto_usd:.2f}',
                    'currency': 'USD',
                    'quantity': 1,
                }]
            },
            'amount': {
                'total': f'{monto_usd:.2f}',
                'currency': 'USD',
            },
            'description': f'Compra de entradas - Teatro Al Aire Libre - Ref: {referencia}',
            'custom': referencia,
        }],
    })

    if payment.create():
        return payment
    else:
        # Error al crear el pago
        error_msg = payment.error.get('message', 'Error desconocido de PayPal')
        raise ValueError(f'Error al crear pago en PayPal: {error_msg}')


def ejecutar_pago(payment_id, payer_id):
    """
    Ejecuta (confirma) un pago después de que el usuario lo aprueba en PayPal.

    Args:
        payment_id: ID del pago de PayPal
        payer_id: ID del pagador de PayPal

    Returns:
        Objeto Payment ejecutado o None si hay error
    """
    configure_paypal()

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({'payer_id': payer_id}):
        return payment
    else:
        error_msg = payment.error.get('message', 'Error desconocido de PayPal')
        raise ValueError(f'Error al ejecutar pago en PayPal: {error_msg}')


def obtener_pago(payment_id):
    """
    Obtiene un pago de PayPal por su ID.

    Args:
        payment_id: ID del pago de PayPal

    Returns:
        Objeto Payment o None
    """
    configure_paypal()

    try:
        return paypalrestsdk.Payment.find(payment_id)
    except Exception:
        return None
