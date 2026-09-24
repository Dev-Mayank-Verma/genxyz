from urllib.parse import urljoin
import requests
from .config import settings

class RegistrarError(RuntimeError):
    pass

class RegistrarClient:
    """Thin adapter for an authorized registrar/reseller API.

    The exact Gen.xyz web checkout is not hard-coded here. Use an official API/
    reseller agreement and map its JSON contract to these four methods.
    """
    def __init__(self):
        if not settings.registrar_base_url or not settings.registrar_api_key:
            raise RegistrarError("Registrar API credentials are not configured.")
        self.base=settings.registrar_base_url.rstrip('/') + '/'
        self.headers={"Authorization": f"Bearer {settings.registrar_api_key}", "Accept":"application/json", "Content-Type":"application/json"}

    def _post(self, path, payload):
        r=requests.post(urljoin(self.base, path.lstrip('/')), json=payload, headers=self.headers, timeout=25)
        if not r.ok:
            raise RegistrarError(f"Registrar returned HTTP {r.status_code}: {r.text[:300]}")
        return r.json()

    def _get(self, path, params=None):
        r=requests.get(urljoin(self.base, path.lstrip('/')), params=params, headers=self.headers, timeout=25)
        if not r.ok:
            raise RegistrarError(f"Registrar returned HTTP {r.status_code}: {r.text[:300]}")
        return r.json()

    def availability(self, domain):
        data=self._get(settings.availability_path, {"domain":domain})
        return bool(data.get("available", False)), data

    def price(self, domain, years=1, coupon=None):
        payload={"domain":domain, "years":years}
        if coupon:
            payload["coupon"] = coupon
        data=self._post(settings.price_path, payload)
        return data

    def register(self, contact, domain, years=1, coupon=None):
        payload={"domain":domain, "years":years, "contact":contact}
        if coupon:
            payload["coupon"] = coupon
        return self._post(settings.register_path, payload)

    def status(self, order_id):
        return self._get(settings.status_path.format(order_id=order_id))
