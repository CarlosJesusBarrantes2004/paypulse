import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

ML_SERVICE_URL = getattr(
    settings, "ML_SERVICE_URL", "http://127.0.0.1:8002/api/v1/predict"
)


class FraudDetectionException(Exception):
    pass


class FrauDetectionService:
    @staticmethod
    def evaluar_transaccion(monto: float, v_features: dict = None) -> dict:
        """
        Consulta el microservicio de ML para verificar riesgo de fraude.
        """
        # Si no se envían v_features (ej. tarjeta nueva), inicializamos en 0.0
        if v_features is None:
            v_features = {f"V{i}": 0.0 for i in range(1, 29)}

        payload = {
            "amount": float(monto),
            "time": 0.0,
            "v_features": v_features,
        }

        try:
            response = requests.post(ML_SERVICE_URL, json=payload, timeout=2.0)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error en ML Service: Status {response.status_code}")
                return {
                    "es_fraude": False,
                    "probabilidad_fraude": 0.0,
                    "accion_sugerida": "APROBAR",
                }
        except requests.RequestException as e:
            logger.warning(
                f"MIcroservicio de ML inaccesible: {e}. Continuando con pago."
            )
            return {
                "es_fraude": False,
                "probabilidad_fraude": 0.0,
                "accion_sugerida": "APROBAR",
            }
