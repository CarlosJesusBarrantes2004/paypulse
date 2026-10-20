import uuid
import time
import random
from decimal import Decimal
from typing import Dict, Any


class PasarelaExcepcion(Exception):
    pass


class PasarelaRedExcepcion(Exception):
    pass


class StripeMockService:
    @staticmethod
    def cobrar(
        monto: Decimal, moneda: str, token_tarjeta: str = "tok_visa"
    ) -> Dict[str, Any]:
        # 1. Simular latencia de red (entre 100ms y 400ms)
        time.sleep(random.uniform(0.1, 0.4))

        # 2. Simular fallos transitorios de red (15% de probabilidad)
        # Esto nos permite probar si nuestro mecanismo de reintentos funciona
        probabilidad_fallo = random.random()
        if probabilidad_fallo < 0.15:
            raise PasarelaRedExcepcion(
                "503 Service Unavailable: Error de conexión con el proveedor de pagos."
            )

        # 3. Simular rechazo de tarjeta si se envía un token específico de prueba
        if token_tarjeta == "tok_declined":
            raise PasarelaExcepcion(
                "Card Declined: Fondos insuficientes o tarjeta bloqueada."
            )

        # 4. Respuesta exitosa simulada
        return {
            "id": f"ch_stripe_{uuid.uuid4().hex[:12]}",
            "monto": str(monto),
            "moneda": moneda,
            "status": "succeeded",
            "metodo_pago": "credit_card",
        }
