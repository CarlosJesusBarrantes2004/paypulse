import json
from typing import Callable
from django.core.cache import cache
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.conf import settings


class IdempotencyMiddleware:
    """
    Middleware que garantiza la idempotencia en peticiones mutativas (POST/PUT/PATCH)
    utilizando el header 'X-Idempotency-Key' respaldado en Redis.
    """

    IDEMPOTENCY_HEADER = "HTTP_X_IDEMPOTENCY_KEY"
    CACHE_TTL_SECONDS = getattr(settings, "IDEMPOTENCY_CACHE_TTL", 86400)

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method not in (
            "POST",
            "PUT",
            "PATCH",
        ) or not request.path.startswith("/api/v1/pagos/"):
            return self.get_response(request)

        idempotency_key = request.META.get(self.IDEMPOTENCY_HEADER)

        if not idempotency_key:
            return self.get_response(request)

        cache_key = f"idempotency:{idempotency_key}"
        lock_key = f"lock:idempotency:{idempotency_key}"

        cached_response = cache.get(cache_key)
        if cached_response:
            return JsonResponse(
                data=cached_response["data"],
                status=cached_response["status"],
                headers={"X-Cache-Lookup": "HIT-IDEMPOTENT"},
            )

        acquired_lock = cache.add(lock_key, "IN_PROGRESS", timeout=30)
        if not acquired_lock:
            return JsonResponse(
                data={
                    "error": "Transacción en proceso.",
                    "detalle": "Existe una petición idéntica procesándose en este momento. Reintente en unos segundos.",
                },
                status=409,
            )

        try:
            response = self.get_response(request)

            if 200 <= response.status_code < 500:
                try:
                    response_data = json.loads(response.content.decode("utf-8"))
                except:
                    response_data = {
                        "raw_content": response.content.decode("utf-8", errors="ignore")
                    }

                payload_to_cache = {
                    "data": response_data,
                    "status": response.status_code,
                }
                cache.set(cache_key, payload_to_cache, timeout=self.CACHE_TTL_SECONDS)

            return response
        finally:
            cache.delete(lock_key)
