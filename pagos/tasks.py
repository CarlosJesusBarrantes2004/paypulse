import logging
from celery import shared_task
from pagos.models import TransaccionPago

logger = logging.getLogger(__name__)


@shared_task()
def generar_comprobante_pago_async(transaccion_id: str) -> dict[str, str]:
    try:
        transaccion = TransaccionPago.objects.get(id=transaccion_id)
        cliente = transaccion.cliente

        logger.info(
            f"Generando comprobante PDF para la transacción {transaccion_id} del cliente {cliente.email} por el monto {transaccion.monto}."
        )

        return {
            "mensaje": "Comprobante generado exitosamente.",
            "comprobante_id": "jeh32rkjrw",
        }
    except TransaccionPago.DoesNotExist:
        logger.error(f"Transacción no encontrada con id {transaccion_id}.")
        return {"status": "error", "reason": "transaction_not_found"}
