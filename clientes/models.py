import uuid
from django.db import models

# Create your models here.


class Cliente(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    nombre = models.CharField(max_length=150)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clientes"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.email})"
