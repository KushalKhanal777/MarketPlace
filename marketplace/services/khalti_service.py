import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def initiate_payment(order, request):
    """
    Initiate a Khalti ePayment via the official API.

    Sends a POST to https://dev.khalti.com/api/v2/epayment/initiate/
    with: return_url, website_url, amount, purchase_order_id,
    purchase_order_name, customer_info.

    Returns a dict with 'payment_url' and 'pidx' on success,
    or raises ValueError with the error message.
    """
    if not settings.KHALTI_SECRET_KEY:
        raise ValueError("Khalti secret key is not configured.")

    initiate_url = f"{settings.KHALTI_API_BASE_URL}/epayment/initiate/"

    amount_paisa = int(float(order.total_amount) * 100)

    return_url = request.build_absolute_uri(
        f'/payment/khalti/{order.id}/verify/'
    )
    website_url = settings.SITE_URL

    payload = {
        "return_url": return_url,
        "website_url": website_url,
        "amount": amount_paisa,
        "purchase_order_id": order.order_number,
        "purchase_order_name": f"Order {order.order_number}",
        "customer_info": {
            "name": order.full_name or order.user.get_full_name() or order.user.username,
            "email": order.email,
            "phone": order.phone,
        },
    }

    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            initiate_url,
            json=payload,
            headers=headers,
            timeout=30,
        )
        try:
            data = response.json()
        except (ValueError, TypeError):
            logger.error("Khalti initiate returned non-JSON response (%s): %s", response.status_code, response.text[:500])
            raise ValueError("Khalti returned an invalid response. Please try again.")

        if response.status_code not in (200, 201):
            logger.error("Khalti initiate failed (%s): %s", response.status_code, data)
            error_msg = data.get("detail", data.get("error", "Payment initiation failed"))
            if isinstance(error_msg, dict):
                error_msg = str(error_msg)
            raise ValueError(error_msg)

        return {
            "payment_url": data["payment_url"],
            "pidx": data["pidx"],
        }

    except requests.exceptions.RequestException as e:
        logger.error("Khalti API request failed: %s", str(e))
        raise ValueError("Could not connect to Khalti. Please try again.")


def verify_payment(pidx):
    """
    Verify a Khalti ePayment after the user returns from the payment page.

    Sends a POST to https://dev.khalti.com/api/v2/epayment/lookup/
    with the pidx.

    Returns the full verification response dict on success,
    or raises ValueError with the error message.
    """
    if not settings.KHALTI_SECRET_KEY:
        raise ValueError("KHALTI secret key is not configured.")

    lookup_url = f"{settings.KHALTI_API_BASE_URL}/epayment/lookup/"

    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            lookup_url,
            json={"pidx": pidx},
            headers=headers,
            timeout=30,
        )
        try:
            data = response.json()
        except (ValueError, TypeError):
            logger.error("Khalti lookup returned non-JSON response (%s): %s", response.status_code, response.text[:500])
            raise ValueError("Khalti returned an invalid response. Please try again.")

        if response.status_code not in (200, 201):
            logger.error("Khalti lookup failed (%s): %s", response.status_code, data)
            error_msg = data.get("detail", data.get("error", "Payment verification failed"))
            if isinstance(error_msg, dict):
                error_msg = str(error_msg)
            raise ValueError(error_msg)

        return data

    except requests.exceptions.RequestException as e:
        logger.error("Khalti API request failed: %s", str(e))
        raise ValueError("Could not connect to Khalti. Please try again.")
