"""
Servicio de integración con PayPal Sandbox usando la API REST directa.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

PAYPAL_BASE = {
    'sandbox': 'https://api-m.sandbox.paypal.com',
    'live': 'https://api-m.paypal.com',
}


def _get_access_token():
    """Obtiene un access token de PayPal."""
    base = PAYPAL_BASE.get(settings.PAYPAL_MODE, PAYPAL_BASE['sandbox'])
    resp = requests.post(
        f'{base}/v1/oauth2/token',
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        headers={'Accept': 'application/json', 'Accept-Language': 'en_US'},
        data={'grant_type': 'client_credentials'},
    )
    resp.raise_for_status()
    return resp.json()['access_token']


def crear_pago(monto_usd, referencia, evento_id, return_url, cancel_url):
    """Crea un pago en PayPal y retorna el dict con id y approval_url."""
    base = PAYPAL_BASE.get(settings.PAYPAL_MODE, PAYPAL_BASE['sandbox'])
    token = _get_access_token()

    payload = {
        'intent': 'CAPTURE',
        'purchase_units': [{
            'reference_id': referencia,
            'description': f'Entradas Teatro Al Aire Libre - Evento #{evento_id}',
            'amount': {
                'currency_code': 'USD',
                'value': f'{monto_usd:.2f}',
            },
        }],
        'application_context': {
            'brand_name': 'Teatro Al Aire Libre',
            'landing_page': 'BILLING',
            'user_action': 'PAY_NOW',
            'return_url': return_url,
            'cancel_url': cancel_url,
        },
    }

    resp = requests.post(
        f'{base}/v2/checkout/orders',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
        },
        json=payload,
    )

    data = resp.json()

    if resp.status_code not in (200, 201):
        error_msg = data.get('message', str(data))
        logger.error(f'PayPal error al crear orden: {error_msg}')
        raise ValueError(f'Error de PayPal: {error_msg}')

    approval_url = None
    for link in data.get('links', []):
        if link.get('rel') == 'approve':
            approval_url = link['href']
            break

    logger.info(f'PayPal orden creada: {data["id"]} - Ref: {referencia}')
    return data['id'], approval_url


def capturar_pago(order_id):
    """Captura (confirma) un pago después de que el usuario lo aprueba."""
    base = PAYPAL_BASE.get(settings.PAYPAL_MODE, PAYPAL_BASE['sandbox'])
    token = _get_access_token()

    resp = requests.post(
        f'{base}/v2/checkout/orders/{order_id}/capture',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
        },
    )

    data = resp.json()

    if resp.status_code not in (200, 201):
        error_msg = data.get('message', str(data))
        logger.error(f'PayPal error al capturar: {error_msg}')
        raise ValueError(f'Error al confirmar pago: {error_msg}')

    status = data.get('status', '')
    logger.info(f'PayPal captura: {order_id} - Estado: {status}')
    return data


def verificar_orden(order_id):
    """Obtiene el estado de una orden de PayPal."""
    base = PAYPAL_BASE.get(settings.PAYPAL_MODE, PAYPAL_BASE['sandbox'])
    token = _get_access_token()

    resp = requests.get(
        f'{base}/v2/checkout/orders/{order_id}',
        headers={
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}',
        },
    )

    if resp.status_code == 200:
        return resp.json()
    return None
