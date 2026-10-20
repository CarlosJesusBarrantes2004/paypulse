import uuid
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from clientes.models import Cliente

# Create your models here.


class EstadoPago(models.TextChoices):
    PENDING = "PENDING", "Pendiente"
    PROCESSING = "PROCESSING", "En Proceso"
    SUCCEEDED = "SUCCEEDED", "Exitoso"
    FAILED = "FAILED", "Fallido"
    REFUNDED = "REFUNDED", "Reembolsado"


class TransaccionPago(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name="transacciones"
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=3, default="USD")
    estado = models.CharField(
        max_length=20,
        choices=EstadoPago.choices,
        default=EstadoPago.PENDING,
        db_index=True,
    )
    idempotency_key = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    proveedor_pago_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID externo retornado por Stripe/MercadoPago",
    )
    error_detalle = models.TextField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True, db_index=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transacciones_pago"
        ordering = ["-creado_en"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(monto__gt=Decimal("0.00")),
                name="check_transaccion_monto_positivo",
            )
        ]

    def __str__(self) -> str:
        return f"Tx {self.id} | {self.monto} {self.moneda} | {self.estado}"

    def cambiar_estado(self, nuevo_estado: str, error_msg: str = None) -> None:
        TRANSACCIONES_VALIDAS = {
            EstadoPago.PENDING: [EstadoPago.PROCESSING, EstadoPago.FAILED],
            EstadoPago.PROCESSING: [EstadoPago.SUCCEEDED, EstadoPago.FAILED],
            EstadoPago.SUCCEEDED: [EstadoPago.REFUNDED],
            EstadoPago.FAILED: [],
            EstadoPago.REFUNDED: [],
        }

        if nuevo_estado not in TRANSACCIONES_VALIDAS[self.estado]:
            raise ValidationError(
                f"Transición de estado inválida: Imposible pasar de '{self.estado}' a '{nuevo_estado}'."
            )

        self.estado = nuevo_estado
        if error_msg:
            self.error_detalle = error_msg
        self.save(update_fields=["estado", "error_detalle", "actualizado_en"])


class Suscripcion(models.Model):
    class EstadoSuscripcion(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        CANCELADA = "CANCELADA", "Cancelada"
        PAUSADA = "PAUSADA", "Pausada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="suscripciones"
    )
    plan_nombre = models.CharField(max_length=100)
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20,
        choices=EstadoSuscripcion.choices,
        default=EstadoSuscripcion.ACTIVA,
    )
    proximo_cobro = models.DateTimeField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "suscripciones"

    def __str__(self) -> str:
        return f"Suscripción {self.plan_nombre} - {self.cliente.nombre}"
