from django.urls import path
from pagos.views import ProcesarPagoView

urlpatterns = [
    path("procesar/", ProcesarPagoView.as_view(), name="procesar_pago"),
]
