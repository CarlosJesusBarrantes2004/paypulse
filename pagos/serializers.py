from rest_framework import serializers


class ProcesarPagoSerializer(serializers.Serializer):
    cliente_id = serializers.UUIDField(required=True)
    monto = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    moneda = serializers.CharField(max_length=3, default="USD")
    token_tarjeta = serializers.CharField(max_length=50, default="tok_visa")
    v_features = serializers.DictField(
        child=serializers.FloatField(),
        required=False,
        allow_null=True,
        default=None,
    )
