class MillyException(Exception):
    def __init__(self, detail: str | None = None):
        self.detail = detail

    status = 500
    msg = "Unknown error"


class ServiceException(MillyException):
    status = 500
    msg = "Service Exception"


class ClientException(MillyException):
    status = 400
    msg = "Client error"


class InvalidParameter(ClientException):
    msg = "Invalid parameter"


class ValueNotFound(ClientException):
    msg = "Value not found"


class ValidationFailed(ClientException):
    msg = "Validation failed"


class Unauthorized(ClientException):
    status = 401
    msg = "Unauthorized"


class ArgumentMissingException(ClientException):
    msg = "Argument missing"


class NoMorePage(ClientException):
    msg = "No more page"


class Duplicated(ClientException):
    msg = "Duplicated"


class NotFound(ClientException):
    msg = "NotFound"


class DBOptimisticLockError(ServiceException):
    msg = "DB Insert Conflict Error"


class ParameterRequired(InvalidParameter):
    msg = "Parameter required"


class Unauthenticated(ClientException):
    status = 401
    msg = "Unauthenticated"
