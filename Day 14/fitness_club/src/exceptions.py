class ValidationError(Exception):
    pass


class ClientNotFound(Exception):
    pass


class MembershipExpired(Exception):
    pass


class MembershipFrozen(Exception):
    pass


class WorkoutFull(Exception):
    pass


class MembershipNotFound(Exception):
    pass