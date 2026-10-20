import time
import random
import logging
from typing import Callable, Any, Type, Tuple
from pagos.services.gateway import PasarelaRedExcepcion

logger = logging.getLogger(__name__)


def ejecutar_con_reintentos(
    func: Callable[..., Any],
    *args,
    excepciones_reintentables: Tuple[Type[Exception], ...] = (PasarelaRedExcepcion,),
    max_reintentos: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
    **kwargs,
) -> Any:
    intento = 0
    while True:
        try:
            return func(*args, **kwargs)
        except excepciones_reintentables as exc:
            intento += 1
            if intento > max_reintentos:
                logger.error(
                    f"Se agotaron los {max_reintentos} reintentos contra la pasarela. Fallo final: {str(exc)}."
                )
                raise exc

            exp_delay = min(max_delay, base_delay * (2 ** (intento - 1)))
            jitter = random.uniform(0, 0.2 * exp_delay)
            total_delay = exp_delay + jitter

            logger.warning(
                f"Intento {intento}/{max_reintentos} falló por '{str(exc)}'."
                f"Reintentando en {total_delay:.2f} segundos..."
            )
            time.sleep(total_delay)
