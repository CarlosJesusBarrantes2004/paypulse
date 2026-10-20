import hmac
import hashlib
from django.conf import settings


class FirmadorWebhookService:
    @staticmethod
    def calcular_firma(payload_bytes: bytes, secret_key: str) -> str:
        return hmac.new(
            key=secret_key.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256
        ).hexdigest()

    @classmethod
    def verificar_firma(cls, payload_bytes: bytes, firma_recibida: str) -> bool:
        if not firma_recibida:
            return False

        secret_key = getattr(settings, "PASARELA_SECRET_HMAC", "")
        firma_esperada = cls.calcular_firma(payload_bytes, secret_key)

        return hmac.compare_digest(firma_esperada, firma_recibida)
