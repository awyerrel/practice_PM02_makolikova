class DomainError(Exception):
    pass

class ValidationError(DomainError):
    pass

class NotFoundError(DomainError):
    pass

class RouteNotFoundError(NotFoundError):
    pass

class HotelNotFoundError(NotFoundError):
    pass

class CalculationError(DomainError):
    pass

class ZeroSpeedError(CalculationError):
    pass

class APIConnectionError(DomainError):
    pass