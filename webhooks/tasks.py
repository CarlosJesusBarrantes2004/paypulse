import logging
from celery import shared_task
from django.core.cache import cache
from pagos.models import TransaccionPago, EstadoPago

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def procesar_evento_webhook_async(self, evento_id: str, evento_payload: dict):
    cache_key = f"webook_processed:{evento_id}"
    if not cache.add(cache_key, "PROCESSED", timeout=86400):
        logger.info(f"Webhook {evento_id} ignorado por duplicado.")
        return {"status": "ignored", "reason": "duplicate_event"}

    tipo_evento = evento_payload.get("tipo")
    datos = evento_payload.get("data", {})

    logger.info(f"Procesando evento de webhook {evento_id} tipo: {tipo_evento}.")

    try:
        if tipo_evento == "pago.exitoso":
            proveedor_id = datos.get("proveedor_pago_id")
            transaccion = TransaccionPago.objects.get(proveedor_pago_id=proveedor_id)
            if transaccion.estado != EstadoPago.SUCCEEDED:
                transaccion.cambiar_estado(EstadoPago.SUCCEEDED)

        elif tipo_evento == "pago.reembolsado":
            proveedor_id = datos.get("proveedor_pago_id")
            transaccion = TransaccionPago.objects.get(proveedor_pago_id=proveedor_id)
            if transaccion.estado == EstadoPago.SUCCEEDED:
                transaccion.cambiar_estado(EstadoPago.REFUNDED)

        return {"status": "success", "evento_id": evento_id}
    except TransaccionPago.DoesNotExist:
        logger.error(f"Transacción no encontrada para el evento {evento_id}.")
        return {"status": "error", "reason": "transaction_not_found"}
    except Exception as exc:
        logger.error(f"Error procesando webhook {evento_id}: {str(exc)}.")
        raise self.retry(exc=exc)
