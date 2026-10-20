import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from webhooks.services.signature import FirmadorWebhookService
from webhooks.tasks import procesar_evento_webhook_async

# Create your views here.


class ReceiverWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload_bytes = request.body
        firma_header = request.META.get("HTTP_X_SIGNATURE")

        if not FirmadorWebhookService.verificar_firma(payload_bytes, firma_header):
            return Response(
                {
                    "error": "Firma no válida.",
                    "detalle": "Firma criptográfica HMAC no coincide.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            payload_data = json.loads(payload_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            return Response(
                {"error": "JSON inválido."}, status=status.HTTP_400_BAD_REQUEST
            )

        evento_id = payload_data.get("evento_id")
        if not evento_id:
            return Response(
                {
                    "error": "Payload incompleto.",
                    "detalle": "Falta el campo 'evento_id'.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        procesar_evento_webhook_async.delay(evento_id, payload_data)

        return Response(
            {"status": "recibido", "evento_id": evento_id}, status=status.HTTP_200_OK
        )
