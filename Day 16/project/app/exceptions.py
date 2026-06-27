class EntityNotFoundException(Exception):
    """Выбрасывается, если сущность не найдена."""

    pass


class DeliveryCalculationException(Exception):
    """Ошибка расчета стоимости доставки."""

    pass