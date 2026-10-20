from decimal import Decimal
from django.db import transaction
from clientes.models import Cliente
from pagos.models import TransaccionPago, EstadoPago
from pagos.services.gateway import (
    StripeMockService,
    PasarelaExcepcion,
    PasarelaRedExcepcion,
)
from pagos.services.resilience import ejecutar_con_reintentos
from pagos.services.fraud_client import FrauDetectionService
from pagos.tasks import generar_comprobante_pago_async


class PagoService:
    @staticmethod
    def procesar_pago(
        cliente_id: str,
        monto: Decimal,
        moneda: str = "USD",
        idempotency_key: str = None,
        token_tarjeta: str = "tok_visa",
        v_features: dict = None,
    ) -> TransaccionPago:
        cliente = Cliente.objects.get(id=cliente_id, activo=True)

        with transaction.atomic():
            transaccion = TransaccionPago.objects.create(
                cliente=cliente,
                monto=monto,
                moneda=moneda,
                estado=EstadoPago.PENDING,
                idempotency_key=idempotency_key,
            )

        transaccion.cambiar_estado(EstadoPago.PROCESSING)

        evaluacion_ml = FrauDetectionService.evaluar_transaccion(
            monto=float(monto), v_features=v_features
        )

        if evaluacion_ml.get("es_fraude"):
            transaccion.cambiar_estado(
                EstadoPago.FAILED,
                error_msg=f"Transacción bloqueada por Machine Learning. Riesgo: {evaluacion_ml.get("probabilidad_fraude")*100}%",
            )
            return transaccion

        try:
            respuesta_gateway = ejecutar_con_reintentos(
                StripeMockService.cobrar,
                monto=monto,
                moneda=moneda,
                token_tarjeta=token_tarjeta,
                max_reintentos=3,
            )

            transaccion.proveedor_pago_id = respuesta_gateway["id"]
            transaccion.save(update_fields=["proveedor_pago_id"])
            transaccion.cambiar_estado(EstadoPago.SUCCEEDED)

            transaction.on_commit(
                lambda: generar_comprobante_pago_async.delay(str(transaccion.id))
            )
        except (PasarelaExcepcion, PasarelaRedExcepcion) as exc:
            transaccion.cambiar_estado(EstadoPago.FAILED, error_msg=str(exc))

        return transaccion
