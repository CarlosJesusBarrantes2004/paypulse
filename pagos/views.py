from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from clientes.models import Cliente
from pagos.serializers import ProcesarPagoSerializer
from pagos.services.pago_service import PagoService

# Create your views here.


class ProcesarPagoView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ProcesarPagoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = serializer.validated_data
        idempotency_key = request.META.get("HTTP_X_IDEMPOTENCY_KEY")

        try:
            transaccion = PagoService.procesar_pago(
                cliente_id=str(datos["cliente_id"]),
                monto=datos["monto"],
                moneda=datos["moneda"],
                idempotency_key=idempotency_key,
                token_tarjeta=datos["token_tarjeta"],
                v_features=datos.get("v_features"),
            )

            respuesta_payload = {
                "id": str(transaccion.id),
                "monto": str(transaccion.monto),
                "moneda": transaccion.moneda,
                "estado": transaccion.estado,
                "proveedor_pago_id": transaccion.proveedor_pago_id,
                "error_detalle": transaccion.error_detalle,
            }

            status_code = (
                status.HTTP_201_CREATED
                if transaccion.estado == "SUCCEDED"
                else status.HTTP_402_PAYMENT_REQUIRED
            )

            return Response(respuesta_payload, status=status_code)
        except Cliente.DoesNotExist:
            return Response(
                {"error": "Cliente no encontrado o inactivo."},
                status=status.HTTP_404_NOT_FOUND,
            )
